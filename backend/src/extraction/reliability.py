"""
Measured reliability of each rule type, used as the confidence of rule-extracted obligations.

The confidence of a rule obligation is not set by hand: it is the precision of rules v2 for that obligation type
on unseen text, i.e. the share of held-out paragraphs flagged with the type that the pre-registered gold labels
also give that type. The unseen text is Part 3 of the UK Money Laundering Regulations 2017, labelled after the
rules were frozen (data/heldout/gold_labels_uk_mlr_2017.yaml), scored at paragraph level by src.heldout.evaluate.
Types the rules never flagged there have no measured precision (None). Two such cases are kept apart: the gold
labels give the type to some paragraphs and the rules found none of them (a measured miss, recall 0), or neither
the gold labels nor the rules give the type to any paragraph (no evidence either way).
"""
from typing import Any, Dict, Optional

from src.extraction import frames

RELIABILITY_SET = "uk_mlr_2017"
RELIABILITY_LEVEL = "paragraph"
NO_RELIABILITY_BASIS = "Not measured: no reliability data was given to the extractor."


def measured_precision(data_dir: str, set_name: str = RELIABILITY_SET) -> Dict[str, Dict[str, Any]]:
    """Every rule type -> {"correct": tp, "flagged": tp + fp, "precision": tp / flagged or None,
    "gold": tp + fn (paragraphs the gold labels give the type), "missed": fn, "basis": sentence}."""
    # imported here: src.heldout.evaluate imports the extractor, which must not import evaluate at module load
    from src.heldout import evaluate

    corpus = evaluate.load_corpus(data_dir, set_name)
    predictions = evaluate.rules_v2_predictions(corpus, corpus.spec.jurisdiction)
    by_type = evaluate.score(corpus, predictions)[RELIABILITY_LEVEL]["by_type"]
    result: Dict[str, Dict[str, Any]] = {}
    for rule_type in frames.TYPES:
        scores = by_type.get(rule_type, {"tp": 0, "fp": 0, "fn": 0})
        correct, flagged = scores["tp"], scores["tp"] + scores["fp"]
        entry: Dict[str, Any] = {"correct": correct, "flagged": flagged,
                                 "precision": round(correct / flagged, 4) if flagged else None,
                                 "gold": scores["tp"] + scores["fn"], "missed": scores["fn"]}
        entry["basis"] = basis_sentence(entry, corpus.spec.title)
        result[rule_type] = entry
    return result


def basis_sentence(entry: Dict[str, Any], set_title: str) -> str:
    """One sentence naming the sample behind a type's precision, or saying why it was not measured."""
    if not entry["flagged"] and entry["gold"]:
        paragraphs = "1 paragraph" if entry["gold"] == 1 else f"{entry['gold']} paragraphs"
        return (f"Not measured: rules v2 flagged no paragraph with this type in unseen text ({set_title}), "
                f"although the gold labels give it to {paragraphs} there; the rules found none of them.")
    if not entry["flagged"]:
        return (f"Not measured: rules v2 flagged no paragraph with this type in unseen text ({set_title}), "
                f"and the gold labels give it to no paragraph there either.")
    return (f"Rules v2 on unseen text ({set_title}, labelled after the rules were frozen): "
            f"{entry['correct']} of {entry['flagged']} paragraphs flagged with this type were correct.")


def confidence_for(reliability: Optional[Dict[str, Dict[str, Any]]], rule_type: str) -> Dict[str, Any]:
    """Obligation fields for one rule type: confidence = precision rounded to 2 places (None if unmeasured);
    confidence_kind is "measured_on_heldout" only when a measured precision exists."""
    entry = (reliability or {}).get(rule_type)
    if entry is None:
        return {"confidence": None, "confidence_basis": NO_RELIABILITY_BASIS, "confidence_kind": None}
    precision = entry["precision"]
    if precision is None:
        return {"confidence": None, "confidence_basis": entry["basis"], "confidence_kind": None}
    return {"confidence": round(precision, 2), "confidence_basis": entry["basis"],
            "confidence_kind": "measured_on_heldout"}
