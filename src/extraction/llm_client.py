import os
import logging
from typing import Type, TypeVar, Optional, Any, Union, List
from pydantic import BaseModel

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class LLMClient:
    """
    大語言模型 API 客戶端封裝，支持真實 Gemini API 與離線 Mock 模式。
    """
    def __init__(self, api_key: Optional[str] = None):
        # 優先從傳入的參數讀取，再從環境變數讀取
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # 決定是否啟用真實 API
        if self.api_key and self.api_key != "mock" and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.is_mock = False
                logger.info(f"真實 Gemini LLM 客戶端已成功初始化。Model: {self.model_name}")
            except Exception as e:
                self.client = None
                self.is_mock = True
                logger.error(f"真實 Gemini LLM 初始化失敗，Fallback 至 Mock 模式。Error: {e}")
        else:
            self.client = None
            self.is_mock = True
            logger.warning("未檢測到有效 GEMINI_API_KEY，系統已自動 Fallback 至 Mock LLM 離線模式。")

    def generate_structured(self, prompt: str, response_schema: Type[T], system_instruction: Optional[str] = None) -> T:
        """
        發送 prompt 給 LLM 並返回符合指定 Pydantic Schema 的結構化資料。
        """
        if not self.is_mock and self.client:
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,
                )
                if system_instruction:
                    config.system_instruction = system_instruction
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # 確保返回的 text 不為空，若為空拋出異常
                if not response.text:
                    raise ValueError("Gemini API 回傳空內容")
                    
                return response_schema.model_validate_json(response.text)
            except Exception as e:
                logger.error(f"真實 Gemini API 呼叫失敗，將 Fallback 至 Mock 資料。Error: {e}")
                # 呼叫失敗，退回 Mock 模式
        
        return self._generate_mock(prompt, response_schema)

    def _generate_mock(self, prompt: str, response_schema: Type[T]) -> T:
        """
        在 Mock 模式下，根據目標型別與 Prompt 內的關鍵特徵，動態合成符合合約的 Mock 資料。
        """
        schema_name = response_schema.__name__
        logger.info(f"[MockLLMClient] 正在為 Schema: {schema_name} 生成 Mock 數據")
        
        prompt_lower = prompt.lower()
        
        # 1. 處理智能切片 (Clause 提取結果)
        if "clause" in schema_name.lower():
            # 假設 schema_name 是 ClausesExtractionResult
            # 我們需要回傳一個包含多個 Clause 的物件
            # 根據 prompt 中是否有 "mas" 或 "626" 來回傳對應的 mock 數據
            if "626" in prompt_lower or "mas" in prompt_lower:
                # 模擬從 MAS 626 PDF 抽取的 Clause
                mock_clauses = [
                    {
                        "clause_id": "mas626_cdd_mock_001",
                        "source_document_id": "mas_notice_626_2026",
                        "section_ref": "Section 6.1 (a)",
                        "parent_clause_id": None,
                        "raw_text": "A bank shall identify the customer and verify the customer's identity using reliable, independent source documents.",
                        "normalized_text": "a bank shall identify the customer and verify the customer's identity using reliable, independent source documents",
                        "citations": ["MAS Notice 626 Section 6.1(a)"]
                    },
                    {
                        "clause_id": "mas626_cdd_mock_002",
                        "source_document_id": "mas_notice_626_2026",
                        "section_ref": "Section 6.2 (b)",
                        "parent_clause_id": "mas626_cdd_mock_001",
                        "raw_text": "The bank shall identify the beneficial owner and take reasonable measures to verify the identity of the beneficial owner.",
                        "normalized_text": "the bank shall identify the beneficial owner and take reasonable measures to verify the identity of the beneficial owner",
                        "citations": ["MAS Notice 626 Section 6.2(b)"]
                    }
                ]
            else:
                # 預設通用
                mock_clauses = [
                    {
                        "clause_id": "gen_cdd_mock_001",
                        "source_document_id": "generic_policy_2026",
                        "section_ref": "Section 1",
                        "parent_clause_id": None,
                        "raw_text": "Financial institutions must identify customers and verify their identity.",
                        "normalized_text": "financial institutions must identify customers and verify their identity",
                        "citations": ["Generic Policy Section 1"]
                    }
                ]
            
            # 動態裝載
            # 假設 response_schema 是一個包裝類別：
            # class ClausesExtractionResult(BaseModel):
            #     clauses: List[Clause]
            # 我們可以用 model_validate 載入
            try:
                return response_schema.model_validate({"clauses": mock_clauses})
            except Exception:
                # 如果 schema 本身就是 Clause 類別（而不是包裝類別）
                return response_schema.model_validate(mock_clauses[0])
                
        # 2. 處理合規義務 (Obligation 提取結果)
        elif "obligation" in schema_name.lower():
            if "mas" in prompt_lower or "626" in prompt_lower:
                mock_obs = [
                    {
                        "obligation_id": "ob_verify_customer_mas_mock",
                        "source_clause_ids": ["mas626_cdd_mock_001"],
                        "jurisdiction": "Singapore",
                        "actor": "bank",
                        "action": "identify_and_verify",
                        "object": "customer_identity",
                        "applies_to": {"customer_type": "individual"},
                        "conditions": ["establishing_business_relations"],
                        "exceptions": [],
                        "required_evidence": ["full_name", "unique_id_number"],
                        "review_flags": ["missing_mandatory_identification_fields"],
                        "confidence": 0.95,
                        "review_status": "approved"
                    },
                    {
                        "obligation_id": "ob_identify_ubo_25_mas_mock",
                        "source_clause_ids": ["mas626_cdd_mock_002"],
                        "jurisdiction": "Singapore",
                        "actor": "bank",
                        "action": "identify_and_verify",
                        "object": "beneficial_owner",
                        "applies_to": {"customer_type": "legal_person"},
                        "conditions": ["controlling_ownership_interest_above_25_percent"],
                        "exceptions": [],
                        "required_evidence": ["ubo_declaration", "corporate_profile"],
                        "review_flags": ["ubo_not_identified"],
                        "confidence": 0.92,
                        "review_status": "approved"
                    }
                ]
            else:
                mock_obs = [
                    {
                        "obligation_id": "ob_generic_cdd_mock",
                        "source_clause_ids": ["gen_cdd_mock_001"],
                        "jurisdiction": "Global",
                        "actor": "financial_institution",
                        "action": "identify_and_verify",
                        "object": "customer_identity",
                        "applies_to": {},
                        "conditions": ["cdd_triggered"],
                        "exceptions": [],
                        "required_evidence": ["reliable_independent_source_documents"],
                        "review_flags": [],
                        "confidence": 0.90,
                        "review_status": "approved"
                    }
                ]
            
            try:
                return response_schema.model_validate({"obligations": mock_obs})
            except Exception:
                return response_schema.model_validate(mock_obs[0])
                
        # 3. 預設 Fallback (防空值錯誤)
        return response_schema.model_validate({})
