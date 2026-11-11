import json
import os
import pytest
from src.extraction import llm_client as llm_client_module
from src.extraction.llm_client import LLMClient
from src.extraction.llm_extractor import (
    LLM_CONFIDENCE_BASIS,
    LLMHierarchicalChunker,
    LLMObligation,
    LLMStructuredExtractor,
    LLMExtractorPipeline,
    ClausesExtractionResult,
    ObligationsExtractionResult
)
from src.contracts.models import SourceDocument, Clause, Obligation

def test_llm_client_fallback_mode(monkeypatch):
    """
    驗證當沒有 GEMINI_API_KEY 時，LLMClient 能自動降級至 Mock 模式，並回傳結構化 mock 數據。
    """
    # 強制清空 API Key 環境變數以模擬離線/CI 測試環境
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    client = LLMClient(api_key=None)
    assert client.is_mock is True, "LLMClient 應在無金鑰時自動Fallback至 Mock 模式"
    assert client.mock_responses == 0
    
    # 測試智能段落切片的 Mock 結構回傳
    result_clauses = client.generate_structured(
        prompt="Please parse MAS 626 PDF document",
        response_schema=ClausesExtractionResult
    )
    
    assert isinstance(result_clauses, ClausesExtractionResult)
    assert len(result_clauses.clauses) > 0
    for clause in result_clauses.clauses:
        assert isinstance(clause, Clause)
        assert clause.clause_id is not None
        assert clause.raw_text is not None

    # 測試合規義務抽取的 Mock 結構回傳
    result_obs = client.generate_structured(
        prompt="Please extract obligations for MAS 626",
        response_schema=ObligationsExtractionResult
    )
    
    assert isinstance(result_obs, ObligationsExtractionResult)
    # 每次 mock 回應都會被記錄，匯入流程據此拒絕把合成資料寫進知識庫
    assert client.mock_responses == 2
    assert len(result_obs.obligations) > 0
    for ob in result_obs.obligations:
        assert isinstance(ob, LLMObligation)
        assert ob.obligation_id is not None
        assert ob.action is not None
        assert ob.object is not None

def test_llm_extractor_pipeline_flow():
    """
    驗證二階段 LLM Ingestion Pipeline 完整呼叫流程。
    """
    pipeline = LLMExtractorPipeline(api_key="mock")
    assert pipeline.llm_client.is_mock is True
    
    doc_id = "mas_notice_626_2026"
    raw_text = "This is a raw text content of MAS Notice 626 containing CDD requirements."
    
    clauses, obligations = pipeline.run_ingestion(doc_id, raw_text)
    
    # 1. 斷言 Clauses 切片成果
    assert len(clauses) > 0, "智能切片不應為空"
    for clause in clauses:
        assert isinstance(clause, Clause)
        assert clause.source_document_id == doc_id
        assert clause.clause_id.startswith("mas")
        assert len(clause.citations) > 0
        
    # 2. 斷言 Obligations 抽取成果
    assert len(obligations) > 0, "義務抽取不應為空"
    for ob in obligations:
        assert isinstance(ob, Obligation)
        assert ob.review_status == "pending_human_review", "自動導入的義務預設狀態應為 pending_human_review"
        assert ob.jurisdiction == "Singapore"
        # 模型自評的信心值保留，但要註明未經校準
        assert ob.confidence is not None
        assert ob.confidence_basis == "Self-reported by the LLM during PDF import; not calibrated."
        assert ob.confidence_kind == "self_reported"
        assert ob.explanations == {}

        # 驗證 Clause-level Provenance
        assert len(ob.source_clause_ids) > 0, "合規義務必須有關聯的源 Clause ID"
        for ref_clause_id in ob.source_clause_ids:
            # 驗證義務引用的 Clause ID 是否存在於剛剛切分出的 Clause 列表之中
            matching_clauses = [c for c in clauses if c.clause_id == ref_clause_id]
            assert len(matching_clauses) > 0, f"義務關聯的源 Clause ID '{ref_clause_id}' 不存在於產出的 clauses 中"
            
    # 3. 驗證樹狀階層結構完整性
    parent_child_checked = False
    for c in clauses:
        if c.parent_clause_id is not None:
            # 驗證其 parent 是否存在於列表中
            parents = [parent for parent in clauses if parent.clause_id == c.parent_clause_id]
            assert len(parents) == 1, f"Clause '{c.clause_id}' 的 parent_clause_id '{c.parent_clause_id}' 不存在"
            parent_child_checked = True
            
    assert parent_child_checked is True, "Mock 測試數據應包含至少一組樹狀 parent-child 條款關係以驗證層級完整性"


# --- 模型回應的驗證：模型亂填程式負責的欄位時，不能讓整個 Section 的義務一起被丟掉 ---------------------------

_BASE = dict(source_clause_ids=["mas_c1"], jurisdiction="X", actor="bank", action="verify", object="customer")

# 模型自行填了規則理由、信心種類、出處說明與審查狀態，格式全都不合 Obligation；信心值 95 超出 0 到 1
_MALFORMED = {"obligations": [
    {**_BASE, "obligation_id": "ob_out_of_range", "confidence": 95, "confidence_kind": "self-reported",
     "confidence_basis": 123, "review_status": "done", "explanations": {"mas_c1": ["shall verify"]}},
    {**_BASE, "obligation_id": "ob_scored", "confidence": 0.97, "confidence_kind": "measured_on_heldout",
     "explanations": {"mas_c1": [{"rule": "x", "obligation_type": "verify_customer", "message": "made up",
                                  "spans": [{"clause_id": "mas_c1", "end": 4, "text": "Bank"}]}]}},
    {**_BASE, "obligation_id": "ob_unscored", "confidence_kind": "measured_on_heldout"},
]}


class _FakeNIMResponse:
    def __init__(self, content: str):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class _FakeHTTPClient:
    """代替 httpx.Client：記下送出的 payload，回傳固定的模型輸出。"""
    sent = []

    def __init__(self, content: str):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None):
        _FakeHTTPClient.sent.append(json)
        return _FakeNIMResponse(self.content)


@pytest.fixture
def nim_client(monkeypatch):
    """走真正的 NIM 解析路徑（model_validate_json），只把 HTTP 換掉；驗證失敗時不等重試。"""
    _FakeHTTPClient.sent = []
    monkeypatch.setattr(llm_client_module.httpx, "Client",
                        lambda timeout=None: _FakeHTTPClient(json.dumps(_MALFORMED)))
    monkeypatch.setattr(llm_client_module.time, "sleep", lambda seconds: None)
    client = LLMClient(api_key="offline-test-key")
    assert client.provider == "nvidia_nim"
    return client


def test_the_response_schema_holds_only_what_the_model_fills():
    schema = json.dumps(ObligationsExtractionResult.model_json_schema())
    for field_name in ("explanations", "RuleReason", "confidence_kind", "confidence_basis", "review_status"):
        assert field_name not in schema
    confidence = ObligationsExtractionResult.model_json_schema()["$defs"]["LLMObligation"]["properties"]["confidence"]
    assert {"minimum": 0, "maximum": 1, "type": "number"} in confidence["anyOf"]


@pytest.mark.parametrize("confidence,expected", [(95, None), (-0.1, None), ("high", None), (True, None),
                                                 (float("nan"), None), ("0.8", 0.8), (0, 0.0), (1, 1.0)])
def test_a_self_reported_confidence_outside_0_to_1_is_ignored(confidence, expected):
    raw = {"obligations": [{**_BASE, "obligation_id": "ob", "confidence": confidence}]}
    (ob,) = ObligationsExtractionResult.model_validate(raw).obligations
    assert ob.confidence == expected


def test_malformed_model_fields_do_not_drop_the_section(nim_client):
    """模型輸出以原始 JSON 經過 LLMClient 的 NIM 解析路徑：多餘欄位被忽略，三筆義務都留下，不降級成 mock。"""
    clause = Clause(clause_id="mas_c1", source_document_id="mas", section_ref="6.1", raw_text="Bank shall verify.",
                    normalized_text="bank shall verify.", citations=["mas_c1"])

    obligations = LLMStructuredExtractor(nim_client).extract_obligations([clause])

    assert nim_client.mock_responses == 0 and len(_FakeHTTPClient.sent) == 1
    prompt = _FakeHTTPClient.sent[0]["messages"][-1]["content"]
    assert "confidence_kind" not in prompt and "RuleReason" not in prompt and "explanations" not in prompt
    by_id = {ob.obligation_id: ob for ob in obligations}
    assert list(by_id) == ["ob_out_of_range", "ob_scored", "ob_unscored"]
    for ob in obligations:
        assert isinstance(ob, Obligation)
        assert ob.explanations == {} and ob.review_status == "pending_human_review"
        assert ob.jurisdiction == "Singapore"  # 依 clause ID 補填
    # 超出範圍的分數不採用，等同沒給：沒有信心值、種類與出處說明
    assert (by_id["ob_out_of_range"].confidence, by_id["ob_out_of_range"].confidence_kind,
            by_id["ob_out_of_range"].confidence_basis) == (None, None, None)
    # 模型有給分數才標為 self_reported（模型自稱的 measured_on_heldout 不採用），並註明未經校準
    assert (by_id["ob_scored"].confidence, by_id["ob_scored"].confidence_kind,
            by_id["ob_scored"].confidence_basis) == (0.97, "self_reported", LLM_CONFIDENCE_BASIS)
    assert (by_id["ob_unscored"].confidence, by_id["ob_unscored"].confidence_kind,
            by_id["ob_unscored"].confidence_basis) == (None, None, None)
