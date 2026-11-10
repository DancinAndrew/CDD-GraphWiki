"""
Score the rule-based extractors on held-out regulatory text.

    PYTHONPATH=backend python -m src.heldout.evaluate

Each held-out set is a regulation converted to the parser's Markdown format plus gold labels that were committed
before the rules being tested were run on it (see data/heldout/ANNOTATION_GUIDELINE.md). Two rule versions are
scored side by side:

- rules_v1: the original extractor (src/extraction/extractor_v1.py, frozen), written against the development
  excerpts in data/sources/;
- rules_v2: the current extractor (src/extraction/extractor.py), redesigned after the v1 errors on the MAS
  Notice 626 held-out set. That set is therefore no longer unseen for v2; sets added after v2 was frozen are.

Results go to data/heldout/results/<set>/rules_<version>_{predictions.yaml,report.txt,summary.json}.
"""
import os
import re
import json
import argparse
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple

import yaml

from src.contracts.models import Clause
from src.ingestion.parser import SemanticHierarchicalSegmenter
from src.extraction import extractor_v1
from src.extraction.extractor import RuleBasedObligationExtractor
from src.paths import find_data_dir

OBLIGATION_WORDS = re.compile(r"\b(shall|must)\b")


@dataclass(frozen=True)
class HeldOutSpec:
    name: str            # short name, used for result folders
    gold: str            # gold label file, relative to data/heldout
    document_id: str
    jurisdiction: str
    title: str           # how prompts and reports name the document
    description: str     # one line for the LLM prompt


HELDOUT_SETS: Dict[str, HeldOutSpec] = {
    "mas_notice_626": HeldOutSpec(
        "mas_notice_626", "gold_labels.yaml", "mas_notice_626", "Singapore", "MAS Notice 626",
        "Singapore AML/CFT rules for banks"),
}
DEFAULT_SET = "mas_notice_626"


@dataclass
class HeldOutCorpus:
    spec: HeldOutSpec
    clauses: List[Clause]          # every clause of the document, in document order
    held_out: List[Clause]         # clauses that are scored
    paragraph_of: Dict[str, str]   # clause_id -> paragraph number, e.g. "6.14A"
    gold: Dict[str, Set[str]]      # clause_id -> gold types (held-out clauses only)
    types: List[str]
    development_paragraphs: List[str]


def paragraph_number(clause: Clause) -> str:
    parts = clause.section_ref.split(" > ")
    return parts[1] if len(parts) > 1 else ""


def load_corpus(data_dir: str, set_name: str = DEFAULT_SET) -> HeldOutCorpus:
    spec = HELDOUT_SETS[set_name]
    with open(os.path.join(data_dir, "heldout", spec.gold), encoding="utf-8") as f:
        gold_doc = yaml.safe_load(f)
    repo_root = os.path.dirname(os.path.abspath(data_dir))  # corpus paths in the gold file are repo-relative
    with open(os.path.join(repo_root, gold_doc["corpus"]), encoding="utf-8") as f:
        markdown = f.read()
    _, clauses = SemanticHierarchicalSegmenter(spec.document_id).parse(markdown)

    development = set(gold_doc.get("development_paragraphs") or [])
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
    return HeldOutCorpus(spec, clauses, held_out, paragraph_of, gold, list(gold_doc["types"]), sorted(development))


# --- the two rule versions ----------------------------------------------------------------------------------

def rules_v1_predictions(corpus: HeldOutCorpus, jurisdiction: str) -> Dict[str, Set[str]]:
    """The frozen v1 extractor: one type per clause, judged on the clause plus its ancestors' text."""
    extractor = extractor_v1.RuleBasedObligationExtractor(jurisdictions={corpus.spec.document_id: jurisdiction})
    contexts = extractor_v1.build_contexts(corpus.clauses)
    predictions: Dict[str, Set[str]] = {}
    for clause in corpus.held_out:
        match, _ = extractor.match_clause(clause, contexts.get(clause.clause_id, ""))
        predictions[clause.clause_id] = {match.rule} if match else set()
    return predictions


def rules_v2_predictions(corpus: HeldOutCorpus, jurisdiction: str) -> Dict[str, Set[str]]:
    """The current extractor, run on the whole document so lists and cross-references are resolved."""
    extractor = RuleBasedObligationExtractor(jurisdictions={corpus.spec.document_id: jurisdiction})
    types = extractor.classify(corpus.clauses)
    return {c.clause_id: set(types.get(c.clause_id, set())) for c in corpus.held_out}


RULE_VERSIONS: Dict[str, Tuple[str, Callable[[HeldOutCorpus, str], Dict[str, Set[str]]]]] = {
    "rules_v1": ("Rule-based extractor v1 (frozen, written against the development excerpts)", rules_v1_predictions),
    "rules_v2": ("Rule-based extractor v2 (language frames)", rules_v2_predictions),
}


# --- scoring -----------------------------------------------------------------------------------------------

Pair = Tuple[str, str]  # (clause_id or paragraph, type)


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
        "document": corpus.spec.title,
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
    rows = []
    for clause in corpus.held_out:
        gold, pred = corpus.gold[clause.clause_id], predictions.get(clause.clause_id, set())
        if gold != pred:
            rows.append({
                "clause_id": clause.clause_id,
                "paragraph": corpus.paragraph_of[clause.clause_id],
                "missed": sorted(gold - pred),
                "spurious": sorted(pred - gold),
                "text": re.sub(r"^#+\s*\S+\s*", "", clause.raw_text)[:220],
            })
    return rows


def format_report(title: str, stats: Dict[str, Any], scores: Dict[str, Any],
                  errors: List[Dict[str, Any]], notes: Iterable[str] = ()) -> str:
    lines = [title, "=" * len(title), ""]
    lines.append(f"Corpus: {stats['numbered_paragraphs']} numbered paragraphs ({stats['clause_records']} clause records) "
                 f"of {stats['document']}; {stats['development_paragraphs']} development paragraphs excluded.")
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


def results_dir(data_dir: str, set_name: str) -> str:
    return os.path.join(data_dir, "heldout", "results", set_name)


V1_NOTES = {
    "mas_notice_626": ["The rules assign at most one type per clause; clauses with two gold types can only be half found."],
}
V2_NOTES = {
    "mas_notice_626": ["v2 was designed after studying the v1 errors on these paragraphs, so this is not an unseen-data score."],
}


def run_set(data_dir: str, set_name: str, out_dir: str) -> Dict[str, Any]:
    corpus = load_corpus(data_dir, set_name)
    stats = corpus_stats(corpus)
    os.makedirs(out_dir, exist_ok=True)
    summary: Dict[str, Any] = {"corpus": stats}
    for version, (title, predict) in RULE_VERSIONS.items():
        predictions = predict(corpus, corpus.spec.jurisdiction)
        scores = score(corpus, predictions)
        notes = (V1_NOTES if version == "rules_v1" else V2_NOTES).get(set_name, [])
        with open(os.path.join(out_dir, f"{version}_predictions.yaml"), "w", encoding="utf-8") as f:
            yaml.dump([{"clause_id": c.clause_id, "types": sorted(predictions[c.clause_id])}
                       for c in corpus.held_out if predictions[c.clause_id]], f, allow_unicode=True, sort_keys=False)
        with open(os.path.join(out_dir, f"{version}_report.txt"), "w", encoding="utf-8") as f:
            f.write(format_report(f"{title} on held-out {corpus.spec.title} paragraphs", stats, scores,
                                  error_rows(corpus, predictions), notes))
        summary[version] = scores
    with open(os.path.join(out_dir, "rules_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    return summary


def run(data_dir: str, out_root: str = None) -> Dict[str, Any]:
    out_root = out_root or os.path.join(data_dir, "heldout", "results")
    return {name: run_set(data_dir, name, os.path.join(out_root, name)) for name in HELDOUT_SETS}


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="Score the rule-based extractors on held-out regulatory text")
    parser.add_argument("--out", default=os.path.join(data_dir, "heldout", "results"))
    args = parser.parse_args()
    for set_name, summary in run(data_dir, args.out).items():
        for version in RULE_VERSIONS:
            o = summary[version]["paragraph"]["overall"]
            print(f"{set_name:<16} {version}  paragraph: found {o['tp']}/{o['tp'] + o['fn']}, precision {o['precision']:.2f}  "
                  f"| clause P {summary[version]['clause']['overall']['precision']:.2f} R {summary[version]['clause']['overall']['recall']:.2f}")


if __name__ == "__main__":
    main()
