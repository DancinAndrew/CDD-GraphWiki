import os
import yaml
import pytest
from pathlib import Path
from src.contracts.models import SourceDocument, Clause
from src.ingestion.parser import SemanticHierarchicalSegmenter, run_pipeline

@pytest.fixture(scope="module")
def parsed_data():
    """
    執行 Ingestion Pipeline 並載入生成的文件進行測試。
    """
    src_dir = "data/sources"
    out_dir = "data/processed"
    
    # 確保輸出目錄與檔案在測試前被跑過
    run_pipeline(src_dir, out_dir)
    
    # 載入產出的 YAML 檔案
    with open(os.path.join(out_dir, "source_documents.yaml"), "r", encoding="utf-8") as f:
        docs = yaml.safe_load(f)
    with open(os.path.join(out_dir, "clauses.yaml"), "r", encoding="utf-8") as f:
        clauses = yaml.safe_load(f)
        
    return docs, clauses


def test_pydantic_contract_validation(parsed_data):
    """
    驗證解析出的 SourceDocument 與 Clause 100% 符合 Pydantic 資料合約。
    """
    docs, clauses = parsed_data
    
    assert len(docs) > 0, "Source documents should not be empty"
    assert len(clauses) > 0, "Clauses should not be empty"
    
    # 逐一驗證 Pydantic 合約
    for doc_dict in docs:
        try:
            SourceDocument.model_validate(doc_dict)
        except Exception as e:
            pytest.fail(f"SourceDocument validation failed for {doc_dict.get('source_document_id')}: {e}")
            
    for clause_dict in clauses:
        try:
            Clause.model_validate(clause_dict)
        except Exception as e:
            pytest.fail(f"Clause validation failed for {clause_dict.get('clause_id')}: {e}")


def test_hierarchical_referential_integrity(parsed_data):
    """
    驗證法規樹層級參照完整性：
    每個 Clause 的 parent_clause_id 若非 None，則必須指向一個確實存在的 Clause。
    """
    _, clauses = parsed_data
    
    clause_ids = {c["clause_id"] for c in clauses}
    
    for c in clauses:
        parent_id = c.get("parent_clause_id")
        if parent_id is not None:
            assert parent_id in clause_ids, (
                f"Referential Integrity Violation: Clause '{c['clause_id']}' "
                f"has a dangling parent_clause_id '{parent_id}' which does not exist in parsed data."
            )


def test_id_stability_and_idempotency():
    """
    驗證穩定 ID 生成與 Parser 冪等性。
    重複解析同一個 Markdown 文件，ID 必須完全恆定。
    """
    doc_id = "test_stability_doc"
    markdown_content = """# Test Title

## Section 1: Introduction
Welcome to testing.

### 1.1 Requirements
(a) You must pass tests.
(b) Rerun should not shift IDs.
  (i) Stated rule.
"""
    
    # 第一次運行解析
    segmenter = SemanticHierarchicalSegmenter(source_document_id=doc_id)
    _, clauses_run1 = segmenter.parse(markdown_content)
    
    # 第二次運行解析
    _, clauses_run2 = segmenter.parse(markdown_content)
    
    assert len(clauses_run1) == len(clauses_run2)
    
    # 斷言 ID 完全一致
    ids_run1 = [c.clause_id for c in clauses_run1]
    ids_run2 = [c.clause_id for c in clauses_run2]
    assert ids_run1 == ids_run2, "Parser is not idempotent! IDs shifted between runs."
    
    # 驗證 ID 的層級路徑正確性
    expected_ids = [
        "test_stability_doc_s_1_introduction",
        "test_stability_doc_s_1_introduction_1_1_requirements",
        "test_stability_doc_s_1_introduction_1_1_requirements_a",
        "test_stability_doc_s_1_introduction_1_1_requirements_b",
        "test_stability_doc_s_1_introduction_1_1_requirements_b_i"
    ]
    
    for expected in expected_ids:
        assert expected in ids_run1, f"Expected stable ID '{expected}' was not generated."


def test_id_stability_under_non_structural_changes():
    """
    驗證在進行無結構變更（增減空白、修改普通內文）時，ID 依然保持穩定。
    """
    doc_id = "test_stability_doc"
    
    markdown_run1 = """# Test Title

## Section 1: Introduction
Some introductory text.

### 1.1 Requirements
(a) You must pass tests.
"""
    
    # 稍微調整內文與空白，但不改變標題與列表結構
    markdown_run2 = """# Test Title   

## Section 1: Introduction
Different introductory text with some   extra spaces.

### 1.1 Requirements
(a) You must pass tests successfully!
"""
    
    segmenter = SemanticHierarchicalSegmenter(source_document_id=doc_id)
    _, clauses_run1 = segmenter.parse(markdown_run1)
    _, clauses_run2 = segmenter.parse(markdown_run2)
    
    assert len(clauses_run1) == len(clauses_run2)
    
    ids_run1 = [c.clause_id for c in clauses_run1]
    ids_run2 = [c.clause_id for c in clauses_run2]
    
    assert ids_run1 == ids_run2, "IDs shifted under non-structural changes! Stable ID mechanism failed."
