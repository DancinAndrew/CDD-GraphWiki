"""
Deletion tests for the LLM's quoted evidence, mirroring the tests run on the rules' reasons.

    PYTHONPATH=backend python -m src.heldout.llm_compare run --set uk_mlr_2017 --evidence   # labels with quotes
    PYTHONPATH=backend python -m src.heldout.llm_faithfulness run --set uk_mlr_2017          # calls the model
    PYTHONPATH=backend python -m src.heldout.llm_faithfulness score                          # offline

The heldout-v2-evidence run gives, for every (clause, type) it labels, the words that it says show the type.
For every such label with at least one quote found in the paragraph, two perturbed copies of the paragraph are
sent with the same prompt:

- deletion (comprehensiveness): every occurrence of every located quote of the label, anywhere in the paragraph,
  becomes one space. Passes iff the answer no longer gives the label. This is harsher than the rules' test, which
  removes only the located spans: a quote that occurs more than once loses every occurrence (the report counts
  such labels, and coverage counts every deleted occurrence).
- rationale-only (sufficiency): each clause line keeps only the located quotes that fall in it. Passes iff the
  answer still gives the label.

Quotes match whole words only: a quote that starts or ends with a letter or digit must not continue a word of the
text there ("on" does not match inside "person").

Failed requests, and answers that are not JSON or not in the requested shape (an entry that is not an object,
lacks clause_id or type, or cites a clause ID that was not sent), are counted on their own and never as passes or
failures. Coverage (deleted characters over the characters of the clauses they touch plus the labelled clause)
shows whether a label passes by quoting whole clauses. Answers are cached in data/heldout/llm_runs/<set>/faithfulness/<slug>_evidence.jsonl; `run` resumes
from that cache and `score` needs no model.
"""
import os
import sys
import json
import time
import argparse
import statistics
from typing import Any, Collection, Dict, List, Optional, Sequence, Tuple

import httpx

from src.paths import find_data_dir
from src.heldout.evaluate import HELDOUT_SETS, HeldOutCorpus, load_corpus, results_dir
from src.heldout import llm_compare
from src.heldout.llm_compare import (
    clause_lines, DEFAULT_MODEL, DEFAULT_BASE_URL, EVIDENCE_SUFFIX, PROMPT_VERSION_EVIDENCE, SEED,
)

TESTS = ("deletion", "rationale_only")
Span = Tuple[int, int]  # [start, end) in a clause text as sent

# typographic characters the model may swap for plain ones (or the reverse) when it copies a quote
_FOLD = {**{c: "'" for c in "‘’‚‛′`"}, **{c: '"' for c in "“”„‟″"},
         **{c: "-" for c in "–—‐‑‒−―"}, " ": " ", " ": " ", " ": " "}


# --- quote location -------------------------------------------------------------------------------------------

def normalise(text: str) -> Tuple[str, List[int]]:
    """Lower case, plain quotes and dashes, whitespace runs as one space; with the original index of each character."""
    out: List[str] = []
    index: List[int] = []
    for i, ch in enumerate(text):
        ch = _FOLD.get(ch, ch)
        if ch.isspace():
            if out and out[-1] == " ":
                continue
            ch = " "
        for low in ch.lower():
            out.append(low)
            index.append(i)
    return "".join(out), index


def _norm_quote(quote: str) -> str:
    return normalise(quote)[0].strip()


def find_all(quote: str, text: str) -> List[Span]:
    """
    Every non-overlapping whole-word occurrence of the quote in the text, as spans of the original text: where the
    quote starts (ends) with a letter or digit, the text must not have one just before (after) the match.
    """
    needle = _norm_quote(quote)
    if not needle:
        return []
    hay, index = normalise(text)
    spans, start = [], 0
    while True:
        at = hay.find(needle, start)
        if at == -1:
            return spans
        end = at + len(needle)
        if ((needle[0].isalnum() and at > 0 and hay[at - 1].isalnum())
                or (needle[-1].isalnum() and end < len(hay) and hay[end].isalnum())):
            start = at + 1  # inside a word: look further on
            continue
        spans.append((index[at], index[end - 1] + 1))
        start = end


def locate(quote: str, clauses: Sequence[Tuple[str, str]], clause_id: str) -> Optional[Tuple[str, Span]]:
    """First occurrence of the quote: in the labelled clause if there, else in the paragraph's other clauses in order."""
    order = [c for c in clauses if c[0] == clause_id] + [c for c in clauses if c[0] != clause_id]
    for cid, text in order:
        spans = find_all(quote, text)
        if spans:
            return cid, spans[0]
    return None


def _merge(spans: List[Span]) -> List[Span]:
    merged: List[List[int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(s, e) for s, e in merged]


# --- perturbations --------------------------------------------------------------------------------------------

def deletion_spans(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str]) -> Dict[str, List[Span]]:
    """Every occurrence of every quote, by clause (overlaps merged); clauses without one are left out."""
    spans = {cid: _merge([s for q in quotes for s in find_all(q, text)]) for cid, text in clauses}
    return {cid: s for cid, s in spans.items() if s}


def deletion_text(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str]) -> str:
    """Every occurrence of every quote, in every clause, replaced by one space."""
    deleted = deletion_spans(clauses, quotes)
    out = []
    for cid, text in clauses:
        for start, end in reversed(deleted.get(cid, [])):
            text = text[:start] + " " + text[end:]
        out.append((cid, text))
    return clause_lines(out)


def rationale_spans(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str],
                    clause_id: str) -> Dict[str, List[Span]]:
    """The first located occurrence of each quote, grouped by clause (overlaps merged)."""
    spans: Dict[str, List[Span]] = {}
    for q in quotes:
        found = locate(q, clauses, clause_id)
        if found:
            spans.setdefault(found[0], []).append(found[1])
    return {cid: _merge(s) for cid, s in spans.items()}


def rationale_only_text(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str], clause_id: str) -> str:
    """Each clause keeps only the located quotes that fall in it, joined by spaces; the others become empty."""
    spans = rationale_spans(clauses, quotes, clause_id)
    return clause_lines([(cid, " ".join(text[s:e] for s, e in spans.get(cid, []))) for cid, text in clauses])


def repeated_quotes(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str]) -> List[str]:
    """The quotes that occur more than once in the paragraph (the deletion test removes every occurrence)."""
    return [q for q in quotes if sum(len(find_all(q, text)) for _, text in clauses) > 1]


def coverage(clauses: Sequence[Tuple[str, str]], quotes: Sequence[str], clause_id: str) -> float:
    """
    Deleted characters (every occurrence of every quote, as the deletion test removes them) / characters of the
    clause texts they touch plus the labelled clause.
    """
    spans = deletion_spans(clauses, quotes)
    touched = set(spans) | {clause_id}
    total = sum(len(text) for cid, text in clauses if cid in touched)
    kept = sum(e - s for ss in spans.values() for s, e in ss)
    return kept / total if total else 0.0


# --- the labels under test ------------------------------------------------------------------------------------

def evidence_category(given: int, located: int) -> str:
    if given == 0:
        return "no_evidence"
    if located == given:
        return "all_located"
    return "none_located" if located == 0 else "some_located"


def label_items(corpus: HeldOutCorpus, runs: str) -> List[Dict[str, Any]]:
    """
    Every predicted (clause_id, type) of the evidence run, in paragraph and clause order, with its quotes, which
    of them were found, and the two perturbed paragraphs (only for labels with at least one located quote).
    """
    loaded = llm_compare.load_answers(runs, corpus)
    evidence = loaded["evidence"]
    units = {u["paragraph"]: u for u in llm_compare.paragraph_units(corpus)}
    items = []
    for paragraph, unit in units.items():
        clauses = unit["clauses"]  # the clause texts exactly as sent, without the "[id] " prefix
        for clause_id in unit["clause_ids"]:
            for t in corpus.types:
                if (clause_id, t) not in evidence:
                    continue
                quotes = evidence[(clause_id, t)]
                located = [q for q in quotes if locate(q, clauses, clause_id)]
                item = {"paragraph": paragraph, "clause_id": clause_id, "type": t, "quotes": quotes,
                        "located": located, "category": evidence_category(len(quotes), len(located))}
                if located:
                    item["perturbed"] = {"deletion": deletion_text(clauses, located),
                                         "rationale_only": rationale_only_text(clauses, located, clause_id)}
                    item["coverage"] = coverage(clauses, located, clause_id)
                    item["repeated_quotes"] = repeated_quotes(clauses, located)
                items.append(item)
    return items


def perturbed_prompt(system: str, corpus: HeldOutCorpus, item: Dict[str, Any], test: str) -> Tuple[str, str]:
    """The user prompt for one test (same paragraph header as the run) and the SHA-256 of system + user."""
    user = llm_compare.user_prompt(corpus, item["paragraph"], item["perturbed"][test])
    return user, llm_compare.prompt_sha256(system, user)


def _key(record: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return record["paragraph"], record["clause_id"], record["type"], record["test"]


def read_cache(path: str) -> Dict[Tuple[str, str, str, str], Dict[str, Any]]:
    """
    The last record per (paragraph, clause_id, type, test). A line that is not JSON (cut off while a run was
    writing it) is skipped with a message, so that test counts as not run.
    """
    cache: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    print(f"{path}: skipping line {n}, not valid JSON (partially written?)", file=sys.stderr)
                    continue
                cache[_key(record)] = record
    return cache


def default_runs(data_dir: str, set_name: str, model: str) -> str:
    return llm_compare.runs_path(data_dir, set_name, model, EVIDENCE_SUFFIX)


def default_cache(data_dir: str, set_name: str, model: str) -> str:
    return os.path.join(data_dir, "heldout", "llm_runs", set_name, "faithfulness",
                        f"{llm_compare.model_slug(model)}{EVIDENCE_SUFFIX}.jsonl")


# --- run (calls the model) ------------------------------------------------------------------------------------

def run(data_dir: str, set_name: str, model: str, base_url: str, runs: str, cache_path: str,
        limit: Optional[int] = None) -> None:
    """Send the perturbed paragraphs of the first `limit` testable labels; skip those already answered."""
    conn = llm_compare.endpoint(base_url, data_dir)
    corpus = load_corpus(data_dir, set_name)
    system = llm_compare.system_prompt(data_dir, corpus, evidence=True)
    items = [i for i in label_items(corpus, runs) if i["located"]]
    items = items[:limit] if limit else items
    cache = read_cache(cache_path)
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:  # rewrite the cache with one record per key, then append
        for record in cache.values():
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    todo = [(item, test) for item in items for test in TESTS]
    with open(cache_path, "a", encoding="utf-8") as out, httpx.Client(timeout=600) as client:
        for n, (item, test) in enumerate(todo, 1):
            user, sha = perturbed_prompt(system, corpus, item, test)
            key = (item["paragraph"], item["clause_id"], item["type"], test)
            old = cache.get(key)
            if old and "response" in old and old.get("perturbed_sha256") == sha and old.get("model") == model:
                continue
            record: Dict[str, Any] = {
                "paragraph": item["paragraph"], "clause_id": item["clause_id"], "type": item["type"], "test": test,
                "perturbed_sha256": sha, "model": model, "prompt_version": PROMPT_VERSION_EVIDENCE,
                "seed": SEED, "temperature": 0.0, "base_url": base_url,
            }
            if any(host in base_url for host in ("localhost", "127.0.0.1")):
                record["thinking"] = False  # Ollama's native API with reasoning mode off, as in llm_compare
                record["num_predict"] = llm_compare.MAX_NEW_TOKENS
            started = time.monotonic()
            record.update(llm_compare.chat(client, model, base_url, conn, system, user))
            record["seconds"] = round(time.monotonic() - started, 2)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{n}/{len(todo)}] {item['clause_id']} {item['type']} {test}: "
                  f"{llm_compare.request_status(record)} ({record['seconds']:.1f} s)")


# --- score (offline) ------------------------------------------------------------------------------------------

def answer_problem(response: str, clause_ids: Collection[str],
                   types: Optional[Collection[str]] = None) -> Optional[str]:
    """
    Why the answer cannot be scored, or None if it can: it must be JSON, an object whose "labels" is a list, and
    every entry an object with a clause_id among the paragraph's clause_ids and a "type" or "types" key whose
    values are type names (one of `types`, when given). An answer in a drifted shape must count neither as
    "the label disappeared" nor as "the label is still there".
    """
    try:
        parsed = llm_compare.parse_answer(response)
    except ValueError:  # includes json.JSONDecodeError
        return "answer is not valid JSON"
    if not isinstance(parsed, dict) or not isinstance(parsed.get("labels"), list):
        return 'answer is not an object with a "labels" list'
    for entry in parsed["labels"]:
        if not isinstance(entry, dict):
            return f"an entry is not an object: {json.dumps(entry, ensure_ascii=False)[:80]}"
        if "clause_id" not in entry:
            return f"an entry has no clause_id: {json.dumps(entry, ensure_ascii=False)[:80]}"
        if "type" not in entry and "types" not in entry:
            return f"an entry has no type: {json.dumps(entry, ensure_ascii=False)[:80]}"
        if str(entry["clause_id"]) not in clause_ids:
            return f"cites a clause ID that was not sent: {entry['clause_id']}"
        given = entry["types"] if "types" in entry else entry["type"]
        names = given if isinstance(given, list) else [given]
        if not names or any(not isinstance(n, str) or (types is not None and n not in types) for n in names):
            return f"an entry has a missing or unknown type: {json.dumps(entry, ensure_ascii=False)[:80]}"
    return None


def answer_types(response: str, clause_id: str, clause_ids: Collection[str],
                 types: Optional[Collection[str]] = None) -> Optional[List[str]]:
    """
    The types the answer gives the clause, or None if the answer cannot be scored (see answer_problem):
    such an answer is counted on its own, never as a pass or a failure.
    """
    if answer_problem(response, clause_ids, types) is not None:
        return None
    labels = llm_compare.answer_labels(response)
    return sorted({str(t) for label in labels if label["clause_id"] == clause_id for t in label["types"]})


def _ratio(k: int, n: int) -> Dict[str, Any]:
    return {"passed": k, "tested": n, "rate": round(k / n, 4) if n else None}


def score(data_dir: str, corpus: HeldOutCorpus, runs: str, cache_path: str) -> Optional[Dict[str, Any]]:
    """
    Faithfulness of the evidence run's quotes, from the two caches; needs no model. A cached answer counts only if
    it was given for exactly the perturbed prompt rebuilt here (same SHA-256); otherwise the test is "not run".
    None (with a message) if the runs file is empty or partially written.
    """
    try:
        first = llm_compare.read_records(runs)[0]
    except llm_compare.RunsFileError as e:
        print(f"skipping {runs}: {e}", file=sys.stderr)
        return None
    system = llm_compare.system_prompt(data_dir, corpus, evidence=True)
    items = label_items(corpus, runs)
    cache = read_cache(cache_path)
    clause_ids = {u["paragraph"]: set(u["clause_ids"]) for u in llm_compare.paragraph_units(corpus)}
    used: List[Dict[str, Any]] = []  # the cached records that match a test here
    outcome: Dict[Tuple[str, str, str], Dict[str, Any]] = {}  # (clause, type, test) -> result
    failures, request_failures = [], []
    for item in items:
        if not item["located"]:
            continue
        for test in TESTS:
            key = (item["paragraph"], item["clause_id"], item["type"], test)
            record = cache.get(key)
            result: Dict[str, Any]
            if (record is None or record.get("model") != first["model"]
                    or record.get("perturbed_sha256") != perturbed_prompt(system, corpus, item, test)[1]):
                outcome[(item["clause_id"], item["type"], test)] = {"status": "not_run"}  # none for this prompt/model
                continue
            used.append(record)
            ids = clause_ids[item["paragraph"]]
            types = None if "error" in record else answer_types(record["response"], item["clause_id"], ids, corpus.types)
            if types is None:  # failed, not JSON or off-format: neither a pass nor a failure
                result = {"status": "failed_request" if "error" in record else "unparseable"}
                request_failures.append({"clause_id": item["clause_id"], "type": item["type"], "test": test,
                                         "error": record.get("error") or answer_problem(record["response"], ids, corpus.types)})
            else:
                present = item["type"] in types
                passed = not present if test == "deletion" else present
                result = {"status": "passed" if passed else "failed", "answer_types": types}
                if not passed:
                    failures.append({"paragraph": item["paragraph"], "clause_id": item["clause_id"],
                                     "type": item["type"], "test": test, "quotes": item["located"],
                                     "answer_types": types})
            outcome[(item["clause_id"], item["type"], test)] = result
    return _summarise(corpus, first, items, outcome, failures, request_failures, used)


def _counts(items: List[Dict[str, Any]], outcome: Dict[Tuple[str, str, str], Dict[str, Any]]) -> Dict[str, Any]:
    tested = [i for i in items if i["located"]]
    result: Dict[str, Any] = {"labels": len(items), "labels_tested": len(tested)}
    for test in TESTS:
        got = [outcome[(i["clause_id"], i["type"], test)]["status"] for i in tested]
        answered = [s for s in got if s in ("passed", "failed")]
        result[test] = {**_ratio(got.count("passed"), len(answered)),
                        "failed_requests": got.count("failed_request"), "unparseable": got.count("unparseable"),
                        "not_run": got.count("not_run")}
    both_answered = [i for i in tested
                     if all(outcome[(i["clause_id"], i["type"], t)]["status"] in ("passed", "failed") for t in TESTS)]
    both_passed = [i for i in both_answered
                   if all(outcome[(i["clause_id"], i["type"], t)]["status"] == "passed" for t in TESTS)]
    result["both"] = _ratio(len(both_passed), len(both_answered))
    return result


def _summarise(corpus: HeldOutCorpus, first: Dict[str, Any], items: List[Dict[str, Any]],
               outcome: Dict[Tuple[str, str, str], Dict[str, Any]], failures: List[Dict[str, Any]],
               request_failures: List[Dict[str, Any]], used: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories = {c: 0 for c in ("all_located", "some_located", "none_located", "no_evidence")}
    for item in items:
        categories[item["category"]] += 1
    covers = [i["coverage"] for i in items if i["located"]]
    summary: Dict[str, Any] = {
        "set": corpus.spec.name, "model": first.get("model"), "prompt_version": first.get("prompt_version"),
        "evidence": {"quotes_given": sum(len(i["quotes"]) for i in items),
                     "quotes_located": sum(len(i["located"]) for i in items),
                     "labels_by_category": categories,
                     "labels_with_repeated_quotes": sum(1 for i in items if i.get("repeated_quotes"))},
        **_counts(items, outcome),
        "coverage": {"mean": round(statistics.mean(covers), 4) if covers else None,
                     "median": round(statistics.median(covers), 4) if covers else None},
        "generation": llm_compare.generation_stats(used),
        "by_type": {},
        "failures": failures,
        "request_failures": request_failures,
    }
    for t in corpus.types:
        of_type = [i for i in items if i["type"] == t]
        if of_type:
            summary["by_type"][t] = _counts(of_type, outcome)
    return summary


def format_report(summary: Dict[str, Any], title: str) -> str:
    def line(name: str, r: Dict[str, Any]) -> str:
        extra = [f"{r[k]} {k.replace('_', ' ')}" for k in ("failed_requests", "unparseable", "not_run") if r.get(k)]
        return f"{name}: {r['passed']}/{r['tested']} passed" + (f" ({', '.join(extra)})" if extra else "")

    e = summary["evidence"]
    head = f"Faithfulness of the quoted evidence of {summary['model']} on held-out {title} paragraphs"
    lines = [head, "=" * len(head), "",
             f"Prompt {summary['prompt_version']}: the model labels each clause and quotes the words that show the type.",
             "Deletion: every whole-word occurrence of the label's located quotes becomes a space; passes iff the label "
             "disappears.",
             "Rationale-only: each clause keeps only the located quotes in it; passes iff the label stays.",
             "Failed requests and answers not in the requested shape (not JSON, an entry without clause_id or type, a "
             "clause ID that was not sent) are counted on their own, never as passes or failures.", "",
             f"Labels: {summary['labels']}; quotes given {e['quotes_given']}, found in the paragraph {e['quotes_located']}.",
             "Labels by evidence: " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in e["labels_by_category"].items()),
             f"Labels tested (at least one quote found): {summary['labels_tested']}; with a quote that occurs more "
             f"than once in the paragraph (every occurrence deleted): {e['labels_with_repeated_quotes']}",
             "  " + line("Deletion", summary["deletion"]),
             "  " + line("Rationale-only", summary["rationale_only"]),
             "  " + line("Both", summary["both"])]
    c = summary["coverage"]
    if c["mean"] is not None:
        lines.append(f"  Coverage (deleted characters / characters of the clauses they touch): "
                     f"mean {c['mean']:.2f}, median {c['median']:.2f}")
    lines.append("  " + llm_compare.format_generation(summary["generation"]))
    lines += ["", "By type:"]
    for t, r in summary["by_type"].items():
        lines.append(f"  {t:<20} labels {r['labels']}, tested {r['labels_tested']}; deletion "
                     f"{r['deletion']['passed']}/{r['deletion']['tested']}, rationale-only "
                     f"{r['rationale_only']['passed']}/{r['rationale_only']['tested']}, both "
                     f"{r['both']['passed']}/{r['both']['tested']}")
    lines += ["", f"Failures ({len(summary['failures'])}):"]
    for f in summary["failures"]:
        lines.append(f"- {f['paragraph']:<7} {f['clause_id']} {f['type']} {f['test']}: answer gives "
                     f"[{', '.join(f['answer_types'])}]")
        lines.append("    quotes: " + " | ".join(f"\"{q}\"" for q in f["quotes"]))
    if summary["request_failures"]:
        lines += ["", f"Requests without a usable answer ({len(summary['request_failures'])}):"]
        for f in summary["request_failures"]:
            lines.append(f"- {f['clause_id']} {f['type']} {f['test']}: {f['error']}")
    return "\n".join(lines) + "\n"


def score_files(data_dir: str, set_name: str, runs: str, cache_path: str, out_dir: str) -> Optional[Dict[str, Any]]:
    """Score into out_dir; None (nothing written) if the runs file is empty or partially written."""
    corpus = load_corpus(data_dir, set_name)
    summary = score(data_dir, corpus, runs, cache_path)
    if summary is None:
        return None
    slug = os.path.splitext(os.path.basename(runs))[0]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"llm_{slug}_faithfulness.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out_dir, f"llm_{slug}_faithfulness.txt"), "w", encoding="utf-8") as f:
        f.write(format_report(summary, corpus.spec.title))
    return summary


def score_all(data_dir: str, model: str = DEFAULT_MODEL, out_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Every held-out set that has both the evidence run and the faithfulness cache; results go to
    data/heldout/results/<set>, or to <out_dir>/<set> when out_dir is given.
    """
    summaries = {}
    for set_name in HELDOUT_SETS:
        runs, cache = default_runs(data_dir, set_name, model), default_cache(data_dir, set_name, model)
        if os.path.exists(runs) and os.path.exists(cache):
            target = os.path.join(out_dir, set_name) if out_dir else results_dir(data_dir, set_name)
            summary = score_files(data_dir, set_name, runs, cache, target)
            if summary is not None:
                summaries[set_name] = summary
    return summaries


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="Deletion tests for the LLM's quoted evidence on held-out text")
    parser.add_argument("command", choices=["run", "score"])
    parser.add_argument("--set", default=None, choices=sorted(HELDOUT_SETS))
    parser.add_argument("--model", default=os.getenv("HELDOUT_LLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.getenv("HELDOUT_LLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--limit", type=int, default=None, help="run: only the first N testable labels")
    parser.add_argument("--runs", default=None, help="evidence run to test (default: the cached <model>_evidence.jsonl)")
    parser.add_argument("--cache", default=None, help="faithfulness answers (default: llm_runs/<set>/faithfulness/)")
    parser.add_argument("--out", default=None, help="score: result folder (default: data/heldout/results/<set>; "
                                                    "without --runs or --cache: <out>/<set>)")
    args = parser.parse_args()
    if args.command == "run" or args.runs or args.cache:
        if not args.set:
            parser.error("--set is needed with run, --runs or --cache")
        runs = args.runs or default_runs(data_dir, args.set, args.model)
        cache = args.cache or default_cache(data_dir, args.set, args.model)
        if args.command == "run":
            run(data_dir, args.set, args.model, args.base_url, runs, cache, args.limit)
        # results of a non-default run or cache (a smoke test) go next to its cache, not into the committed results
        custom = bool(args.runs or args.cache)
        out = args.out or (os.path.dirname(os.path.abspath(cache)) if custom else results_dir(data_dir, args.set))
        summary = score_files(data_dir, args.set, runs, cache, out)
        summaries = {args.set: summary} if summary is not None else {}
    else:
        summaries = score_all(data_dir, args.model, args.out)
    for set_name, s in summaries.items():
        print(f"{set_name:<16} labels {s['labels']}, tested {s['labels_tested']} | deletion "
              f"{s['deletion']['passed']}/{s['deletion']['tested']}, rationale-only "
              f"{s['rationale_only']['passed']}/{s['rationale_only']['tested']}, both "
              f"{s['both']['passed']}/{s['both']['tested']} | coverage mean {s['coverage']['mean']}")


if __name__ == "__main__":
    main()
