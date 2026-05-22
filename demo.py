import os
import yaml
from datetime import datetime
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    Conflict,
    CDDChecklist
)
from src.decision.engine import CDDChecklistEngine
from src.audit.logger import AuditLogger
from src.audit.manager import ReviewCaseManager
from src.audit.generator import AuditReportGenerator
from src.graph.builder import GraphBuilder
from src.graph.visualization import GraphExporter

def main():
    print("=" * 80)
    print("🛡️  CDD-GraphWiki - 合規推理與鏈式防篡改審計系統啟動  🛡️")
    print("=" * 80)

    # 1. 定義數據路徑並加載金標數據集
    gold_dir = "data/gold"
    processed_dir = "data/processed"
    
    print("\n[步驟 1] 正在載入 CDD-GraphWiki 金標法規知識與客戶情境...")
    
    with open(os.path.join(gold_dir, "customer_contexts.yaml"), "r", encoding="utf-8") as f:
        raw_customers = yaml.safe_load(f)
    with open(os.path.join(gold_dir, "obligations.yaml"), "r", encoding="utf-8") as f:
        raw_obligations = yaml.safe_load(f)
    with open(os.path.join(gold_dir, "clauses.yaml"), "r", encoding="utf-8") as f:
        raw_clauses = yaml.safe_load(f)
    with open(os.path.join(gold_dir, "source_documents.yaml"), "r", encoding="utf-8") as f:
        raw_documents = yaml.safe_load(f)
        
    raw_conflicts = []
    conflict_file = os.path.join(processed_dir, "conflicts.yaml") if os.path.exists(
        os.path.join(processed_dir, "conflicts.yaml")
    ) else os.path.join(gold_dir, "conflicts.yaml")
    if os.path.exists(conflict_file):
        with open(conflict_file, "r", encoding="utf-8") as f:
            raw_conflicts = yaml.safe_load(f)

    # 轉化為強型別模型
    customers = [CustomerContext(**c) for c in raw_customers]
    obligations = [Obligation(**o) for o in raw_obligations]
    clauses = [Clause(**cl) for cl in raw_clauses]
    documents = [SourceDocument(**doc) for doc in raw_documents]
    conflicts = [Conflict(**conf) for conf in raw_conflicts]

    print(f"  ✓ 成功加載 {len(documents)} 份原始法規文件")
    print(f"  ✓ 成功加載 {len(clauses)} 條細粒度法規條款")
    print(f"  ✓ 成功加載 {len(obligations)} 條合規義務規則")
    print(f"  ✓ 成功加載 {len(customers)} 名典型客戶畫像情境")

    # 2. 初始化決策引擎與審計引擎
    print("\n[步驟 2] 初始化推理決策引擎與防篡改審計日誌軌跡...")
    engine = CDDChecklistEngine()
    
    # 建立日誌文件路徑
    audit_file = "data/processed/audit_log.json"
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)
    if os.path.exists(audit_file):
        os.remove(audit_file)
        
    logger = AuditLogger(filepath=audit_file)
    manager = ReviewCaseManager(logger=logger)

    # 3. 觸發自動決策推理並記錄生命週期元數據
    print("\n[步驟 3] 執行合規 Checklist 自動決策推理，並自動記錄生命週期...")
    checklists = {}
    
    # 挑選一個典型的普通政要 (PEP) 客戶 "cust_individual_pep" 進行示範
    demo_customer = None
    for c in customers:
        if c.customer_id == "cust_individual_pep":
            demo_customer = c
            break
            
    if not demo_customer:
        demo_customer = customers[0]
        
    for cust in customers:
        checklist = engine.generate_checklist(cust, obligations, conflicts)
        checklists[checklist.checklist_id] = checklist
        
        # 記錄推理決策生命週期到防篡改日誌中
        logger.log_reasoning(
            operator="CDD_Reasoning_Engine",
            customer_id=cust.customer_id,
            checklist_id=checklist.checklist_id,
            decision=checklist.decision,
            ingestion_hash="hash_ingest_pep_mas626",
            graph_version="g_v1.0.0",
            rule_version="r_v2.1.0"
        )
        print(f"  ✓ 客戶 {cust.customer_id} ➔ 決策: {checklist.decision.upper()} (需人工介入: {checklist.human_review_required})")

    # 4. 人機協同人工審批與最終決策覆寫
    print("\n[步驟 4] 模擬人機協同：合規官審核案件並執行決策覆寫...")
    
    # 針對 demo_customer (PEP 人物，機器初審決策為 EDD，但 human_review_required=True)
    chk_demo = checklists[f"chk_{demo_customer.customer_id.replace('cust_', '')}"]
    
    # 創建審查案件
    case = manager.create_case(
        customer_id=demo_customer.customer_id,
        checklist_id=chk_demo.checklist_id,
        review_reason=["pep_exposure_detected", "high_risk_ubo_jurisdiction"]
    )
    print(f"  ✓ 人工審查案件建立成功: {case.case_id} (狀態: {case.approval_status})")
    
    # 模擬合規官審批並覆寫決策為最高難度 EDD
    reviewer_notes = "合規官已審核該 PEP 人物；股權嵌套結構清晰，但由於其關聯之 UBO 國家風險較高，人工最終核准其 Enhanced Due Diligence 決策邊界，並解除 Routing 狀態。"
    updated_case = manager.apply_review_decision(
        case_id=case.case_id,
        approval_status="approved",
        reviewer_decision="enhanced_due_diligence",
        notes=reviewer_notes,
        reviewer_id="Compliance_Officer_Alice",
        checklists=checklists
    )
    print(f"  ✓ 合規官 Alice 完成審核，決策覆寫為: {updated_case.reviewer_decision.upper()}")
    print(f"  ✓ 關聯 Checklist {chk_demo.checklist_id} 人工介入標記已重置為: {chk_demo.human_review_required}")

    # 5. 一鍵導出磨砂玻璃 HTML 審計報告
    print("\n[步驟 5] 正在生成 PII 客戶個資去敏感之 HTML 暗黑磨砂玻璃合規審計報告...")
    generator = AuditReportGenerator(logger=logger)
    report_pkg = generator.generate_report_package(
        customer=demo_customer,
        checklist=chk_demo,
        review_case=updated_case
    )
    
    report_output_path = "audit_report_demo.html"
    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(report_pkg["html"])
        
    print(f"  ✓ 審計報告導出成功! ➔ 儲存路徑: {os.path.abspath(report_output_path)}")

    # 6. 構建並導出 D3.js 互動式合規知識圖譜
    print("\n[步驟 6] 構建法規合規知識圖譜並導出 D3 互動式 HTML 網頁...")
    
    # 將推理產出的 Checklist 加入圖譜中展示決策鏈
    active_checklists = list(checklists.values())
    
    regulatory_graph = GraphBuilder.build_regulatory_graph(
        documents=documents,
        clauses=clauses,
        obligations=obligations,
        concepts=[],
        conflicts=conflicts,
        customers=customers,
        checklists=active_checklists
    )
    
    graph_output_path = "regulatory_graph_demo.html"
    GraphExporter.export_to_html(regulatory_graph, graph_output_path)
    print(f"  ✓ 交互式圖譜導出成功! ➔ 儲存路徑: {os.path.abspath(graph_output_path)}")

    print("\n" + "=" * 80)
    print("🎉  CDD-GraphWiki 一鍵演示啟動成功!  🎉")
    print("=" * 80)
    print(f"\n您可以直接在瀏覽器中雙擊打開以下兩個極具現代美學質感的 HTML 頁面進行體驗：")
    print(f"1. 🛡️  去敏感磨砂玻璃稽核審計報告: {os.path.abspath(report_output_path)}")
    print(f"2. 🕸️  互動式合規知識圖譜與決策鏈: {os.path.abspath(graph_output_path)}")
    print("\n完整防篡改審計鏈 JSON 日誌已同步持久化寫入: data/processed/audit_log.json")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
