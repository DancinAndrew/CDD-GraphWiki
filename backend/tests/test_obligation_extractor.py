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
        return RuleBasedObligationExtractor(confidence_threshold=0.75)

    def test_extractor_success_and_json_schema(self, extractor):
        # 建立一個應能成功抽取的真實或 Mock Clause (例如 MAS 626 關於 CDD 的條款)
        clause = Clause(
            clause_id="mas626_clause_01",
            source_document_id="mas_notice_626",
            section_ref="Paragraph 4.1",
            raw_text="A bank shall perform customer due diligence (CDD) measures when establishing business relations with a customer.",
            normalized_text="a bank shall perform customer due diligence cdd measures when establishing business relations with a customer.",
            citations=["MAS Notice 626 Para 4.1"]
        )

        ob, reason = extractor.extract_obligation(clause)
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

    def test_extractor_failure_low_confidence(self):
        # 使用極高的 confidence_threshold 來迫使低置信度分類生效
        strict_extractor = RuleBasedObligationExtractor(confidence_threshold=0.99)
        
        clause = Clause(
            clause_id="mas626_clause_01",
            source_document_id="mas_notice_626",
            section_ref="Paragraph 4.1",
            raw_text="A bank shall perform customer due diligence (CDD) measures when establishing business relations with a customer.",
            normalized_text="a bank shall perform customer due diligence cdd measures when establishing business relations with a customer.",
            citations=["MAS Notice 626 Para 4.1"]
        )

        ob, reason = strict_extractor.extract_obligation(clause)
        # confidence 計算為 (1.0 + 1.0 + 0.7) / 3 = 0.9，低於 0.99 應被拒絕
        assert ob is None
        assert reason == "LOW_CONFIDENCE"

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
