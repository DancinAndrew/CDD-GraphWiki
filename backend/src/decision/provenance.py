from typing import Any, Dict, List
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    CDDChecklist,
    ProvenanceNode,
    ExplanationPath
)
from src.decision.engine import PathStep, TriggerSpec, checked_by, read_attribute, route
from src.decision.explain import obligation_for_item


def _format_value(value: Any) -> str:
    return "未提供" if value is None else str(value)


def _fact_nodes(steps: List[PathStep], customer: CustomerContext) -> List[ProvenanceNode]:
    """決策路徑上讀到的每個屬性一個節點（同一屬性被多個測試讀取時合併），附讀到的值與測試結果。"""
    facts: Dict[str, Dict[str, Any]] = {}
    for step in steps:
        for attribute in step.test.attributes:
            fact = facts.setdefault(attribute, {"value": read_attribute(customer, attribute), "tests": []})
            fact["tests"].append({
                "test_id": step.test.test_id,
                "question": step.test.question,
                "outcome": step.outcome,
            })
    nodes = []
    for attribute, fact in facts.items():
        name = attribute.split(".", 1)[-1]
        answers = "；".join(f"{t['question']}{'是' if t['outcome'] else '否'}" for t in fact["tests"])
        nodes.append(ProvenanceNode(
            node_id=f"fact_{name}",
            node_type="customer_fact",
            label=f"客戶特徵：{attribute} = {_format_value(fact['value'])}（{answers}）",
            properties={name: fact["value"], "attribute": attribute, "tests": fact["tests"]},
        ))
    return nodes


def _condition_fact_nodes(spec: TriggerSpec, customer: CustomerContext) -> List[ProvenanceNode]:
    """由標記自己的條件檢查的屬性：每個屬性一個節點，附讀到的值與條件。"""
    return [
        ProvenanceNode(
            node_id=f"fact_{attribute.split('.', 1)[-1]}",
            node_type="customer_fact",
            label=f"客戶特徵：{attribute} = {_format_value(read_attribute(customer, attribute))}"
                  f"（標記條件 {spec.condition} 成立）",
            properties={attribute.split(".", 1)[-1]: read_attribute(customer, attribute), "attribute": attribute,
                        "trigger_condition": spec.condition},
        )
        for attribute in spec.attributes
    ]


def _path_sentence(steps: List[PathStep], customer: CustomerContext) -> str:
    parts = []
    for step in steps:
        observed = "、".join(f"{a} = {_format_value(read_attribute(customer, a))}" for a in step.test.attributes)
        parts.append(f"{step.test.question}{'是' if step.outcome else '否'}（{observed}）")
    return " → ".join(parts)


class ProvenanceEngine:
    """
    可解釋合規推理與條款級雙向溯源引擎。
    提供為檢核表項目回溯推理合規鏈與生成人類可讀 Markdown 審計軌跡報告之功能。
    解釋完全取自引擎的決策樹：事實節點是路徑上讀到的屬性，義務來自葉節點宣告的 (文件, 義務)，
    不再以關鍵字猜測。
    """

    def explain_item(
        self,
        checklist: CDDChecklist,
        target_item: str,
        customer: CustomerContext,
        obligations: List[Obligation],
        clauses: List[Clause],
        documents: List[SourceDocument]
    ) -> ExplanationPath:
        """
        為檢核清單中的特定要求文件或風險標記回溯推理，產出結構化的 ExplanationPath：
        路徑上讀到的客戶特徵 ➔ 葉節點宣告的義務 ➔ 條文 ➔ 來源文件。
        文件引用義務的錨點條文；風險標記引用 TriggerSpec 宣告、寫出這個條件的那一條出處條文。
        項目不在清單中、與客戶的決策路徑對不上、或風險標記對這位客戶不成立時拋出 ValueError。
        """
        is_document = target_item in checklist.required_documents
        is_trigger = target_item in checklist.risk_triggers
        if not (is_document or is_trigger):
            raise ValueError(f"{target_item!r} is not a required document or risk trigger of {checklist.checklist_id}")

        leaf, steps = route(customer)
        ob_id = obligation_for_item(leaf, target_item)
        ob = next((o for o in obligations if o.obligation_id == ob_id), None)
        if ob is None:
            raise ValueError(f"Obligation {ob_id} for {target_item!r} is not in the knowledge base")
        spec = None if is_document else next(t for t in leaf.triggers if t.trigger == target_item)
        if spec is not None and not spec.raised_for(customer):
            # 傳入的清單和客戶資料對不上（例如舊的清單）：不替一個不成立的標記編造解釋
            raise ValueError(f"Risk trigger {target_item!r} does not hold for {customer.customer_id}: "
                             f"its condition {spec.condition} is false")
        if spec is not None:
            # 風險標記：用寫出這個條件的那一條，而不是義務的錨點條文
            clause_id, clause_role = spec.clause_id, "寫出這個條件的條文"
            if clause_id not in ob.source_clause_ids:
                raise ValueError(f"Clause {clause_id} declared by {target_item!r} is not a source clause of {ob_id}")
        else:
            clause_id, clause_role = ob.source_clause_ids[0], "錨點條文"
        clause = next((c for c in clauses if c.clause_id == clause_id), None)
        if clause is None:
            raise ValueError(f"Clause {clause_id} of {ob_id} is not in the knowledge base")
        doc = next((d for d in documents if d.source_document_id == clause.source_document_id), None)
        if doc is None:
            raise ValueError(f"Source document {clause.source_document_id} of {clause_id} is not in the knowledge base")

        ob_node = ProvenanceNode(
            node_id=ob.obligation_id,
            node_type="obligation",
            label=f"合規義務：{ob.obligation_id}",
            properties={
                "action": ob.action,
                "object": ob.object,
                "jurisdiction": ob.jurisdiction,
                "required_evidence": ob.required_evidence
            }
        )
        clause_node = ProvenanceNode(
            node_id=clause.clause_id,
            node_type="clause",
            label=f"法規條款：{clause.section_ref}",
            properties={
                "raw_text": clause.raw_text,
                "normalized_text": clause.normalized_text,
                "section_ref": clause.section_ref,
                "citations": clause.citations
            }
        )
        doc_node = ProvenanceNode(
            node_id=doc.source_document_id,
            node_type="document",
            label=f"法規源文件：{doc.title}",
            properties={
                "title": doc.title,
                "issuer": doc.issuer,
                "jurisdiction": doc.jurisdiction,
                "version": doc.version,
                "local_path": doc.local_path
            }
        )

        # 繁體中文論述：全部由路徑、葉節點、義務、條文與規則理由組成
        if is_document:
            item_sentence = f"此分支要求文件『{target_item}』，葉節點宣告它依據義務 {ob.obligation_id}"
        else:
            how = checked_by(spec, steps)
            if how == "decision_path":
                assertion = f"斷言的客戶屬性 {'、'.join(spec.attributes)} 已在決策路徑上檢驗，對本客戶成立"
            elif how == "own_condition":
                observed = "、".join(f"{a} = {_format_value(read_attribute(customer, a))}" for a in spec.attributes)
                assertion = f"決策路徑沒有讀 {'、'.join(spec.attributes)}，由標記自己的條件 {spec.condition} 檢查（{observed}），成立才列出"
            else:
                assertion = "它不對客戶屬性下斷言，只陳述分支的結果"
            item_sentence = (f"此分支標記風險『{target_item}』（{assertion}），"
                             f"葉節點宣告它依據義務 {ob.obligation_id}")
        reasons = getattr(ob, "explanations", {}).get(clause_id, [])
        messages = [r.message if hasattr(r, "message") else r.get("message", "") for r in reasons]
        reason_sentence = ("規則理由：" + " ".join(messages)) if messages else f"此義務在{clause_role}上沒有記錄規則理由。"
        desc = (
            f"決策路徑：{_path_sentence(steps, customer)} → 分支「{leaf.label}」（{leaf.leaf_id}）。"
            f"{item_sentence}（{ob.action} {ob.object}），{clause_role}為 {doc.title} 第 {clause.section_ref} 條。"
            f"{reason_sentence}"
        )

        facts = _fact_nodes(steps, customer)
        if spec is not None and checked_by(spec, steps) == "own_condition":
            on_path = {n.node_id for n in facts}
            facts += [n for n in _condition_fact_nodes(spec, customer) if n.node_id not in on_path]
        return ExplanationPath(
            target_item=target_item,
            path_nodes=[*facts, ob_node, clause_node, doc_node],
            description=desc
        )

    def generate_audit_report(self, paths: List[ExplanationPath]) -> str:
        """
        將合規解釋路徑格式化為精美的人類可讀 Markdown 審計軌跡報告。
        """
        report_lines = [
            "# CDD 合規決策審計軌跡報告 (CDD Compliance Decision Audit Trail Report)",
            "",
            "本報告針對客戶的盡職調查 (CDD/EDD) 決策檢核表要求進行了深度溯源與法理合規解釋，打通了「客戶特徵 ➔ 適用義務 ➔ 原始法條 ➔ 監管文件」的完整雙向溯源系譜。",
            "",
            "---",
            ""
        ]

        report_lines.append("## 📋 決策解釋路徑清單")
        report_lines.append("")

        for path in paths:
            report_lines.append(f"### 🔍 檢核項目：{path.target_item}")
            report_lines.append("")
            report_lines.append("**合規論述摘要：**")
            report_lines.append(path.description)
            report_lines.append("")
            
            # 有向流程標籤表示
            labels = [node.label for node in path.path_nodes]
            flow_str = " ➔ ".join(f"`{label}`" for label in labels)
            report_lines.append("**有向合規溯源鏈：**")
            report_lines.append(flow_str)
            report_lines.append("")

            # 條款級法律原文引述
            clause_node = None
            doc_node = None
            for node in path.path_nodes:
                if node.node_type == "clause":
                    clause_node = node
                elif node.node_type == "document":
                    doc_node = node

            if clause_node and doc_node:
                report_lines.append("**條款級法律原文引述：**")
                report_lines.append(f"> **發行機構與文件**：{doc_node.properties.get('issuer')} - {doc_node.properties.get('title')} (版本: {doc_node.properties.get('version')})  ")
                report_lines.append(f"> **法條條目**：{clause_node.properties.get('section_ref')}  ")
                report_lines.append("> **原始明文引述**：  ")
                
                raw_text = clause_node.properties.get("raw_text", "")
                text_lines = raw_text.split("\n")
                for line in text_lines:
                    report_lines.append(f"> {line}")
            
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")

        return "\n".join(report_lines)
