"""
檢核表決策樹與解釋的忠實度測試：
- 決策樹與獨立寫成的 if/else 參考實作在完整格點上輸出完全相同
- 和重構前引擎的差異，正好只出現在三項修正影響的客戶群
- 五位範例客戶的分支、路徑與文件 → 義務對應
- 每個回報的反事實套用後都能重現
- 路徑加上標記條件足以決定輸出：同一簽章的客戶清單完全相同
- 風險標記宣告的義務、由什麼保證成立、列出的標記一定對客戶成立、引擎不讀的屬性
"""
import itertools
import os
import random
from typing import Dict, List, Literal

import pytest
import yaml
from fastapi.testclient import TestClient

from src.contracts.models import CDDChecklist, Clause, Conflict, CustomerContext, Obligation, SourceDocument
from src.decision.engine import LEAVES, OWNERSHIP_CHART, CDDChecklistEngine, checked_by, route
from src.decision.explain import apply_change, explain

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(REPO_ROOT, "data", "processed")
GOLD_DIR = os.path.join(REPO_ROOT, "data", "gold")


def _load(directory: str, filename: str, model):
    with open(os.path.join(directory, filename), "r", encoding="utf-8") as f:
        return [model(**item) for item in yaml.safe_load(f) or []]


@pytest.fixture(scope="module")
def kb():
    return {
        "customers": {c.customer_id: c for c in _load(GOLD_DIR, "customer_contexts.yaml", CustomerContext)},
        "obligations": _load(PROCESSED_DIR, "obligations.yaml", Obligation),
        "conflicts": _load(PROCESSED_DIR, "conflicts.yaml", Conflict),
        "clauses": _load(PROCESSED_DIR, "clauses.yaml", Clause),
        "documents": _load(PROCESSED_DIR, "source_documents.yaml", SourceDocument),
    }


def _explain(kb, customer, conflicts=None):
    conflicts = kb["conflicts"] if conflicts is None else conflicts
    return explain(customer, kb["obligations"], conflicts, kb["clauses"], kb["documents"])


# ---------- 重構前引擎的凍結副本（只作為等價比對的參考，不要修改） ----------

def reference_generate_checklist(customer: CustomerContext, obligations: List[Obligation],
                                 conflicts: List[Conflict]) -> CDDChecklist:
    customer_id = customer.customer_id
    decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = "standard_cdd"
    required_documents: List[str] = []
    risk_triggers: List[str] = []
    applicable_obligations: List[str] = []
    unresolved_conflicts: List[str] = []
    human_review_required = False

    if customer.customer_type == "individual":
        if customer.pep_exposure:
            if customer.ubo_country_risk == "high" or customer.registration_jurisdiction.lower() == "myanmar":
                decision = "enhanced_due_diligence"
                required_documents = ["Rejected Onboarding Notification"]
                risk_triggers = ["pep_from_high_risk_jurisdiction", "onboarding_prohibited_by_policy"]
                applicable_obligations = ["ob_pep_prohibitions_gb"]
                human_review_required = True
            else:
                decision = "enhanced_due_diligence"
                required_documents = [
                    "National Identity Card (NRIC) or Passport",
                    "Proof of Address",
                    "Senior Management Approval Form",
                    "Source of Funds Declaration & Evidence",
                    "Source of Wealth Declaration & Evidence",
                    "Head of Compliance Approval Form"
                ]
                risk_triggers = ["pep_exposure_detected"]
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_pep_edd_mas", "ob_pep_approval_gb"
                ]
                human_review_required = True
        else:
            decision = "standard_cdd"
            required_documents = ["National Identity Card (NRIC)", "Proof of Residential Address"]
            risk_triggers = []
            applicable_obligations = ["ob_cdd_on_relationship_mas", "ob_verify_customer_mas"]
            human_review_required = False

    elif customer.customer_type == "corporate":
        if customer.ubo_status == "unclear" or customer.registration_jurisdiction.lower() == "cayman islands":
            decision = "enhanced_due_diligence"
            required_documents = ["Account Opening Rejection Notice", "STR Evaluation File"]
            risk_triggers = ["unclear_ubo_status", "excessive_layering_5", "missing_source_of_funds_evidence"]
            applicable_obligations = [
                "ob_cdd_on_relationship_mas", "ob_identify_ubo_mas", "ob_identify_ubo_10_gb", "ob_cdd_incomplete_mas"
            ]
            human_review_required = True
        else:
            decision = "standard_cdd"
            share_pct = customer.custom_attributes.get("major_shareholder_pct", 0)
            if 10 <= share_pct <= 25:
                required_documents = [
                    "Certificate of Incorporation",
                    "ACRA Company Profile",
                    "Shareholder Registry",
                    "UBO 15% Shareholder Identity Document (NRIC/Passport)"
                ]
                risk_triggers = ["internal_ubo_threshold_triggered_10_percent"]
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_identify_ubo_mas", "ob_identify_ubo_10_gb"
                ]
                human_review_required = True
            else:
                required_documents = ["Certificate of Incorporation", "ACRA Company Profile"]
                risk_triggers = []
                applicable_obligations = ["ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_identify_ubo_mas"]
                human_review_required = False

    ob_dict = {ob.obligation_id: ob for ob in obligations}
    citations: List[str] = []
    for ob_id in applicable_obligations:
        ob = ob_dict.get(ob_id)
        if ob and ob.source_clause_ids and ob.source_clause_ids[0] not in citations:
            citations.append(ob.source_clause_ids[0])

    applicable_clause_ids = {
        cid for ob_id in applicable_obligations if ob_id in ob_dict for cid in ob_dict[ob_id].source_clause_ids
    }
    for conflict in conflicts:
        if conflict.adjudication_status != "resolved" and applicable_clause_ids.intersection(conflict.source_clause_ids):
            unresolved_conflicts.append(conflict.conflict_id)
    if unresolved_conflicts:
        human_review_required = True

    return CDDChecklist(
        checklist_id=f"chk_{customer_id.replace('cust_', '')}",
        customer_id=customer_id,
        decision=decision,
        required_documents=required_documents,
        risk_triggers=risk_triggers,
        applicable_obligations=applicable_obligations,
        unresolved_conflicts=unresolved_conflicts,
        human_review_required=human_review_required,
        citations=citations
    )


# ---------- 修正後規格的參考實作（獨立於決策樹，用 if/else 寫） ----------
# 與上面的舊引擎相比，三項修正：
# 1. 風險標記只在條件對客戶成立時列出；UBO 不明分支不再無條件列出多層持股與資金來源標記
# 2. 多層持股依銀行政策 1.2(b) 的 3 層（不是 5 層），而且 UBO 已識別時成為真正的分支：高風險、簽核持股架構圖
# 3. 資金與財富來源只在有法源的 PEP 分支檢查（MAS 8.3(b)）；註冊在開曼群島不再等於 CDD 無法完成

UBO_15_ID = "UBO 15% Shareholder Identity Document (NRIC/Passport)"


def revised_reference_generate_checklist(customer: CustomerContext, obligations: List[Obligation],
                                         conflicts: List[Conflict]) -> CDDChecklist:
    decision: Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"] = "standard_cdd"
    required_documents: List[str] = []
    risk_triggers: List[str] = []
    applicable_obligations: List[str] = []
    human_review_required = False
    complex_ownership = customer.ownership_layers >= 3

    if customer.customer_type == "individual":
        if customer.pep_exposure:
            if customer.ubo_country_risk == "high" or customer.registration_jurisdiction.lower() == "myanmar":
                decision = "enhanced_due_diligence"
                required_documents = ["Rejected Onboarding Notification"]
                risk_triggers = ["pep_from_high_risk_jurisdiction", "onboarding_prohibited_by_policy"]
                applicable_obligations = ["ob_pep_prohibitions_gb"]
                human_review_required = True
            else:
                decision = "enhanced_due_diligence"
                required_documents = [
                    "National Identity Card (NRIC) or Passport", "Proof of Address", "Senior Management Approval Form",
                    "Source of Funds Declaration & Evidence", "Source of Wealth Declaration & Evidence",
                    "Head of Compliance Approval Form",
                ]
                risk_triggers = ["pep_exposure_detected"]
                if not customer.source_of_funds_available:
                    risk_triggers.append("missing_source_of_funds_evidence")
                if not customer.source_of_wealth_available:
                    risk_triggers.append("missing_source_of_wealth_evidence")
                applicable_obligations = [
                    "ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_pep_edd_mas", "ob_pep_approval_gb"]
                human_review_required = True
        else:
            required_documents = ["National Identity Card (NRIC)", "Proof of Residential Address"]
            applicable_obligations = ["ob_cdd_on_relationship_mas", "ob_verify_customer_mas"]

    elif customer.customer_type == "corporate":
        if customer.ubo_status == "unclear":
            decision = "enhanced_due_diligence"
            required_documents = ["Account Opening Rejection Notice", "STR Evaluation File"]
            risk_triggers = ["unclear_ubo_status"] + (["complex_ownership_3_layers"] if complex_ownership else [])
            applicable_obligations = [
                "ob_cdd_on_relationship_mas", "ob_identify_ubo_mas", "ob_identify_ubo_10_gb", "ob_cdd_incomplete_mas"]
            human_review_required = True
        else:
            share_pct = customer.custom_attributes.get("major_shareholder_pct", 0)
            threshold = 10 <= share_pct <= 25
            ubo_documents = ["Shareholder Registry", UBO_15_ID] if threshold else []
            threshold_trigger = ["internal_ubo_threshold_triggered_10_percent"] if threshold else []
            required_documents = ["Certificate of Incorporation", "ACRA Company Profile"] + ubo_documents
            applicable_obligations = ["ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_identify_ubo_mas"]
            if complex_ownership:
                decision = "enhanced_due_diligence"
                required_documents.append(OWNERSHIP_CHART)
                risk_triggers = ["complex_ownership_3_layers"] + threshold_trigger
                applicable_obligations.append("ob_identify_ubo_10_gb")
                human_review_required = True
            elif threshold:
                risk_triggers = threshold_trigger
                applicable_obligations.append("ob_identify_ubo_10_gb")
                human_review_required = True

    ob_dict = {ob.obligation_id: ob for ob in obligations}
    citations: List[str] = []
    for ob_id in applicable_obligations:
        ob = ob_dict.get(ob_id)
        if ob and ob.source_clause_ids and ob.source_clause_ids[0] not in citations:
            citations.append(ob.source_clause_ids[0])
    applicable_clause_ids = {
        cid for ob_id in applicable_obligations if ob_id in ob_dict for cid in ob_dict[ob_id].source_clause_ids}
    unresolved_conflicts = [
        conflict.conflict_id for conflict in conflicts
        if conflict.adjudication_status != "resolved" and applicable_clause_ids.intersection(conflict.source_clause_ids)
    ]
    return CDDChecklist(
        checklist_id=f"chk_{customer.customer_id.replace('cust_', '')}",
        customer_id=customer.customer_id,
        decision=decision,
        required_documents=required_documents,
        risk_triggers=risk_triggers,
        applicable_obligations=applicable_obligations,
        unresolved_conflicts=unresolved_conflicts,
        human_review_required=human_review_required or bool(unresolved_conflicts),
        citations=citations,
    )


# ---------- 等價性：完整格點 ----------

JURISDICTIONS = ["Singapore", "Myanmar", "MYANMAR", "Cayman Islands", "cayman islands", "Hong Kong"]
SHAREHOLDER_PCTS = [None, 0, 9, 10, 15, 25, 26, 40]  # None = 未提供
LAYERS = [0, 2, 3, 5]  # 3 層門檻兩側各兩個值


def _customer(i, customer_type, pep, risk, ubo_status, jurisdiction, pct, layers, sof, sow) -> CustomerContext:
    custom = {} if pct is None else {"major_shareholder_pct": pct}
    return CustomerContext(
        customer_id=f"cust_grid_{i}", customer_type=customer_type, registration_jurisdiction=jurisdiction,
        ownership_layers=layers, ubo_status=ubo_status, ubo_country_risk=risk, pep_exposure=pep,
        source_of_funds_available=sof, source_of_wealth_available=sow, custom_attributes=custom,
    )


def _grid() -> List[CustomerContext]:
    axes = itertools.product(
        ["individual", "corporate"], [True, False], ["low", "medium", "high"], ["identified", "unclear"],
        JURISDICTIONS, SHAREHOLDER_PCTS, LAYERS, [True, False], [True, False],
    )
    return [_customer(i, *values) for i, values in enumerate(axes)]


def _all_pending(conflicts: List[Conflict]) -> List[Conflict]:
    return [c.model_copy(update={"adjudication_status": "pending_human_review", "resolved_by": None}) for c in conflicts]


def test_decision_tree_matches_revised_reference_on_full_grid(kb):
    customers = _grid()
    assert len(customers) == 2 * 2 * 3 * 2 * 6 * 8 * 4 * 2 * 2
    engine = CDDChecklistEngine()
    conflict_sets = {
        "processed": kb["conflicts"],
        "empty": [],
        "all_pending": _all_pending(kb["conflicts"]),
    }
    for name, conflicts in conflict_sets.items():
        mismatches = [
            c.customer_id for c in customers
            if engine.generate_checklist(c, kb["obligations"], conflicts)
            != revised_reference_generate_checklist(c, kb["obligations"], conflicts)
        ]
        assert mismatches == [], f"{name}: {mismatches[:5]}"


def _fix_group(c: CustomerContext) -> str:
    """這位客戶落在哪一項修正影響的客戶群；不受影響時為空字串。"""
    if c.customer_type == "individual":
        high_risk = c.ubo_country_risk == "high" or c.registration_jurisdiction.lower() == "myanmar"
        if c.pep_exposure and not high_risk and not (c.source_of_funds_available and c.source_of_wealth_available):
            return "pep_missing_evidence"
        return ""
    if c.ubo_status == "unclear":
        return "unclear_ubo_flags"
    if c.ownership_layers >= 3:
        return "complex_ownership"
    if c.registration_jurisdiction.lower() == "cayman islands":
        return "cayman_not_blocked"
    return ""


def test_changes_from_the_previous_engine_are_exactly_the_intended_ones(kb):
    """舊引擎與新引擎的輸出不同，若且唯若客戶落在三項修正影響的客戶群；每一群只改了該改的欄位。"""
    engine = CDDChecklistEngine()
    changed_fields: Dict[str, set] = {}
    for customer in _grid():
        before = reference_generate_checklist(customer, kb["obligations"], kb["conflicts"])
        after = engine.generate_checklist(customer, kb["obligations"], kb["conflicts"])
        group = _fix_group(customer)
        assert (before != after) == bool(group), (customer, group)
        if group:
            fields = {f for f in CDDChecklist.model_fields if getattr(before, f) != getattr(after, f)}
            changed_fields.setdefault(group, set()).update(fields)
    # PEP 與 UBO 不明：分支不變，只有風險標記改變
    assert changed_fields["pep_missing_evidence"] == {"risk_triggers"}
    assert changed_fields["unclear_ubo_flags"] == {"risk_triggers"}
    # 多層持股、開曼但 UBO 已識別：走到不同的分支
    assert {"decision", "required_documents", "risk_triggers"} <= changed_fields["complex_ownership"]
    assert {"decision", "required_documents", "applicable_obligations"} <= changed_fields["cayman_not_blocked"]


def test_three_layers_is_the_boundary_and_cayman_alone_does_not_block(kb):
    engine = CDDChecklistEngine()
    corp = kb["customers"]["cust_corp_standard"]  # 2 層、新加坡、15% 股東、UBO 已識別
    two = engine.generate_checklist(corp, kb["obligations"], kb["conflicts"])
    three = engine.generate_checklist(corp.model_copy(update={"ownership_layers": 3}), kb["obligations"], kb["conflicts"])
    assert two.decision == "standard_cdd" and "complex_ownership_3_layers" not in two.risk_triggers
    assert three.decision == "enhanced_due_diligence"
    assert three.risk_triggers == ["complex_ownership_3_layers", "internal_ubo_threshold_triggered_10_percent"]
    assert three.required_documents[-1] == OWNERSHIP_CHART

    cayman = corp.model_copy(update={"registration_jurisdiction": "Cayman Islands"})
    checklist = engine.generate_checklist(cayman, kb["obligations"], kb["conflicts"])
    assert checklist == engine.generate_checklist(corp, kb["obligations"], kb["conflicts"])
    assert "Account Opening Rejection Notice" not in checklist.required_documents


# ---------- 五位範例客戶 ----------

EXPECTED_FIXTURES: Dict[str, dict] = {
    "cust_individual_low_risk": {
        "branch": "individual_standard",
        "path": [("is_individual", True), ("is_pep", False)],
        "items": [("National Identity Card (NRIC)", "ob_verify_customer_mas"),
                  ("Proof of Residential Address", "ob_verify_customer_mas")],
    },
    "cust_corp_standard": {
        "branch": "corporate_internal_ubo_threshold",
        "path": [("is_individual", False), ("is_corporate", True), ("corporate_cdd_blocked", False),
                 ("complex_ownership", False), ("internal_ubo_threshold", True)],
        "items": [("Certificate of Incorporation", "ob_verify_customer_mas"),
                  ("ACRA Company Profile", "ob_verify_customer_mas"),
                  ("Shareholder Registry", "ob_identify_ubo_10_gb"),
                  ("UBO 15% Shareholder Identity Document (NRIC/Passport)", "ob_identify_ubo_10_gb")],
    },
    "cust_individual_pep": {
        "branch": "individual_pep",
        "path": [("is_individual", True), ("is_pep", True), ("pep_high_risk", False)],
        "items": [("National Identity Card (NRIC) or Passport", "ob_verify_customer_mas"),
                  ("Proof of Address", "ob_verify_customer_mas"),
                  ("Senior Management Approval Form", "ob_pep_edd_mas"),
                  ("Source of Funds Declaration & Evidence", "ob_pep_edd_mas"),
                  ("Source of Wealth Declaration & Evidence", "ob_pep_edd_mas"),
                  ("Head of Compliance Approval Form", "ob_pep_approval_gb")],
    },
    "cust_individual_high_risk_pep": {
        "branch": "individual_pep_high_risk",
        "path": [("is_individual", True), ("is_pep", True), ("pep_high_risk", True)],
        "items": [("Rejected Onboarding Notification", "ob_pep_prohibitions_gb")],
    },
    "cust_corp_unclear_ubo": {
        "branch": "corporate_cdd_incomplete",
        "path": [("is_individual", False), ("is_corporate", True), ("corporate_cdd_blocked", True)],
        "items": [("Account Opening Rejection Notice", "ob_cdd_incomplete_mas"),
                  ("STR Evaluation File", "ob_cdd_incomplete_mas")],
    },
}


@pytest.mark.parametrize("customer_id", sorted(EXPECTED_FIXTURES))
def test_fixture_customer_explanation(kb, customer_id):
    expected = EXPECTED_FIXTURES[customer_id]
    customer = kb["customers"][customer_id]
    exp = _explain(kb, customer)
    checklist = CDDChecklistEngine().generate_checklist(customer, kb["obligations"], kb["conflicts"])

    assert exp.branch.id == expected["branch"]
    assert [(s.test_id, s.outcome) for s in exp.path] == expected["path"]
    assert [(i.document, i.obligation_id) for i in exp.items] == expected["items"]
    # 解釋與清單一致：文件順序、決策、標記
    assert [i.document for i in exp.items] == checklist.required_documents
    assert exp.decision == checklist.decision
    assert [t.trigger for t in exp.risk_triggers] == checklist.risk_triggers
    assert set(exp.obligations_without_documents) | {i.obligation_id for i in exp.items} == set(checklist.applicable_obligations)
    for item in exp.items:
        assert item.obligation_found
        ob = next(o for o in kb["obligations"] if o.obligation_id == item.obligation_id)
        assert [c.clause_id for c in item.source_clauses] == ob.source_clause_ids
        assert all(c.raw_text for c in item.source_clauses)
        for clause in item.source_clauses:
            for hl in clause.highlights:
                assert clause.raw_text[hl["start"]:hl["end"]] == hl["text"]
    # OR 測試列出每個條件；單一條件測試不列
    for step in exp.path:
        assert (len(step.parts) > 0) == (step.test_id == "pep_high_risk")
        if step.parts:
            assert step.outcome == any(p.holds for p in step.parts)


def test_pep_items_cite_related_conflict_with_status(kb):
    exp = _explain(kb, kb["customers"]["cust_individual_pep"])
    edd = next(i for i in exp.items if i.obligation_id == "ob_pep_edd_mas")
    conflict = next(c for c in edd.conflicts if c.conflict_id == "conf_pep_jurisdiction")
    assert conflict.adjudication_status == "resolved"
    assert conflict.resolved_by


# ---------- 反事實 ----------

def _added(old, new):
    return [x for x in new if x not in old]


def _assert_counterfactuals_reproduce(kb, customer, conflicts=None):
    conflicts = kb["conflicts"] if conflicts is None else conflicts
    engine = CDDChecklistEngine()
    base = engine.generate_checklist(customer, kb["obligations"], conflicts)
    exp = _explain(kb, customer, conflicts)
    for cf in exp.counterfactuals:
        changed = apply_change(customer, cf.attribute, cf.counterfactual_value)
        if not cf.computed:
            # 引擎無法重算的改值：說明原因，不報告任何差異
            with pytest.raises(TypeError):
                engine.generate_checklist(changed, kb["obligations"], conflicts)
            assert cf.value_note and "不是數字" in cf.value_note
            assert cf.decision is None and cf.branch is None and cf.human_review is None
            assert not (cf.documents_added or cf.obligations_added or cf.triggers_added or cf.conflicts_added)
            continue
        after = engine.generate_checklist(changed, kb["obligations"], conflicts)
        expected_decision = None if after.decision == base.decision else [base.decision, after.decision]
        expected_review = (None if after.human_review_required == base.human_review_required
                           else [base.human_review_required, after.human_review_required])
        assert cf.decision == expected_decision
        assert cf.human_review == expected_review
        assert cf.documents_added == [d for d in after.required_documents if d not in base.required_documents]
        assert cf.documents_removed == [d for d in base.required_documents if d not in after.required_documents]
        assert cf.obligations_added == [o for o in after.applicable_obligations if o not in base.applicable_obligations]
        assert cf.obligations_removed == [o for o in base.applicable_obligations if o not in after.applicable_obligations]
        assert cf.triggers_added == [t for t in after.risk_triggers if t not in base.risk_triggers]
        assert cf.triggers_removed == [t for t in base.risk_triggers if t not in after.risk_triggers]
        assert cf.conflicts_added == _added(base.unresolved_conflicts, after.unresolved_conflicts)
        assert cf.conflicts_removed == _added(after.unresolved_conflicts, base.unresolved_conflicts)
        assert cf.citations_added == _added(base.citations, after.citations)
        assert cf.citations_removed == _added(after.citations, base.citations)
        # 只保留真的改變輸出的反事實
        assert (cf.decision or cf.human_review or cf.documents_added or cf.documents_removed
                or cf.obligations_added or cf.obligations_removed or cf.triggers_added or cf.triggers_removed)
        assert (route(changed)[0].leaf_id != route(customer)[0].leaf_id) == (cf.branch is not None)
    return exp


@pytest.mark.parametrize("customer_id", sorted(EXPECTED_FIXTURES))
def test_fixture_counterfactuals_reproduce(kb, customer_id):
    exp = _assert_counterfactuals_reproduce(kb, kb["customers"][customer_id])
    assert exp.counterfactuals, "every fixture customer has at least one output-changing single attribute"


def test_counterfactuals_reproduce_on_random_customers(kb):
    rng = random.Random(4)
    for customer in _random_customers(rng, 200):
        _assert_counterfactuals_reproduce(kb, customer)
    # 衝突全部待裁決時，反事實也要報告新增或消失的未裁決衝突
    pending = _all_pending(kb["conflicts"])
    for customer in _random_customers(random.Random(5), 100):
        _assert_counterfactuals_reproduce(kb, customer, pending)


def test_counterfactual_reports_new_pending_conflict(kb):
    """審查早已因未裁決衝突而必要時，human_review 不變；新出現的衝突要由 conflicts_added 說出來。"""
    pending = _all_pending(kb["conflicts"])
    exp = _explain(kb, kb["customers"]["cust_individual_low_risk"], pending)
    assert exp.unresolved_conflicts == ["conf_occasional_threshold"]
    assert exp.human_review_required is True and exp.branch_human_review_required is False
    cf = next(c for c in exp.counterfactuals if c.attribute == "pep_exposure")
    assert cf.human_review is None
    assert cf.conflicts_added == ["conf_pep_jurisdiction"] and cf.conflicts_removed == []
    assert cf.citations_added  # PEP 義務的錨點條文


def test_non_numeric_shareholder_pct_does_not_break_explain(kb):
    """持股比例為 null 或字串的個人客戶：引擎照常產出清單，解釋也不能失敗；
    改成企業的反事實引擎算不出來，列為 computed=False 並說明原因。"""
    engine = CDDChecklistEngine()
    base = kb["customers"]["cust_individual_low_risk"]
    for value in (None, "15%"):
        customer = base.model_copy(update={"custom_attributes": {"major_shareholder_pct": value}})
        checklist = engine.generate_checklist(customer, kb["obligations"], kb["conflicts"])
        assert checklist == revised_reference_generate_checklist(customer, kb["obligations"], kb["conflicts"])
        exp = _assert_counterfactuals_reproduce(kb, customer)
        assert exp.decision == checklist.decision
        uncomputed = [(c.attribute, c.counterfactual_value) for c in exp.counterfactuals if not c.computed]
        assert uncomputed == [("customer_type", "corporate")]
        assert repr(value) in next(c for c in exp.counterfactuals if not c.computed).value_note
        # 算不出所有改值的屬性，不能說它「改了也不影響」
        assert "customer_type" not in {a.attribute for a in exp.attributes_read_but_not_decisive}

    # 企業客戶的持股比例是布林：看不出在哪一區，三區各試一次；15% 以內的值會改走內部門檻分支
    corp = kb["customers"]["cust_corp_standard"].model_copy(update={"custom_attributes": {"major_shareholder_pct": True}})
    exp = _assert_counterfactuals_reproduce(kb, corp)
    pct = [c for c in exp.counterfactuals if c.attribute == "custom_attributes.major_shareholder_pct"]
    assert [c.counterfactual_value for c in pct] == [10]
    assert pct[0].branch[1].id == "corporate_internal_ubo_threshold"
    assert "不是數字" in pct[0].value_note


def test_counterfactual_examples(kb):
    high_risk = _explain(kb, kb["customers"]["cust_individual_high_risk_pep"])
    by_attr = {(c.attribute, c.counterfactual_value): c for c in high_risk.counterfactuals}
    # 緬甸 + 高風險：只改註冊地或只改國家風險，另一個條件仍成立，輸出不變，所以不列出
    assert ("registration_jurisdiction", "Singapore") not in by_attr
    assert ("ubo_country_risk", "low") not in by_attr
    branch = by_attr[("pep_exposure", False)].branch
    assert [b.id for b in branch] == ["individual_pep_high_risk", "individual_standard"]
    # 分支標籤與葉節點宣告的一致
    assert [b.label for b in branch] == [LEAVES[b.id].label for b in branch]

    corp = _explain(kb, kb["customers"]["cust_corp_standard"])
    pct = {c.counterfactual_value: c for c in corp.counterfactuals if c.attribute == "custom_attributes.major_shareholder_pct"}
    assert set(pct) == {9, 26}
    assert pct[26].documents_removed == ["Shareholder Registry", UBO_15_ID]
    assert pct[26].human_review == [True, False]
    # 2 層改成 3 層：持股結構複雜，升為高風險並加上持股架構圖
    layers = next(c for c in corp.counterfactuals if c.attribute == "ownership_layers")
    assert layers.counterfactual_value == 3
    assert layers.decision == ["standard_cdd", "enhanced_due_diligence"]
    assert layers.branch[1].id == "corporate_complex_ownership_internal_ubo_threshold"
    assert layers.documents_added == [OWNERSHIP_CHART]
    assert layers.triggers_added == ["complex_ownership_3_layers"]
    # 註冊地只在 PEP 分支比對緬甸，對企業沒有影響
    assert "registration_jurisdiction" not in {c.attribute for c in corp.counterfactuals}

    unclear = _explain(kb, kb["customers"]["cust_corp_unclear_ubo"])
    by_attr = {c.attribute: c for c in unclear.counterfactuals}
    assert list(by_attr) == ["customer_type", "ubo_status", "ownership_layers"]
    # UBO 改為已識別：5 層持股仍是高風險，但不再拒絕開戶
    assert by_attr["ubo_status"].branch[1].id == "corporate_complex_ownership"
    assert by_attr["ubo_status"].decision is None
    assert "Account Opening Rejection Notice" in by_attr["ubo_status"].documents_removed
    # 層數降到 2：仍拒絕開戶，只少了多層持股標記
    assert by_attr["ownership_layers"].branch is None
    assert by_attr["ownership_layers"].triggers_removed == ["complex_ownership_3_layers"]

    pep = _explain(kb, kb["customers"]["cust_individual_pep"])
    funds = next(c for c in pep.counterfactuals if c.attribute == "source_of_funds_available")
    assert funds.counterfactual_value is False and funds.branch is None
    assert funds.triggers_added == ["missing_source_of_funds_evidence"]


# ---------- 路徑足以決定輸出 ----------

def _random_customers(rng: random.Random, n: int) -> List[CustomerContext]:
    customers = []
    for i in range(n):
        pct = rng.choice([None, rng.randint(0, 60), rng.choice([9, 10, 25, 26])])
        custom = {} if pct is None else {"major_shareholder_pct": pct}
        if rng.random() < 0.3:
            custom["has_bearer_shares"] = rng.choice([True, False])
        customers.append(CustomerContext(
            customer_id=f"cust_rand_{i}",
            customer_type=rng.choice(["individual", "corporate"]),
            registration_jurisdiction=rng.choice(JURISDICTIONS + ["myanmar", "CAYMAN ISLANDS", "United Kingdom"]),
            ownership_layers=rng.randint(0, 8),
            ubo_status=rng.choice(["identified", "unclear"]),
            ubo_country_risk=rng.choice(["low", "medium", "high"]),
            pep_exposure=rng.choice([True, False]),
            source_of_funds_available=rng.choice([True, False]),
            source_of_wealth_available=rng.choice([True, False]),
            custom_attributes=custom,
        ))
    return customers


def test_path_and_trigger_conditions_are_sufficient_for_the_checklist(kb):
    """簽章 = 路徑上每個測試的結果，加上葉節點中由標記自己條件檢查的標記是否成立；同一簽章的清單完全相同。"""
    engine = CDDChecklistEngine()
    groups: Dict[tuple, set] = {}
    leaves = set()
    for customer in _random_customers(random.Random(20261110), 3000):
        leaf, steps = route(customer)
        leaves.add(leaf.leaf_id)
        conditions = tuple((spec.trigger, spec.raised_for(customer)) for spec in leaf.triggers
                           if checked_by(spec, steps) == "own_condition")
        signature = (tuple((s.test.test_id, s.outcome) for s in steps), conditions)
        checklist = engine.generate_checklist(customer, kb["obligations"], kb["conflicts"])
        output = checklist.model_dump(exclude={"checklist_id", "customer_id"})
        groups.setdefault(signature, set()).add(repr(sorted(output.items())))
    assert len(leaves) == 8  # 八個可達的葉節點都被抽到（other_customer_type 不可達）
    # PEP 的資金、財富來源各兩種，UBO 不明的多層持股兩種，其餘六個葉節點各一種
    assert len(groups) == 4 + 2 + 6
    assert all(len(outputs) == 1 for outputs in groups.values())


def test_every_listed_trigger_holds_for_the_customer(kb):
    """列出的標記對客戶一定成立；路徑保證的標記走到葉節點就成立，所以不會被濾掉；
    沒列出的只會是由自己條件檢查、且不成立的標記。"""
    for customer in _random_customers(random.Random(11), 1500):
        leaf, steps = route(customer)
        for spec in leaf.triggers:
            if checked_by(spec, steps) == "decision_path":
                assert spec.holds(customer) is True, (customer, spec.trigger)
        exp = _explain(kb, customer)
        assert all(t.holds in (True, None) for t in exp.risk_triggers)
        assert all(t.checked_by == "own_condition" and t.holds is False for t in exp.triggers_not_raised)
        # 兩份清單合起來正好是葉節點宣告的全部標記，不重複
        shown = [t.trigger for t in exp.risk_triggers] + [t.trigger for t in exp.triggers_not_raised]
        assert sorted(shown) == sorted(s.trigger for s in leaf.triggers)


# ---------- 風險標記與未讀屬性 ----------

# ---------- 讀到但不具決定性的屬性 ----------

def test_attributes_read_but_not_decisive_examples(kb):
    high_risk = _explain(kb, kb["customers"]["cust_individual_high_risk_pep"])
    by_attr = {a.attribute: a for a in high_risk.attributes_read_but_not_decisive}
    # 緬甸 + 國家風險高：OR 的兩個條件都成立，單獨改其中一個仍是「是」
    assert list(by_attr) == ["ubo_country_risk", "registration_jurisdiction"]
    assert "registration_jurisdiction" in by_attr["ubo_country_risk"].reason
    assert "ubo_country_risk" in by_attr["registration_jurisdiction"].reason
    # 開曼不再是 CDD 無法完成的條件：UBO 不明的企業，UBO 狀態本身就是決定性的
    assert _explain(kb, kb["customers"]["cust_corp_unclear_ubo"]).attributes_read_but_not_decisive == []
    assert _explain(kb, kb["customers"]["cust_individual_low_risk"]).attributes_read_but_not_decisive == []


def test_attributes_read_but_not_decisive_partition_the_path(kb):
    """讀到的每個屬性（路徑上的，加上標記自己條件讀的），不是出現在反事實裡，就是列為不具決定性，
    兩者不重疊；列為不具決定性的屬性，每個候選改值重跑引擎都得到相同的清單。"""
    from src.decision.explain import counterfactual_candidates

    engine = CDDChecklistEngine()
    for customer in list(kb["customers"].values()) + _random_customers(random.Random(7), 150):
        exp = _explain(kb, customer)
        own_conditions = [t for t in exp.risk_triggers + exp.triggers_not_raised if t.checked_by == "own_condition"]
        read_on_path = {a for step in exp.path for a in step.attributes} | {a for t in own_conditions for a in t.attributes}
        decisive = {c.attribute for c in exp.counterfactuals}
        not_decisive = {a.attribute for a in exp.attributes_read_but_not_decisive}
        assert not_decisive <= read_on_path
        assert not (decisive & not_decisive)
        assert read_on_path <= decisive | not_decisive
        base = engine.generate_checklist(customer, kb["obligations"], kb["conflicts"])
        for attribute, value, _ in counterfactual_candidates(customer):
            if attribute in not_decisive:
                changed = apply_change(customer, attribute, value)
                assert engine.generate_checklist(changed, kb["obligations"], kb["conflicts"]) == base


def test_attributes_not_read(kb):
    """標記的條件也算讀取：持股層數、資金與財富來源現在都會被讀，沒讀的只剩其他自訂屬性。"""
    for customer in kb["customers"].values():
        exp = _explain(kb, customer)
        assert exp.attributes_not_read == [
            f"custom_attributes.{key}" for key in customer.custom_attributes if key != "major_shareholder_pct"]


def test_triggers_report_what_guarantees_them(kb):
    unclear = kb["customers"]["cust_corp_unclear_ubo"]
    triggers = {t.trigger: t for t in _explain(kb, unclear).risk_triggers}
    assert list(triggers) == ["unclear_ubo_status", "complex_ownership_3_layers"]
    assert triggers["unclear_ubo_status"].checked_by == "decision_path"
    # UBO 不明就已拒絕，路徑不讀層數；多層持股由標記自己的條件檢查，5 層成立
    layered = triggers["complex_ownership_3_layers"]
    assert layered.checked_by == "own_condition" and layered.holds is True
    assert layered.condition == "ownership_layers >= 3" and layered.observed == {"ownership_layers": 5}

    # 同一個客戶只有 2 層：多層持股檢查過但不成立，列在 triggers_not_raised
    two_layers = _explain(kb, unclear.model_copy(update={"ownership_layers": 2}))
    assert [t.trigger for t in two_layers.risk_triggers] == ["unclear_ubo_status"]
    assert [(t.trigger, t.holds, t.observed) for t in two_layers.triggers_not_raised] == [
        ("complex_ownership_3_layers", False, {"ownership_layers": 2})]

    # UBO 已識別的多層持股企業：同一個標記改由決策路徑保證
    identified = _explain(kb, unclear.model_copy(update={"ubo_status": "identified"}))
    assert identified.branch.id == "corporate_complex_ownership"
    assert [(t.trigger, t.checked_by) for t in identified.risk_triggers] == [
        ("complex_ownership_3_layers", "decision_path")]


def test_pep_source_of_funds_and_wealth_are_checked(kb):
    pep = kb["customers"]["cust_individual_pep"]
    exp = _explain(kb, pep)
    assert [t.trigger for t in exp.risk_triggers] == ["pep_exposure_detected"]
    assert [t.trigger for t in exp.triggers_not_raised] == [
        "missing_source_of_funds_evidence", "missing_source_of_wealth_evidence"]
    missing = _explain(kb, pep.model_copy(update={"source_of_wealth_available": False}))
    assert [t.trigger for t in missing.risk_triggers] == ["pep_exposure_detected", "missing_source_of_wealth_evidence"]
    assert missing.decision == exp.decision and [i.document for i in missing.items] == [i.document for i in exp.items]


def test_trigger_without_attributes(kb):
    exp = _explain(kb, kb["customers"]["cust_individual_high_risk_pep"])
    triggers = {t.trigger: t for t in exp.risk_triggers}
    assert triggers["onboarding_prohibited_by_policy"].attributes == []
    assert triggers["onboarding_prohibited_by_policy"].checked_by == "branch_outcome"
    assert triggers["onboarding_prohibited_by_policy"].holds is None
    assert triggers["pep_from_high_risk_jurisdiction"].checked_by == "decision_path"
    assert triggers["pep_from_high_risk_jurisdiction"].holds is True


# 每個風險標記宣告的義務、寫出這個條件的那條出處條文，以及條文中的原文
GB_1_2 = "mock_internal_policy_s_1_customer_onboarding_standards_1_2_beneficial_ownership_verification"
GB_1_4 = "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons"
MAS_8_3 = "mas_notice_626_8_enhanced_cdd_8_3"
TRIGGER_OBLIGATIONS = {
    "pep_from_high_risk_jurisdiction": ("ob_pep_prohibitions_gb", GB_1_4, "(PEPs) from high-risk jurisdictions"),
    "onboarding_prohibited_by_policy": ("ob_pep_prohibitions_gb", GB_1_4,
                                        "strictly prohibits establishing business relationships"),
    "pep_exposure_detected": ("ob_pep_edd_mas", MAS_8_3, "determined by the bank to be a politically exposed person"),
    "missing_source_of_funds_evidence": ("ob_pep_edd_mas", f"{MAS_8_3}_b", "source of funds"),
    "missing_source_of_wealth_evidence": ("ob_pep_edd_mas", f"{MAS_8_3}_b", "source of wealth"),
    "unclear_ubo_status": ("ob_cdd_incomplete_mas", "mas_notice_626_6_cdd_6_35", "unable to complete the measures"),
    "complex_ownership_3_layers": ("ob_identify_ubo_10_gb", f"{GB_1_2}_b",
                                   "three or more layers of intermediary holding companies"),
    "internal_ubo_threshold_triggered_10_percent": ("ob_identify_ubo_10_gb", f"{GB_1_2}_a",
                                                    "ownership threshold of 10% or more"),
}


def test_every_trigger_declares_its_obligation(kb):
    """每個葉節點的每個標記都宣告義務與條文；義務是這個葉節點的適用義務，宣告的條文是該義務的出處條文之一，
    且條文本身寫出這個條件。"""
    from src.decision.explain import obligation_for_item

    ob_dict = {o.obligation_id: o for o in kb["obligations"]}
    clause_dict = {c.clause_id: c for c in kb["clauses"]}
    declared = [(leaf, spec) for leaf in LEAVES.values() for spec in leaf.triggers]
    assert {spec.trigger for _, spec in declared} == set(TRIGGER_OBLIGATIONS)
    for leaf, spec in declared:
        ob_id, clause_id, phrase = TRIGGER_OBLIGATIONS[spec.trigger]
        assert (spec.obligation_id, spec.clause_id) == (ob_id, clause_id), (leaf.leaf_id, spec.trigger)
        assert obligation_for_item(leaf, spec.trigger) == ob_id
        assert ob_id in leaf.obligations, (leaf.leaf_id, spec.trigger)
        assert clause_id in ob_dict[ob_id].source_clause_ids, spec.trigger
        assert phrase in clause_dict[clause_id].raw_text, spec.trigger


def test_trigger_explanation_carries_declared_obligation(kb):
    exp = _explain(kb, kb["customers"]["cust_corp_unclear_ubo"])
    triggers = {t.trigger: t for t in exp.risk_triggers}
    assert triggers["unclear_ubo_status"].obligation_id == "ob_cdd_incomplete_mas"
    assert triggers["unclear_ubo_status"].clause_id == "mas_notice_626_6_cdd_6_35"
    assert triggers["complex_ownership_3_layers"].obligation_id == "ob_identify_ubo_10_gb"
    assert triggers["complex_ownership_3_layers"].clause_id == f"{GB_1_2}_b"
    for customer in kb["customers"].values():
        exp = _explain(kb, customer)
        for t in exp.risk_triggers + exp.triggers_not_raised:
            assert (t.obligation_id, t.clause_id) == TRIGGER_OBLIGATIONS[t.trigger][:2]


def test_fatf_10_d_mentions_source_of_funds_but_no_obligation_cites_it(kb):
    """非 PEP 客戶不檢查資金來源的依據要與資料一致：FATF 10(d) 提到資金來源卻沒有義務引用；
    引用資金來源的義務出處只有 MAS 8.3(b) 與銀行政策 1.4(a)，兩者都是 PEP 義務。"""
    cited = {cid: ob for ob in kb["obligations"] for cid in ob.source_clause_ids}
    mentions = [c for c in kb["clauses"] if "source of funds" in c.raw_text.lower()]
    assert "fatf_rec10_rec_10_cdd_measures_d" in {c.clause_id for c in mentions}
    assert "fatf_rec10_rec_10_cdd_measures_d" not in cited
    cited_mentions = {c.clause_id: cited[c.clause_id].obligation_id for c in mentions if c.clause_id in cited}
    assert cited_mentions == {"mas_notice_626_8_enhanced_cdd_8_3_b": "ob_pep_edd_mas",
                              f"{GB_1_4}_a": "ob_pep_approval_gb"}


# ---------- API ----------

@pytest.fixture(scope="module")
def client():
    from src.api.main import app
    with TestClient(app) as c:
        yield c


# ---------- 不需另收文件的義務也列出相關衝突 ----------

def test_obligation_conflicts_cover_every_applicable_obligation(kb):
    """衝突全部待裁決時，每個未裁決衝突都能在 obligation_conflicts 找到說明與狀態，
    包括只落在不需另收文件義務（ob_cdd_on_relationship_mas）上的 conf_occasional_threshold。"""
    pending = _all_pending(kb["conflicts"])
    for customer_id in EXPECTED_FIXTURES:
        customer = kb["customers"][customer_id]
        exp = _explain(kb, customer, pending)
        assert list(exp.obligation_conflicts) == list(route(customer)[0].obligations)
        shown = {c.conflict_id for refs in exp.obligation_conflicts.values() for c in refs}
        assert set(exp.unresolved_conflicts) <= shown
        for item in exp.items:
            assert item.conflicts == exp.obligation_conflicts[item.obligation_id]

    low = _explain(kb, kb["customers"]["cust_individual_low_risk"], pending)
    assert "ob_cdd_on_relationship_mas" in low.obligations_without_documents
    refs = low.obligation_conflicts["ob_cdd_on_relationship_mas"]
    assert [(c.conflict_id, c.adjudication_status) for c in refs] == [("conf_occasional_threshold", "pending_human_review")]
    assert refs[0].description

    # 已裁決的資料：狀態照實列出，審查來自分支本身
    pep = _explain(kb, kb["customers"]["cust_individual_pep"])
    assert [c.adjudication_status for c in pep.obligation_conflicts["ob_cdd_on_relationship_mas"]] == ["resolved"]
    assert pep.branch_human_review_required is True and pep.unresolved_conflicts == []


def test_explanation_api(client):
    response = client.get("/api/v1/customers/cust_corp_unclear_ubo/explanation")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_corp_unclear_ubo"
    assert data["checklist_id"] == "chk_corp_unclear_ubo"
    assert data["branch"]["id"] == "corporate_cdd_incomplete"
    assert [s["test_id"] for s in data["path"]] == ["is_individual", "is_corporate", "corporate_cdd_blocked"]
    assert {i["obligation_id"] for i in data["items"]} == {"ob_cdd_incomplete_mas"}
    assert {i["obligation_confidence_kind"] for i in data["items"]} == {None}  # cdd_incomplete 在保留文本上未量測
    triggers = {t["trigger"]: t for t in data["risk_triggers"]}
    assert triggers["complex_ownership_3_layers"]["clause_id"] == f"{GB_1_2}_b"
    assert triggers["complex_ownership_3_layers"]["checked_by"] == "own_condition"
    assert data["triggers_not_raised"] == []
    assert data["items"][0]["source_clauses"][0]["clause_id"] == "mas_notice_626_6_cdd_6_35"
    assert data["attributes_not_read"] == ["custom_attributes.layering_reason", "custom_attributes.has_bearer_shares"]

    missing = client.get("/api/v1/customers/cust_does_not_exist/explanation")
    assert missing.status_code == 404


def test_source_clause_reasons_and_highlights(kb):
    """規則理由原樣列出；高亮只取落在本條文的片段，同一片段被多條規則引用時合併。"""
    from types import SimpleNamespace
    from src.decision.explain import explain_clause

    clause_dict = {c.clause_id: c for c in kb["clauses"]}
    doc_dict = {d.source_document_id: d for d in kb["documents"]}
    clause = clause_dict["mas_notice_626_6_cdd_6_35"]
    start = clause.raw_text.index("shall not")
    span = {"clause_id": clause.clause_id, "start": start, "end": start + 9, "text": "shall not"}
    parent_span = {"clause_id": "mas_notice_626_6_cdd", "start": 0, "end": 3, "text": "abc"}
    reasons = [
        {"rule": "incomplete.unable_and_stop", "obligation_type": "refuse_relationship", "message": "m1",
         "spans": [span, parent_span], "depends_on": []},
        {"rule": "other.rule", "obligation_type": "refuse_relationship", "message": "m2", "spans": [span],
         "depends_on": []},
    ]
    ob = SimpleNamespace(explanations={clause.clause_id: reasons})
    evidence = explain_clause(clause.clause_id, ob, clause_dict, doc_dict)
    assert evidence.reasons == reasons
    assert evidence.document_title == doc_dict["mas_notice_626"].title
    assert evidence.highlights == [{**{k: span[k] for k in ("start", "end", "text")},
                                    "rules": ["incomplete.unable_and_stop", "other.rule"]}]
    assert clause.raw_text[start:start + 9] == "shall not"
    # 沒有 explanations 屬性的義務（例如人工標註或 LLM 匯入）：沒有理由也沒有高亮
    empty = explain_clause(clause.clause_id, SimpleNamespace(), clause_dict, doc_dict)
    assert empty.reasons == [] and empty.highlights == []


def test_confidence_kind_is_passed_through(kb):
    exp = _explain(kb, kb["customers"]["cust_individual_pep"])
    ob_dict = {o.obligation_id: o for o in kb["obligations"]}
    for item in exp.items:
        ob = ob_dict[item.obligation_id]
        assert item.obligation_confidence_kind == ob.confidence_kind
        assert (item.obligation_confidence_kind == "measured_on_heldout") == (item.obligation_confidence is not None)
    assert {i.obligation_confidence_kind for i in exp.items} == {"measured_on_heldout", None}


def test_inherited_items_show_lead_in_evidence(kb):
    """條列項目繼承上層引言的類型：上層的理由片段（含往上一層 depends_on 的片段）列為 context_evidence，
    每個片段都解析到知識庫條文、文字與原文一致；本條文的高亮不受影響。"""
    clause_dict = {c.clause_id: c for c in kb["clauses"]}
    exp = _explain(kb, kb["customers"]["cust_individual_pep"])
    item = next(i for i in exp.items if i.document == "Source of Funds Declaration & Evidence")
    by_clause = {sc.clause_id: sc for sc in item.source_clauses}
    lead_in = "mas_notice_626_8_enhanced_cdd_8_3"

    # 引言本身的理由全在本條文：沒有上層依據
    assert by_clause[lead_in].context_evidence == []
    item_b = by_clause[f"{lead_in}_b"]
    texts = [e["text"] for e in item_b.context_evidence]
    # list.inherit 自己的片段（列表引言），加上它依賴的 8.3#pep_edd 理由（pep.enhanced）的字詞
    assert "following enhanced CDD measures" in texts
    assert {"shall", "enhanced CDD", "politically exposed"} <= set(texts)
    for entry in item_b.context_evidence:
        clause = clause_dict[entry["clause_id"]]
        assert entry["clause_id"] != item_b.clause_id
        assert entry["section_ref"] == clause.section_ref
        assert clause.raw_text[entry["start"]:entry["end"]] == entry["text"]
        assert entry["rules"]
    rules = {e["text"]: e["rules"] for e in item_b.context_evidence}
    assert rules["following enhanced CDD measures"] == ["list.inherit"]
    assert rules["enhanced CDD"] == ["pep.enhanced"]
    # 本條文的高亮只含本條文的片段（list.inherit 的片段都在引言，所以是空的）
    assert item_b.highlights == []


def test_context_evidence_follows_depends_on_all_the_way_up(kb):
    """1.2(b)(i) 依賴 1.2(b)，1.2(b) 再依賴 1.2：遞移追到底，所以看得到 1.2(b) 的冒號和 1.2 的依據字詞，
    且都標為上層條文；這組片段等於刪字測試用的 rationale 去掉本條文的部分。"""
    exp = _explain(kb, kb["customers"]["cust_corp_unclear_ubo"])
    item = next(i for i in exp.items if i.obligation_id == "ob_cdd_incomplete_mas")
    assert all(sc.context_evidence == [] for sc in item.source_clauses)  # 6.35 的理由都在本條文

    from src.decision.explain import explain_clause, label_reasons
    clause_dict = {c.clause_id: c for c in kb["clauses"]}
    doc_dict = {d.source_document_id: d for d in kb["documents"]}
    ob = next(o for o in kb["obligations"] if o.obligation_id == "ob_identify_ubo_10_gb")
    evidence = explain_clause(f"{GB_1_2}_b_i", ob, clause_dict, doc_dict, label_reasons(kb["obligations"]))
    by_clause = {}
    for e in evidence.context_evidence:
        by_clause.setdefault(e["clause_id"], []).append(e["text"])
    assert by_clause[f"{GB_1_2}_b"] == [":"]
    assert GB_1_2 in by_clause and by_clause[GB_1_2]  # the top lead-in's own evidence words
    assert {e["relation"] for e in evidence.context_evidence} == {"ancestor"}



def test_context_evidence_equals_independent_rationale_for_every_leaf_obligation(kb):
    """顯示的上層與引用依據，等於刪字測試的 rationale 去掉本條文的部分。rationale 由
    classify_traced 對知識庫條文重新追蹤得出，不讀義務裡存的 explanations；
    對每個葉節點用到的義務的每條出處條文都比對。"""
    from src.decision.explain import explain_clause, label_reasons
    from src.extraction import faithfulness
    from src.extraction.extractor import RuleBasedObligationExtractor

    trace = RuleBasedObligationExtractor().classify_traced(kb["clauses"])
    clause_dict = {c.clause_id: c for c in kb["clauses"]}
    doc_dict = {d.source_document_id: d for d in kb["documents"]}
    ob_dict = {o.obligation_id: o for o in kb["obligations"]}
    labels = label_reasons(kb["obligations"])
    used = list(dict.fromkeys(ob_id for leaf in LEAVES.values() for ob_id in leaf.obligations))
    checked = 0
    for ob_id in used:
        ob = ob_dict[ob_id]
        for cid in ob.source_clause_ids:
            # 只從義務取它對這條條文的類型名稱；片段全部來自獨立的 trace
            types = {r.obligation_type for r in ob.explanations.get(cid, [])}
            assert len(types) == 1, (ob_id, cid, types)
            type_ = types.pop()
            assert type_ in trace.get(cid, {}), (ob_id, cid)
            evidence = explain_clause(cid, ob, clause_dict, doc_dict, labels)
            expected = {other: spans for other, spans in faithfulness.rationale(trace, cid, type_).items()
                        if other != cid}
            shown: Dict[str, list] = {}
            for e in evidence.context_evidence:
                shown.setdefault(e["clause_id"], []).append((e["start"], e["end"]))
            assert {c: faithfulness.merge_spans(spans) for c, spans in shown.items()} == expected, (ob_id, cid)
            checked += 1
    assert checked >= 20


def test_evidence_from_a_cited_paragraph_is_labelled_referenced(kb):
    """MAS 6.6 依「for the purposes of paragraph 6.5」引用 6.5；6.5 不是 6.6 的上層條文，所以標為 referenced，
    引用者是 6.6 自己。6.6(a)(i) 本身沒有引用任何條文：它看到的 6.5 片段也是 referenced，但引用者是上層的 6.6。"""
    exp = _explain(kb, kb["customers"]["cust_individual_low_risk"])
    item = next(i for i in exp.items if i.obligation_id == "ob_verify_customer_mas")
    by_clause = {sc.clause_id: sc for sc in item.source_clauses}
    mas_6_5, mas_6_6 = "mas_notice_626_6_cdd_6_5", "mas_notice_626_6_cdd_6_6"

    lead = [e for e in by_clause[mas_6_6].context_evidence if e["clause_id"] == mas_6_5]
    assert lead and {e["relation"] for e in lead} == {"referenced"}
    assert {(e["cited_by"]["clause_id"], e["cited_by"]["relation"]) for e in lead} == {(mas_6_6, "self")}

    item_i = by_clause[f"{mas_6_6}_a_i"]
    assert "6.5" not in item_i.raw_text
    cited = [e for e in item_i.context_evidence if e["clause_id"] == mas_6_5]
    assert cited and {e["relation"] for e in cited} == {"referenced"}
    assert {(e["cited_by"]["clause_id"], e["cited_by"]["relation"]) for e in cited} == {(mas_6_6, "ancestor")}
    assert {e["cited_by"]["section_ref"] for e in cited} == {kb_section_ref(kb, mas_6_6)}
    # 上層條文的片段：6.6(a) 的片段由 6.6(a)(i) 自己的 list.inherit 用到
    parent = [e for e in item_i.context_evidence if e["clause_id"] == f"{mas_6_6}_a"]
    assert parent and {e["relation"] for e in parent} == {"ancestor"}
    assert {e["cited_by"]["relation"] for e in parent} == {"self"}


def kb_section_ref(kb, clause_id):
    return next(c.section_ref for c in kb["clauses"] if c.clause_id == clause_id)


def test_a_nan_shareholding_is_not_treated_as_a_number():
    from src.decision.explain import _is_number
    assert _is_number(15) and _is_number(9.5)
    assert not _is_number(float("nan")) and not _is_number(float("inf")) and not _is_number(True) and not _is_number("15%")
