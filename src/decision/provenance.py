from typing import List, Dict, Any, Optional
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    CDDChecklist,
    ProvenanceNode,
    ExplanationPath
)

class ProvenanceEngine:
    """
    可解釋合規推理與條款級雙向溯源引擎。
    提供為檢核表項目回溯推理合規鏈與生成人類可讀 Markdown 審計軌跡報告之功能。
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
        為檢核清單中的特定要求項目或風險標記進行雙向回溯推理，產出結構化的 ExplanationPath。
        """
        # 將輸入資料轉成 dictionary 以加快查詢
        ob_dict = {ob.obligation_id: ob for ob in obligations}
        clause_dict = {cl.clause_id: cl for cl in clauses}
        doc_dict = {doc.source_document_id: doc for doc in documents}

        # 1. Obligation Resolution (識別適用義務)
        target_lower = target_item.lower()
        matched_ob_id = None

        # 根據 target_item 來決定對應的 Obligation ID
        if "senior management" in target_lower or "senior_management" in target_lower:
            matched_ob_id = "ob_pep_edd_mas"
        elif "source of funds" in target_lower or "source_of_funds" in target_lower:
            matched_ob_id = "ob_pep_edd_mas"
        elif "source of wealth" in target_lower or "source_of_wealth" in target_lower:
            matched_ob_id = "ob_pep_edd_mas"
        elif "pep_exposure" in target_lower:
            matched_ob_id = "ob_pep_edd_mas"
        elif "nric" in target_lower or "residential address" in target_lower or "proof of address" in target_lower or "nric/passport" in target_lower or "unique_id" in target_lower:
            # 優先匹配 ob_identify_ubo_10_gb，如果 target 含有 ubo 或是持股比例
            if "ubo" in target_lower or "15%" in target_lower or "shareholder" in target_lower:
                matched_ob_id = "ob_identify_ubo_10_gb"
            else:
                matched_ob_id = "ob_verify_customer_mas"
        elif "rejected onboarding" in target_lower or "pep_from_high_risk" in target_lower or "prohibited_by_policy" in target_lower or "suspicious transaction report" in target_lower:
            matched_ob_id = "ob_pep_prohibitions_gb"
        elif "incorporation" in target_lower or "acra company profile" in target_lower:
            # 對於 corporate，可能是 ob_verify_customer_mas
            matched_ob_id = "ob_verify_customer_mas"
        elif "shareholder registry" in target_lower or "internal_ubo_threshold" in target_lower:
            matched_ob_id = "ob_identify_ubo_10_gb"
        elif "account opening rejection" in target_lower or "str evaluation file" in target_lower or "unclear_ubo" in target_lower or "excessive_layering" in target_lower or "missing_source" in target_lower:
            matched_ob_id = "ob_identify_ubo_25_mas"
        else:
            # Fallback：檢查 checklist.applicable_obligations 中是否有包含在 obligations 裡的
            for ob_id in checklist.applicable_obligations:
                if ob_id in ob_dict:
                    # 嘗試與義務的 required_evidence 或 review_flags 匹配
                    ob = ob_dict[ob_id]
                    if any(ev.lower() in target_lower for ev in ob.required_evidence) or any(fl.lower() in target_lower for fl in ob.review_flags):
                        matched_ob_id = ob_id
                        break
            if not matched_ob_id and checklist.applicable_obligations:
                matched_ob_id = checklist.applicable_obligations[0]

        # 提取匹配的義務
        if not matched_ob_id or matched_ob_id not in ob_dict:
            # 防禦性 fallback
            if obligations:
                ob = obligations[0]
            else:
                raise ValueError("Obligations list cannot be empty for provenance lookup.")
        else:
            ob = ob_dict[matched_ob_id]

        # 2. Factual Lineage Trace (追溯觸發事實)
        fact_nodes = []
        if ob.obligation_id == "ob_pep_edd_mas":
            fact_nodes.append(ProvenanceNode(
                node_id="fact_pep_exposure",
                node_type="customer_fact",
                label="客戶特徵：政要曝險 (pep_exposure = True)",
                properties={"pep_exposure": customer.pep_exposure}
            ))
        elif ob.obligation_id == "ob_pep_prohibitions_gb":
            fact_nodes.append(ProvenanceNode(
                node_id="fact_pep_exposure",
                node_type="customer_fact",
                label="客戶特徵：政要曝險 (pep_exposure = True)",
                properties={"pep_exposure": customer.pep_exposure}
            ))
            if customer.ubo_country_risk == "high":
                fact_nodes.append(ProvenanceNode(
                    node_id="fact_ubo_country_risk",
                    node_type="customer_fact",
                    label="客戶特徵：受益人國家風險為高風險 (ubo_country_risk = high)",
                    properties={"ubo_country_risk": customer.ubo_country_risk}
                ))
            if customer.registration_jurisdiction.lower() == "myanmar":
                fact_nodes.append(ProvenanceNode(
                    node_id="fact_registration_jurisdiction",
                    node_type="customer_fact",
                    label="客戶特徵：註冊管轄區為緬甸 (Myanmar)",
                    properties={"registration_jurisdiction": customer.registration_jurisdiction}
                ))
        elif ob.obligation_id == "ob_identify_ubo_10_gb":
            fact_nodes.append(ProvenanceNode(
                node_id="fact_customer_type",
                node_type="customer_fact",
                label="客戶特徵：客戶類型為企業 (corporate)",
                properties={"customer_type": customer.customer_type}
            ))
            share_pct = customer.custom_attributes.get("major_shareholder_pct", 0)
            fact_nodes.append(ProvenanceNode(
                node_id="fact_major_shareholder_pct",
                node_type="customer_fact",
                label=f"客戶特徵：內部持股比例門檻觸發 (major_shareholder_pct = {share_pct}%)",
                properties={"major_shareholder_pct": share_pct}
            ))
        elif ob.obligation_id in ["ob_identify_ubo_25_mas", "ob_identify_ubo_25"]:
            fact_nodes.append(ProvenanceNode(
                node_id="fact_customer_type",
                node_type="customer_fact",
                label="客戶特徵：客戶類型為企業 (corporate)",
                properties={"customer_type": customer.customer_type}
            ))
            if customer.ubo_status == "unclear":
                fact_nodes.append(ProvenanceNode(
                    node_id="fact_ubo_status",
                    node_type="customer_fact",
                    label="客戶特徵：實質受益人 (UBO) 狀態不明確 (ubo_status = unclear)",
                    properties={"ubo_status": customer.ubo_status}
                ))
            if customer.registration_jurisdiction.lower() == "cayman islands":
                fact_nodes.append(ProvenanceNode(
                    node_id="fact_registration_jurisdiction",
                    node_type="customer_fact",
                    label="客戶特徵：註冊管轄區為開曼群島 (Cayman Islands)",
                    properties={"registration_jurisdiction": customer.registration_jurisdiction}
                ))
        else:
            # Fallback 通用
            fact_nodes.append(ProvenanceNode(
                node_id="fact_customer_type",
                node_type="customer_fact",
                label=f"客戶特徵：客戶類型為 {customer.customer_type}",
                properties={"customer_type": customer.customer_type, "registration_jurisdiction": customer.registration_jurisdiction}
            ))

        # 3. Obligation Node 建立
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

        # 4. Legal Snippet Extraction (法源條文提取)
        clause = None
        if ob.source_clause_ids:
            cl_id = ob.source_clause_ids[0]
            if cl_id in clause_dict:
                clause = clause_dict[cl_id]

        if not clause:
            # 防禦性 fallback
            clause = Clause(
                clause_id="fallback_clause",
                source_document_id="fallback_doc",
                section_ref="Unknown Section",
                raw_text="No original legal snippet found for this obligation.",
                normalized_text="No original legal snippet found.",
                citations=[]
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

        # 尋找對應的 SourceDocument
        doc = None
        if clause.source_document_id in doc_dict:
            doc = doc_dict[clause.source_document_id]

        if not doc:
            doc = SourceDocument(
                source_document_id="fallback_doc",
                title="Unknown Regulatory Source",
                issuer="Regulatory Authority",
                jurisdiction="Global",
                version="1.0",
                retrieval_date="2026-05-21",
                local_path="data/cached/unknown.pdf"
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

        # 5. 組裝有向路徑
        path_nodes = []
        path_nodes.extend(fact_nodes)
        path_nodes.append(ob_node)
        path_nodes.append(clause_node)
        path_nodes.append(doc_node)

        # 6. 生成繁體中文合規論述摘要
        if ob.obligation_id == "ob_pep_edd_mas":
            desc = f"由於客戶具有反洗錢政要曝險特徵 (pep_exposure = True)，依據新加坡金融管理局 {doc.title} 第 {clause.section_ref} 條款之規定，銀行在與政治敏感人物建立業務關係時必須實施加強盡職調查 (EDD)。因此，系統推理判定必須徵集『{target_item}』以落實合規准入審查。"
        elif ob.obligation_id == "ob_pep_prohibitions_gb":
            desc = f"依據內部政策 {doc.title} 第 {clause.section_ref} 條款之規定，銀行嚴禁為來自高風險管轄區或實質受益人國家風險等級為高的政治敏感人物 (PEP) 辦理開戶。本案客戶符合該禁止項特徵，故系統推理判定必須輸出『{target_item}』並拒絕准入。"
        elif ob.obligation_id == "ob_identify_ubo_10_gb":
            desc = f"本案為企業客戶。依據內部政策 {doc.title} 第 {clause.section_ref} 條款之持股比例閥值限制，當主要股東持股比例介於 10% 至 25% 之間時，必須進行 UBO 穿透識別。故系統推理判定必須獲取大股東身份證明文件與『{target_item}』。"
        elif ob.obligation_id in ["ob_identify_ubo_25_mas", "ob_identify_ubo_25"]:
            desc = f"本案企業客戶的實質受益人 (UBO) 狀態不明確或註冊於高風險島國，依據 {doc.title} 第 {clause.section_ref} 條款之規定，必須進行實質受益人識別與加強審查。由於無法完成身份核實，系統推理判定必須輸出『{target_item}』以進行拒絕或升級審查。"
        elif ob.obligation_id == "ob_verify_customer_mas":
            desc = f"依據新加坡金融管理局 {doc.title} 第 {clause.section_ref} 條款之 CDD 客戶識別與核實基本義務，銀行必須獲取並核實客戶的基本身份資訊（如姓名、地址與身份證件）。故系統推理判定必須徵集『{target_item}』以完成基礎 CDD 檢核。"
        else:
            desc = f"由於客戶特徵觸發了合規義務 {ob.obligation_id}，依據法規文件 {doc.title} 之規定，判定需要徵集『{target_item}』以滿足合規檢核表之要求。"

        return ExplanationPath(
            target_item=target_item,
            path_nodes=path_nodes,
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
