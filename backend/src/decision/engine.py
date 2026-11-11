from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union

from src.contracts.models import CustomerContext, Obligation, Conflict, CDDChecklist

Decision = Literal["simplified_cdd", "standard_cdd", "enhanced_due_diligence"]

# 內部持股門檻讀取的自訂屬性；未提供時視為 0
SHAREHOLDER_PCT_ATTR = "custom_attributes.major_shareholder_pct"


def read_attribute(customer: CustomerContext, attribute: str) -> Any:
    """讀出決策樹用到的客戶屬性；custom_attributes.<key> 讀自訂屬性，未提供時為 None。"""
    if attribute.startswith("custom_attributes."):
        return customer.custom_attributes.get(attribute.split(".", 1)[1])
    return getattr(customer, attribute)


def _shareholder_pct(customer: CustomerContext) -> Any:
    return customer.custom_attributes.get("major_shareholder_pct", 0)


@dataclass(frozen=True)
class Condition:
    """測試的一個條件：讀一個屬性，判斷是否成立。"""
    attribute: str
    description: str
    predicate: Callable[[CustomerContext], bool]


@dataclass(frozen=True)
class DecisionTest:
    """決策樹節點上的測試；有多個條件時是 OR（任一成立即為「是」）。"""
    test_id: str
    question: str
    conditions: Tuple[Condition, ...]

    @property
    def attributes(self) -> List[str]:
        return list(dict.fromkeys(c.attribute for c in self.conditions))

    def evaluate(self, customer: CustomerContext) -> Tuple[bool, List[bool]]:
        # 為了解釋，OR 的每個條件都會算出來；結果與短路求值相同
        results = [bool(c.predicate(customer)) for c in self.conditions]
        return any(results), results


@dataclass(frozen=True)
class TriggerSpec:
    """葉節點宣告的風險標記：它依據哪個義務、對哪些客戶屬性下了斷言，以及斷言對這位客戶是否成立。
    obligation_id 必須明確宣告：只連到出處條文確實寫出這個條件的義務；知識庫沒有任何義務對這位客戶要求這個條件時為 None。
    clause_id 是該義務出處條文中寫出這個條件的那一條（不一定是義務的錨點條文）；沒有義務時為 None。
    attributes 為空代表它只是陳述分支的結果（例如禁止開戶），不對客戶屬性下斷言。"""
    trigger: str
    obligation_id: Optional[str]
    clause_id: Optional[str] = None
    attributes: Tuple[str, ...] = ()
    holds: Optional[Callable[[CustomerContext], bool]] = None


@dataclass(frozen=True)
class Leaf:
    """決策樹的葉節點：宣告這個分支的完整輸出。items 是 (文件, 義務 ID)，順序即清單順序。"""
    leaf_id: str
    label: str
    decision: Decision
    items: Tuple[Tuple[str, str], ...]
    triggers: Tuple[TriggerSpec, ...]
    obligations: Tuple[str, ...]
    human_review_required: bool

    @property
    def required_documents(self) -> List[str]:
        return [document for document, _ in self.items]

    @property
    def risk_triggers(self) -> List[str]:
        return [t.trigger for t in self.triggers]


@dataclass(frozen=True)
class Node:
    test: DecisionTest
    yes: Union["Node", Leaf]
    no: Union["Node", Leaf]


@dataclass(frozen=True)
class PathStep:
    """決策路徑上的一步：做了哪個測試、條件各自的結果與整體結果。"""
    test: DecisionTest
    outcome: bool
    condition_results: Tuple[bool, ...]


# ---------- 測試 ----------

T_IS_INDIVIDUAL = DecisionTest("is_individual", "客戶是否為個人？", (
    Condition("customer_type", 'customer_type == "individual"', lambda c: c.customer_type == "individual"),
))
T_IS_PEP = DecisionTest("is_pep", "客戶是否為政治敏感人物（PEP）？", (
    Condition("pep_exposure", "pep_exposure is True", lambda c: c.pep_exposure is True),
))
T_PEP_HIGH_RISK = DecisionTest("pep_high_risk", "政要是否與高風險地區有關（受益人國家風險為高，或註冊地為緬甸）？", (
    Condition("ubo_country_risk", 'ubo_country_risk == "high"', lambda c: c.ubo_country_risk == "high"),
    Condition("registration_jurisdiction", 'registration_jurisdiction.lower() == "myanmar"',
              lambda c: c.registration_jurisdiction.lower() == "myanmar"),
))
T_IS_CORPORATE = DecisionTest("is_corporate", "客戶是否為企業？", (
    Condition("customer_type", 'customer_type == "corporate"', lambda c: c.customer_type == "corporate"),
))
T_CORPORATE_CDD_BLOCKED = DecisionTest("corporate_cdd_blocked", "企業 CDD 是否無法完成（實質受益人不明，或註冊地為開曼群島）？", (
    Condition("ubo_status", 'ubo_status == "unclear"', lambda c: c.ubo_status == "unclear"),
    Condition("registration_jurisdiction", 'registration_jurisdiction.lower() == "cayman islands"',
              lambda c: c.registration_jurisdiction.lower() == "cayman islands"),
))
T_INTERNAL_UBO_THRESHOLD = DecisionTest("internal_ubo_threshold", "主要股東持股是否落在內部政策門檻 10% 至 25%（未提供時視為 0）？", (
    Condition(SHAREHOLDER_PCT_ATTR, "10 <= major_shareholder_pct <= 25", lambda c: 10 <= _shareholder_pct(c) <= 25),
))

# ---------- 葉節點 ----------

NRIC_PASSPORT = "National Identity Card (NRIC) or Passport"

# 風險標記引用的條文（data/processed/clauses.yaml 的條文 ID）：寫出標記條件的那一條
_GB_1_2 = "mock_internal_policy_s_1_customer_onboarding_standards_1_2_beneficial_ownership_verification"
_GB_1_2_A = f"{_GB_1_2}_a"
_GB_1_2_B = f"{_GB_1_2}_b"
_GB_1_4 = "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons"
_MAS_8_3 = "mas_notice_626_8_enhanced_cdd_8_3"
_MAS_6_35 = "mas_notice_626_6_cdd_6_35"

L_INDIVIDUAL_PEP_HIGH_RISK = Leaf(
    leaf_id="individual_pep_high_risk",
    label="高風險地區政要：依銀行政策禁止開戶",
    decision="enhanced_due_diligence",
    items=(("Rejected Onboarding Notification", "ob_pep_prohibitions_gb"),),
    triggers=(
        # 銀行政策 1.4：「prohibits establishing business relationships with ... (PEPs) from high-risk jurisdictions」
        TriggerSpec("pep_from_high_risk_jurisdiction", obligation_id="ob_pep_prohibitions_gb",
                    clause_id=_GB_1_4,
                    attributes=("pep_exposure", "ubo_country_risk", "registration_jurisdiction"),
                    holds=lambda c: c.pep_exposure is True and (
                        c.ubo_country_risk == "high" or c.registration_jurisdiction.lower() == "myanmar")),
        # 同一條（銀行政策 1.4）：「Global Bank strictly prohibits establishing business relationships」
        TriggerSpec("onboarding_prohibited_by_policy", obligation_id="ob_pep_prohibitions_gb", clause_id=_GB_1_4),
    ),
    obligations=("ob_pep_prohibitions_gb",),
    human_review_required=True,
)
L_INDIVIDUAL_PEP = Leaf(
    leaf_id="individual_pep",
    label="一般政要：加強盡職調查（EDD）並經核准",
    decision="enhanced_due_diligence",
    items=(
        (NRIC_PASSPORT, "ob_verify_customer_mas"),
        ("Proof of Address", "ob_verify_customer_mas"),
        ("Senior Management Approval Form", "ob_pep_edd_mas"),
        ("Source of Funds Declaration & Evidence", "ob_pep_edd_mas"),
        ("Source of Wealth Declaration & Evidence", "ob_pep_edd_mas"),
        ("Head of Compliance Approval Form", "ob_pep_approval_gb"),
    ),
    # MAS 8.3：「where a customer ... is determined by the bank to be a politically exposed person」
    triggers=(TriggerSpec("pep_exposure_detected", obligation_id="ob_pep_edd_mas", clause_id=_MAS_8_3,
                          attributes=("pep_exposure",), holds=lambda c: c.pep_exposure is True),),
    # MAS 8.3 的加強 CDD，加上銀行政策 1.4(a) 對非高風險地區 PEP 的核准要求
    obligations=("ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_pep_edd_mas", "ob_pep_approval_gb"),
    human_review_required=True,
)
L_INDIVIDUAL_STANDARD = Leaf(
    leaf_id="individual_standard",
    label="一般個人：標準 CDD",
    decision="standard_cdd",
    items=(
        ("National Identity Card (NRIC)", "ob_verify_customer_mas"),
        ("Proof of Residential Address", "ob_verify_customer_mas"),
    ),
    triggers=(),
    obligations=("ob_cdd_on_relationship_mas", "ob_verify_customer_mas"),
    human_review_required=False,
)
L_CORPORATE_CDD_INCOMPLETE = Leaf(
    leaf_id="corporate_cdd_incomplete",
    label="企業 CDD 無法完成：拒絕開戶並評估申報可疑交易",
    decision="enhanced_due_diligence",
    items=(
        ("Account Opening Rejection Notice", "ob_cdd_incomplete_mas"),
        ("STR Evaluation File", "ob_cdd_incomplete_mas"),
    ),
    triggers=(
        # MAS 6.35：「Where the bank is unable to complete the measures as required by paragraphs 6, 7 and 8」；
        # 識別實質受益人是第 6 段（6.14）的措施，UBO 不明即無法完成。這是一步推論：
        # 直接寫出「unclear beneficial ownership」的銀行政策 1.3 沒有被抽成任何義務
        TriggerSpec("unclear_ubo_status", obligation_id="ob_cdd_incomplete_mas", clause_id=_MAS_6_35,
                    attributes=("ubo_status",), holds=lambda c: c.ubo_status == "unclear"),
        # 銀行政策 1.2(b)：「three or more layers of intermediary holding companies」→ (i)「classified as
        # presenting a high risk」；5 層以上落在這個條件內（條文門檻是 3 層，標記用的是 5 層）
        TriggerSpec("excessive_layering_5", obligation_id="ob_identify_ubo_10_gb", clause_id=_GB_1_2_B,
                    attributes=("ownership_layers",), holds=lambda c: c.ownership_layers >= 5),
        # 沒有法源：知識庫中沒有任何義務對這位客戶要求資金來源證明。FATF 第 10 項 (d) 提到資金來源，
        # 但沒有從它抽出義務；MAS 8.3(b) 與銀行政策 1.4(a) 只對 PEP 要求
        TriggerSpec("missing_source_of_funds_evidence", obligation_id=None,
                    attributes=("source_of_funds_available",), holds=lambda c: c.source_of_funds_available is False),
    ),
    # 無法完成 CDD（UBO 不明）時，MAS 6.35 要求不得建立業務關係並考慮申報 STR；
    # 多層持股依銀行政策 1.2(b) 視為高風險
    obligations=("ob_cdd_on_relationship_mas", "ob_identify_ubo_mas", "ob_identify_ubo_10_gb", "ob_cdd_incomplete_mas"),
    human_review_required=True,
)
L_CORPORATE_INTERNAL_UBO_THRESHOLD = Leaf(
    leaf_id="corporate_internal_ubo_threshold",
    label="企業主要股東達內部 10% 門檻：加驗股東身分",
    decision="standard_cdd",
    items=(
        ("Certificate of Incorporation", "ob_verify_customer_mas"),
        ("ACRA Company Profile", "ob_verify_customer_mas"),
        ("Shareholder Registry", "ob_identify_ubo_10_gb"),
        ("UBO 15% Shareholder Identity Document (NRIC/Passport)", "ob_identify_ubo_10_gb"),
    ),
    # 銀行政策 1.2(a)：「an ownership threshold of 10% or more (which is stricter than the regulatory baseline of 25%)」
    triggers=(TriggerSpec("internal_ubo_threshold_triggered_10_percent", obligation_id="ob_identify_ubo_10_gb",
                          clause_id=_GB_1_2_A,
                          attributes=(SHAREHOLDER_PCT_ATTR,), holds=lambda c: 10 <= _shareholder_pct(c) <= 25),),
    obligations=("ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_identify_ubo_mas", "ob_identify_ubo_10_gb"),
    human_review_required=True,
)
L_CORPORATE_STANDARD = Leaf(
    leaf_id="corporate_standard",
    label="一般企業：標準 CDD",
    decision="standard_cdd",
    items=(
        ("Certificate of Incorporation", "ob_verify_customer_mas"),
        ("ACRA Company Profile", "ob_verify_customer_mas"),
    ),
    triggers=(),
    obligations=("ob_cdd_on_relationship_mas", "ob_verify_customer_mas", "ob_identify_ubo_mas"),
    human_review_required=False,
)
L_OTHER = Leaf(
    leaf_id="other_customer_type",
    label="其他客戶類型：預設標準 CDD，無文件要求",
    decision="standard_cdd",
    items=(),
    triggers=(),
    obligations=(),
    human_review_required=False,
)

DECISION_TREE = Node(
    T_IS_INDIVIDUAL,
    yes=Node(T_IS_PEP,
             yes=Node(T_PEP_HIGH_RISK, yes=L_INDIVIDUAL_PEP_HIGH_RISK, no=L_INDIVIDUAL_PEP),
             no=L_INDIVIDUAL_STANDARD),
    no=Node(T_IS_CORPORATE,
            yes=Node(T_CORPORATE_CDD_BLOCKED,
                     yes=L_CORPORATE_CDD_INCOMPLETE,
                     no=Node(T_INTERNAL_UBO_THRESHOLD, yes=L_CORPORATE_INTERNAL_UBO_THRESHOLD, no=L_CORPORATE_STANDARD)),
            no=L_OTHER),
)


def _collect(node: Union[Node, Leaf], tests: Dict[str, DecisionTest], leaves: Dict[str, Leaf]) -> None:
    if isinstance(node, Leaf):
        leaves[node.leaf_id] = node
        return
    tests[node.test.test_id] = node.test
    _collect(node.yes, tests, leaves)
    _collect(node.no, tests, leaves)


TESTS: Dict[str, DecisionTest] = {}
LEAVES: Dict[str, Leaf] = {}
_collect(DECISION_TREE, TESTS, LEAVES)

# 決策樹讀取的所有客戶屬性（依首次出現順序）
ATTRIBUTES_READ: List[str] = list(dict.fromkeys(a for t in TESTS.values() for a in t.attributes))


def route(customer: CustomerContext) -> Tuple[Leaf, List[PathStep]]:
    """沿決策樹走到葉節點，回傳葉節點與經過的每個測試。"""
    node: Union[Node, Leaf] = DECISION_TREE
    steps: List[PathStep] = []
    while isinstance(node, Node):
        outcome, results = node.test.evaluate(customer)
        steps.append(PathStep(node.test, outcome, tuple(results)))
        node = node.yes if outcome else node.no
    return node, steps


def checklist_id_for(customer_id: str) -> str:
    return f"chk_{customer_id.replace('cust_', '')}"


class CDDChecklistEngine:
    """
    客戶 CDD 檢核推理引擎。
    決策分支是明確的決策樹（DECISION_TREE）：節點是測試，葉節點宣告輸出（文件與其義務、風險標記、
    適用義務、是否需人工審查），因此每個決策都能沿路徑完整解釋。引用與未決衝突則由義務的出處推導：
    - citations：適用義務的錨點條文 ID（解析出的條文）
    - unresolved_conflicts：與適用義務相關、尚未人工裁決的衝突，有的話一律送人工審查
    """

    def generate_checklist(
        self,
        customer: CustomerContext,
        obligations: List[Obligation],
        conflicts: List[Conflict]
    ) -> CDDChecklist:
        """
        輸入單一客戶情境與法規/政策義務、衝突列表，推理生成對應的強型別 CDDChecklist。
        """
        leaf, _ = route(customer)
        applicable_obligations = list(leaf.obligations)
        human_review_required = leaf.human_review_required

        # 引用由出處推導：每個適用義務引用它的錨點條文（source_clause_ids 第一條），
        # 所以每個引用都是解析出的條文 ID，能在圖譜中解析到原文
        ob_dict = {ob.obligation_id: ob for ob in obligations}
        citations: List[str] = []
        for ob_id in applicable_obligations:
            ob = ob_dict.get(ob_id)
            if ob and ob.source_clause_ids and ob.source_clause_ids[0] not in citations:
                citations.append(ob.source_clause_ids[0])

        # 與適用義務相關、但尚未經人工裁決的衝突：列入清單並強制送人工審查
        applicable_clause_ids = {
            cid for ob_id in applicable_obligations if ob_id in ob_dict for cid in ob_dict[ob_id].source_clause_ids
        }
        unresolved_conflicts: List[str] = []
        for conflict in conflicts:
            if conflict.adjudication_status != "resolved" and applicable_clause_ids.intersection(conflict.source_clause_ids):
                unresolved_conflicts.append(conflict.conflict_id)
        if unresolved_conflicts:
            human_review_required = True

        return CDDChecklist(
            checklist_id=checklist_id_for(customer.customer_id),
            customer_id=customer.customer_id,
            decision=leaf.decision,
            required_documents=leaf.required_documents,
            risk_triggers=leaf.risk_triggers,
            applicable_obligations=applicable_obligations,
            unresolved_conflicts=unresolved_conflicts,
            human_review_required=human_review_required,
            citations=citations
        )


class ChecklistEvaluator:
    """
    黃金數據對齊評估工具。
    比對引擎自動產出的 CDDChecklist 列表與 data/gold/checklists.yaml 的期望值，
    計算 Precision、Recall 與 F1-score，以量化合規推理對齊性。
    """

    def evaluate_alignment(
        self,
        generated: List[CDDChecklist],
        expected: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        比對產出列表與預期金標字典列表，計算並返回對齊性指標。
        """
        # 將 generated 轉為 map 以方便透過 customer_id 檢索
        gen_map = {item.customer_id: item for item in generated}
        
        total_fields = 0
        correct_fields = 0
        
        # 定義需要對齊的 6 大關鍵欄位
        fields_to_compare = [
            "decision",
            "required_documents",
            "risk_triggers",
            "applicable_obligations",
            "human_review_required",
            "citations"
        ]
        
        for exp in expected:
            cust_id = exp["customer_id"]
            if cust_id not in gen_map:
                # 缺失對應的預測，預設此客戶的所有欄位均不對齊
                total_fields += len(fields_to_compare)
                continue
                
            gen = gen_map[cust_id]
            
            for field in fields_to_compare:
                total_fields += 1
                
                gen_val = getattr(gen, field)
                exp_val = exp[field]
                
                # 針對列表型欄位，進行不區分順序的集合/列表值比對
                if isinstance(exp_val, list):
                    if sorted(list(gen_val)) == sorted(list(exp_val)):
                        correct_fields += 1
                else:
                    # 針對單一值欄位 (decision, human_review_required)
                    if gen_val == exp_val:
                        correct_fields += 1
                        
        if total_fields == 0:
            precision = 0.0
            recall = 0.0
            f1 = 0.0
        else:
            precision = correct_fields / total_fields
            recall = correct_fields / total_fields  # 因為對齊樣本數與預測數一對一對等
            if precision + recall == 0:
                f1 = 0.0
            else:
                f1 = 2 * precision * recall / (precision + recall)
                
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "total_evaluated_fields": float(total_fields),
            "aligned_fields": float(correct_fields)
        }
