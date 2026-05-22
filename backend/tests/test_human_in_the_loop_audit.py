import os
import json
import pytest
from datetime import datetime
from pydantic import ValidationError
from src.contracts.models import CustomerContext, CDDChecklist, ReviewCase, AuditLogEntry
from src.audit.logger import AuditLogger
from src.audit.manager import ReviewCaseManager
from src.audit.generator import AuditReportGenerator

def test_audit_logger_hash_chain_and_integrity(tmp_path):
    """
    驗證 AuditLogger 的鏈式哈希鏈與完整性自我校驗。
    包含：級聯雜湊計算、持久化加載，以及手動篡改 Payload 時觸發完整性驗證失敗。
    """
    log_file = os.path.join(tmp_path, "audit.json")
    logger = AuditLogger(filepath=log_file)

    # 1. 寫入多條日誌
    entry1 = logger.log_event(
        event_type="reasoning_triggered",
        operator="system_engine",
        customer_id="cust_01",
        payload={"action": "calculate_risk", "score": 85}
    )
    
    entry2 = logger.log_event(
        event_type="case_created",
        operator="system_engine",
        customer_id="cust_01",
        payload={"reason": "pep_exposure"}
    )

    # 2. 驗證雜湊鏈的基本屬性
    assert len(logger.entries) == 2
    assert entry1.previous_hash == "0" * 64
    assert entry2.previous_hash == entry1.current_hash
    assert entry1.current_hash != ""
    assert entry2.current_hash != ""
    
    # 3. 驗證完整性自檢
    assert logger.verify_integrity() is True

    # 4. 驗證檔案持久化與加載
    logger2 = AuditLogger(filepath=log_file)
    assert len(logger2.entries) == 2
    assert logger2.verify_integrity() is True
    assert logger2.entries[1].previous_hash == logger2.entries[0].current_hash

    # 5. 模擬惡意篡改資料載荷 (Payload)
    logger2.entries[0].payload["score"] = 99  # 手動修改 Payload
    assert logger2.verify_integrity() is False  # 驗證應該報警並返回 False


def test_review_case_manager_and_override_workflow():
    """
    驗證 ReviewCaseManager 案件生命週期管理與合規官決策覆寫機制。
    模擬合規官將機器決策覆寫為 EDD，並斷言 Checklist 同步更新與日誌鏈織入。
    """
    logger = AuditLogger()
    manager = ReviewCaseManager(logger=logger)

    # 1. 建立 mock 客戶 Checklist 與 Case
    customer_id = "cust_corp_standard"
    checklist_id = "chk_corp_standard"
    
    mock_checklist = CDDChecklist(
        checklist_id=checklist_id,
        customer_id=customer_id,
        decision="standard_cdd",
        required_documents=["Certificate of Incorporation"],
        risk_triggers=["minor_attribute"],
        applicable_obligations=["ob_verify_customer_mas"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 6.13"]
    )
    
    checklists = {checklist_id: mock_checklist}

    # 2. 創建人工審核案件
    case = manager.create_case(
        customer_id=customer_id,
        checklist_id=checklist_id,
        review_reason=["internal_ubo_threshold_triggered_10_percent"]
    )
    
    assert case.approval_status == "pending_review"
    assert case.customer_id == customer_id
    assert case.checklist_id == checklist_id
    
    # 檢查是否寫入 case_created 審計事件
    assert len(logger.entries) == 1
    assert logger.entries[0].event_type == "case_created"
    assert logger.entries[0].customer_id == customer_id

    # 3. 模擬合規官進行審批，並實施決策覆寫
    notes = "Reviewed corporate layers; major shareholder holds 15%, triggering EDD override."
    reviewer_id = "compliance_officer_alice"
    
    updated_case = manager.apply_review_decision(
        case_id=case.case_id,
        approval_status="approved",
        reviewer_decision="enhanced_due_diligence",
        notes=notes,
        reviewer_id=reviewer_id,
        checklists=checklists
    )

    # 4. 斷言案件狀態已更新
    assert updated_case.approval_status == "approved"
    assert updated_case.reviewer_decision == "enhanced_due_diligence"
    assert updated_case.reviewed_by == reviewer_id
    assert updated_case.reviewer_notes == notes

    # 5. 斷言關聯的 CDDChecklist 是否已被完美覆寫且解鎖
    assert mock_checklist.decision == "enhanced_due_diligence"
    assert mock_checklist.human_review_required is False
    assert any("compliance_officer_alice" in cit for cit in mock_checklist.citations)

    # 6. 檢查審計日誌是否正確寫入
    assert len(logger.entries) == 2
    assert logger.entries[1].event_type == "case_reviewed"
    assert logger.entries[1].payload["new_decision"] == "enhanced_due_diligence"
    assert logger.entries[1].payload["previous_decision"] == "standard_cdd"
    assert logger.verify_integrity() is True


def test_audit_report_generator_and_pii_redaction():
    """
    驗證 AuditReportGenerator 的報告包生成、Citation 溯源展示與 PII 客戶個資脫敏功能。
    """
    logger = AuditLogger()
    manager = ReviewCaseManager(logger=logger)
    generator = AuditReportGenerator(logger=logger)

    customer_id = "cust_individual_pep"
    checklist_id = "chk_individual_pep"

    customer = CustomerContext(
        customer_id=customer_id,
        customer_type="individual",
        registration_jurisdiction="Singapore",
        ownership_layers=1,
        ubo_status="identified",
        ubo_country_risk="high",
        pep_exposure=True,
        source_of_funds_available=True,
        source_of_wealth_available=True,
        custom_attributes={}
    )

    checklist = CDDChecklist(
        checklist_id=checklist_id,
        customer_id=customer_id,
        decision="enhanced_due_diligence",
        required_documents=["National Identity Card", "Senior Management Approval Form"],
        risk_triggers=["pep_exposure_detected"],
        applicable_obligations=["ob_pep_edd_mas"],
        unresolved_conflicts=[],
        human_review_required=True,
        citations=["MAS Notice 626 Paragraph 7.2"]
    )

    # 1. 記錄推理事件與案件事件
    logger.log_reasoning(
        operator="system_engine",
        customer_id=customer_id,
        checklist_id=checklist_id,
        decision="enhanced_due_diligence",
        ingestion_hash="hash_ingest_abc123",
        graph_version="g_v1.0.4",
        rule_version="r_v2.0.1"
    )

    case = manager.create_case(
        customer_id=customer_id,
        checklist_id=checklist_id,
        review_reason=["pep_exposure_detected"]
    )

    # 模擬審核
    manager.apply_review_decision(
        case_id=case.case_id,
        approval_status="approved",
        reviewer_decision="enhanced_due_diligence",
        notes="Approved onboarding high risk PEP with senior mgmt signoff.",
        reviewer_id="compliance_officer_bob",
        checklists={checklist_id: checklist}
    )

    # 2. 一鍵生成報告包
    report_package = generator.generate_report_package(
        customer=customer,
        checklist=checklist,
        review_case=case
    )

    assert "markdown" in report_package
    assert "html" in report_package

    md_report = report_package["markdown"]
    html_report = report_package["html"]

    # 3. 斷言 PII 客戶個資遮罩脫敏效果
    # 原始的 cust_individual_pep 不應完整出現在報告中，應該為脫敏形式
    assert customer_id not in md_report
    assert customer_id not in html_report
    
    redacted_cust_id = generator.redact_id(customer_id)
    assert redacted_cust_id in md_report
    assert redacted_cust_id in html_report

    # 4. 驗證報告包含 Citation、Ingestion 哈希與防篡改簽名自檢
    assert "hash_ingest_abc123" in md_report or "hash_ingest_abc123" in html_report
    assert "g_v1.0.4" in md_report or "g_v1.0.4" in html_report
    assert "r_v2.0.1" in md_report or "r_v2.0.1" in html_report
    assert "MAS Notice 626 Paragraph 7.2" in md_report
    assert "compliance_officer_bob" in md_report
    assert "完整性驗證通過 🟢" in html_report or "完整性驗證狀態: 🟢 通過" in md_report


def test_contracts_validation_exceptions():
    """
    驗證 Pydantic 強型別合約的邊界約束與驗證異常。
    """
    # 1. 驗證異常的 ReviewCase 狀態
    with pytest.raises(ValidationError):
        ReviewCase(
            case_id="rev_cust_01",
            customer_id="cust_01",
            checklist_id="chk_01",
            review_reason=["some_reason"],
            approval_status="invalid_status_value",  # 狀態值不在 Literals 中
            timestamp=datetime.utcnow()
        )

    # 2. 驗證異常的 AuditLogEntry 事件類型
    with pytest.raises(ValidationError):
        AuditLogEntry(
            log_id="log_01",
            timestamp=datetime.utcnow(),
            event_type="invalid_event_type",  # 事件類型不在 Literals 中
            operator="user",
            customer_id="cust_01",
            payload={},
            previous_hash="0"*64,
            current_hash="0"*64
        )
