"""
Every rules-v2 decision keeps its reasons: the rule that fired, one sentence, and the exact text it rests on.
The deletion tests in src/extraction/faithfulness.py check that the cited text is what the decision used.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import yaml

from src.contracts.models import Clause, Obligation
from src.extraction import frames, faithfulness
from src.extraction.extractor import _paragraph_of
from src.graph.builder import GraphBuilder
from src.heldout.evaluate import HELDOUT_SETS, load_corpus

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = os.environ["CDD_PROCESSED_DIR"]  # rebuilt by conftest.py
DOC = "test_doc"


def _clauses(*rows: Tuple[str, Optional[str], str]) -> List[Clause]:
    """rows: (paragraph or paragraph/item, parent id or None, raw text)"""
    clauses = []
    for ref, parent, text in rows:
        paragraph, _, item = ref.partition("/")
        section_ref = f"1 Test > {paragraph}" + (f" > ({item})" if item else "")
        clause_id = f"{DOC}_{ref.replace('.', '_').replace('/', '_')}"
        clauses.append(Clause(clause_id=clause_id, source_document_id=DOC, section_ref=section_ref,
                              parent_clause_id=parent, raw_text=text, normalized_text=text.lower(),
                              citations=[clause_id]))
    return clauses


def _development_documents() -> Dict[str, List[Clause]]:
    with open(os.path.join(PROCESSED, "clauses.yaml"), encoding="utf-8") as f:
        clauses = [Clause.model_validate(c) for c in yaml.safe_load(f)]
    documents: Dict[str, List[Clause]] = {}
    for clause in clauses:
        documents.setdefault(clause.source_document_id, []).append(clause)
    return documents


def _all_documents() -> List[Tuple[str, List[Clause]]]:
    documents = [(f"dev:{name}", clauses) for name, clauses in _development_documents().items()]
    documents += [(name, load_corpus(str(REPO_ROOT / "data"), name).clauses) for name in HELDOUT_SETS]
    return documents


@pytest.fixture(scope="module")
def dev_trace():
    clauses = _development_documents()["mas_notice_626"]
    return clauses, frames.classify_traced(clauses, _paragraph_of)


# --- the trace -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,clauses", _all_documents(), ids=lambda x: x if isinstance(x, str) else "")
def test_the_trace_gives_the_same_types_and_cites_real_text(name, clauses):
    traced = frames.classify_traced(clauses, _paragraph_of)
    assert {cid: set(types) for cid, types in traced.items()} == frames.classify(clauses, _paragraph_of)
    by_id = {c.clause_id: c for c in clauses}
    for clause_id, types in traced.items():
        for type_, reasons in types.items():
            assert reasons, f"{clause_id} {type_} has no reason"
            for reason in reasons:
                assert reason.obligation_type == type_ and reason.message
                assert reason.spans or reason.depends_on, f"{clause_id} {type_} {reason.rule} cites nothing"
                for span in reason.spans:
                    raw = by_id[span.clause_id].raw_text
                    assert raw[span.start:span.end] == span.text and span.text.strip() == span.text
                    assert frames.body_start(raw) <= span.start < span.end <= len(raw)
                for label in reason.depends_on:
                    dep_clause, _, dep_type = label.rpartition("#")
                    assert dep_type in traced[dep_clause], f"{clause_id} depends on missing label {label}"


@pytest.mark.parametrize("raw", [
    "### 6.14A For the purposes of paragraph 6.14,\n  the bank shall obtain:",
    "(ii) a  value\ttransfer   originator ",
    "  ## 3 Title",
    "(a)",
    "19(3)(b) İstanbul branch  — must verify",
    # "İ" lower-cases to two characters, and a word-final "Σ" lower-cases to "ς" only in the whole string
    "### 1.1 The bank shall identify each customer, including branches in İSTANBUL and at ΟΔΟΣ ΑΘΗΝΑΣ.",
])
def test_body_offsets_point_back_into_the_raw_text(raw):
    body, positions = frames.body_text(raw), frames.body_offsets(raw)
    assert len(positions) == len(body)
    for i, ch in enumerate(body):
        source = raw[positions[i]]
        assert ch in source.lower() or ch.upper() == source or (ch == " " and source.isspace())
    assert positions == sorted(positions)
    assert frames.body_start(raw) == (positions[0] if positions else len(raw))


def test_a_clause_with_dotted_capital_i_and_final_sigma_is_traced():
    clauses = _clauses(("1.1", None, "### 1.1 The bank shall identify the customer at İSTANBUL ΟΔΟΣ."))
    traced = frames.classify_traced(clauses, _paragraph_of)
    assert set(traced[f"{DOC}_1_1"]) == {"verify_customer"}
    assert [s.text for s in traced[f"{DOC}_1_1"]["verify_customer"][0].spans] == ["shall", "identify", "the customer"]
    (result,) = faithfulness.evaluate_document(clauses, _paragraph_of, traced)
    assert result.comprehensive and result.sufficient


def test_sentence_offsets_match_the_sentences():
    text = "the bank shall, e.g. by phone, verify the customer. it must; then stop.  done"
    spans = frames.sentence_spans(text)
    assert [s for _, s in spans] == frames.sentences(text)
    assert all(text[start:start + len(s)] == s for start, s in spans)


def test_the_cdd_incomplete_reason_cites_unable_and_shall_not_commence(dev_trace):
    clauses, traced = dev_trace
    reasons = traced["mas_notice_626_6_cdd_6_35"]["cdd_incomplete"]
    assert [r.rule for r in reasons] == ["incomplete.unable_and_stop"]
    texts = {s.text for s in reasons[0].spans}
    assert {"unable to complete", "shall not commence"} <= texts


def _message(raw_rows, clause_id: str, type_: str) -> str:
    (reason,) = frames.classify_traced(_clauses(*raw_rows), _paragraph_of)[clause_id][type_]
    return reason.message


def test_messages_say_what_the_rule_checked_not_a_relation_it_did_not():
    # The PEP and incomplete rules only test that their words occur in one sentence; the messages say so, even
    # where the rule fires on a sentence that says the opposite.
    rows = [("8.2", None, "### 8.2 A bank shall not reject an account application solely because the applicant "
                          "is a politically exposed person.")]
    assert _message(rows, f"{DOC}_8_2", "pep_prohibition") == (
        '"reject" and "account" occur in a sentence that mentions a politically exposed person ("politically exposed").')
    rows = [("8.1", None, "### 8.1 A bank must not treat a customer as a politically exposed person merely because "
                          "enhanced monitoring was applied.")]
    assert _message(rows, f"{DOC}_8_1", "pep_edd") == (
        '"must" and "enhanced monitoring" occur in a sentence that mentions a politically exposed person '
        '("politically exposed").')
    rows = [("9.1", None, "### 9.1 Where the bank is unable to comply with paragraph 4, it shall not open the account.")]
    assert _message(rows, f"{DOC}_9_1", "cdd_incomplete") == '"unable to comply" and "shall not open" occur in one sentence.'


def test_starts_with_names_the_item_only_for_the_first_sentence_of_a_list_item():
    rows = [("5.1", None, "### 5.1 Records of the customer are kept for five years. Verify the customer's records "
                          "annually.")]
    assert _message(rows, f"{DOC}_5_1", "verify_customer") == (
        'The sentence starts with "verify", whose object is the customer.')
    rows = [("5.2", None, "### 5.2 The bank shall –"),
            ("5.2/a", f"{DOC}_5_2", "(a) verify the customer's identity;")]
    traced = frames.classify_traced(_clauses(*rows), _paragraph_of)
    (reason,) = traced[f"{DOC}_5_2_a"]["verify_customer"]
    assert reason.message == 'The item starts with "verify", whose object is the customer.'


def test_a_trigger_message_says_where_the_condition_was_found():
    rows = [("6.29", None, "### 6.29 The bank shall perform CDD measures where it has doubts about the customer."),
            ("6.31", None, "### 6.31 A bank that undertakes a transaction shall –"),
            ("6.31/a", f"{DOC}_6_31", "(a) perform CDD measures;")]
    traced = frames.classify_traced(_clauses(*rows), _paragraph_of)
    (own,) = traced[f"{DOC}_6_29"]["cdd_triggers"]
    assert own.message == ('"shall" governs "perform" with the object "cdd measures", and the condition "where" '
                           'occurs in the same sentence.')
    (enclosing,) = traced[f"{DOC}_6_31_a"]["cdd_triggers"]
    assert enclosing.message == ('The item starts with "perform" with the object "cdd measures", and the condition '
                                 '"that undertakes" occurs in the enclosing text.')


def test_an_inherited_item_cites_its_lead_in(dev_trace):
    clauses, traced = dev_trace
    (reason,) = traced["mas_notice_626_6_cdd_6_3_a"]["cdd_triggers"]
    assert reason.rule == "list.inherit"
    assert reason.depends_on == ["mas_notice_626_6_cdd_6_3#cdd_triggers"]
    assert [(s.clause_id, s.text) for s in reason.spans] == [("mas_notice_626_6_cdd_6_3", "when -")]
    lead_texts = {s.text for r in traced["mas_notice_626_6_cdd_6_3"]["cdd_triggers"] for s in r.spans}
    assert {"shall", "perform", "when"} <= lead_texts


def test_a_cross_reference_depends_on_the_referenced_paragraph():
    clauses = _clauses(
        ("6.14", None, "### 6.14 The bank shall identify the beneficial owners of the customer."),
        ("6.14B", None, "### 6.14B The bank shall verify the identity of each person identified under paragraph 6.14."),
    )
    (reason,) = frames.classify_traced(clauses, _paragraph_of)[f"{DOC}_6_14B"]["identify_ubo"]
    assert reason.rule == "identify.cross_reference"
    assert reason.depends_on == [f"{DOC}_6_14#identify_ubo"]
    assert [s.text for s in reason.spans] == ["shall", "verify", "person identified under paragraph 6.14"]


def test_every_alternative_condition_is_recorded():
    clauses = _clauses(("27.2", None, "### 27.2 A bank must apply customer due diligence measures if the bank carries "
                                      "out an occasional transaction that amounts to a transfer of funds exceeding £1,000."))
    (reason,) = frames.classify_traced(clauses, _paragraph_of)[f"{DOC}_27_2"]["cdd_triggers"]
    texts = [s.text for s in reason.spans]
    assert {"must", "apply", "customer due diligence measures", "if", "£1"} <= set(texts)
    assert texts.count("transaction") == 1  # the amount alternative brings its "transaction" too


# --- deletion tests ------------------------------------------------------------------------------------------

def test_a_label_whose_rationale_is_comprehensive_and_sufficient():
    clauses = _clauses(("1.1", None, "### 1.1 Before opening an account, the bank shall identify each customer "
                                     "and keep the records for five years."))
    (result,) = faithfulness.evaluate_document(clauses, _paragraph_of)
    assert (result.clause_id, result.type) == (f"{DOC}_1_1", "verify_customer")
    assert result.comprehensive and result.sufficient
    assert result.rationale == [f"{DOC}_1_1: shall", f"{DOC}_1_1: identify", f"{DOC}_1_1: each customer"]
    assert 0 < result.coverage < 0.5


def test_the_deletion_test_runs_on_the_whole_document():
    clauses = _clauses(
        ("3.2", None, "### 3.2 A bank shall perform CDD measures when -"),
        ("3.2/a", f"{DOC}_3_2", "(a) it establishes business relations with a customer;"),
    )
    traced = frames.classify_traced(clauses, _paragraph_of)
    spans = faithfulness.rationale(traced, f"{DOC}_3_2_a", "cdd_triggers")
    assert set(spans) == {f"{DOC}_3_2"}  # the item's own text plays no part: its rationale is in the lead-in
    after = frames.classify(faithfulness.delete_rationale(clauses, spans), _paragraph_of)
    assert after[f"{DOC}_3_2_a"] == set()
    kept = faithfulness.keep_only_rationale(clauses, spans)
    assert kept[1].raw_text == "(a) " and frames.classify(kept, _paragraph_of)[f"{DOC}_3_2_a"] == {"cdd_triggers"}
    results = {r.clause_id: r for r in faithfulness.evaluate_document(clauses, _paragraph_of)}
    assert results[f"{DOC}_3_2_a"].comprehensive and results[f"{DOC}_3_2_a"].sufficient


def test_the_summary_separates_list_structure_labels_from_own_evidence():
    clauses = _clauses(
        ("3.2", None, "### 3.2 A bank shall perform CDD measures when -"),
        ("3.2/a", f"{DOC}_3_2", "(a) it establishes business relations with a customer;"),
        ("3.3", None, "### 3.3 The bank shall –"),
        ("3.3/a", f"{DOC}_3_3", "(a) identify the beneficial owners of the customer;"),
    )
    results = {(r.clause_id, r.type): r for r in faithfulness.evaluate_document(clauses, _paragraph_of)}
    assert {k: (r.rules[0], r.evidence_kind, r.cites_own_clause) for k, r in results.items()} == {
        (f"{DOC}_3_2", "cdd_triggers"): ("trigger.cdd_on_condition", "own_evidence", True),
        (f"{DOC}_3_2_a", "cdd_triggers"): ("list.inherit", "list_structure", False),  # cites only the lead-in
        (f"{DOC}_3_3", "identify_ubo"): ("list.propagate", "list_structure", True),   # its own "–"
        (f"{DOC}_3_3_a", "identify_ubo"): ("identify.subject", "own_evidence", True),
    }
    summary = faithfulness.summarize(list(results.values()))
    assert summary["cites_own_clause"] == 3
    assert {k: v["labels"] for k, v in summary["by_evidence"].items()} == {"own_evidence": 2, "list_structure": 2}
    assert list(summary["by_rule"]) == ["identify.subject", "list.inherit", "list.propagate", "trigger.cdd_on_condition"]
    report = faithfulness.format_report("t", summary)
    assert "Labels whose rationale cites text in their own clause: 3/4" in report
    assert "By first rule:" in report and "list structure (list.inherit, list.propagate)" in report


def test_a_type_that_another_clause_restores_fails_comprehensiveness():
    # Lead-in and item each give identify_ubo with their own words, so neither inherits. Delete the lead-in's
    # rationale and its item gives the type back through "shall –" propagation; delete the item's and it inherits
    # the type from the lead-in. The reasons are what the decision used; the type is over-determined.
    clauses = _clauses(
        ("6.14", None, "### 6.14 The bank shall identify the beneficial owners. To do so, the bank shall –"),
        ("6.14/a", f"{DOC}_6_14", "(a) identify the natural persons who ultimately own the legal person;"),
    )
    traced = frames.classify_traced(clauses, _paragraph_of)
    assert [r.rule for r in traced[f"{DOC}_6_14_a"]["identify_ubo"]] == ["identify.subject"]
    results = {r.clause_id: r for r in faithfulness.evaluate_document(clauses, _paragraph_of, traced)}
    for result in results.values():
        assert not result.comprehensive and result.types_after_deletion == ["identify_ubo"]
        assert result.sufficient
    summary = faithfulness.summarize(list(results.values()))
    assert (summary["labels"], summary["comprehensive"], summary["sufficient"]) == (2, 0, 2)
    assert [(f["clause_id"], f["test"]) for f in summary["failures"]] == [
        (f"{DOC}_6_14", "comprehensiveness"), (f"{DOC}_6_14_a", "comprehensiveness")]
    assert "comprehensiveness failed" in faithfulness.format_report("t", summary)


# --- where the reasons go ------------------------------------------------------------------------------------

def test_rule_obligations_carry_reasons_for_every_source_clause():
    with open(os.path.join(PROCESSED, "obligations.yaml"), encoding="utf-8") as f:
        obligations = [Obligation.model_validate(o) for o in yaml.safe_load(f)]
    for ob in obligations:
        assert list(ob.explanations) == ob.source_clause_ids, ob.obligation_id
        types = {r.obligation_type for reasons in ob.explanations.values() for r in reasons}
        assert len(types) == 1 and all(ob.explanations.values()), ob.obligation_id


def test_rule_obligation_reasons_name_the_obligations_own_rule_type():
    """Every reason of a rule obligation is for the rule type its obligation ID was built from."""
    import re
    from src.extraction.extractor import profile_for

    def rule_type_of(ob: Obligation) -> str:
        hits = [t for t in frames.TYPES
                if re.fullmatch(re.escape(profile_for(t, ob.jurisdiction).obligation_id).replace(r"\{pct\}", r"(?:_\d+)?"),
                                ob.obligation_id)]
        assert len(hits) == 1, (ob.obligation_id, hits)
        return hits[0]

    with open(os.path.join(PROCESSED, "obligations.yaml"), encoding="utf-8") as f:
        obligations = [Obligation.model_validate(o) for o in yaml.safe_load(f)]
    assert obligations
    for ob in obligations:
        rule_type = rule_type_of(ob)
        reasons = [r for clause_reasons in ob.explanations.values() for r in clause_reasons]
        assert reasons and all(r.obligation_type == rule_type for r in reasons), ob.obligation_id


def test_reference_edges_carry_the_reason_messages():
    clauses = _clauses(("9.1", None, "### 9.1 No bank shall open or maintain an anonymous account."))
    from src.extraction.extractor import RuleBasedObligationExtractor, extract_obligations
    obligations, _ = extract_obligations(clauses, RuleBasedObligationExtractor(jurisdictions={DOC: "Testland"}))
    graph = GraphBuilder.build_regulatory_graph([], clauses, obligations, [], [])
    (edge,) = [e for e in graph.edges if e.edge_type == "references_clause" and e.source_id == obligations[0].obligation_id]
    assert edge.properties["reasons"] == [obligations[0].explanations[f"{DOC}_9_1"][0].message]


def test_the_pipeline_reports_explanation_faithfulness():
    with open(os.path.join(PROCESSED, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    xf = summary["explanation_faithfulness"]
    assert xf["labels"] > 0 and 0 <= xf["comprehensive"] <= xf["labels"] and 0 <= xf["sufficient"] <= xf["labels"]
    assert 0 < xf["coverage_median"] < 1
    assert sum(v["labels"] for v in xf["by_evidence"].values()) == xf["labels"]
    assert sum(v["labels"] for v in xf["by_rule"].values()) == xf["labels"]
    assert 0 < xf["cites_own_clause"] <= xf["labels"]
    assert os.path.exists(os.path.join(PROCESSED, "explanation_faithfulness.txt"))
