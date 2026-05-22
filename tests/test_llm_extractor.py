import os
import pytest
from src.extraction.llm_client import LLMClient
from src.extraction.llm_extractor import (
    LLMHierarchicalChunker,
    LLMStructuredExtractor,
    LLMExtractorPipeline,
    ClausesExtractionResult,
    ObligationsExtractionResult
)
from src.contracts.models import SourceDocument, Clause, Obligation

def test_llm_client_fallback_mode():
    """
    驗證當沒有 GEMINI_API_KEY 時，LLMClient 能自動降級至 Mock 模式，並回傳結構化 mock 數據。
    """
    # 強制清空 API Key 環境變數以模擬離線/CI 測試環境
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
        
    client = LLMClient(api_key=None)
    assert client.is_mock is True, "LLMClient 應在無金鑰時自動Fallback至 Mock 模式"
    
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
    assert len(result_obs.obligations) > 0
    for ob in result_obs.obligations:
        assert isinstance(ob, Obligation)
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
