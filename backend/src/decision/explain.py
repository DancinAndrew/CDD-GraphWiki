"""
檢核表的忠實解釋：決策路徑、文件與法源、風險標記與單一屬性反事實。

所有內容都直接讀自 engine.DECISION_TREE（引擎實際走的路徑與葉節點宣告），不另寫一套說法：
- path：經過的每個測試、讀到的屬性值、結果；OR 測試另列每個條件是否成立
- items：每份文件依據的義務、義務的出處條文、規則理由與高亮片段（落在其他條文、例如上層引言的理由片段另列為
  context_evidence，並記下是哪一條條文的理由引用了它）、相關衝突
- obligation_conflicts：每個適用義務（含不需另收文件的義務）的相關衝突與裁決狀態
- risk_triggers：每個標記宣告依據的義務與寫出條件的條文（沒有法源時明說）、斷言了哪些客戶屬性，
  這些屬性是否在路徑上被檢驗、斷言對本客戶是否成立
- counterfactuals：只改一個屬性、重跑引擎後輸出真的改變的情況（引擎無法重算的改值也列出並說明）
- attributes_read_but_not_decisive：路徑上讀到、但單獨改成任何候選值都不會改變輸出的屬性
- attributes_not_read：決策樹從不讀取的客戶屬性
"""
import math
from typing import Any, Dict, List, Optional, Tuple, get_args

from pydantic import BaseModel, Field

from src.contracts.models import CDDChecklist, Clause, Conflict, CustomerContext, Obligation, SourceDocument
from src.decision.engine import (
    ATTRIBUTES_READ,
    SHAREHOLDER_PCT_ATTR,
    CDDChecklistEngine,
    Leaf,
    PathStep,
    read_attribute,
    route,
)


class ConditionResult(BaseModel):
    """OR 測試中單一條件的結果。"""
    attribute: str
    condition: str
    observed: Any = None
    holds: bool


class DecisionStep(BaseModel):
    test_id: str
    question: str
    attributes: List[str]
    observed: Dict[str, Any]
    outcome: bool
    parts: List[ConditionResult] = Field(default_factory=list, description="只有 OR 測試才列出")


class BranchRef(BaseModel):
    id: str
    label: str


class SourceClauseEvidence(BaseModel):
    clause_id: str
    section_ref: Optional[str] = None
    document_title: Optional[str] = None
    raw_text: Optional[str] = None
    reasons: List[Dict[str, Any]] = Field(default_factory=list, description="規則理由（RuleReason）")
    highlights: List[Dict[str, Any]] = Field(default_factory=list, description="落在本條文內的理由片段")
    context_evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="理由片段中落在其他條文的部分（例如條列項目繼承的上層引言），含沿 depends_on 遞移追到的理由片段；"
                    "relation 為片段所在條文和本條文的關係：ancestor（上層條文）、descendant（下層項目）或 "
                    "referenced（其他條文，經引用而來）；cited_by 是理由用到這個片段的條文（clause_id、section_ref，"
                    "relation 為它和本條文的關係，self 代表本條文自己）",
    )


class ConflictRef(BaseModel):
    conflict_id: str
    conflict_type: str
    description: str
    adjudication_status: str
    reconciliation_rule: Optional[str] = None
    resolved_by: Optional[str] = None


class DocumentItemExplanation(BaseModel):
    document: str
    obligation_id: str
    obligation_found: bool
    obligation_confidence: Optional[float] = None
    obligation_confidence_basis: Optional[str] = None
    obligation_confidence_kind: Optional[str] = Field(
        None, description="measured_on_heldout（保留文本實測）、self_reported（模型自評）或 None（未量測）")
    source_clauses: List[SourceClauseEvidence] = Field(default_factory=list)
    conflicts: List[ConflictRef] = Field(default_factory=list)


class RiskTriggerExplanation(BaseModel):
    trigger: str
    obligation_id: Optional[str] = Field(
        None, description="葉節點為這個標記宣告的義務；知識庫沒有任何義務對這位客戶要求這個條件時為 None")
    clause_id: Optional[str] = Field(None, description="該義務出處條文中寫出這個條件的那一條；沒有義務時為 None")
    note: Optional[str] = Field(None, description="obligation_id 為 None 時說明它沒有法源")
    attributes: List[str]
    tested_by_decision: bool = Field(..., description="斷言的屬性都在決策路徑上被讀取；沒有屬性時為 True")
    holds: Optional[bool] = Field(None, description="斷言對本客戶是否成立；不對屬性下斷言時為 None")


class Counterfactual(BaseModel):
    attribute: str
    current_value: Any = None
    counterfactual_value: Any = None
    value_note: Optional[str] = None
    branch: Optional[List[BranchRef]] = Field(None, description="分支改變時為 [原分支, 新分支]（ID 與標籤）")
    decision: Optional[List[str]] = None
    documents_added: List[str] = Field(default_factory=list)
    documents_removed: List[str] = Field(default_factory=list)
    obligations_added: List[str] = Field(default_factory=list)
    obligations_removed: List[str] = Field(default_factory=list)
    triggers_added: List[str] = Field(default_factory=list)
    triggers_removed: List[str] = Field(default_factory=list)
    conflicts_added: List[str] = Field(default_factory=list, description="改值後新出現的未裁決衝突")
    conflicts_removed: List[str] = Field(default_factory=list, description="改值後不再適用的未裁決衝突")
    citations_added: List[str] = Field(default_factory=list)
    citations_removed: List[str] = Field(default_factory=list)
    human_review: Optional[List[bool]] = None
    computed: bool = Field(True, description="False 代表引擎無法用改值後的資料重算，value_note 說明原因，其餘差異欄位為空")


class NonDecisiveAttribute(BaseModel):
    """路徑上讀到、但單獨改成任何候選值都不會改變輸出的屬性。"""
    attribute: str
    observed: Any = None
    reason: str


class ChecklistExplanation(BaseModel):
    customer_id: str
    checklist_id: str
    decision: str
    human_review_required: bool
    branch_human_review_required: bool = Field(
        ..., description="葉節點本身是否要求人工審查；為 False 而 human_review_required 為 True 時，審查來自未裁決衝突")
    unresolved_conflicts: List[str] = Field(default_factory=list)
    branch: BranchRef
    path: List[DecisionStep]
    items: List[DocumentItemExplanation]
    obligations_without_documents: List[str]
    obligation_conflicts: Dict[str, List[ConflictRef]] = Field(
        default_factory=dict, description="每個適用義務（依葉節點宣告順序，含不需另收文件的義務）的相關衝突")
    risk_triggers: List[RiskTriggerExplanation]
    counterfactuals: List[Counterfactual]
    attributes_read_but_not_decisive: List[NonDecisiveAttribute] = Field(default_factory=list)
    attributes_not_read: List[str]


OTHER_JURISDICTION = "Singapore"
OTHER_JURISDICTION_NOTE = "代表緬甸與開曼群島以外的任何管轄區（決策樹只比對這兩個值）"
NO_OBLIGATION_NOTE = "知識庫中沒有任何義務對這位客戶要求這個條件，所以這個標記不引用任何義務。"
# 個別標記的補充：資料裡確實提到這個條件、但沒有成為適用義務的條文
NO_OBLIGATION_DETAILS = {
    "missing_source_of_funds_evidence": (
        "FATF 第 10 項 (d) 提到資金來源，但沒有從它抽出義務；"
        "MAS 8.3(b) 與銀行政策 1.4(a) 要求資金來源，但只適用於政治敏感人物（PEP）。"
    ),
}


def _as_dict(item: Any) -> Dict[str, Any]:
    return item.model_dump() if hasattr(item, "model_dump") else dict(item)


def obligation_for_item(leaf: Leaf, target_item: str) -> str:
    """
    檢核項目對應的義務，只看葉節點宣告：
    - 文件：葉節點 items 中該文件的義務
    - 風險標記：TriggerSpec 宣告的 obligation_id
    對不上、或標記宣告沒有義務時拋出 ValueError，不做猜測。
    """
    for document, ob_id in leaf.items:
        if document == target_item:
            return ob_id
    for spec in leaf.triggers:
        if spec.trigger == target_item:
            if spec.obligation_id is None:
                raise ValueError(
                    f"Risk trigger {target_item!r} in branch {leaf.leaf_id} declares no obligation: "
                    "no obligation in the knowledge base requires this condition for this customer")
            return spec.obligation_id
    raise ValueError(f"{target_item!r} is not declared by branch {leaf.leaf_id}")


def describe_steps(steps: List[PathStep], customer: CustomerContext) -> List[DecisionStep]:
    result = []
    for step in steps:
        attributes = step.test.attributes
        parts = []
        if len(step.test.conditions) > 1:
            parts = [
                ConditionResult(attribute=c.attribute, condition=c.description,
                                observed=read_attribute(customer, c.attribute), holds=holds)
                for c, holds in zip(step.test.conditions, step.condition_results)
            ]
        result.append(DecisionStep(
            test_id=step.test.test_id,
            question=step.test.question,
            attributes=attributes,
            observed={a: read_attribute(customer, a) for a in attributes},
            outcome=step.outcome,
            parts=parts,
        ))
    return result


def _highlights(clause_id: str, reasons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """理由片段中落在本條文的部分；同一片段被多條規則引用時合併規則名。"""
    spans: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for reason in reasons:
        for span in reason.get("spans", []):
            span = _as_dict(span)
            if span.get("clause_id") != clause_id:
                continue
            key = (span["start"], span["end"])
            entry = spans.setdefault(key, {"start": span["start"], "end": span["end"], "text": span["text"], "rules": []})
            if reason.get("rule") not in entry["rules"]:
                entry["rules"].append(reason.get("rule"))
    return [spans[k] for k in sorted(spans)]


def label_reasons(obligations: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """所有義務的規則理由，依標記 '<clause_id>#<type>' 索引，用來追 depends_on。"""
    index: Dict[str, List[Dict[str, Any]]] = {}
    for ob in obligations:
        for clause_id, reasons in getattr(ob, "explanations", {}).items():
            for reason in reasons:
                reason = _as_dict(reason)
                index.setdefault(f"{clause_id}#{reason.get('obligation_type')}", []).append(reason)
    return index


def _context_evidence(clause_id: str, reasons: List[Dict[str, Any]], labels: Dict[str, List[Dict[str, Any]]],
                      clause_dict: Dict[str, Clause]) -> List[Dict[str, Any]]:
    """
    理由片段中不在本條文的部分（例如條列項目的上層引言），並沿 depends_on 一路追下去（遞移、不重複），
    所以多層條列的項目也看得到最上層引言裡的依據字詞；這和刪字測試用的 rationale 是同一組片段。
    relation 說明片段所在條文和本條文的關係：ancestor（上層條文）、descendant（下層項目）、referenced（其他條文）。
    cited_by 是理由用到這個片段的條文：本條文自己的理由為本條文，經 depends_on 追到的理由為持有那條
    depends_on 的條文（廣度優先，取最先追到的一條），所以看得出引用是本條文還是上層引言做的。
    同一片段合併規則名。
    """
    # (理由, 用到它的條文)：本條文的理由由本條文用到；經 depends_on 追到的理由由持有 depends_on 的條文用到
    collected: List[Tuple[Dict[str, Any], str]] = [(reason, clause_id) for reason in reasons]
    seen: set = set()
    queue = [(label, clause_id) for reason in reasons for label in reason.get("depends_on", [])]
    while queue:
        label, citing = queue.pop(0)
        if label in seen:
            continue
        seen.add(label)
        owner = label.rpartition("#")[0]
        for reason in labels.get(label, []):
            collected.append((reason, citing))
            queue.extend((dep, owner) for dep in reason.get("depends_on", []))

    def ancestors(cid: str) -> List[str]:
        chain, current = [], clause_dict.get(cid)
        while current is not None and current.parent_clause_id:
            chain.append(current.parent_clause_id)
            current = clause_dict.get(current.parent_clause_id)
        return chain

    own_ancestors = set(ancestors(clause_id))

    def relation_to_clause(cid: str) -> str:
        if cid == clause_id:
            return "self"
        if cid in own_ancestors:
            return "ancestor"
        if clause_id in ancestors(cid):
            return "descendant"
        return "referenced"

    def section_ref(cid: str) -> Optional[str]:
        clause = clause_dict.get(cid)
        return clause.section_ref if clause else None

    spans: Dict[Tuple[str, int, int], Dict[str, Any]] = {}
    for reason, citing in collected:
        for span in reason.get("spans", []):
            span = _as_dict(span)
            if span.get("clause_id") == clause_id:
                continue
            key = (span["clause_id"], span["start"], span["end"])
            entry = spans.setdefault(key, {
                "clause_id": span["clause_id"],
                "section_ref": section_ref(span["clause_id"]),
                "relation": relation_to_clause(span["clause_id"]),
                "cited_by": {"clause_id": citing, "section_ref": section_ref(citing),
                             "relation": relation_to_clause(citing)},
                "start": span["start"],
                "end": span["end"],
                "text": span["text"],
                "rules": [],
            })
            if reason.get("rule") not in entry["rules"]:
                entry["rules"].append(reason.get("rule"))
    clause_order = list(dict.fromkeys(k[0] for k in spans))
    return [spans[k] for k in sorted(spans, key=lambda k: (clause_order.index(k[0]), k[1], k[2]))]


def explain_clause(clause_id: str, ob: Obligation, clause_dict: Dict[str, Clause],
                   doc_dict: Dict[str, SourceDocument],
                   labels: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> SourceClauseEvidence:
    """labels 是 label_reasons() 的索引，用來追 depends_on；未給時只用這個義務自己的理由。"""
    reasons = [_as_dict(r) for r in getattr(ob, "explanations", {}).get(clause_id, [])]
    if labels is None:
        labels = label_reasons([ob])
    context = _context_evidence(clause_id, reasons, labels, clause_dict)
    clause = clause_dict.get(clause_id)
    if clause is None:
        return SourceClauseEvidence(clause_id=clause_id, reasons=reasons, context_evidence=context)
    doc = doc_dict.get(clause.source_document_id)
    return SourceClauseEvidence(
        clause_id=clause_id,
        section_ref=clause.section_ref,
        document_title=doc.title if doc else None,
        raw_text=clause.raw_text,
        reasons=reasons,
        highlights=_highlights(clause_id, reasons),
        context_evidence=context,
    )


def related_conflicts(ob: Obligation, conflicts: List[Conflict]) -> List[ConflictRef]:
    """和義務出處條文有交集的衝突；引擎用同一個條件找出未裁決衝突。"""
    source_ids = set(ob.source_clause_ids)
    return [
        ConflictRef(
            conflict_id=cf.conflict_id,
            conflict_type=cf.conflict_type,
            description=cf.description,
            adjudication_status=cf.adjudication_status,
            reconciliation_rule=cf.reconciliation_rule,
            resolved_by=cf.resolved_by,
        )
        for cf in conflicts if source_ids.intersection(cf.source_clause_ids)
    ]


def _explain_document(document: str, ob_id: str, ob_dict: Dict[str, Obligation], conflicts: List[Conflict],
                      clause_dict: Dict[str, Clause], doc_dict: Dict[str, SourceDocument],
                      labels: Dict[str, List[Dict[str, Any]]]) -> DocumentItemExplanation:
    ob = ob_dict.get(ob_id)
    if ob is None:
        return DocumentItemExplanation(document=document, obligation_id=ob_id, obligation_found=False)
    return DocumentItemExplanation(
        document=document,
        obligation_id=ob_id,
        obligation_found=True,
        obligation_confidence=getattr(ob, "confidence", None),
        obligation_confidence_basis=getattr(ob, "confidence_basis", None),
        obligation_confidence_kind=getattr(ob, "confidence_kind", None),
        source_clauses=[explain_clause(cid, ob, clause_dict, doc_dict, labels) for cid in ob.source_clause_ids],
        conflicts=related_conflicts(ob, conflicts),
    )


def no_obligation_note(trigger: str) -> str:
    detail = NO_OBLIGATION_DETAILS.get(trigger)
    return f"{NO_OBLIGATION_NOTE}{detail}" if detail else NO_OBLIGATION_NOTE


def explain_triggers(leaf: Leaf, steps: List[PathStep], customer: CustomerContext) -> List[RiskTriggerExplanation]:
    read_on_path = {a for step in steps for a in step.test.attributes}
    return [
        RiskTriggerExplanation(
            trigger=spec.trigger,
            obligation_id=spec.obligation_id,
            clause_id=spec.clause_id,
            note=no_obligation_note(spec.trigger) if spec.obligation_id is None else None,
            attributes=list(spec.attributes),
            tested_by_decision=all(a in read_on_path for a in spec.attributes),
            holds=bool(spec.holds(customer)) if spec.attributes and spec.holds else None,
        )
        for spec in leaf.triggers
    ]


def attributes_not_read(customer: CustomerContext) -> List[str]:
    """決策樹從不讀取的客戶屬性（customer_id 只用來命名清單，不算決策屬性）。"""
    fields = [
        name for name in CustomerContext.model_fields
        if name not in ("customer_id", "custom_attributes") and name not in ATTRIBUTES_READ
    ]
    custom = [
        f"custom_attributes.{key}" for key in customer.custom_attributes
        if f"custom_attributes.{key}" not in ATTRIBUTES_READ
    ]
    return fields + custom


# ---------- 反事實 ----------

def _literal_values(field: str) -> Tuple[Any, ...]:
    return get_args(CustomerContext.model_fields[field].annotation)


def _is_number(value: Any) -> bool:
    """A finite int or float (NaN would fall in no region of the 10–25 test, so it is treated as not a number)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def counterfactual_candidates(customer: CustomerContext) -> List[Tuple[str, Any, Optional[str]]]:
    """每個決策屬性的單一改值候選：(屬性, 新值, 說明)。"""
    candidates: List[Tuple[str, Any, Optional[str]]] = []
    for value in _literal_values("customer_type"):
        if value != customer.customer_type:
            candidates.append(("customer_type", value, None))
    candidates.append(("pep_exposure", not customer.pep_exposure, None))
    for field in ("ubo_country_risk", "ubo_status"):
        for value in _literal_values(field):
            if value != getattr(customer, field):
                candidates.append((field, value, None))

    jurisdiction = customer.registration_jurisdiction.lower()
    if jurisdiction == "myanmar":
        jurisdictions = [(OTHER_JURISDICTION, OTHER_JURISDICTION_NOTE), ("Cayman Islands", None)]
    elif jurisdiction == "cayman islands":
        jurisdictions = [(OTHER_JURISDICTION, OTHER_JURISDICTION_NOTE), ("Myanmar", None)]
    else:
        jurisdictions = [("Myanmar", None), ("Cayman Islands", None)]
    candidates += [("registration_jurisdiction", value, note) for value, note in jurisdictions]

    # 持股比例分三區（<10、10..25、>25），每個不在的區取最接近的值；未提供視為 0（與引擎相同）。
    # 目前值不是數字（null、字串、布林）時看不出在哪一區，三區各取一個值，並在說明裡講明
    pct = customer.custom_attributes.get("major_shareholder_pct", 0)
    if _is_number(pct):
        region = "below" if pct < 10 else ("within" if pct <= 25 else "above")
        nearest = {"below": 9, "within": min(max(pct, 10), 25), "above": 26}
        for name in ("below", "within", "above"):
            if name != region:
                candidates.append((SHAREHOLDER_PCT_ATTR, nearest[name], None))
    else:
        note = f"目前的值 {pct!r} 不是數字，看不出落在哪一區，所以三個區間各試一個值"
        candidates += [(SHAREHOLDER_PCT_ATTR, value, note) for value in (9, 10, 26)]
    return candidates


def apply_change(customer: CustomerContext, attribute: str, value: Any) -> CustomerContext:
    if attribute.startswith("custom_attributes."):
        custom = dict(customer.custom_attributes)
        custom[attribute.split(".", 1)[1]] = value
        return customer.model_copy(update={"custom_attributes": custom})
    return customer.model_copy(update={attribute: value})


def _added(old: List[str], new: List[str]) -> List[str]:
    return [x for x in new if x not in old]


def compare_checklists(before: CDDChecklist, after: CDDChecklist) -> Dict[str, Any]:
    """反事實要報告的差異；全部為空代表輸出沒有改變。"""
    return {
        "decision": [before.decision, after.decision] if before.decision != after.decision else None,
        "documents_added": _added(before.required_documents, after.required_documents),
        "documents_removed": _added(after.required_documents, before.required_documents),
        "obligations_added": _added(before.applicable_obligations, after.applicable_obligations),
        "obligations_removed": _added(after.applicable_obligations, before.applicable_obligations),
        "triggers_added": _added(before.risk_triggers, after.risk_triggers),
        "triggers_removed": _added(after.risk_triggers, before.risk_triggers),
        "conflicts_added": _added(before.unresolved_conflicts, after.unresolved_conflicts),
        "conflicts_removed": _added(after.unresolved_conflicts, before.unresolved_conflicts),
        "citations_added": _added(before.citations, after.citations),
        "citations_removed": _added(after.citations, before.citations),
        "human_review": ([before.human_review_required, after.human_review_required]
                         if before.human_review_required != after.human_review_required else None),
    }


def _uncomputable_note(changed: CustomerContext) -> Optional[str]:
    """引擎無法處理改值後的客戶時說明原因；目前只有持股比例不是數字、又被決策樹比較的情況。"""
    pct = changed.custom_attributes.get("major_shareholder_pct", 0)
    if _is_number(pct) or isinstance(pct, bool):
        return None
    return (f"引擎無法用這個改值重算：改值後決策樹會比較 {SHAREHOLDER_PCT_ATTR} 與 10、25，"
            f"但它的值 {pct!r} 不是數字，所以不知道結果")


def _run_candidates(customer: CustomerContext, checklist: CDDChecklist, obligations: List[Obligation],
                    conflicts: List[Conflict]) -> List[Tuple[str, Any, Optional[str], Optional[Dict[str, Any]]]]:
    """
    每個候選改值重跑引擎：(屬性, 新值, 說明, 差異)。引擎無法重算時差異為 None、說明講原因；
    只接受已知的原因（持股比例不是數字），其他錯誤照常拋出，不掩蓋引擎的問題。
    """
    engine = CDDChecklistEngine()
    runs = []
    for attribute, value, note in counterfactual_candidates(customer):
        changed = apply_change(customer, attribute, value)
        try:
            diff: Optional[Dict[str, Any]] = compare_checklists(
                checklist, engine.generate_checklist(changed, obligations, conflicts))
        except TypeError:
            reason = _uncomputable_note(changed)
            if reason is None:
                raise
            note = f"{note}；{reason}" if note else reason
            diff = None
        runs.append((attribute, value, note, diff))
    return runs


def explain_counterfactuals(customer: CustomerContext, runs: List[Tuple[str, Any, Optional[str], Optional[Dict[str, Any]]]]
                            ) -> List[Counterfactual]:
    """輸出真的改變的改值，以及引擎無法重算的改值（computed=False）。"""
    leaf, _ = route(customer)
    result = []
    for attribute, value, note, diff in runs:
        common = dict(attribute=attribute, current_value=read_attribute(customer, attribute),
                      counterfactual_value=value, value_note=note)
        if diff is None:
            result.append(Counterfactual(**common, computed=False))
            continue
        if not any(diff.values()):
            continue
        new_leaf, _ = route(apply_change(customer, attribute, value))
        result.append(Counterfactual(
            **common,
            branch=([BranchRef(id=leaf.leaf_id, label=leaf.label), BranchRef(id=new_leaf.leaf_id, label=new_leaf.label)]
                    if new_leaf.leaf_id != leaf.leaf_id else None),
            **diff,
        ))
    return result


def _not_decisive_reason(attribute: str, steps: List[PathStep], customer: CustomerContext) -> str:
    """一句話說明為什麼單獨改這個屬性不會改變輸出。"""
    for step in steps:
        conditions = step.test.conditions
        if not step.outcome or len(conditions) < 2 or attribute not in step.test.attributes:
            continue
        others = [c for c, holds in zip(conditions, step.condition_results) if holds and c.attribute != attribute]
        if others:
            other = others[0]
            return (f"「{step.test.question}」任一條件成立即為「是」，另一個條件 "
                    f"{other.attribute} = {read_attribute(customer, other.attribute)!r} 也成立，所以只改這個屬性結果仍為「是」")
    return "路徑讀到這個屬性，但把它單獨改成任何候選值、重跑引擎後檢核表都不變"


def attributes_read_but_not_decisive(customer: CustomerContext, steps: List[PathStep],
                                     runs: List[Tuple[str, Any, Optional[str], Optional[Dict[str, Any]]]]
                                     ) -> List[NonDecisiveAttribute]:
    """路徑上讀到、每個候選改值都算得出來且都不改變輸出的屬性（有算不出來的改值就不下這個結論）。"""
    read_on_path = list(dict.fromkeys(a for step in steps for a in step.test.attributes))
    result = []
    for attribute in read_on_path:
        diffs = [diff for attr, _, _, diff in runs if attr == attribute]
        if not diffs or any(diff is None or any(diff.values()) for diff in diffs):
            continue
        result.append(NonDecisiveAttribute(
            attribute=attribute,
            observed=read_attribute(customer, attribute),
            reason=_not_decisive_reason(attribute, steps, customer),
        ))
    return result


def explain(customer: CustomerContext, obligations: List[Obligation], conflicts: List[Conflict],
            clauses: List[Clause], documents: List[SourceDocument]) -> ChecklistExplanation:
    """為單一客戶產出完整的檢核表解釋；檢核表本身由同一個引擎產生。"""
    checklist = CDDChecklistEngine().generate_checklist(customer, obligations, conflicts)
    leaf, steps = route(customer)
    ob_dict = {ob.obligation_id: ob for ob in obligations}
    clause_dict = {cl.clause_id: cl for cl in clauses}
    doc_dict = {doc.source_document_id: doc for doc in documents}
    with_documents = {ob_id for _, ob_id in leaf.items}
    labels = label_reasons(obligations)
    runs = _run_candidates(customer, checklist, obligations, conflicts)

    return ChecklistExplanation(
        customer_id=customer.customer_id,
        checklist_id=checklist.checklist_id,
        decision=checklist.decision,
        human_review_required=checklist.human_review_required,
        branch_human_review_required=leaf.human_review_required,
        unresolved_conflicts=checklist.unresolved_conflicts,
        branch=BranchRef(id=leaf.leaf_id, label=leaf.label),
        path=describe_steps(steps, customer),
        items=[_explain_document(document, ob_id, ob_dict, conflicts, clause_dict, doc_dict, labels)
               for document, ob_id in leaf.items],
        obligations_without_documents=[ob_id for ob_id in leaf.obligations if ob_id not in with_documents],
        obligation_conflicts={ob_id: related_conflicts(ob_dict[ob_id], conflicts)
                              for ob_id in leaf.obligations if ob_id in ob_dict},
        risk_triggers=explain_triggers(leaf, steps, customer),
        counterfactuals=explain_counterfactuals(customer, runs),
        attributes_read_but_not_decisive=attributes_read_but_not_decisive(customer, steps, runs),
        attributes_not_read=attributes_not_read(customer),
    )
