"""
Independent review of pre-registered held-out labels, rebuilt from the reviewers' committed answers.

    PYTHONPATH=backend python -m src.heldout.label_review

The protocol, written before any reviewer ran, is data/heldout/reviews/<set>/PROTOCOL.md. Stage 1 reviewers
(two blind annotators and a critic) look for problems; every clause where one of them differs from the
pre-registered labels becomes a candidate. Stage 2 adjudicators vote on each candidate. This module turns those
committed answers into:

- stage2/candidates.md: the sheet the adjudicators were given (reviewers anonymised);
- decisions.yaml: the votes and the outcome of each candidate under the protocol's decision rule;
- the revised label file named by HeldOutSpec.revised_gold: the pre-registered labels with the accepted changes
  and nothing else, so the revision can never contain a hand edit;
- agreement.json: how far the blind annotators agree with the pre-registered labels before adjudication;
- scores_before_after.{json,txt}: every system scored against the pre-registered and the revised labels, plus a
  sensitivity check with the readings most adjudicators preferred but did not find required by the guideline.

The scores in data/heldout/results/ stay against the pre-registered labels.
"""
import json
import os
from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Set, Tuple

import yaml

from src.heldout.evaluate import (
    HeldOutCorpus, RULE_VERSIONS, label_file, load_corpus, score,
)
from src.paths import find_data_dir


@dataclass(frozen=True)
class ReviewSpec:
    folder: str                               # relative to data/heldout
    adjudicator_models: Dict[int, str]        # Agent model alias each adjudicator ran on
    stage1_model: str                         # the session model the stage 1 reviewers ran on


REVIEWS: Dict[str, ReviewSpec] = {
    "uk_mlr_2017": ReviewSpec("reviews/uk_mlr_2017", {1: "opus", 2: "fable", 3: "sonnet"}, "claude-opus-5-5"),
}

# the adjudicators saw the stage 1 reviewers under these names
ANONYMOUS = {"critic_c": "Reviewer 1", "annotator_a": "Reviewer 2", "annotator_b": "Reviewer 3"}
REAL_NAME = {v: k for k, v in ANONYMOUS.items()}
ADJUDICATORS = (1, 2, 3)

DECISION_RULE = ("A label changes only when at least two of the three adjudicators choose the same set of types, "
                 "that set differs from the pre-registered one, and each of them says the guideline decides the case, "
                 "says the pre-registered label breaks it and quotes the wording. Otherwise the label stays; when at "
                 "least two adjudicators say the guideline does not decide the case it is recorded as a guideline gap.")


def review_dir(data_dir: str, set_name: str) -> str:
    return os.path.join(data_dir, "heldout", REVIEWS[set_name].folder)


def _yaml(path: str) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _clause_text(corpus: HeldOutCorpus) -> Dict[str, str]:
    return {c.clause_id: c.raw_text.lstrip("#").strip() for c in corpus.clauses}


def _held_ids(corpus: HeldOutCorpus) -> List[str]:
    return [c.clause_id for c in corpus.held_out]


def _notes(data_dir: str, corpus: HeldOutCorpus) -> Dict[str, str]:
    doc = _yaml(os.path.join(data_dir, "heldout", corpus.spec.gold))
    return {label["clause_id"]: label.get("note", "") for label in doc["labels"]}


# --- stage 1 ------------------------------------------------------------------------------------------------

@dataclass
class Annotator:
    labels: Dict[str, Set[str]]
    reasons: Dict[str, str]
    hard_cases: Dict[str, str]


def load_annotator(path: str, corpus: HeldOutCorpus) -> Annotator:
    doc = _yaml(path)
    labels: Dict[str, Set[str]] = {cid: set() for cid in _held_ids(corpus)}
    reasons: Dict[str, str] = {}
    for entry in doc.get("labels") or []:
        cid, types = entry["clause_id"], set(entry.get("types") or [])
        if cid not in labels:
            raise ValueError(f"{path}: {cid} is not a held-out clause")
        if not types <= set(corpus.types):
            raise ValueError(f"{path}: unknown types {types - set(corpus.types)} for {cid}")
        labels[cid] |= types
        reasons[cid] = entry.get("reason", "")
    hard = {entry["clause_id"]: entry.get("note", "") for entry in doc.get("hard_cases") or []}
    return Annotator(labels, reasons, hard)


def load_critic(path: str, corpus: HeldOutCorpus) -> Dict[str, Dict[str, Any]]:
    """The critic's problems that propose a different set of types; remarks that propose none are left out."""
    problems: Dict[str, Dict[str, Any]] = {}
    for p in _yaml(path).get("problems") or []:
        cid, proposed = p["clause_id"], set(p.get("proposed") or [])
        if cid not in corpus.gold:
            raise ValueError(f"{path}: {cid} is not a held-out clause")
        if not proposed <= set(corpus.types):
            raise ValueError(f"{path}: unknown types {proposed - set(corpus.types)} for {cid}")
        if proposed != corpus.gold[cid]:
            problems[cid] = {"proposed": proposed, "reason": p.get("reason", ""),
                             "basis": p.get("guideline_basis", ""), "confidence": p.get("confidence", "")}
    return problems


def build_candidates(data_dir: str, corpus: HeldOutCorpus) -> List[Dict[str, Any]]:
    """Every held-out clause where a stage 1 reviewer's set of types differs from the pre-registered set."""
    folder = os.path.join(review_dir(data_dir, corpus.spec.name), "stage1")
    a = load_annotator(os.path.join(folder, "annotator_a.yaml"), corpus)
    b = load_annotator(os.path.join(folder, "annotator_b.yaml"), corpus)
    critic = load_critic(os.path.join(folder, "critic_c.yaml"), corpus)
    notes = _notes(data_dir, corpus)
    candidates = []
    for cid in _held_ids(corpus):
        gold = corpus.gold[cid]
        views = []
        for name, ann in (("annotator_a", a), ("annotator_b", b)):
            why = ann.reasons.get(cid) or ("(gave this clause no type)" if not ann.labels[cid] else "")
            if cid in ann.hard_cases:
                why = (why + " | hard case: " + ann.hard_cases[cid]).strip(" |")
            views.append((ANONYMOUS[name], ann.labels[cid], why))
        if cid in critic:
            c = critic[cid]
            views.append((ANONYMOUS["critic_c"], c["proposed"],
                          f"{c['reason']} | guideline: {c['basis']} | confidence: {c['confidence']}"))
        if all(types == gold for _, types, _ in views):
            continue
        alternatives: Dict[Tuple[str, ...], List[Dict[str, str]]] = {}
        for reviewer, types, why in views:
            if types != gold:
                alternatives.setdefault(tuple(sorted(types)), []).append({"reviewer": reviewer, "reason": why})
        candidates.append({
            "id": f"K{len(candidates) + 1:03d}", "clause_id": cid, "paragraph": corpus.paragraph_of[cid],
            "pre_registered": sorted(gold), "pre_registered_note": notes.get(cid, ""),
            "alternatives": [{"types": list(k), "argued_by": v} for k, v in alternatives.items()],
            "found_by": sorted({x["reviewer"] for v in alternatives.values() for x in v}),
        })
    return candidates


def candidates_sheet(corpus: HeldOutCorpus, candidates: List[Dict[str, Any]]) -> str:
    """The adjudicators' sheet: candidates grouped by paragraph, each paragraph shown whole for context."""
    text = _clause_text(corpus)
    lines = ["# Candidates for adjudication", "",
             "Each candidate is one clause where at least one reviewer's set of types differs from the pre-registered label.",
             "Reviewers are anonymised. 'Pre-registered' is the label under review, not a reference answer.", ""]
    by_paragraph: Dict[str, List[Dict[str, Any]]] = {}
    for k in candidates:
        by_paragraph.setdefault(k["paragraph"], []).append(k)
    for paragraph, ks in by_paragraph.items():
        lines += [f"## Paragraph {paragraph}", "", "Whole paragraph (context):", ""]
        lines += [f"- `{cid}`: {text[cid]}" for cid in _held_ids(corpus) if corpus.paragraph_of[cid] == paragraph]
        lines.append("")
        for k in ks:
            lines += [f"### {k['id']}  `{k['clause_id']}`", "",
                      f"Text: {text[k['clause_id']]}", "",
                      f"Pre-registered types: {k['pre_registered'] or '[] (no type)'}",
                      f"Pre-registered note: {k['pre_registered_note'] or '(none)'}", ""]
            for alt in k["alternatives"]:
                lines.append(f"Alternative {alt['types'] or '[] (no type)'}:")
                lines += [f"  - {x['reviewer']}: {x['reason']}" for x in alt["argued_by"]]
            lines.append("")
    return "\n".join(lines) + "\n"


def _pairs(labels: Dict[str, Set[str]], key) -> Set[Tuple[str, str]]:
    return {(key(cid), t) for cid, types in labels.items() for t in types}


def _agreement_f1(x: Set[Tuple[str, str]], y: Set[Tuple[str, str]]) -> Dict[str, Any]:
    tp = len(x & y)
    return {"both": tp, "only_first": len(x - y), "only_second": len(y - x),
            "f1": round(2 * tp / (len(x) + len(y)), 4) if x or y else 1.0}


def agreement(data_dir: str, corpus: HeldOutCorpus) -> Dict[str, Any]:
    """F1 over (unit, type) pairs between the blind annotators and the pre-registered labels, before adjudication."""
    folder = os.path.join(review_dir(data_dir, corpus.spec.name), "stage1")
    a = load_annotator(os.path.join(folder, "annotator_a.yaml"), corpus).labels
    b = load_annotator(os.path.join(folder, "annotator_b.yaml"), corpus).labels
    result: Dict[str, Any] = {}
    for level, key in (("clause", lambda c: c), ("paragraph", lambda c: corpus.paragraph_of[c])):
        g, pa, pb = _pairs(corpus.gold, key), _pairs(a, key), _pairs(b, key)
        result[level] = {"annotator_a_vs_pre_registered": _agreement_f1(pa, g),
                         "annotator_b_vs_pre_registered": _agreement_f1(pb, g),
                         "annotator_a_vs_annotator_b": _agreement_f1(pa, pb)}
    result["note"] = ("Annotators A and B ran on the same model; identical answers show the labels are reproducible "
                      "by that model under the guideline, not that two independent readers agree.")
    return result


# --- stage 2 ------------------------------------------------------------------------------------------------

def _truthy(value: Any) -> bool:
    return value is True or str(value).lower() in ("true", "yes")


def load_votes(data_dir: str, corpus: HeldOutCorpus, candidates: List[Dict[str, Any]]) -> Dict[str, Dict[int, Dict]]:
    folder = os.path.join(review_dir(data_dir, corpus.spec.name), "stage2")
    by_id = {k["id"]: k for k in candidates}
    votes: Dict[str, Dict[int, Dict]] = {k["id"]: {} for k in candidates}
    for n in ADJUDICATORS:
        for v in _yaml(os.path.join(folder, f"adjudicator_{n}.yaml"))["decisions"]:
            k = by_id.get(v["candidate"])
            if k is None or v["clause_id"] != k["clause_id"]:
                raise ValueError(f"adjudicator {n}: {v['candidate']} does not match the candidates")
            if not set(v.get("types") or []) <= set(corpus.types):
                raise ValueError(f"adjudicator {n}: unknown types for {v['candidate']}")
            if n in votes[v["candidate"]]:
                raise ValueError(f"adjudicator {n}: {v['candidate']} answered twice")
            votes[v["candidate"]][n] = v
    missing = [cid for cid, vs in votes.items() if set(vs) != set(ADJUDICATORS)]
    if missing:
        raise ValueError(f"candidates without three votes: {missing}")
    return votes


def decide(candidate: Dict[str, Any], votes: Dict[int, Dict]) -> Dict[str, Any]:
    """The protocol's decision rule (see DECISION_RULE)."""
    original = tuple(candidate["pre_registered"])
    change: Counter = Counter()
    undecided = 0
    for v in votes.values():
        types = tuple(sorted(set(v.get("types") or [])))
        if not _truthy(v.get("decided_by_guideline")):
            undecided += 1
        elif (types != original and _truthy(v.get("pre_registered_breaks_guideline"))
              and (v.get("guideline_quote") or "").strip()):
            change[types] += 1
    winner = [t for t, n in change.items() if n >= 2]
    if winner:
        outcome, final = "changed", list(winner[0])
    elif undecided >= 2:
        outcome, final = "guideline_gap", list(original)
    else:
        outcome, final = "kept", list(original)
    # not part of the rule: another reading two or more adjudicators chose without finding it required
    chosen = Counter(tuple(sorted(set(v.get("types") or []))) for v in votes.values())
    preferred = [list(t) for t, n in chosen.items() if n >= 2 and t != original]
    return {"outcome": outcome, "types": final, "preferred_reading": preferred[0] if preferred else None}


def decisions(data_dir: str, corpus: HeldOutCorpus, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    votes = load_votes(data_dir, corpus, candidates)
    models = REVIEWS[corpus.spec.name].adjudicator_models
    rows = []
    for k in candidates:
        d = decide(k, votes[k["id"]])
        row = {"candidate": k["id"], "clause_id": k["clause_id"], "paragraph": k["paragraph"],
               "pre_registered": k["pre_registered"], "outcome": d["outcome"], "types": d["types"],
               "found_by": sorted(REAL_NAME[r] for r in k["found_by"])}
        if d["preferred_reading"] is not None and d["outcome"] != "changed":
            row["majority_preferred_reading"] = d["preferred_reading"]
        row["votes"] = [{"adjudicator": n, "model": models[n], "types": sorted(set(v.get("types") or [])),
                         "decided_by_guideline": _truthy(v.get("decided_by_guideline")),
                         "pre_registered_breaks_guideline": _truthy(v.get("pre_registered_breaks_guideline")),
                         "guideline_quote": v.get("guideline_quote", ""), "reason": v.get("reason", "")}
                        for n, v in sorted(votes[k["id"]].items())]
        rows.append(row)
    return rows


# --- revised labels -----------------------------------------------------------------------------------------

def apply_decisions(gold: Dict[str, Set[str]], rows: List[Dict[str, Any]], include_preferred: bool = False
                    ) -> Dict[str, Set[str]]:
    """The pre-registered labels with the changed decisions applied; with include_preferred, also the readings most
    adjudicators preferred (sensitivity check only)."""
    labels = {cid: set(types) for cid, types in gold.items()}
    for row in rows:
        if row["outcome"] == "changed":
            labels[row["clause_id"]] = set(row["types"])
        elif include_preferred and row.get("majority_preferred_reading") is not None:
            labels[row["clause_id"]] = set(row["majority_preferred_reading"])
    return labels


def revised_label_doc(data_dir: str, corpus: HeldOutCorpus, rows: List[Dict[str, Any]]) -> str:
    """The revised label file: pre-registered entries in their order, changed entries replaced, emptied ones dropped,
    new ones inserted in document order."""
    spec = corpus.spec
    doc = _yaml(os.path.join(data_dir, "heldout", spec.gold))
    changed = {row["clause_id"]: row for row in rows if row["outcome"] == "changed"}
    entries = {label["clause_id"]: dict(label) for label in doc["labels"]}
    for cid, row in changed.items():
        entry = entries.get(cid, {"clause_id": cid, "paragraph": corpus.paragraph_of[cid]})
        entry["types"] = list(row["types"])
        entry["review"] = row["candidate"]
        entries[cid] = entry
    order = {cid: i for i, cid in enumerate(_held_ids(corpus))}
    labels = sorted((e for e in entries.values() if e["types"]), key=lambda e: order[e["clause_id"]])
    folder = REVIEWS[spec.name].folder
    out = {k: v for k, v in doc.items() if k != "labels"}
    out["pre_registered_labels"] = spec.gold
    out["review"] = f"{folder}/decisions.yaml"
    out["changes"] = [{"candidate": row["candidate"], "clause_id": cid, "from": row["pre_registered"],
                       "to": row["types"]} for cid, row in changed.items()]
    out["labels"] = labels
    header = (f"# Revised held-out labels for {spec.title}: the pre-registered labels ({spec.gold}) with the\n"
              f"# changes accepted by the independent review in {folder} (PROTOCOL.md, decisions.yaml). Generated by\n"
              "# src.heldout.label_review from the reviewers' committed answers; do not edit by hand.\n")
    return header + yaml.dump(out, allow_unicode=True, sort_keys=False, width=120)


# --- scores against both label sets --------------------------------------------------------------------------

def _llm_predictions(data_dir: str, corpus: HeldOutCorpus) -> Dict[str, Dict[str, Set[str]]]:
    from src.heldout import llm_compare  # imported here: llm_compare needs httpx, the review itself does not

    folder = os.path.join(data_dir, "heldout", "llm_runs", corpus.spec.name)
    runs: Dict[str, Dict[str, Set[str]]] = {}
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if name.endswith(".jsonl"):
            runs[f"llm_{name[:-6]}"] = llm_compare.load_answers(os.path.join(folder, name), corpus)["predictions"]
    return runs


def scores_before_after(data_dir: str, corpus: HeldOutCorpus, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    label_sets = {
        "pre_registered": corpus.gold,
        "revised": apply_decisions(corpus.gold, rows),
        "sensitivity_preferred_readings": apply_decisions(corpus.gold, rows, include_preferred=True),
    }
    systems = {version: predict(corpus, corpus.spec.jurisdiction) for version, (_, predict) in RULE_VERSIONS.items()}
    systems.update(_llm_predictions(data_dir, corpus))
    result: Dict[str, Any] = {"label_sets": {}, "systems": {}}
    for name, labels in label_sets.items():
        labelled = [cid for cid, types in labels.items() if types]
        result["label_sets"][name] = {
            "clauses": len(labelled), "pairs": sum(len(labels[c]) for c in labelled),
            "paragraphs": len({corpus.paragraph_of[c] for c in labelled}),
            "paragraph_type_pairs": len({(corpus.paragraph_of[c], t) for c in labelled for t in labels[c]}),
        }
    for system, predictions in systems.items():
        result["systems"][system] = {name: score(replace(corpus, gold=labels), predictions)
                                     for name, labels in label_sets.items()}
    return result


def format_scores(corpus: HeldOutCorpus, scores: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    title = f"Scores on held-out {corpus.spec.title} against the pre-registered and the revised labels"
    outcomes = Counter(row["outcome"] for row in rows)
    preferred = sum(1 for row in rows if row.get("majority_preferred_reading") is not None)
    lines = [title, "=" * len(title), "",
             f"Review: {len(rows)} candidates; {outcomes['changed']} changed, {outcomes['kept']} kept, "
             f"{outcomes['guideline_gap']} guideline gaps (label kept).",
             f"Sensitivity: the revised labels plus the {preferred} readings that two or more adjudicators preferred "
             "without finding them required by the guideline. Not adopted; shown to bound the effect of unclear cases.",
             ""]
    for name, stats in scores["label_sets"].items():
        lines.append(f"{name:<32} {stats['clauses']} clauses ({stats['pairs']} clause-type pairs), "
                     f"{stats['paragraphs']} paragraphs ({stats['paragraph_type_pairs']} paragraph-type pairs)")
    for level in ("paragraph", "clause"):
        lines += ["", f"{level.capitalize()} level  precision / recall / F1  (TP, FP, FN)"]
        for system, by_labels in scores["systems"].items():
            for name, s in by_labels.items():
                o = s[level]["overall"]
                lines.append(f"  {system:<26} {name:<32} {o['precision']:.2f} / {o['recall']:.2f} / {o['f1']:.2f}  "
                             f"({o['tp']}, {o['fp']}, {o['fn']})")
    return "\n".join(lines) + "\n"


# --- driver -------------------------------------------------------------------------------------------------

def _decisions_yaml(corpus: HeldOutCorpus, rows: List[Dict[str, Any]]) -> str:
    spec = REVIEWS[corpus.spec.name]
    doc = {"set": corpus.spec.name, "protocol": "PROTOCOL.md", "decision_rule": DECISION_RULE,
           "stage1_model": spec.stage1_model,
           "adjudicator_models": {f"adjudicator_{n}": m for n, m in spec.adjudicator_models.items()},
           "outcomes": dict(sorted(Counter(row["outcome"] for row in rows).items())),
           "decisions": rows}
    return ("# Generated by src.heldout.label_review from stage1/ and stage2/; do not edit by hand.\n"
            + yaml.dump(doc, allow_unicode=True, sort_keys=False, width=120))


def run(data_dir: str, set_name: str) -> Dict[str, Any]:
    corpus = load_corpus(data_dir, set_name, labels="pre_registered")
    folder = review_dir(data_dir, set_name)
    candidates = build_candidates(data_dir, corpus)
    rows = decisions(data_dir, corpus, candidates)
    outputs = {
        os.path.join(folder, "stage2", "candidates.md"): candidates_sheet(corpus, candidates),
        os.path.join(folder, "decisions.yaml"): _decisions_yaml(corpus, rows),
        os.path.join(data_dir, "heldout", label_file(corpus.spec, "revised")): revised_label_doc(data_dir, corpus, rows),
        os.path.join(folder, "agreement.json"): json.dumps(agreement(data_dir, corpus), indent=2) + "\n",
    }
    for path, content in outputs.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    scores = scores_before_after(data_dir, corpus, rows)
    with open(os.path.join(folder, "scores_before_after.json"), "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)
        f.write("\n")
    with open(os.path.join(folder, "scores_before_after.txt"), "w", encoding="utf-8") as f:
        f.write(format_scores(corpus, scores, rows))
    return {"rows": rows, "scores": scores}


def main() -> None:
    data_dir = find_data_dir()
    for set_name in REVIEWS:
        result = run(data_dir, set_name)
        outcomes = Counter(row["outcome"] for row in result["rows"])
        print(f"{set_name}: {len(result['rows'])} candidates, " + ", ".join(f"{k} {v}" for k, v in sorted(outcomes.items())))
        for system, by_labels in result["scores"]["systems"].items():
            parts = [f"{name} F1 {s['paragraph']['overall']['f1']:.2f}" for name, s in by_labels.items()]
            print(f"  {system:<26} paragraph: " + " | ".join(parts))


if __name__ == "__main__":
    main()
