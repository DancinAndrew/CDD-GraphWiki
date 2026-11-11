import os
import sys
import json
import pytest
import yaml
from jsonschema import validate

# 確保 src 可以被導入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.contracts.models import Clause, Obligation
from src.extraction.extractor import RuleBasedObligationExtractor, ObligationExtractionPipeline

SCHEMAS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'schemas'))



def load_json_schema(filename):
    filepath = os.path.join(SCHEMAS_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)


class TestObligationExtractor:
    
    @pytest.fixture
    def extractor(self):
        return RuleBasedObligationExtractor()

    def test_extractor_success_and_json_schema(self, extractor):
        # MAS Notice 626 第 6.3(a) 段（逐字原文），上層段落是 CDD 觸發句
        clause = Clause(
            clause_id="mas_notice_626_6_cdd_6_3_a",
            source_document_id="mas_notice_626",
            section_ref="6 Customer Due Diligence > 6.3 > (a)",
            raw_text="(a) the bank establishes business relations with any customer;",
            normalized_text="(a) the bank establishes business relations with any customer;",
            citations=["mas_notice_626_6_cdd_6_3_a"]
        )
        context = "### 6.3 a bank shall perform the measures as required by paragraphs 6, 7 and 8 when -"

        ob, reason = extractor.extract_obligation(clause, context)
        assert ob is not None
        assert reason is None
        
        # 驗證抽取結果
        assert ob.obligation_id == "ob_cdd_on_relationship_mas"
        assert ob.jurisdiction == "Singapore"
        assert ob.actor == "bank"
        assert ob.action == "perform_cdd"
        assert ob.object == "customer"
        assert "establishing_business_relations" in ob.conditions
        
        # 100% 通過 Pydantic 校驗 (因為已經是 Pydantic 實體)
        assert isinstance(ob, Obligation)

        # 100% 通過 JSON Schema 校驗
        schema = load_json_schema("Obligation.schema.json")
        ob_dict = ob.model_dump()
        validate(instance=ob_dict, schema=schema)

    def test_extractor_failure_non_obligation_text(self, extractor):
        # 背景描述或目錄標題
        clause = Clause(
            clause_id="mas626_cdd_measures",
            source_document_id="mas_notice_626",
            section_ref="Section 4",
            raw_text="CUSTOMER DUE DILIGENCE",
            normalized_text="customer due diligence",
            citations=["MAS Notice 626 Section 4"]
        )

        ob, reason = extractor.extract_obligation(clause)
        assert ob is None
        assert reason == "NON_OBLIGATION_TEXT"

    def test_extractor_failure_missing_core_elements(self, extractor):
        # 含有 "shall" 但缺少明確的 actor、action 或 object
        clause = Clause(
            clause_id="mas626_clause_99",
            source_document_id="mas_notice_626",
            section_ref="Paragraph 9.9",
            raw_text="The process shall be maintained in accordance with guidelines.",
            normalized_text="the process shall be maintained in accordance with guidelines.",
            citations=["MAS Notice 626 Para 9.9"]
        )

        ob, reason = extractor.extract_obligation(clause)
        assert ob is None
        assert reason == "MISSING_CORE_ELEMENTS"

    def test_extractor_without_reliability_leaves_confidence_empty(self, extractor):
        # 沒有給量測資料時不填信心值，出處說明寫明沒有量測；不再有 LOW_CONFIDENCE 這種未命中原因
        clause = Clause(
            clause_id="mas_notice_626_6_cdd_6_3_a",
            source_document_id="mas_notice_626",
            section_ref="6 Customer Due Diligence > 6.3 > (a)",
            raw_text="(a) the bank establishes business relations with any customer;",
            normalized_text="(a) the bank establishes business relations with any customer;",
            citations=["mas_notice_626_6_cdd_6_3_a"]
        )
        context = "### 6.3 a bank shall perform the measures as required by paragraphs 6, 7 and 8 when -"

        ob, reason = extractor.extract_obligation(clause, context)
        assert reason is None
        assert ob.confidence is None
        assert ob.confidence_basis == "Not measured: no reliability data was given to the extractor."
        assert ob.confidence_kind is None
        assert not hasattr(extractor, "confidence_threshold")

    def test_extractor_uses_given_reliability(self):
        # 信心值 = 給定的量測精確率四捨五入到小數兩位，出處說明照抄
        reliability = {"cdd_triggers": {"correct": 8, "flagged": 9, "precision": 0.8889, "basis": "measured on X"}}
        extractor = RuleBasedObligationExtractor(reliability=reliability)
        clause = Clause(
            clause_id="mas_notice_626_6_cdd_6_3_a",
            source_document_id="mas_notice_626",
            section_ref="6 Customer Due Diligence > 6.3 > (a)",
            raw_text="(a) the bank establishes business relations with any customer;",
            normalized_text="(a) the bank establishes business relations with any customer;",
            citations=["mas_notice_626_6_cdd_6_3_a"]
        )
        ob, _ = extractor.extract_obligation(
            clause, "### 6.3 a bank shall perform the measures as required by paragraphs 6, 7 and 8 when -")
        assert ob.confidence == 0.89
        assert ob.confidence_basis == "measured on X"
        assert ob.confidence_kind == "measured_on_heldout"

    def test_evaluation_metrics_calculation(self, tmp_path):
        # 手動測試 evaluate_against_gold 計算精度、召回率與 F1-score 的正確性
        pipeline = ObligationExtractionPipeline()
        
        # 1. 建立測試用的 Gold 數據集檔案
        gold_obs = [
            Obligation(
                obligation_id="ob_1",
                source_clause_ids=["c1"],
                jurisdiction="Singapore",
                actor="bank",
                action="perform_cdd",
                object="customer",
                confidence=0.95,
                review_status="approved"
            ),
            Obligation(
                obligation_id="ob_2",
                source_clause_ids=["c2"],
                jurisdiction="Global",
                actor="financial_institution",
                action="prohibit",
                object="anonymous_accounts",
                confidence=0.92,
                review_status="approved"
            )
        ]
        
        gold_file = tmp_path / "gold_obligations.yaml"
        with open(gold_file, "w", encoding="utf-8") as f:
            yaml.dump([g.model_dump() for g in gold_obs], f)

        # 2. 建立測試用的 Extracted 數據集 (部分匹配，有缺失、有欄位不完全對齊)
        extracted_obs = [
            # 完美匹配 ob_1
            Obligation(
                obligation_id="ob_1",
                source_clause_ids=["c1"],
                jurisdiction="Singapore",
                actor="bank",
                action="perform_cdd",
                object="customer",
                confidence=0.95,
                review_status="approved"
            ),
            # ob_2 欄位部分不對齊 (actor 與 action 對齊，但 object 不對齊)
            Obligation(
                obligation_id="ob_2",
                source_clause_ids=["c2"],
                jurisdiction="Global",
                actor="financial_institution",
                action="prohibit",
                object="other_object",
                confidence=0.92,
                review_status="approved"
            ),
            # 多出來的 ob_3 (會降低 Precision)
            Obligation(
                obligation_id="ob_3",
                source_clause_ids=["c3"],
                jurisdiction="Singapore",
                actor="bank",
                action="perform_edd",
                object="pep",
                confidence=0.90,
                review_status="approved"
            )
        ]

        report_file = tmp_path / "report.txt"
        pipeline.evaluate_against_gold(extracted_obs, str(gold_file), report_file)
        
        # 驗證報告檔案是否生成
        assert report_file.exists()
        
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 預期指標計算：
        # - Gold Count = 2 (ob_1, ob_2)
        # - Extracted Count = 3 (ob_1, ob_2, ob_3)
        # - Match Count = 2 (ob_1, ob_2)
        # - Precision = 2/3 = 0.67
        # - Recall = 2/2 = 1.00
        # - F1 = 2 * (2/3) * 1 / (2/3 + 1) = (4/3) / (5/3) = 0.80
        # - Field Accuracy:
        #   - ob_1 欄位對齊：actor(OK), action(OK), object(OK) = 1.0
        #   - ob_2 欄位對齊：actor(OK), action(OK), object(Fail) = 2/3 = 0.67
        #   - 平均 Field Accuracy = (1.0 + 0.67) / 2 = 0.83
        
        assert "Precision (精準率): 0.67" in content
        assert "Recall (召回率): 1.00" in content
        assert "F1-Score: 0.80" in content
        assert "Field-level Alignment Accuracy: 0.83" in content


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _load(path):
    with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_thresholds_are_parsed_from_clause_text():
    from src.extraction.extractor import parse_amount, parse_percent, trigger_conditions
    assert parse_amount("above the applicable designated threshold (USD/EUR 15,000)") == (15000, "usd_eur")
    assert parse_amount("any transaction of a value exceeding S$20,000, other than") == (20000, "sgd")
    # 銀行政策同時提到 10% 與 25%：取「threshold of」後面的門檻
    assert parse_percent("apply an ownership threshold of 10% or more (which is stricter than the regulatory baseline of 25%)") == 10
    assert parse_percent("It may be based on a threshold, e.g. any person owning more than a certain percentage of the company (e.g. 25%).") == 25
    assert trigger_conditions("(ii) carrying out occasional transactions: (i) above the applicable designated threshold (USD/EUR 15,000); or") == ["occasional_transaction_above_15000_usd_eur"]


def test_rules_do_not_depend_on_clause_ids():
    """同一段文字換一個條文 ID，抽取結果應完全相同（規則只看文字與管轄區）。"""
    extractor = RuleBasedObligationExtractor()
    text = "(a) The bank shall apply an ownership threshold of 10% or more (which is stricter than the regulatory baseline of 25%) to identify UBOs."
    results = []
    for cid in ["mock_internal_policy_x", "mock_internal_policy_renamed_clause"]:
        clause = Clause(clause_id=cid, source_document_id="mock_internal_policy", section_ref="1.2 > (a)",
                        raw_text=text, normalized_text=text.lower(), citations=[cid])
        ob, _ = extractor.extract_obligation(clause)
        results.append((ob.obligation_id, ob.jurisdiction, ob.conditions))
    assert results[0] == results[1] == ("ob_identify_ubo_10_gb", "Internal", ["controlling_ownership_interest_above_10_percent"])


def test_extraction_on_parsed_sources_matches_gold_with_provenance(tmp_path):
    """在解析出的條文上跑抽取：13 條金標義務全部命中，且錨點條文、管轄區、出處集合都對。"""
    from src.extraction.extractor import extract_obligations, load_jurisdictions
    clauses = [Clause(**c) for c in _load("data/gold/clauses.yaml")]
    extractor = RuleBasedObligationExtractor(jurisdictions=load_jurisdictions(os.path.join(REPO_ROOT, "data/gold/source_documents.yaml")))
    obligations, _ = extract_obligations(clauses, extractor)

    metrics = ObligationExtractionPipeline().evaluate_against_gold(
        obligations, os.path.join(REPO_ROOT, "data/gold/obligations.yaml"), tmp_path / "report.txt")
    assert metrics["matched"] == metrics["gold"] == metrics["extracted"] == 13
    assert metrics["provenance_matches"] == 13
    assert metrics["exact_source_matches"] == 13

    by_id = {o.obligation_id: o for o in obligations}
    # MAS Notice 626 沒有數字門檻：實質受益人義務不應帶 25% 條件
    assert by_id["ob_identify_ubo_mas"].conditions == []
    assert "controlling_ownership_interest_above_25_percent" in by_id["ob_identify_ubo_25"].conditions
    assert all(o.jurisdiction == "Singapore" for o in obligations if o.obligation_id.endswith("_mas"))
    # MAS 6.14B（驗證受益人身分）以交叉引用「identified under paragraph 6.14」歸入實質受益人義務
    assert "mas_notice_626_6_cdd_6_14b" in by_id["ob_identify_ubo_mas"].source_clause_ids
    # 銀行政策 1.4 的禁令與 1.4(a) 的核准要求是兩條不同的義務
    assert by_id["ob_pep_prohibitions_gb"].source_clause_ids == ["mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons"]
    assert by_id["ob_pep_approval_gb"].source_clause_ids == ["mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons_a"]
    assert by_id["ob_cdd_incomplete_mas"].source_clause_ids == ["mas_notice_626_6_cdd_6_35"]
    # 銀行政策 1.1「Every customer must be identified and verified」是第 2 版規則找到、原本漏標的義務
    assert by_id["ob_verify_customer_gb"].source_clause_ids[0] == "mock_internal_policy_s_1_customer_onboarding_standards_1_1_customer_identification"


def test_provenance_mismatch_is_reported(tmp_path):
    """抽到正確 ID 但出處錯（例如把銀行政策條文標成 MAS 義務）時，報告要標成 MISMATCH。"""
    gold = [Obligation(obligation_id="ob_x", source_clause_ids=["mas_clause"], jurisdiction="Singapore",
                       actor="bank", action="identify_and_verify", object="beneficial_owner", confidence=0.9)]
    gold_file = tmp_path / "gold.yaml"
    with open(gold_file, "w", encoding="utf-8") as f:
        yaml.dump([g.model_dump() for g in gold], f)
    wrong = [gold[0].model_copy(update={"source_clause_ids": ["policy_clause"], "jurisdiction": "Internal"})]
    metrics = ObligationExtractionPipeline().evaluate_against_gold(wrong, str(gold_file), tmp_path / "r.txt")
    assert metrics["matched"] == 1 and metrics["provenance_matches"] == 0
    assert "Provenance: [MISMATCH]" in (tmp_path / "r.txt").read_text(encoding="utf-8")
