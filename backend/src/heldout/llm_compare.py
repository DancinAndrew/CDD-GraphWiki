"""
Run an LLM extractor on the same held-out paragraphs as the rules and score it the same way.

    ollama pull qwen3.5:9b
    PYTHONPATH=backend python -m src.heldout.llm_compare run --set uk_mlr_2017   # calls the model
    PYTHONPATH=backend python -m src.heldout.llm_compare run --set uk_mlr_2017 --evidence   # labels with quotes
    PYTHONPATH=backend python -m src.heldout.llm_compare score                   # offline: scores every cached run

`run` sends one held-out paragraph per request, with the task definition taken from
data/heldout/ANNOTATION_GUIDELINE.md, and stores every raw answer in data/heldout/llm_runs/<set>/<model>.jsonl.
The default model is the open-weight qwen3.5:9b served locally by Ollama (temperature 0, fixed seed), so the
run needs no API key. Any OpenAI-compatible endpoint works through --base-url and --model; a remote endpoint
reads its key from NVIDIA_API_KEY. There is no mock fallback: a failed request is recorded as a failure and
counted as "no types". `score` needs no model, so anyone can recompute the numbers from the cached answers.

Two prompt versions share the same task definition. "heldout-v1" (the headline comparison) asks for labels only.
"heldout-v2-evidence" (`run --evidence`, cached as <model>_evidence.jsonl) asks for one entry per clause and type
with the exact words that show the type; src/heldout/llm_faithfulness.py then tests whether the answer depends on
those words. Every scored run also reports how it agrees with rules v2 on the same text (trust tiers).
"""
import os
import re
import sys
import json
import time
import hashlib
import argparse
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from src.paths import find_data_dir
from src.heldout.evaluate import (
    HELDOUT_SETS, HeldOutCorpus, load_corpus, score, corpus_stats, error_rows, format_report, results_dir,
    rules_v2_predictions,
)

DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Ollama's OpenAI-compatible endpoint
SEED = 7
PROMPT_VERSION = "heldout-v1"
PROMPT_VERSION_EVIDENCE = "heldout-v2-evidence"
EVIDENCE_SUFFIX = "_evidence"

SYSTEM_PROMPT = """You annotate clauses of {title} ({description}) with obligation types.

{guideline}

Answer with JSON only, in this form:
{{"labels": [{{"clause_id": "<an id from the input>", "types": ["<type>", ...]}}]}}
List only clauses that have at least one type. Use only the eight type names above. If no clause has a type, answer {{"labels": []}}."""

# Same task text as heldout-v1; only the answer format differs: one entry per clause and type, with quotes.
SYSTEM_PROMPT_EVIDENCE = """You annotate clauses of {title} ({description}) with obligation types.

{guideline}

Answer with JSON only, in this form:
{{"labels": [{{"clause_id": "<an id from the input>", "type": "<type>", "evidence": ["<words copied exactly from the input>", ...]}}]}}
Give one entry per clause and type. In "evidence", give the shortest exact quotes from the paragraph text (the clause itself or its lead-in) that show the clause has this type, copied character for character.
List only clauses that have at least one type. Use only the eight type names above. If no clause has a type, answer {{"labels": []}}."""

USER_PROMPT = """Paragraph {paragraph} of {title}. Each line is one clause: its id in square brackets, then its text.

{clauses}"""


def guideline_text(data_dir: str) -> str:
    """The parts of the annotation guideline that define the task (everything from 'Unit of annotation' on)."""
    with open(os.path.join(data_dir, "heldout", "ANNOTATION_GUIDELINE.md"), encoding="utf-8") as f:
        text = f.read()
    start = text.index("## Unit of annotation")
    end = text.index("## Paragraph-level view")
    return text[start:end].strip()


def paragraph_units(corpus: HeldOutCorpus) -> List[Dict[str, Any]]:
    units: Dict[str, List] = {}
    for clause in corpus.held_out:
        units.setdefault(corpus.paragraph_of[clause.clause_id], []).append(clause)
    out = []
    for paragraph, clauses in units.items():
        # (clause_id, text as sent): the "### 6.14A" heading marker dropped; a text may span several lines
        texts = [(c.clause_id, re.sub(r"^#+\s*\S+\s*", "", c.raw_text).strip()) for c in clauses]
        out.append({"paragraph": paragraph, "clause_ids": [c.clause_id for c in clauses],
                    "text": clause_lines(texts), "clauses": texts})
    return out


def clause_lines(texts: List[Tuple[str, str]]) -> str:
    """The clauses as sent in the prompt: one "[id] text" entry per clause."""
    return "\n".join(f"[{clause_id}] {text}" for clause_id, text in texts)


def _load_env_key(repo_root: str, name: str) -> Optional[str]:
    if os.getenv(name):
        return os.getenv(name)
    env_path = os.path.join(repo_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def system_prompt(data_dir: str, corpus: HeldOutCorpus, evidence: bool = False) -> str:
    template = SYSTEM_PROMPT_EVIDENCE if evidence else SYSTEM_PROMPT
    return template.format(title=corpus.spec.title, description=corpus.spec.description,
                           guideline=guideline_text(data_dir))


def user_prompt(corpus: HeldOutCorpus, paragraph: str, clauses_text: str) -> str:
    return USER_PROMPT.format(paragraph=paragraph, title=corpus.spec.title, clauses=clauses_text)


def prompt_sha256(system: str, user: str) -> str:
    return hashlib.sha256((system + "\n" + user).encode("utf-8")).hexdigest()


def endpoint(base_url: str, data_dir: str) -> Dict[str, Any]:
    """Whether the endpoint is a local Ollama server, and the API key to use."""
    local = any(host in base_url for host in ("localhost", "127.0.0.1"))
    api_key = "ollama" if local else _load_env_key(os.path.dirname(os.path.abspath(data_dir)), "NVIDIA_API_KEY")
    if not api_key:
        sys.exit("NVIDIA_API_KEY is not set for a remote endpoint; `score` works without it on the cached answers.")
    return {"local": local, "api_key": api_key}


# Ollama's JSON mode (mlx runner) sometimes keeps emitting newlines after the JSON object is complete, until the
# context window is full; one paragraph took 20 minutes that way. The cap bounds that tail, but it can also cut a
# real answer short: in the evidence run the model looped through the eight types three times on 34(3) and hit the
# cap after 8,419 characters, so that answer is not valid JSON. New records keep Ollama's stop reason
# ("done_reason" "length" = cut by the cap) and token count, the log prints "truncated" for them, and the scored
# summary counts them (see generation_stats).
MAX_NEW_TOKENS = 2048


def chat(client: httpx.Client, model: str, base_url: str, conn: Dict[str, Any], system: str, user: str) -> Dict[str, Any]:
    """
    One request with up to three attempts: {"response": text, "done_reason", "eval_count"} or {"error": message},
    never a mock answer. done_reason is "length" when the answer was cut by the output cap; eval_count is the
    number of tokens generated (the OpenAI-compatible endpoint's finish_reason and completion_tokens).
    """
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    result: Dict[str, Any] = {}
    for attempt in range(3):
        try:
            if conn["local"]:
                # Ollama's native API, so the model's reasoning mode can be switched off and JSON enforced.
                response = client.post(
                    base_url.replace("/v1", "") + "/api/chat",
                    json={"model": model, "stream": False, "think": False, "format": "json",
                          "options": {"temperature": 0, "seed": SEED, "num_ctx": 8192,
                                      "num_predict": MAX_NEW_TOKENS},
                          "messages": messages},
                )
                response.raise_for_status()
                body = response.json()
                return _answer(body["message"]["content"], body.get("done_reason"), body.get("eval_count"))
            response = client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {conn['api_key']}", "Accept": "application/json"},
                json={"model": model, "temperature": 0.0, "seed": SEED, "max_tokens": 4096,
                      "messages": messages},
            )
            response.raise_for_status()
            body = response.json()
            choice = body["choices"][0]
            return _answer(choice["message"]["content"], choice.get("finish_reason"),
                           (body.get("usage") or {}).get("completion_tokens"))
        except Exception as e:  # recorded, never replaced by a mock answer
            result = {"error": f"{type(e).__name__}: {str(e)[:200]}"}
            time.sleep(2 * (attempt + 1))
    return result


def _answer(content: str, done_reason: Optional[str], eval_count: Optional[int]) -> Dict[str, Any]:
    answer: Dict[str, Any] = {"response": content}
    if done_reason is not None:
        answer["done_reason"] = done_reason
    if eval_count is not None:
        answer["eval_count"] = eval_count
    return answer


def request_status(record: Dict[str, Any]) -> str:
    """For the run log: "error", "truncated" (the answer hit the output cap) or "ok"."""
    if "error" in record:
        return "error"
    return "truncated" if record.get("done_reason") == "length" else "ok"


def parse_answer(content: str) -> Dict[str, Any]:
    """Pull the JSON object out of a model answer (models sometimes wrap it in prose or code fences)."""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.S)
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        raise ValueError("no JSON object in the answer")
    return json.loads(match.group(0))


class RunsFileError(ValueError):
    """A runs file that is empty or has a line that is not JSON (for example cut off by an interrupted write)."""


def read_records(path: str) -> List[Dict[str, Any]]:
    """Every record of a .jsonl runs file, blank lines skipped; RunsFileError if it is empty or not all JSON."""
    records = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise RunsFileError(f"line {n} is not valid JSON ({e}); the file may be partially written")
    if not records:
        raise RunsFileError("the file has no records")
    return records


def _cached(out_path: str, model: str) -> Dict[str, Dict[str, Any]]:
    """
    The records already in out_path or its .partial file (for --resume), by paragraph: the last answer from this
    model, else the last record. Only an answer for the same prompt and model is reused; the rest are asked again.
    """
    def usable(record: Dict[str, Any]) -> bool:
        return "response" in record and record.get("model") == model

    kept: Dict[str, Dict[str, Any]] = {}
    for path in (out_path, out_path + ".partial"):
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:  # a line cut off by an interrupted run: ask that paragraph again
                    continue
                old = kept.get(record["paragraph"])
                if usable(record) or old is None or not usable(old):
                    kept[record["paragraph"]] = record
    return kept


def run_model(data_dir: str, set_name: str, model: str, base_url: str, out_path: str,
              limit: Optional[int] = None, evidence: bool = False, resume: bool = False) -> None:
    """
    One request per held-out paragraph. With resume, answers already in out_path for exactly the same prompt and
    model are kept and only the rest are asked; the file is rewritten in paragraph order. With resume and limit,
    the records of paragraphs outside the first `limit` are kept as they were (resume match = prompt and model
    only, so a resumed file can mix generation settings; the scored summary shows how many records have each).
    """
    conn = endpoint(base_url, data_dir)
    corpus = load_corpus(data_dir, set_name)
    system = system_prompt(data_dir, corpus, evidence)
    all_units = paragraph_units(corpus)
    units = all_units[:limit] if limit else all_units
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    previous = _cached(out_path, model) if resume else {}
    if not resume and os.path.exists(out_path + ".partial"):
        os.remove(out_path + ".partial")
    records: Dict[str, Dict[str, Any]] = {}  # paragraph -> record, for the selected paragraphs
    with httpx.Client(timeout=600) as client:
        for i, unit in enumerate(units, 1):
            user = user_prompt(corpus, unit["paragraph"], unit["text"])
            old = previous.get(unit["paragraph"])
            if (old is not None and "response" in old and old.get("model") == model
                    and old.get("prompt_sha256") == prompt_sha256(system, user)):
                records[unit["paragraph"]] = old
                continue
            record: Dict[str, Any] = {
                "paragraph": unit["paragraph"], "model": model,
                "prompt_version": PROMPT_VERSION_EVIDENCE if evidence else PROMPT_VERSION,
                "prompt_sha256": prompt_sha256(system, user),
                "temperature": 0.0, "seed": SEED, "base_url": base_url,
            }
            if conn["local"]:
                record["thinking"] = False
                record["num_predict"] = MAX_NEW_TOKENS
            started = time.monotonic()
            record.update(chat(client, model, base_url, conn, system, user))
            record["seconds"] = round(time.monotonic() - started, 2)
            records[unit["paragraph"]] = record
            with open(out_path + ".partial", "a", encoding="utf-8") as partial:  # survives an interrupted run
                partial.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(units)}] {unit['paragraph']}: {request_status(record)} "
                  f"({record['seconds']:.1f} s)", flush=True)
    # every paragraph in corpus order: the new or reused record, else the one cached before (resume with limit);
    # cached records of paragraphs that are not in the corpus any more go last, in their old order
    order = [u["paragraph"] for u in all_units]
    known = set(order)
    order += [p for p in previous if p not in known]
    with open(out_path, "w", encoding="utf-8") as out:
        for paragraph in order:
            record = records.get(paragraph) or previous.get(paragraph)
            if record is not None:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
    if os.path.exists(out_path + ".partial"):
        os.remove(out_path + ".partial")


def _label_types(label: Dict[str, Any]) -> List[Any]:
    """The types of one answer entry: heldout-v1 gives "types": [...], heldout-v2-evidence gives "type": "..."."""
    if "types" in label:
        found = label.get("types") or []
    else:
        found = label.get("type")
    if found is None:
        return []
    return list(found) if isinstance(found, list) else [found]


def _label_evidence(label: Dict[str, Any]) -> List[str]:
    quotes = label.get("evidence") or []
    if isinstance(quotes, str):
        quotes = [quotes]
    return [q for q in quotes if isinstance(q, str)] if isinstance(quotes, list) else []


def answer_labels(content: str) -> List[Dict[str, Any]]:
    """The answer's entries as {"clause_id", "types", "evidence"}; raises ValueError if it is not JSON."""
    try:
        labels = parse_answer(content).get("labels", [])
    except json.JSONDecodeError as e:
        raise ValueError(str(e))
    out = []
    for label in labels if isinstance(labels, list) else []:
        if isinstance(label, dict):
            out.append({"clause_id": str(label.get("clause_id", "")), "types": _label_types(label),
                        "evidence": _label_evidence(label)})
    return out


def load_answers(path: str, corpus: HeldOutCorpus) -> Dict[str, Any]:
    """
    Turn cached answers into predictions, counting failures and citations of clause IDs that were not given.
    Also returns the quotes given for each predicted (clause_id, type) ("evidence"; empty for heldout-v1 answers).
    """
    units = {u["paragraph"]: set(u["clause_ids"]) for u in paragraph_units(corpus)}
    types = set(corpus.types)
    predictions: Dict[str, Set[str]] = {c.clause_id: set() for c in corpus.held_out}
    evidence: Dict[Tuple[str, str], List[str]] = {}
    stats = {"paragraphs_sent": 0, "failed_requests": 0, "unparseable_answers": 0,
             "cited_clause_ids": 0, "invalid_clause_ids": [], "invalid_type_names": []}
    seen_paragraphs: Set[str] = set()
    for record in read_records(path):
        seen_paragraphs.add(record["paragraph"])
        stats["paragraphs_sent"] += 1
        if "error" in record:
            stats["failed_requests"] += 1
            continue
        try:
            labels = answer_labels(record["response"])
        except ValueError:
            stats["unparseable_answers"] += 1
            continue
        given = units.get(record["paragraph"], set())
        for label in labels:
            clause_id = label["clause_id"]
            stats["cited_clause_ids"] += 1
            if clause_id not in given:
                stats["invalid_clause_ids"].append(f"{record['paragraph']}: {clause_id}")
                continue
            for t in label["types"]:
                if t in types:
                    predictions[clause_id].add(t)
                    evidence.setdefault((clause_id, t), []).extend(label["evidence"])
                else:
                    stats["invalid_type_names"].append(f"{record['paragraph']}: {t}")
    stats["paragraphs_missing_from_run"] = sorted(set(units) - seen_paragraphs)
    return {"predictions": predictions, "stats": stats, "evidence": evidence}


def generation_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    How the answers were generated: records with and without the output cap (num_predict; a resumed run can mix
    both), answers that are not valid JSON, and answers that hit the cap. Only records made since the stop reason
    is stored can show the cap was hit, so "hit_cap" is out of "with_done_reason".
    """
    answered = [r for r in records if "response" in r]
    invalid_json = 0
    for record in answered:
        try:
            answer_labels(record["response"])
        except ValueError:
            invalid_json += 1
    with_cap = sum(1 for r in records if "num_predict" in r)
    return {"records": len(records), "answers": len(answered), "with_num_predict": with_cap, "without_num_predict": len(records) - with_cap,
            "num_predict_values": sorted({r["num_predict"] for r in records if "num_predict" in r}),
            "invalid_json": invalid_json,
            "with_done_reason": sum(1 for r in answered if "done_reason" in r),
            "hit_cap": sum(1 for r in answered if r.get("done_reason") == "length")}


def format_generation(g: Dict[str, Any]) -> str:
    cap = ", ".join(str(v) for v in g["num_predict_values"])
    text = (f"Generation: {g['records']} records, {g['with_num_predict']} with an output cap"
            f"{f' (num_predict {cap})' if cap else ''}, {g['without_num_predict']} without"
            f"{' (mixed settings)' if g['with_num_predict'] and g['without_num_predict'] else ''}; "
            f"answers not valid JSON: {g['invalid_json']}; answers that hit the cap: {g['hit_cap']} of the "
            f"{g['with_done_reason']} that store the stop reason")
    missing = g["answers"] - g["with_done_reason"]
    return text + (f" (stop reason not stored for {missing})." if missing else ".")


# --- trust tiers: where the LLM and rules v2 agree ------------------------------------------------------------

AGREEMENT_NOTES = {
    "mas_notice_626": "Rules v2 were designed after studying their errors on this set, so the rules' side of "
                      "this comparison is not an unseen-data result.",
}


def agreement_with_rules(corpus: HeldOutCorpus, llm: Dict[str, Set[str]],
                         rules: Dict[str, Set[str]]) -> Dict[str, Any]:
    """
    Three trust tiers over (unit, type) pairs at paragraph and clause level: labelled by both, by the rules only,
    by the LLM only; each with the number of items and how many of them are gold labels.
    """
    result: Dict[str, Any] = {}
    for level, key in (("paragraph", lambda c: corpus.paragraph_of[c]), ("clause", lambda c: c)):
        def pairs(labels: Dict[str, Set[str]]) -> Set[Tuple[str, str]]:
            return {(key(c), t) for c, ts in labels.items() for t in ts}
        gold, by_llm, by_rules = pairs(corpus.gold), pairs(llm), pairs(rules)
        tiers = {"both": by_llm & by_rules, "rules_only": by_rules - by_llm, "llm_only": by_llm - by_rules}
        result[level] = {name: {"items": len(items), "correct": len(items & gold)} for name, items in tiers.items()}
    if corpus.spec.name in AGREEMENT_NOTES:
        result["note"] = AGREEMENT_NOTES[corpus.spec.name]
    return result


def format_agreement(agreement: Dict[str, Any]) -> str:
    lines = ["", "Agreement with rules v2 on the same held-out clauses (trust tiers; correct = also a gold label):"]
    for level in ("paragraph", "clause"):
        parts = [f"{name.replace('_', ' ')} {t['correct']}/{t['items']} correct"
                 for name, t in agreement[level].items()]
        lines.append(f"  {level.capitalize():<9} level: " + "; ".join(parts))
    if "note" in agreement:
        lines.append("  " + agreement["note"])
    return "\n".join(lines) + "\n"


def score_cached(data_dir: str, set_name: str, path: str, out_dir: str) -> Optional[Dict[str, Any]]:
    """Score one cached run into out_dir; None (with a message) if the file is empty or partially written."""
    try:
        records = read_records(path)
    except RunsFileError as e:
        print(f"skipping {path}: {e}", file=sys.stderr)
        return None
    corpus = load_corpus(data_dir, set_name)
    loaded = load_answers(path, corpus)
    predictions, stats = loaded["predictions"], loaded["stats"]
    generation = generation_stats(records)
    first = records[0]
    model, prompt_version = first["model"], first.get("prompt_version", PROMPT_VERSION)
    scores = score(corpus, predictions)
    agreement = agreement_with_rules(corpus, predictions, rules_v2_predictions(corpus, corpus.spec.jurisdiction))
    invalid = len(stats["invalid_clause_ids"])
    notes = [
        f"Model: {model} (temperature 0, seed {SEED}, reasoning mode off, prompt {prompt_version}), one request per held-out paragraph, "
        f"given the task definition from ANNOTATION_GUIDELINE.md.",
        f"Requests: {stats['paragraphs_sent']} sent, {stats['failed_requests']} failed, "
        f"{stats['unparseable_answers']} answers not valid JSON.",
        format_generation(generation),
        f"Citations: {stats['cited_clause_ids']} clause IDs returned, {invalid} not among the clauses sent "
        f"({(invalid / stats['cited_clause_ids'] * 100) if stats['cited_clause_ids'] else 0:.1f}%).",
    ]
    if stats["invalid_clause_ids"]:
        notes.append("Invalid clause IDs: " + "; ".join(stats["invalid_clause_ids"][:20]))
    slug = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"llm_{slug}_report.txt"), "w", encoding="utf-8") as f:
        f.write(format_report(f"LLM extractor ({model}) on held-out {corpus.spec.title} paragraphs",
                              corpus_stats(corpus), scores, error_rows(corpus, predictions), notes))
        f.write(format_agreement(agreement))
    summary = {"model": model, "prompt_version": prompt_version, "requests": {k: v for k, v in stats.items()},
               "generation": generation, "scores": scores, "agreement_with_rules_v2": agreement}
    with open(os.path.join(out_dir, f"llm_{slug}_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return summary


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", model.lower()).strip("_")


def runs_path(data_dir: str, set_name: str, model: str, suffix: str = "") -> str:
    """The cached answers of one model; suffix EVIDENCE_SUFFIX for the heldout-v2-evidence run."""
    return os.path.join(data_dir, "heldout", "llm_runs", set_name, f"{model_slug(model)}{suffix}.jsonl")


def score_all(data_dir: str, out_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Score every cached run of every held-out set; needs no model. Results go to data/heldout/results/<set>, or to
    <out_dir>/<set> when out_dir is given. Empty or partially written run files are skipped.
    """
    summaries: Dict[str, Dict[str, Any]] = {}
    for set_name in HELDOUT_SETS:
        folder = os.path.join(data_dir, "heldout", "llm_runs", set_name)
        if not os.path.isdir(folder):
            continue
        target = os.path.join(out_dir, set_name) if out_dir else results_dir(data_dir, set_name)
        for name in sorted(os.listdir(folder)):
            if name.endswith(".jsonl"):
                summary = score_cached(data_dir, set_name, os.path.join(folder, name), target)
                if summary is not None:
                    summaries[f"{set_name}/{name[:-6]}"] = summary
    return summaries


def _print_summary(key: str, summary: Dict[str, Any]) -> None:
    o = summary["scores"]["paragraph"]["overall"]
    r = summary["requests"]
    print(f"{key:<40} paragraph: found {o['tp']}/{o['tp'] + o['fn']}, precision {o['precision']:.2f} | "
          f"invalid clause IDs {len(r['invalid_clause_ids'])}/{r['cited_clause_ids']}, failed {r['failed_requests']}")


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="LLM comparison on held-out regulatory paragraphs")
    parser.add_argument("command", choices=["run", "score"])
    parser.add_argument("--set", default=None, choices=sorted(HELDOUT_SETS), help="held-out set to run (required for run)")
    parser.add_argument("--model", default=os.getenv("HELDOUT_LLM_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.getenv("HELDOUT_LLM_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--limit", type=int, default=None, help="only the first N paragraphs (smoke test)")
    parser.add_argument("--evidence", action="store_true",
                        help=f"prompt {PROMPT_VERSION_EVIDENCE}: one entry per clause and type, with quoted evidence")
    parser.add_argument("--out", default=None,
                        help="run: write the answers here instead of data/heldout/llm_runs (smoke tests); "
                             "they are then scored into the same folder, and the committed runs are left alone. "
                             "score: write the results to <out>/<set>/ instead of data/heldout/results/<set>/")
    parser.add_argument("--resume", action="store_true",
                        help="keep answers already cached for the same prompt and model; ask only the rest")
    args = parser.parse_args()
    if args.command == "run":
        if not args.set:
            parser.error("run needs --set")
        out = args.out or runs_path(data_dir, args.set, args.model, EVIDENCE_SUFFIX if args.evidence else "")
        run_model(data_dir, args.set, args.model, args.base_url, out, args.limit, args.evidence, args.resume)
        if args.out:
            summary = score_cached(data_dir, args.set, out, os.path.dirname(os.path.abspath(out)))
            if summary is not None:
                _print_summary(os.path.basename(out), summary)
            return
    for key, summary in score_all(data_dir, args.out if args.command == "score" else None).items():
        _print_summary(key, summary)


if __name__ == "__main__":
    main()
