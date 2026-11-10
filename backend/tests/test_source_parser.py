import os
import yaml
import pytest
from pathlib import Path
from src.contracts.models import SourceDocument, Clause
from src.ingestion.parser import SemanticHierarchicalSegmenter, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope="module")
def parsed_data(tmp_path_factory):
    """
    執行 Ingestion Pipeline 並載入生成的文件進行測試。
    """
    src_dir = os.path.join(REPO_ROOT, "data", "sources")
    out_dir = str(tmp_path_factory.mktemp("parsed"))

    # 解析到暫存目錄，不改寫 repo 裡的 data/processed
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


def test_parser_output_matches_reviewed_gold_clauses(parsed_data):
    """
    金標條文是 parser 輸出經人工檢查後凍結的版本；parser 或來源一改動，這個測試就會提醒同步更新。
    """
    _, clauses = parsed_data
    with open(REPO_ROOT / "data" / "gold" / "clauses.yaml", "r", encoding="utf-8") as f:
        gold = yaml.safe_load(f)
    assert clauses == gold


def _squash(text: str) -> str:
    """比對用：去掉所有空白並統一連字號，抵消 PDF 文字抽取的斷行與空格雜訊。"""
    import re
    return re.sub(r"\s+", "", text).replace("–", "-")


def test_mas_excerpt_is_verbatim_from_official_pdf():
    """
    MAS 摘錄的每一行內文（標題與說明除外）都必須能在 repo 內的官方 PDF 文字中逐字找到。
    """
    from pypdf import PdfReader
    pdf_path = REPO_ROOT / "data" / "sources" / "official" / "mas_notice_626.pdf"
    official = _squash(" ".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages))

    lines = (REPO_ROOT / "data" / "sources" / "mas_notice_626.md").read_text(encoding="utf-8").splitlines()
    body = [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith(("#", ">"))]
    assert len(body) >= 20
    missing = [ln for ln in body if _squash(ln) not in official]
    assert missing == [], f"Lines not found verbatim in the official MAS Notice 626 PDF: {missing}"


def test_sources_state_the_thresholds_used_by_conflicts(parsed_data):
    """衝突偵測用到的三個門檻，必須真的出現在解析出的條文裡。"""
    _, clauses = parsed_data
    text = {c["clause_id"]: c["raw_text"] for c in clauses}
    assert "(e.g. 25%)" in text["fatf_rec10_interpretive_note_to_rec_10_p_5_b_footnote_40"]
    assert "USD/EUR 15,000" in text["fatf_rec10_rec_10_when_cdd_is_required_ii"]
    assert "S$20,000" in text["mas_notice_626_6_cdd_6_3_b"]
    assert "10% or more" in text["mock_internal_policy_s_1_customer_onboarding_standards_1_2_beneficial_ownership_verification_a"]
    assert not any("mock" in cid and cid.startswith("mas") for cid in text), "LLM mock clauses must not be in the corpus"
