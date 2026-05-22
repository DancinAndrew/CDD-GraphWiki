import json
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture(scope="module")
def client():
    """
    建立一個 TestClient 測試夾具，使用 with 語法確保啟動與清理事件（如 on_event('startup')）被執行。
    """
    with TestClient(app) as c:
        yield c


def test_list_customers(client):
    """
    驗證獲取所有客戶畫像情境 API。
    """
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    # 驗證強型別結構
    assert "customer_id" in data[0]
    assert "customer_type" in data[0]


def test_get_customer_checklist(client):
    """
    驗證獲取特定客戶的 CDD Checklist API。
    """
    # PEP 客戶
    response = client.get("/api/v1/customers/cust_individual_pep/checklist")
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_individual_pep"
    assert data["decision"] == "enhanced_due_diligence"
    assert data["human_review_required"] is True  # 機器推理結果為 True，尚未被人工審核覆寫


def test_list_cases(client):
    """
    驗證人工審批案件列表 API。
    """
    response = client.get("/api/v1/cases")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # 普通政要 PEP 應該已自動路由進入案件列表中
    pep_cases = [c for c in data if c["customer_id"] == "cust_individual_pep"]
    assert len(pep_cases) == 1
    assert pep_cases[0]["approval_status"] == "pending_review"


def test_review_case_workflow(client):
    """
    驗證完整的人機協同審核覆寫與日誌級聯寫入工作流。
    """
    case_id = "rev_individual_pep"
    
    # 1. 提交審核覆寫 (驗證 Pydantic 強型別白名單校驗)
    review_data = {
        "approval_status": "approved",
        "reviewer_decision": "enhanced_due_diligence",
        "notes": "合規官 Alice 審核通過：該 PEP 實質受益人背景清楚，但因敏感身份最終核准 EDD 決策邊界。",
        "reviewer_id": "Compliance_Officer_Alice"
    }
    
    response = client.post(f"/api/v1/cases/{case_id}/review", json=review_data)
    assert response.status_code == 200
    case_data = response.json()
    assert case_data["case_id"] == case_id
    assert case_data["approval_status"] == "approved"
    assert case_data["reviewed_by"] == "Compliance_Officer_Alice"

    # 2. 驗證對應的 Checklist 熱更新：人工介入標記 human_review_required 應該變為 False
    response = client.get("/api/v1/customers/cust_individual_pep/checklist")
    assert response.status_code == 200
    checklist_data = response.json()
    assert checklist_data["human_review_required"] is False

    # 3. 驗證防篡改日誌中是否已織入 case_reviewed 類型的事件
    response = client.get("/api/v1/audit/logs")
    assert response.status_code == 200
    logs = response.json()
    review_events = [l for l in logs if l["event_type"] == "case_reviewed"]
    assert len(review_events) >= 1
    assert review_events[0]["operator"] == "Compliance_Officer_Alice"

    # 4. 驗證日誌鏈的完整性自我校驗依然保持完整無虞
    response = client.get("/api/v1/audit/verify")
    assert response.status_code == 200
    verify_data = response.json()
    assert verify_data["is_intact"] is True
    assert verify_data["tampered_index"] == -1


def test_review_case_validation_error(client):
    """
    驗證防禦性校驗：輸入非法數據時 API 應正確回傳 422 錯誤，確保安全邊界。
    """
    case_id = "rev_individual_pep"
    
    # 筆記過短 (小於 5 個字元) 或缺欄位
    bad_data = {
        "approval_status": "approved",
        "reviewer_decision": "enhanced_due_diligence",
        "notes": "短",  # 不合規
        "reviewer_id": ""
    }
    
    response = client.post(f"/api/v1/cases/{case_id}/review", json=bad_data)
    assert response.status_code == 422
