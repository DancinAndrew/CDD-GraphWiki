"""
Score the rule-based extractor on held-out MAS Notice 626 paragraphs.

    PYTHONPATH=backend python -m src.heldout.evaluate

The rules were written against the development excerpt in data/sources/. Here they run, unchanged, on the
full Notice; only clauses outside the development paragraphs are scored against data/heldout/gold_labels.yaml.
Writes data/heldout/results/rules_predictions.yaml and rules_report.txt, and prints the headline numbers.
"""
import os
import re
import json
import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Iterable, Any

import yaml

from src.contracts.models import Clause
from src.ingestion.parser import SemanticHierarchicalSegmenter
from src.extraction.extractor import RuleBasedObligationExtractor, build_contexts
from src.paths import find_data_dir

DOC_ID = "mas_notice_626"
JURISDICTION = "Singapore"
OBLIGATION_WORDS = re.compile(r"\b(shall|must)\b")

Pair = Tuple[str, str]  # (clause_id or paragraph, type)


@dataclass
class HeldOutCorpus:
    clauses: List[Clause]          # every clause of the full Notice, in document order
    held_out: List[Clause]         # clauses that are scored
    paragraph_of: Dict[str, str]   # clause_id -> paragraph number, e.g. "6.14A"
    gold: Dict[str, Set[str]]      # clause_id -> gold types (held-out clauses only)
    types: List[str]
    development_paragraphs: List[str]


def paragraph_number(clause: Clause) -> str:
    parts = clause.section_ref.split(" > ")
    return parts[1] if len(parts) > 1 else ""


def load_corpus(data_dir: str) -> HeldOutCorpus:
    heldout_dir = os.path.join(data_dir, "heldout")
    with open(os.path.join(heldout_dir, "gold_labels.yaml"), encoding="utf-8") as f:
        gold_doc = yaml.safe_load(f)
    repo_root = os.path.dirname(os.path.abspath(data_dir))  # corpus paths in the gold file are repo-relative
    with open(os.path.join(repo_root, gold_doc["corpus"]), encoding="utf-8") as f:
        markdown = f.read()
    _, clauses = SemanticHierarchicalSegmenter(DOC_ID).parse(markdown)

    development = set(gold_doc["development_paragraphs"])
    paragraph_of = {c.clause_id: paragraph_number(c) for c in clauses}
    held_out = [c for c in clauses if paragraph_of[c.clause_id] and paragraph_of[c.clause_id] not in development]
    held_ids = {c.clause_id for c in held_out}

    gold: Dict[str, Set[str]] = {c.clause_id: set() for c in held_out}
    for label in gold_doc["labels"]:
        if label["clause_id"] not in held_ids:
            raise ValueError(f"gold label for {label['clause_id']} is not a held-out clause of the corpus")
        unknown = set(label["types"]) - set(gold_doc["types"])
        if unknown:
            raise ValueError(f"unknown types {unknown} for {label['clause_id']}")
        gold[label["clause_id"]] |= set(label["types"])
    return HeldOutCorpus(clauses, held_out, paragraph_of, gold, list(gold_doc["types"]),
                         list(gold_doc["development_paragraphs"]))


def rule_predictions(corpus: HeldOutCorpus) -> Dict[str, Set[str]]:
    """Run the unchanged rule-based extractor on the full Notice and keep the held-out clauses."""
    extractor = RuleBasedObligationExtractor(jurisdictions={DOC_ID: JURISDICTION})
    contexts = build_contexts(corpus.clauses)
    predictions: Dict[str, Set[str]] = {}
    for clause in corpus.held_out:
        match, _ = extractor.match_clause(clause, contexts.get(clause.clause_id, ""))
        predictions[clause.clause_id] = {match.rule} if match else set()
    return predictions


def _pairs(labels: Dict[str, Set[str]], key=lambda clause_id: clause_id) -> Set[Pair]:
    return {(key(clause_id), t) for clause_id, types in labels.items() for t in types}


def _prf(tp: int, fp: int, fn: int) -> Dict[str, Any]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def score(corpus: HeldOutCorpus, predictions: Dict[str, Set[str]]) -> Dict[str, Any]:
    """Clause-level and paragraph-level precision/recall over (unit, type) pairs, overall and per type."""
    by_paragraph = lambda clause_id: corpus.paragraph_of[clause_id]
    result: Dict[str, Any] = {}
    for level, key in (("clause", lambda c: c), ("paragraph", by_paragraph)):
        gold, pred = _pairs(corpus.gold, key), _pairs(predictions, key)
        level_result = {"overall": _prf(len(gold & pred), len(pred - gold), len(gold - pred)), "by_type": {}}
        for t in corpus.types:
            g = {p for p in gold if p[1] == t}
            q = {p for p in pred if p[1] == t}
            if g or q:
                level_result["by_type"][t] = _prf(len(g & q), len(q - g), len(g - q))
        result[level] = level_result
    return result


def corpus_stats(corpus: HeldOutCorpus) -> Dict[str, Any]:
    paragraphs = sorted({corpus.paragraph_of[c.clause_id] for c in corpus.clauses if corpus.paragraph_of[c.clause_id]})
    held_paragraphs = sorted({corpus.paragraph_of[c.clause_id] for c in corpus.held_out})
    with_duty = [c for c in corpus.held_out if OBLIGATION_WORDS.search(c.normalized_text)]
    labelled = [cid for cid, types in corpus.gold.items() if types]
    return {
        "clause_records": len(corpus.clauses),
        "numbered_paragraphs": len(paragraphs),
        "development_paragraphs": len(corpus.development_paragraphs),
        "held_out_paragraphs": len(held_paragraphs),
        "held_out_clauses": len(corpus.held_out),
        "held_out_clauses_with_shall_or_must": len(with_duty),
        "held_out_clauses_labelled_in_scope": len(labelled),
        "held_out_paragraphs_labelled_in_scope": len({corpus.paragraph_of[c] for c in labelled}),
    }


def error_rows(corpus: HeldOutCorpus, predictions: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
    """Every held-out clause where the predicted types differ from the gold types."""
    by_id = {c.clause_id: c for c in corpus.held_out}
    rows = []
    for clause in corpus.held_out:
        gold, pred = corpus.gold[clause.clause_id], predictions.get(clause.clause_id, set())
        if gold != pred:
            rows.append({
                "clause_id": clause.clause_id,
                "paragraph": corpus.paragraph_of[clause.clause_id],
                "missed": sorted(gold - pred),
                "spurious": sorted(pred - gold),
                "text": re.sub(r"^#+\s*[\w.]+\s*", "", by_id[clause.clause_id].raw_text)[:220],
            })
    return rows


def format_report(title: str, stats: Dict[str, Any], scores: Dict[str, Any],
                  errors: List[Dict[str, Any]], notes: Iterable[str] = ()) -> str:
    lines = [title, "=" * len(title), ""]
    lines.append(f"Corpus: {stats['numbered_paragraphs']} numbered paragraphs ({stats['clause_records']} clause records) "
                 f"of MAS Notice 626; {stats['development_paragraphs']} development paragraphs excluded.")
    lines.append(f"Held out: {stats['held_out_paragraphs']} paragraphs, {stats['held_out_clauses']} clauses; "
                 f"{stats['held_out_clauses_labelled_in_scope']} clauses in {stats['held_out_paragraphs_labelled_in_scope']} "
                 f"paragraphs carry one of the modelled types.")
    lines.append(f"Held-out clauses containing 'shall' or 'must': {stats['held_out_clauses_with_shall_or_must']}.")
    lines.extend(notes)
    for level in ("paragraph", "clause"):
        o = scores[level]["overall"]
        lines += ["", f"{level.capitalize()} level (unit, type) pairs: precision {o['precision']:.2f}, recall {o['recall']:.2f}, "
                      f"F1 {o['f1']:.2f}  (TP {o['tp']}, FP {o['fp']}, FN {o['fn']})"]
        for t, m in scores[level]["by_type"].items():
            lines.append(f"  {t:<20} P {m['precision']:.2f}  R {m['recall']:.2f}  (TP {m['tp']}, FP {m['fp']}, FN {m['fn']})")
    lines += ["", f"Disagreements with the gold labels ({len(errors)} clauses):"]
    for e in errors:
        tag = "; ".join(filter(None, [f"missed {', '.join(e['missed'])}" if e["missed"] else "",
                                      f"spurious {', '.join(e['spurious'])}" if e["spurious"] else ""]))
        lines.append(f"- {e['paragraph']:<7} {e['clause_id']}: {tag}")
        lines.append(f"    \"{e['text']}\"")
    return "\n".join(lines) + "\n"


def run(data_dir: str, out_dir: str) -> Dict[str, Any]:
    corpus = load_corpus(data_dir)
    predictions = rule_predictions(corpus)
    stats, scores, errors = corpus_stats(corpus), score(corpus, predictions), error_rows(corpus, predictions)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "rules_predictions.yaml"), "w", encoding="utf-8") as f:
        yaml.dump([{"clause_id": c.clause_id, "types": sorted(predictions[c.clause_id])}
                   for c in corpus.held_out if predictions[c.clause_id]], f, allow_unicode=True, sort_keys=False)
    with open(os.path.join(out_dir, "rules_report.txt"), "w", encoding="utf-8") as f:
        f.write(format_report("Rule-based extractor on held-out MAS Notice 626 paragraphs", stats, scores, errors,
                              ["The rules assign at most one type per clause; clauses with two gold types can only be half found."]))
    summary = {"corpus": stats, "rules": scores}
    with open(os.path.join(out_dir, "rules_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    return summary


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="Score the rule-based extractor on held-out MAS Notice 626 paragraphs")
    parser.add_argument("--out", default=os.path.join(data_dir, "heldout", "results"))
    args = parser.parse_args()
    summary = run(data_dir, args.out)
    for level in ("paragraph", "clause"):
        o = summary["rules"][level]["overall"]
        print(f"{level:<9} precision {o['precision']:.2f}  recall {o['recall']:.2f}  F1 {o['f1']:.2f}  "
              f"(TP {o['tp']}, FP {o['fp']}, FN {o['fn']})")
    print(f"Report: {os.path.join(args.out, 'rules_report.txt')}")


if __name__ == "__main__":
    main()
