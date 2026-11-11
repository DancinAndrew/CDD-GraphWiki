"""
The version-2 rules judge how a requirement is phrased. Each test isolates one mechanism with short
made-up clauses, so the behaviour does not depend on any one regulation's wording.
"""
from typing import Dict, List, Optional, Set, Tuple

from src.contracts.models import Clause
from src.extraction.extractor import RuleBasedObligationExtractor, extract_obligations

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


def _types(*rows) -> Dict[str, Set[str]]:
    extractor = RuleBasedObligationExtractor(jurisdictions={DOC: "Testland"})
    return extractor.classify(_clauses(*rows))


def test_permissions_and_exemptions_switch_a_duty_off():
    types = _types(
        ("6.16", None, "### 6.16 A bank shall not be required to inquire if there exists any beneficial owner in relation to a customer that is -"),
        ("6.16/a", f"{DOC}_6_16", "(a) an entity listed on a stock exchange;"),
        ("6.33", None, "### 6.33 A bank may establish business relations with a customer before completing the verification of the identity of the customer."),
        ("8.4", None, "### 8.4 A bank may adopt a risk-based approach in determining whether to perform enhanced CDD measures for domestic politically exposed persons."),
    )
    assert all(not t for t in types.values()), types


def test_the_subject_decides_the_identification_type():
    types = _types(
        ("1.1", None, "### 1.1 The bank shall identify each customer."),
        ("1.2", None, "### 1.2 The bank shall identify the connected parties of the customer."),
        ("1.3", None, "### 1.3 The bank shall verify the identity of each natural person appointed to act on behalf of the customer."),
        ("1.4", None, "### 1.4 A beneficiary institution shall identify and verify the identity of the wire transfer beneficiary."),
        ("1.5", None, "### 1.5 The bank shall inquire if there exists any beneficial owner in relation to a customer."),
        ("1.6", None, "### 1.6 Every customer must be identified and verified before onboarding."),
    )
    assert types[f"{DOC}_1_1"] == {"verify_customer"}
    assert types[f"{DOC}_1_2"] == set()
    assert types[f"{DOC}_1_3"] == set()
    assert types[f"{DOC}_1_4"] == {"verify_customer"}
    assert types[f"{DOC}_1_5"] == {"identify_ubo"}
    assert types[f"{DOC}_1_6"] == {"verify_customer"}


def test_a_clause_can_carry_two_types():
    types = _types(("2.1", None, "### 2.1 The bank shall complete verification of the identity of a customer and of the "
                                 "beneficial owners of the customer before it establishes business relations."))
    assert types[f"{DOC}_2_1"] == {"verify_customer", "identify_ubo"}


def test_list_items_inherit_conditions_but_not_separate_duties_or_exceptions():
    types = _types(
        ("3.1", None, "### 3.1 A bank that undertakes any transaction of a value exceeding S$20,000 for a walk-in customer shall –"),
        ("3.1/a", f"{DOC}_3_1", "(a) perform CDD measures as if the customer had applied to establish business relations; and"),
        ("3.1/b", f"{DOC}_3_1", "(b) record adequate details of the transaction."),
        ("3.2", None, "### 3.2 A bank shall perform CDD measures when -"),
        ("3.2/a", f"{DOC}_3_2", "(a) it establishes business relations with a customer;"),
        ("3.3", None, "### 3.3 When a bank acquires the business of another bank, it shall perform CDD measures on the customers acquired except where it has –"),
        ("3.3/a", f"{DOC}_3_3", "(a) obtained all corresponding customer records;"),
    )
    assert types[f"{DOC}_3_1_a"] == {"cdd_triggers"}
    assert types[f"{DOC}_3_1_b"] == set()
    assert types[f"{DOC}_3_1"] == {"cdd_triggers"}  # the lead-in takes the one type its items share
    assert types[f"{DOC}_3_2_a"] == {"cdd_triggers"}
    assert types[f"{DOC}_3_3"] == {"cdd_triggers"}
    assert types[f"{DOC}_3_3_a"] == set()           # an exception, not part of the duty


def test_cross_references_resolve_who_is_identified():
    types = _types(
        ("6.14", None, "### 6.14 The bank shall identify the beneficial owners of the customer."),
        ("6.14A", None, "### 6.14A For the purposes of paragraph 6.14, the bank shall obtain at least the following information:"),
        ("6.14A/a", f"{DOC}_6_14A", "(a) full name, including any aliases;"),
        ("6.14B", None, "### 6.14B The bank shall verify the identity of each person identified under paragraph 6.14."),
    )
    assert types[f"{DOC}_6_14A"] == {"identify_ubo"}
    assert types[f"{DOC}_6_14A_a"] == {"identify_ubo"}
    assert types[f"{DOC}_6_14B"] == {"identify_ubo"}


def test_mentions_that_are_not_duties_do_not_count():
    types = _types(
        ("4.1", None, "### 4.1 If a review reveals a failure to verify a UBO, the case must be escalated within 5 business days."),
        ("4.2", None, "### 4.2 The bank shall perform the following measures, in addition to CDD measures, when providing correspondent banking:"),
        ("4.3", None, "### 4.3 A bank shall perform enhanced CDD measures where the customer is a politically exposed person."),
    )
    assert types[f"{DOC}_4_1"] == set()
    assert types[f"{DOC}_4_2"] == set()
    assert types[f"{DOC}_4_3"] == {"pep_edd"}


def test_a_jurisdiction_without_its_own_profile_still_gets_obligations():
    clauses = _clauses(("9.1", None, "### 9.1 No bank shall open or maintain an anonymous account or an account in a fictitious name."))
    obligations, _ = extract_obligations(clauses, RuleBasedObligationExtractor(jurisdictions={DOC: "Testland"}))
    assert [(o.obligation_id, o.jurisdiction, o.source_clause_ids) for o in obligations] == [
        ("ob_prohibit_anonymous_testland", "Testland", [f"{DOC}_9_1"])]


def test_every_type_comes_with_the_rule_that_gave_it():
    clauses = _clauses(
        ("3.1", None, "### 3.1 A bank that undertakes any transaction of a value exceeding S$20,000 for a walk-in customer shall –"),
        ("3.1/a", f"{DOC}_3_1", "(a) perform CDD measures as if the customer had applied to establish business relations; and"),
        ("3.2", None, "### 3.2 A bank shall perform CDD measures when -"),
        ("3.2/a", f"{DOC}_3_2", "(a) it establishes business relations with a customer;"),
    )
    traced = RuleBasedObligationExtractor(jurisdictions={DOC: "Testland"}).classify_traced(clauses)
    rules = {cid: {t: [r.rule for r in reasons] for t, reasons in types.items()} for cid, types in traced.items()}
    assert rules == {
        f"{DOC}_3_1": {"cdd_triggers": ["list.propagate"]},
        f"{DOC}_3_1_a": {"cdd_triggers": ["trigger.cdd_on_condition"]},
        f"{DOC}_3_2": {"cdd_triggers": ["trigger.cdd_on_condition"]},
        f"{DOC}_3_2_a": {"cdd_triggers": ["list.inherit"]},
    }
    # the item's condition sits in its lead-in, so the item's reason cites both clauses
    cited = {(s.clause_id, s.text) for s in traced[f"{DOC}_3_1_a"]["cdd_triggers"][0].spans}
    assert {(f"{DOC}_3_1", "that undertakes"), (f"{DOC}_3_1_a", "perform"), (f"{DOC}_3_1_a", "CDD measures")} <= cited
    assert traced[f"{DOC}_3_1"]["cdd_triggers"][0].depends_on == [f"{DOC}_3_1_a#cdd_triggers"]
