import os
import yaml
from typing import List
from src.contracts.models import Concept, Obligation, Conflict, Clause, SourceDocument
from src.association.concept_mapper import ConceptLoader, ConceptMapper
from src.association.conflict_detector import ConflictDetector

# 定義測試路徑
GOLD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/gold"))
ADJUDICATIONS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/reviews/conflict_adjudications.yaml"))



def test_concept_loader():
    """
    驗證 ConceptLoader 能正確讀取與解析 Markdown 百科檔案。
    """
    concepts_dir = os.path.join(GOLD_DIR, "concepts")
    assert os.path.exists(concepts_dir), "黃金數據集 concepts 目錄不存在"

    concepts = ConceptLoader.load_from_directory(concepts_dir)
    # 應包含 5 大黃金概念
    assert len(concepts) == 5, f"應載入 5 個合規概念，實得: {len(concepts)}"

    # 驗證 UBO 概念屬性
    ubo_concept = next((c for c in concepts if c.concept_id == "ubo"), None)
    assert ubo_concept is not None
    assert "UBO" in ubo_concept.name or "實質受益人" in ubo_concept.name
    assert len(ubo_concept.description) > 10
    assert "beneficial owner" in ubo_concept.aliases
    assert "mas_notice_626_6_cdd_6_13" in ubo_concept.source_clause_ids
    gold_clause_ids = {c["clause_id"] for c in yaml.safe_load(open(os.path.join(GOLD_DIR, "clauses.yaml"), encoding="utf-8"))}
    for concept in concepts:
        assert set(concept.source_clause_ids) <= gold_clause_ids, f"{concept.concept_id} cites unknown clauses"


def test_concept_mapper_alias_resolution():
    """
    驗證 ConceptMapper 的同名化映射，包含不區分大小寫、去空格及變體比對。
    """
    concepts_dir = os.path.join(GOLD_DIR, "concepts")
    concepts = ConceptLoader.load_from_directory(concepts_dir)
    mapper = ConceptMapper(concepts)

    # 1. 測試 UBO 的多種別名變體
    assert mapper.map_alias("UBO") == "ubo"
    assert mapper.map_alias("beneficial owner") == "ubo"
    assert mapper.map_alias("controlling party") == "ubo"
    assert mapper.map_alias("ultimate beneficial owner") == "ubo"
    # 標準化與多餘空格測試
    assert mapper.map_alias("  Beneficial   owner  ") == "ubo"
    assert mapper.map_alias("controlling_party") == "ubo"

    # 2. 測試 PEP 的別名變體
    assert mapper.map_alias("pep") == "pep"
    assert mapper.map_alias("politically exposed person") == "pep"
    assert mapper.map_alias("PEP exposure") == "pep"

    # 3. 測試 CDD 與 EDD 別名
    assert mapper.map_alias("cdd") == "cdd"
    assert mapper.map_alias("customer due diligence") == "cdd"
    assert mapper.map_alias("edd") == "edd"
    assert mapper.map_alias("enhanced due diligence") == "edd"

    # 4. 測試 SOFW 資金財富來源
    assert mapper.map_alias("sofw") == "sofw"
    assert mapper.map_alias("source of wealth") == "sofw"
    assert mapper.map_alias("source of funds") == "sofw"

    # 5. 測試無效與不匹配詞彙
    assert mapper.map_alias("nonexistent_random_word") is None
    assert mapper.map_alias("") is None


def test_conflict_detector_engine(tmp_path):
    """
    驗證 ConflictDetector 引擎能自動檢出 3 大黃金衝突，且與 Ground Truth 完美對齊。
    """
    # 載入 obligations 黃金數據
    ob_file = os.path.join(GOLD_DIR, "obligations.yaml")
    assert os.path.exists(ob_file)
    with open(ob_file, "r", encoding="utf-8") as f:
        ob_data = yaml.safe_load(f)

    obligations = [Obligation(**item) for item in ob_data]
    assert len(obligations) >= 10

    # 執行衝突偵測：傳入條文與文件，衝突會引用實際寫出門檻或禁止字樣的條文；裁決紀錄由人工維護
    clauses = [Clause(**c) for c in yaml.safe_load(open(os.path.join(GOLD_DIR, "clauses.yaml"), encoding="utf-8"))]
    documents = [SourceDocument(**d) for d in yaml.safe_load(open(os.path.join(GOLD_DIR, "source_documents.yaml"), encoding="utf-8"))]
    detector = ConflictDetector(ConflictDetector.load_adjudications(ADJUDICATIONS_FILE))
    detected_conflicts = detector.detect_conflicts(obligations, clauses=clauses, documents=documents)

    # 應剛好自動檢出 3 大核心合規衝突
    assert len(detected_conflicts) == 3, f"應偵測出 3 個衝突，實得: {len(detected_conflicts)}"

    # 載入金標衝突作為 Ground Truth 對比
    gold_conf_file = os.path.join(GOLD_DIR, "conflicts.yaml")
    with open(gold_conf_file, "r", encoding="utf-8") as f:
        gold_data = yaml.safe_load(f)
    gold_conflicts = [Conflict(**item) for item in gold_data]

    # 計算 Precision, Recall & F1-score
    gold_ids = {c.conflict_id for c in gold_conflicts}
    detected_ids = {c.conflict_id for c in detected_conflicts}

    true_positives = len(gold_ids.intersection(detected_ids))
    precision = true_positives / len(detected_ids) if detected_ids else 0.0
    recall = true_positives / len(gold_ids) if gold_ids else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # 驗證 F1-score 必須為 完美對齊的 1.00
    assert f1_score == 1.0, f"衝突偵測比對 F1-score 未達到 1.0，實得: {f1_score}"

    # 引用的條文集合也要和金標一致，而且每組衝突橫跨兩份不同的來源文件
    gold_by_id = {c.conflict_id: c for c in gold_conflicts}
    clause_doc = {c.clause_id: c.source_document_id for c in clauses}
    for conf in detected_conflicts:
        assert set(conf.source_clause_ids) == set(gold_by_id[conf.conflict_id].source_clause_ids)
        assert len({clause_doc[cid] for cid in conf.source_clause_ids}) == 2

    # 驗證每個衝突的欄位完整性
    for conf in detected_conflicts:
        assert conf.conflict_id in ["conf_ubo_threshold", "conf_pep_jurisdiction", "conf_occasional_threshold"]
        assert conf.conflict_type in ["Numerical", "PolicyReversal"]
        assert len(conf.source_clause_ids) >= 2
        assert conf.verifiability == "retrieval-verifiable"
        assert conf.adjudication_status == "resolved"
        assert conf.resolved_by is not None
        assert len(conf.description) > 10

    # 序列化輸出到暫存目錄（data/processed 由管線負責產生）
    out_path = str(tmp_path / "conflicts.yaml")
    detector.save_conflicts_to_yaml(detected_conflicts, out_path)
    assert os.path.exists(out_path)

    # 再次載入輸出的 processed conflicts，確保可序列化性與正確性
    with open(out_path, "r", encoding="utf-8") as f:
        processed_data = yaml.safe_load(f)
    assert len(processed_data) == 3
    for item in processed_data:
        Conflict(**item)  # 應能順利解構通過強型別校驗


def test_conflict_without_adjudication_stays_pending():
    """沒有人工裁決紀錄的衝突，維持 pending_human_review。"""
    obligations = [Obligation(**item) for item in yaml.safe_load(open(os.path.join(GOLD_DIR, "obligations.yaml"), encoding="utf-8"))]
    detected = ConflictDetector().detect_conflicts(obligations)
    assert {c.conflict_id for c in detected} == {"conf_ubo_threshold", "conf_pep_jurisdiction", "conf_occasional_threshold"}
    assert all(c.adjudication_status == "pending_human_review" and c.resolved_by is None for c in detected)


def test_no_conflict_when_thresholds_agree():
    """兩份來源的持股門檻相同時，不應標記衝突（偵測依數值比對，而非寫死）。"""
    obligations = [Obligation(**item) for item in yaml.safe_load(open(os.path.join(GOLD_DIR, "obligations.yaml"), encoding="utf-8"))]
    same = [o.model_copy(update={"conditions": ["controlling_ownership_interest_above_25_percent"]})
            if o.obligation_id == "ob_identify_ubo_10_gb" else o for o in obligations]
    ids = {c.conflict_id for c in ConflictDetector().detect_conflicts(same)}
    assert "conf_ubo_threshold" not in ids


def test_adjudication_does_not_cover_a_changed_conflict():
    """
    新增一份來源讓同一類衝突引用的條文改變時，舊的裁決不能沿用：衝突回到 pending_human_review。
    """
    obligations = [Obligation(**item) for item in yaml.safe_load(open(os.path.join(GOLD_DIR, "obligations.yaml"), encoding="utf-8"))]
    clauses = [Clause(**c) for c in yaml.safe_load(open(os.path.join(GOLD_DIR, "clauses.yaml"), encoding="utf-8"))]
    new_clause = Clause(clause_id="other_bank_policy_ubo", source_document_id="other_bank_policy", section_ref="UBO",
                        raw_text="The bank shall apply an ownership threshold of 20% to identify UBOs.",
                        normalized_text="the bank shall apply an ownership threshold of 20% to identify ubos.",
                        citations=["other_bank_policy_ubo"])
    new_ob = Obligation(obligation_id="ob_identify_ubo_20_other", source_clause_ids=[new_clause.clause_id],
                        jurisdiction="Internal", actor="bank", action="identify_and_verify", object="beneficial_owner",
                        conditions=["controlling_ownership_interest_above_20_percent"], confidence=0.9)
    detector = ConflictDetector(ConflictDetector.load_adjudications(ADJUDICATIONS_FILE))
    detected = {c.conflict_id: c for c in detector.detect_conflicts(obligations + [new_ob], clauses=clauses + [new_clause])}

    ubo = detected["conf_ubo_threshold"]
    assert "other_bank_policy_ubo" in ubo.source_clause_ids
    assert ubo.adjudication_status == "pending_human_review" and ubo.resolved_by is None
    assert "needs a new human decision" in ubo.description
    # 其他兩組衝突的條文沒變，裁決照常套用
    assert detected["conf_occasional_threshold"].adjudication_status == "resolved"
    assert detected["conf_pep_jurisdiction"].adjudication_status == "resolved"
