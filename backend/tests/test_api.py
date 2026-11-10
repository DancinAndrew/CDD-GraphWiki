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

    # 引用是解析出的條文 ID，citation_details 把每一條解析成原文與出處
    assert data["citations"] == [
        "mas_notice_626_6_cdd_6_3",
        "mas_notice_626_6_cdd_6_5",
        "mas_notice_626_8_enhanced_cdd_8_3",
        "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons_a",
    ]
    details = {d["clause_id"]: d for d in data["citation_details"]}
    assert set(details) == set(data["citations"])
    assert details["mas_notice_626_8_enhanced_cdd_8_3"]["source_document_id"] == "mas_notice_626"
    assert "enhanced CDD measures" in details["mas_notice_626_8_enhanced_cdd_8_3"]["raw_text"]


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
    # 人工覆寫只記在稽核日誌，引用仍全是可解析的條文 ID
    assert len(checklist_data["citation_details"]) == len(checklist_data["citations"]) == 4

    # 3. 驗證防篡改日誌中是否已織入 case_reviewed 類型的事件
    response = client.get("/api/v1/audit/logs")
    assert response.status_code == 200
    logs = response.json()
    review_events = [l for l in logs if l["event_type"] == "case_reviewed" and l["payload"].get("case_id") == case_id]
    assert len(review_events) == 1
    assert review_events[-1]["operator"] == "Compliance_Officer_Alice"

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


def test_graph_connects_conflicts_and_citations_to_clauses(client):
    """圖譜上每個衝突節點都連到兩條條文；清單節點也連到它引用的條文。"""
    graph = client.get("/api/v1/graph").json()
    node_types = {n["node_id"]: n["node_type"] for n in graph["nodes"]}
    conflicts = [nid for nid, t in node_types.items() if t == "Conflict"]
    assert len(conflicts) == 3
    for conflict_id in conflicts:
        targets = [l["target"] for l in graph["links"] if l["source"] == conflict_id and l["edge_type"] == "references_clause"]
        assert len(targets) == 2 and all(node_types[t] == "Clause" for t in targets)
    checklist_refs = [l for l in graph["links"]
                      if node_types.get(l["source"]) == "CDDChecklist" and l["edge_type"] == "references_clause"]
    assert checklist_refs


def test_pdf_ingestion_refuses_mock_llm_output(tmp_path):
    """
    沒有 LLM 金鑰時，匯入流程會用到 mock 合成回應；這種結果必須被拒絕，不能寫進知識庫。
    """
    import os
    import shutil
    from src.api import main
    from src.api.dependencies import PROCESSED_DIR

    before = {name: open(os.path.join(PROCESSED_DIR, name), "rb").read()
              for name in ("clauses.yaml", "obligations.yaml", "source_documents.yaml")}
    pdf = tmp_path / "mas.pdf"
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    shutil.copy(os.path.join(repo_root, "data", "sources", "official", "mas_notice_626.pdf"), pdf)

    task_id = "test-mock-ingestion"
    main._ingestion_tasks[task_id] = {"task_id": task_id, "status": "pending", "progress": 0, "logs": [], "error": None}
    main._run_pdf_ingestion_worker(
        task_id=task_id, temp_file_path=str(pdf), doc_id="mas_notice_626_upload", title="MAS Notice 626",
        issuer="MAS", jurisdiction="Singapore", version="2025", effective_date=None, source_url=None, api_key="mock")

    task = main._ingestion_tasks[task_id]
    assert task["status"] == "failed"
    assert "mock" in task["error"]
    after = {name: open(os.path.join(PROCESSED_DIR, name), "rb").read() for name in before}
    assert after == before
    # 被拒絕的上傳檔也會刪掉
    assert not pdf.exists()


class _FakeLLMPipeline:
    """代替真實 LLM：回傳固定的條文與義務，且不使用 mock 回應（mock_responses = 0）。"""
    def __init__(self, clauses, obligations):
        import types
        self.llm_client = types.SimpleNamespace(mock_responses=0)
        self.chunker = types.SimpleNamespace(chunk_document=lambda doc_id, text: clauses)
        self.extractor = types.SimpleNamespace(extract_obligations=lambda cls: obligations)


@pytest.fixture
def isolated_processed(tmp_path, monkeypatch):
    """把 API 的 processed 目錄換成一份暫存複本，匯入測試不影響其他測試。"""
    import shutil
    from src.api import main, dependencies
    target = tmp_path / "processed"
    shutil.copytree(dependencies.PROCESSED_DIR, target)
    monkeypatch.setattr(dependencies, "PROCESSED_DIR", str(target))
    monkeypatch.setattr(main, "PROCESSED_DIR", str(target))
    dependencies.clear_knowledge_base_cache()
    yield target
    dependencies.clear_knowledge_base_cache()


def _run_fake_ingestion(monkeypatch, tmp_path, clauses, obligations):
    from src.api import main
    monkeypatch.setattr(main, "LLMExtractorPipeline", lambda api_key=None: _FakeLLMPipeline(clauses, obligations))
    monkeypatch.setattr(main.PDFTextParser, "extract_text", lambda self, path: "stub text")
    pdf = tmp_path / "upload.pdf"
    pdf.write_bytes(b"%PDF-1.4 stub")
    task_id = f"fake-{len(main._ingestion_tasks)}"
    main._ingestion_tasks[task_id] = {"task_id": task_id, "status": "pending", "progress": 0, "logs": [], "error": None}
    main._run_pdf_ingestion_worker(
        task_id=task_id, temp_file_path=str(pdf), doc_id="other_bank_policy", title="Other Bank Policy",
        issuer="Other Bank", jurisdiction="Internal", version="1", effective_date=None, source_url=None, api_key="x")
    return main._ingestion_tasks[task_id]


def _fake_clause_and_obligations():
    from src.contracts.models import Clause, Obligation
    clause = Clause(clause_id="other_bank_policy_s1", source_document_id="other_bank_policy", section_ref="S1",
                    raw_text="The bank shall identify UBOs holding 15% or more.",
                    normalized_text="the bank shall identify ubos holding 15% or more.", citations=["other_bank_policy_s1"])
    good = Obligation(obligation_id="ob_other_ubo", source_clause_ids=["other_bank_policy_s1"], jurisdiction="Internal",
                      actor="bank", action="identify_and_verify", object="beneficial_owner", confidence=0.9)
    dangling = Obligation(obligation_id="ob_other_ghost", source_clause_ids=["clause_the_llm_made_up"],
                          jurisdiction="Internal", actor="bank", action="prohibit", object="customer", confidence=0.9)
    return clause, good, dangling


def test_ingestion_drops_obligations_citing_unknown_clauses(client, isolated_processed, monkeypatch, tmp_path):
    """LLM 引用不存在的條文時，那條義務被略過；知識庫維持一致，API 仍能正常載入。"""
    import yaml
    from src.api.dependencies import load_knowledge_base, clear_knowledge_base_cache
    clause, good, dangling = _fake_clause_and_obligations()
    task = _run_fake_ingestion(monkeypatch, tmp_path, [clause], [good, dangling])
    assert task["status"] == "completed", task.get("error")

    obligation_ids = {o["obligation_id"] for o in yaml.safe_load((isolated_processed / "obligations.yaml").read_text(encoding="utf-8"))}
    assert "ob_other_ubo" in obligation_ids and "ob_other_ghost" not in obligation_ids
    clear_knowledge_base_cache()
    kb = load_knowledge_base()  # 參照完整性檢查通過
    assert any(c.clause_id == "other_bank_policy_s1" for c in kb["clauses"])


def test_first_ingestion_into_empty_processed_dir_writes_a_complete_kb(client, isolated_processed, monkeypatch, tmp_path):
    """processed 目錄還是空的（知識庫從 gold 載入）時匯入，四個檔案都會寫出，不會留下半套。"""
    import shutil
    from src.api.dependencies import clear_knowledge_base_cache, load_knowledge_base
    shutil.rmtree(isolated_processed)
    isolated_processed.mkdir()
    clear_knowledge_base_cache()

    clause, good, _ = _fake_clause_and_obligations()
    task = _run_fake_ingestion(monkeypatch, tmp_path, [clause], [good])
    assert task["status"] == "completed", task.get("error")
    for name in ("source_documents.yaml", "clauses.yaml", "obligations.yaml", "conflicts.yaml"):
        assert (isolated_processed / name).exists(), name
    clear_knowledge_base_cache()
    assert len(load_knowledge_base()["conflicts"]) == 3


def test_data_dir_honours_env_and_finds_repo_data(monkeypatch, tmp_path):
    """data 目錄的位置：有 CDD_DATA_DIR 就用它；否則往上找到含 data/gold 的目錄（本機或 Docker 的 /app）。"""
    import os
    from src.paths import find_data_dir
    monkeypatch.setenv("CDD_DATA_DIR", str(tmp_path))
    assert find_data_dir() == str(tmp_path)
    monkeypatch.delenv("CDD_DATA_DIR")
    assert os.path.isdir(os.path.join(find_data_dir(), "gold", "concepts"))
