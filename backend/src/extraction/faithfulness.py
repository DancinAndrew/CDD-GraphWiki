"""
Deletion tests for the rule reasons in src/extraction/frames.py.

A label is one (clause_id, type) pair that frames.classify gives. Its rationale is every evidence span of its
reasons plus, transitively, the spans of every label those reasons depend on (a list item's lead-in, the
paragraph a cross-reference points to). Two tests check that the rationale is what the decision rests on:

- Comprehensiveness (delete the rationale): every rationale span, overlaps merged, is replaced by one space in a
  copy of the whole document, which is classified again. The test passes if the type is gone from the clause.
- Sufficiency (keep only the rationale): every clause of the copy keeps its heading, number and list label and
  only the text of its rationale spans, joined by spaces, in order. The test passes if the type is still there.

Coverage is the share of the touched clauses' body text that the rationale highlights, so that a rationale that
highlights whole clauses is visible. These are measured results: the frames are never tuned to pass them.

Labels given by list structure (list.inherit: an item takes its lead-in's type; list.propagate: a "shall –" lead-in
takes its items' type) rest on another label's rationale, so their tests largely repeat that label's. The summary
therefore splits every count into own-evidence and list-structure labels and by the label's first rule, and counts
the labels whose rationale cites text in their own clause.
"""
import copy
import statistics
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from src.extraction import frames

RawSpans = Dict[str, List[Tuple[int, int]]]  # clause_id -> merged (start, end) in raw_text, in order
Trace = Dict[str, Dict[str, list]]            # frames.classify_traced output
LIST_RULES = ("list.inherit", "list.propagate")  # rules that take the type from another label
EVIDENCE_KINDS = {"own_evidence": "own evidence", "list_structure": "list structure (list.inherit, list.propagate)"}


@dataclass
class LabelResult:
    clause_id: str
    type: str
    rules: List[str]                # rule ids of the label's own reasons
    comprehensive: bool             # deleting the rationale removes the type
    sufficient: bool                # the rationale alone keeps the type
    coverage: float
    rationale: List[str]            # "<clause_id>: <span text>" for every merged span
    types_before: List[str]
    types_after_deletion: List[str]
    types_after_keep_only: List[str]
    cites_own_clause: bool = False  # the rationale has a span in the label's own clause

    @property
    def evidence_kind(self) -> str:
        """"list_structure" when the label's first rule takes the type from another label, else "own_evidence"."""
        return "list_structure" if self.rules[0] in LIST_RULES else "own_evidence"


def merge_spans(spans: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    merged: List[Tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def rationale(trace: Trace, clause_id: str, type_: str) -> RawSpans:
    """All evidence spans of a label and, transitively, of every label it depends on."""
    spans: Dict[str, Set[Tuple[int, int]]] = {}
    seen: Set[Tuple[str, str]] = set()
    stack = [(clause_id, type_)]
    while stack:
        label = stack.pop()
        if label in seen:
            continue
        seen.add(label)
        for reason in trace.get(label[0], {}).get(label[1], []):
            for span in reason.spans:
                spans.setdefault(span.clause_id, set()).add((span.start, span.end))
            for dependency in reason.depends_on:
                dep_clause, _, dep_type = dependency.rpartition("#")
                stack.append((dep_clause, dep_type))
    return {cid: merge_spans(s) for cid, s in spans.items()}


def _with_text(clause, raw_text: str):
    if hasattr(clause, "model_copy"):
        return clause.model_copy(update={"raw_text": raw_text})
    clone = copy.copy(clause)
    clone.raw_text = raw_text
    return clone


def delete_rationale(clauses: List, spans: RawSpans) -> List:
    """Copy of the document with every rationale span replaced by one space."""
    perturbed = []
    for clause in clauses:
        raw = clause.raw_text
        for start, end in reversed(spans.get(clause.clause_id, [])):
            raw = raw[:start] + " " + raw[end:]
        perturbed.append(_with_text(clause, raw))
    return perturbed


def keep_only_rationale(clauses: List, spans: RawSpans, body_starts: Optional[Dict[str, int]] = None) -> List:
    """Copy of the document where every clause keeps its heading, number and list label and only its rationale.
    `body_starts` (clause_id -> frames.body_start) saves recomputing them for every label."""
    kept = []
    for clause in clauses:
        raw = clause.raw_text
        start = body_starts[clause.clause_id] if body_starts is not None else frames.body_start(raw)
        prefix = raw[:start]
        texts = [raw[start:end] for start, end in spans.get(clause.clause_id, [])]
        kept.append(_with_text(clause, prefix + " ".join(texts)))
    return kept


def body_lengths(clauses: List) -> Dict[str, int]:
    """Characters of raw_text from where the body starts to the last non-space character, per clause."""
    return {c.clause_id: max(0, len(c.raw_text.rstrip()) - frames.body_start(c.raw_text)) for c in clauses}


def coverage(lengths: Dict[str, int], spans: RawSpans, clause_id: str) -> float:
    """Rationale characters / body characters of the clauses the rationale touches plus the label's own clause."""
    touched = set(spans) | {clause_id}
    highlighted = sum(end - start for cid in spans for start, end in spans[cid])
    total = sum(lengths.get(cid, 0) for cid in touched)
    return highlighted / total if total else 0.0


def evaluate_document(clauses: List, paragraph_of: Callable[[object], str], trace: Optional[Trace] = None,
                      clause_ids: Optional[Set[str]] = None) -> List[LabelResult]:
    """
    Run both deletion tests for every label of one document (clauses in document order), or only for the labels of
    `clause_ids`. Classification always runs on the whole perturbed document.
    """
    trace = trace if trace is not None else frames.classify_traced(clauses, paragraph_of)
    by_id = {c.clause_id: c for c in clauses}
    starts = {c.clause_id: frames.body_start(c.raw_text) for c in clauses}
    lengths = body_lengths(clauses)
    results: List[LabelResult] = []
    for clause in clauses:
        if clause_ids is not None and clause.clause_id not in clause_ids:
            continue
        labels = trace.get(clause.clause_id, {})
        for type_, reasons in labels.items():
            spans = rationale(trace, clause.clause_id, type_)
            after_deletion = frames.classify(delete_rationale(clauses, spans), paragraph_of)[clause.clause_id]
            after_keep_only = frames.classify(keep_only_rationale(clauses, spans, starts), paragraph_of)[clause.clause_id]
            results.append(LabelResult(
                clause_id=clause.clause_id,
                type=type_,
                rules=list(dict.fromkeys(r.rule for r in reasons)),
                comprehensive=type_ not in after_deletion,
                sufficient=type_ in after_keep_only,
                coverage=coverage(lengths, spans, clause.clause_id),
                rationale=[f"{cid}: {' '.join(by_id[cid].raw_text[s:e].split())}"
                           for cid in by_id if cid in spans for s, e in spans[cid]],
                types_before=[t for t in frames.TYPES if t in labels],
                types_after_deletion=[t for t in frames.TYPES if t in after_deletion],
                types_after_keep_only=[t for t in frames.TYPES if t in after_keep_only],
                cites_own_clause=clause.clause_id in spans,
            ))
    return results


def _counts(results: List[LabelResult]) -> Dict[str, object]:
    coverages = [r.coverage for r in results]
    return {
        "labels": len(results),
        "comprehensive": sum(r.comprehensive for r in results),
        "sufficient": sum(r.sufficient for r in results),
        "both": sum(r.comprehensive and r.sufficient for r in results),
        "cites_own_clause": sum(r.cites_own_clause for r in results),
        "coverage_mean": round(statistics.mean(coverages), 4) if coverages else 0.0,
        "coverage_median": round(statistics.median(coverages), 4) if coverages else 0.0,
    }


def _grouped(results: List[LabelResult], key: Callable[[LabelResult], str], order: Iterable[str]) -> Dict[str, object]:
    return {k: _counts([r for r in results if key(r) == k]) for k in order if any(key(r) == k for r in results)}


def summarize(results: List[LabelResult]) -> Dict[str, object]:
    """Counts, coverage, counts per type, per evidence kind and per first rule, and every failed test."""
    summary = _counts(results)
    summary["by_type"] = _grouped(results, lambda r: r.type, frames.TYPES)
    summary["by_evidence"] = _grouped(results, lambda r: r.evidence_kind, EVIDENCE_KINDS)
    summary["by_rule"] = _grouped(results, lambda r: r.rules[0], sorted({r.rules[0] for r in results}))
    failures = []
    for r in results:
        for test, passed, after in (("comprehensiveness", r.comprehensive, r.types_after_deletion),
                                    ("sufficiency", r.sufficient, r.types_after_keep_only)):
            if not passed:
                failures.append({"clause_id": r.clause_id, "type": r.type, "test": test, "rules": r.rules,
                                 "rationale": r.rationale, "types_before": r.types_before, "types_after": after})
    summary["failures"] = failures
    return summary


def _rows(groups: Dict[str, Dict[str, object]], names: Optional[Dict[str, str]] = None) -> List[str]:
    names = {k: (names or {}).get(k, k) for k in groups}
    width = max((len(name) for name in names.values()), default=0)
    return [f"  {names[k]:<{width}}  labels {c['labels']:>3}  comprehensive {c['comprehensive']:>3}  "
            f"sufficient {c['sufficient']:>3}  both {c['both']:>3}  own clause cited {c['cites_own_clause']:>3}  "
            f"coverage mean {c['coverage_mean']:.2f}" for k, c in groups.items()]


def format_report(title: str, summary: Dict[str, object], notes: Iterable[str] = ()) -> str:
    n = summary["labels"]
    lines = [title, "=" * len(title), ""]
    lines.extend(notes)
    lines += [
        f"Labels (clause, type) checked: {n}",
        f"Comprehensiveness (deleting the rationale removes the type): {summary['comprehensive']}/{n}",
        f"Sufficiency (the rationale alone keeps the type): {summary['sufficient']}/{n}",
        f"Both: {summary['both']}/{n}",
        f"Labels whose rationale cites text in their own clause: {summary['cites_own_clause']}/{n}",
        f"Rationale coverage of the touched clauses' text (the clauses it cites plus the label's own clause): "
        f"mean {summary['coverage_mean']:.2f}, median {summary['coverage_median']:.2f}",
        "",
        "By evidence (list-structure labels take their type from another label, so their tests largely repeat "
        "that label's):",
        *_rows(summary["by_evidence"], EVIDENCE_KINDS),
        "",
        "By first rule:",
        *_rows(summary["by_rule"]),
        "",
        "By type:",
        *_rows(summary["by_type"]),
    ]
    failures = summary["failures"]
    lines += ["", f"Failed tests ({len(failures)}):"]
    for f in failures:
        lines.append(f"- {f['clause_id']} {f['type']}: {f['test']} failed (rules: {', '.join(f['rules'])}); "
                     f"types before {f['types_before']}, after {f['types_after']}")
        for span in f["rationale"]:
            lines.append(f"    rationale  {span}")
    return "\n".join(lines) + "\n"
