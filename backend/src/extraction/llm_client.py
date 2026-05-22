import os
import logging
import json
import time
from typing import Type, TypeVar, Optional, Any, Union, List
import httpx
from pydantic import BaseModel

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

def _load_dotenv_manually():
    """
    手動解析根目錄下的 .env 檔案，實現零依賴環境變數載入。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 專案根目錄在 src 的上一層 (src/extraction/llm_client.py -> 3 層向上是根目錄)
    project_root = os.path.dirname(os.path.dirname(current_dir))
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        # 去除引號與空格
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        os.environ[key] = val
            logger.info(f"已成功手動從載入環境配置：{env_path}")
        except Exception as e:
            logger.error(f"手動載入 .env 檔案失敗：{e}")

# 初始化時主動載入環境變數
_load_dotenv_manually()

class LLMClient:
    """
    大語言模型 API 客戶端封裝，支持 NVIDIA NIM、真實 Gemini API 與離線 Mock 模式。
    """
    def __init__(self, api_key: Optional[str] = None):
        # 1. 讀取 NVIDIA NIM 平台配置
        self.nvidia_api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.nim_base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.nim_chunker_model = os.getenv("NIM_CHUNKER_MODEL", "meta/llama-3.3-70b-instruct")
        self.nim_extractor_model = os.getenv("NIM_EXTRACTOR_MODEL", "deepseek-ai/deepseek-r1")
        
        # 2. 讀取 Gemini 配置 (保留原有相容性)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        self.client = None
        self.is_mock = True
        self.provider = "mock"
        
        # 3. 判斷並初始化底層客戶端引擎 (優先選用 NVIDIA NIM，次選 Gemini)
        if self.nvidia_api_key and self.nvidia_api_key != "mock":
            self.is_mock = False
            self.provider = "nvidia_nim"
            logger.info(f"NVIDIA NIM LLM 客戶端初始化成功。Chunker: {self.nim_chunker_model}, Extractor: {self.nim_extractor_model}")
        elif self.gemini_api_key and self.gemini_api_key != "mock" and HAS_GENAI:
            try:
                self.client = genai.Client(api_key=self.gemini_api_key)
                self.is_mock = False
                self.provider = "gemini"
                logger.info(f"真實 Gemini LLM 客戶端已成功初始化。Model: {self.gemini_model_name}")
            except Exception as e:
                logger.error(f"真實 Gemini LLM 初始化失敗，將 Fallback 至 Mock 模式。Error: {e}")
        else:
            logger.warning("未檢測到有效 API 金鑰，系統已自動 Fallback 至 Mock LLM 離線模式。")

    def generate_structured(
        self, 
        prompt: str, 
        response_schema: Type[T], 
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> T:
        """
        發送 prompt 給 LLM 並返回符合指定 Pydantic Schema 的結構化資料。
        支援 NVIDIA NIM、Gemini 及 Mock 降級，並內建 3 次指數退避重試與混合約束。
        """
        if not self.is_mock:
            # === 分支 A: NVIDIA NIM 平台連接路徑 ===
            if self.provider == "nvidia_nim" and self.nvidia_api_key:
                # 動態決定此任務最合適的模型
                if not model_name:
                    schema_name = response_schema.__name__.lower()
                    if "clause" in schema_name:
                        model_name = self.nim_chunker_model
                    elif "obligation" in schema_name:
                        model_name = self.nim_extractor_model
                    else:
                        model_name = self.nim_chunker_model
                
                logger.info(f"[NVIDIA NIM] 正在發送請求至模型: {model_name} (Schema: {response_schema.__name__})")
                
                # 混合約束策略：動態導出 Pydantic 的 JSON Schema 並注入 Prompt 尾端
                schema_json = response_schema.model_json_schema()
                schema_str = json.dumps(schema_json, ensure_ascii=False, indent=2)
                
                augmented_prompt = (
                    f"{prompt}\n\n"
                    f"[IMPORTANT] You MUST return a JSON object strictly matching the following JSON Schema:\n"
                    f"```json\n{schema_str}\n```\n"
                    f"Do NOT wrap the output in ```json tags, just return the raw JSON object conforming exactly to the schema."
                )
                
                headers = {
                    "Authorization": f"Bearer {self.nvidia_api_key}",
                    "Content-Type": "application/json"
                }
                
                is_deepseek = "deepseek" in model_name.lower()
                
                payload = {
                    "model": model_name,
                    "messages": [],
                }
                
                if is_deepseek:
                    # 100% 完美對齊官方呼叫 deepseek-ai/deepseek-v4-pro 之規格配置
                    payload["temperature"] = 1.0
                    payload["top_p"] = 0.95
                    payload["max_tokens"] = 16384
                    payload["chat_template_kwargs"] = {"thinking": False}
                    # 移除非必要之 response_format 強約束，解除約束解碼器對 DeepSeek 生成速度之限制
                else:
                    payload["temperature"] = 0.1
                    payload["response_format"] = {"type": "json_object"}
                
                if system_instruction:
                    payload["messages"].append({"role": "system", "content": system_instruction})
                payload["messages"].append({"role": "user", "content": augmented_prompt})
                
                # 指數退避重試機制 (最多 3 次重試)
                max_retries = 3
                # 針對 DeepSeek 推理模型給予更寬容的 120 秒超時，防止排隊或生成緩慢導致 Timeout
                timeout_val = 120.0 if is_deepseek else 60.0
                
                for attempt in range(max_retries + 1):
                    try:
                        with httpx.Client(timeout=timeout_val) as http_client:
                            response = http_client.post(
                                f"{self.nim_base_url}/chat/completions",
                                json=payload,
                                headers=headers
                            )
                            response.raise_for_status()
                            response_data = response.json()
                            
                            content = response_data["choices"][0]["message"]["content"]
                            if not content:
                                raise ValueError("NVIDIA NIM 回傳空內容")
                            
                            # 健壯性防禦：如果模型在未開 response_format 時回傳了包裹在 Markdown block 中的 JSON，先行去除
                            clean_content = content.strip()
                            if clean_content.startswith("```json"):
                                clean_content = clean_content[7:]
                            if clean_content.startswith("```"):
                                clean_content = clean_content[3:]
                            if clean_content.endswith("```"):
                                clean_content = clean_content[:-3]
                            clean_content = clean_content.strip()
                            
                            # 解析並驗證結構化 JSON
                            return response_schema.model_validate_json(clean_content)
                    except Exception as e:
                        if attempt < max_retries:
                            sleep_time = 2 ** attempt  # 1s, 2s, 4s
                            logger.warning(f"[NVIDIA NIM] 第 {attempt + 1} 次呼叫失敗，將在 {sleep_time} 秒後重試。錯誤: {e}")
                            time.sleep(sleep_time)
                        else:
                            logger.error(f"[NVIDIA NIM] 已重試 {max_retries} 次均告失敗，將優雅 Fallback 至 Mock 模式。最後錯誤: {e}")
            
            # === 分支 B: Gemini API 連接路徑 ===
            elif self.provider == "gemini" and self.client:
                try:
                    config = types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0.1,
                    )
                    if system_instruction:
                        config.system_instruction = system_instruction
                    
                    response = self.client.models.generate_content(
                        model=model_name or self.gemini_model_name,
                        contents=prompt,
                        config=config
                    )
                    
                    if not response.text:
                        raise ValueError("Gemini API 回傳空內容")
                        
                    return response_schema.model_validate_json(response.text)
                except Exception as e:
                    logger.error(f"真實 Gemini API 呼叫失敗，將 Fallback 至 Mock 資料。Error: {e}")
        
        # === 降級 Fallback: Mock 離線數據生成 ===
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
