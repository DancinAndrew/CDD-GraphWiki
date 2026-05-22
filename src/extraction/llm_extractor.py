import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from src.contracts.models import SourceDocument, Clause, Obligation
from src.extraction.llm_client import LLMClient

logger = logging.getLogger(__name__)

class ClausesExtractionResult(BaseModel):
    clauses: List[Clause] = Field(..., description="從文本中智能提取的所有樹狀層級 Clause 條款列表")

class ObligationsExtractionResult(BaseModel):
    obligations: List[Obligation] = Field(..., description="從 Clause 條文中精準提取的強型別合規義務規則列表")

class LLMHierarchicalChunker:
    """
    使用 LLM 進行智能樹狀層級切片的模組。
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def chunk_document(self, doc_id: str, raw_text: str) -> List[Clause]:
        """
        將原始文字通過大語言模型切分為帶有樹狀階層與 Citation 的 Clause 物件列表。
        """
        logger.info(f"開始使用 LLM 智能層級切片 Document: {doc_id}")
        
        system_instruction = (
            "你是一個資深的金融合規大律師與合規架構師。你的任務是閱讀法規原文，"
            "將其智慧切分為具備明確樹狀層級（parent-child）結構的 Clause 物件列表。\n"
            "切分規範：\n"
            "1. 為每一條款產出一個唯一的、具備語意化特徵的 clause_id（例如：'mas626_s6_1' 或 'mas626_s6_1_a'）。\n"
            "2. 明確設定 parent_clause_id，例如 (a) 的 parent 是 6.1 條款。\n"
            "3. 確保 citations 為穩定的引述標識符（例如 ['MAS Notice 626 Section 6.1(a)']）。\n"
            "4. raw_text 必須包含該條款的完整原始文字，normalized_text 則是小寫、去除多餘空白的乾淨文字。"
        )
        
        prompt = (
            f"請解析以下法規源文件文本（文件 ID: {doc_id}），並提取出所有條款 (Clauses)。\n"
            f"源文件文本如下：\n"
            f"\"\"\"\n{raw_text}\n\"\"\""
        )
        
        try:
            result = self.llm_client.generate_structured(
                prompt=prompt,
                response_schema=ClausesExtractionResult,
                system_instruction=system_instruction
            )
            # 確保補填 source_document_id 
            for c in result.clauses:
                c.source_document_id = doc_id
            logger.info(f"智能切片完成，共產出 {len(result.clauses)} 個 Clause 節點")
            return result.clauses
        except Exception as e:
            logger.error(f"LLM 智能切片失敗，Error: {e}")
            raise e

class LLMStructuredExtractor:
    """
    使用 LLM Packaged Section Context 進行強型別合規義務抽取的模組。
    """
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def extract_obligations(self, clauses: List[Clause]) -> List[Obligation]:
        """
        將 clauses 列表按 section_ref 進行 Section-level 打包分組，
        並在全局 Section 上下文中進行強型別義務提取，以保障 Clause-level Provenance。
        """
        if not clauses:
            return []
            
        # 根據 section_ref (或其前綴) 進行 Section-level 打包分組
        sections: Dict[str, List[Clause]] = {}
        for c in clauses:
            sec_name = c.section_ref.split(" > ")[0] if " > " in c.section_ref else c.section_ref
            if sec_name not in sections:
                sections[sec_name] = []
            sections[sec_name].append(c)
            
        all_obligations: List[Obligation] = []
        
        for sec_name, sec_clauses in sections.items():
            logger.info(f"開始為 Section: {sec_name} 打包抽取 Obligations (共 {len(sec_clauses)} 個 Clauses)")
            
            system_instruction = (
                "你是一個資深的金融合規大律師與合規架構師。你的任務是從同一 Section 下的所有 Clause 條款中，"
                "抽取結構化、機器可讀的強型別合規義務 (Obligation) 列表。\n"
                "抽取規範：\n"
                "1. obligation_id 必須是具備語意化的英文 kebab-case/snake_case ID（例如：'ob_verify_customer_identity'）。\n"
                "2. 必須 100% 確保 Clause-level Provenance：在 source_clause_ids 欄位中，填入此 Obligation 源自的 Clause ID 列表（支持一對多關聯）。\n"
                "3. actor 是執行義務的主體（例如 'bank', 'financial_institution'）。\n"
                "4. action 是核心動作（例如 'identify_and_verify', 'perform_edd'）。\n"
                "5. object 是核心對象（例如 'customer_identity', 'beneficial_owner'）。\n"
                "6. applies_to 包含約束客戶特徵的字典，例如：{'customer_type': 'legal_person'}。\n"
                "7. conditions 包含觸發此義務的事實條件列表。\n"
                "8. exceptions 包含例外免除條件列表。\n"
                "9. required_evidence 包含執行此義務所需的合規憑證（如 'ubo_declaration'）。\n"
                "10. review_flags 包含觸發人工合規審查的特徵信號。"
            )
            
            # 打包 clauses Context
            clauses_context = []
            for c in sec_clauses:
                clauses_context.append(
                    f"Clause ID: {c.clause_id}\n"
                    f"Section Ref: {c.section_ref}\n"
                    f"Text: {c.raw_text}\n"
                    f"Citations: {c.citations}\n"
                    f"------------------------"
                )
            clauses_text = "\n".join(clauses_context)
            
            prompt = (
                f"請分析以下 Section: {sec_name} 的條款上下文，點石成金抽取強型別的 Obligations。\n"
                f"所有條款列表如下：\n"
                f"\"\"\"\n{clauses_text}\n\"\"\""
            )
            
            try:
                result = self.llm_client.generate_structured(
                    prompt=prompt,
                    response_schema=ObligationsExtractionResult,
                    system_instruction=system_instruction
                )
                
                # 簡單後處理與補填數據
                for ob in result.obligations:
                    # 確保 jurisdiction 與 source clauses 一致
                    if ob.source_clause_ids:
                        ref_id = ob.source_clause_ids[0]
                        ob.jurisdiction = "Singapore" if "mas" in ref_id else ("Global" if "fatf" in ref_id else "Internal")
                    else:
                        ob.jurisdiction = "Singapore"
                    
                    ob.review_status = "pending_human_review"
                    all_obligations.append(ob)
            except Exception as e:
                logger.error(f"Section {sec_name} 義務抽取失敗，Error: {e}")
                
        logger.info(f"Section Obligations 抽取完成，共產出 {len(all_obligations)} 個 Obligations")
        return all_obligations

class LLMExtractorPipeline:
    """
    大語言模型法規導入管線控制器。
    """
    def __init__(self, api_key: Optional[str] = None):
        self.llm_client = LLMClient(api_key=api_key)
        self.chunker = LLMHierarchicalChunker(self.llm_client)
        self.extractor = LLMStructuredExtractor(self.llm_client)

    def run_ingestion(self, doc_id: str, raw_text: str) -> Tuple[List[Clause], List[Obligation]]:
        """
        執行完整的二階段 LLM Ingestion。
        第一階段：智能樹狀層級切片 (Clause 提取)
        第二階段：打包上下文結構化義務抽取 (Obligation 提取)
        """
        logger.info(f"開始為 Document ID: {doc_id} 執行二階段 LLM Ingestion Pipeline")
        
        # 1. 執行智能切片
        clauses = self.chunker.chunk_document(doc_id, raw_text)
        
        # 2. 執行結構化抽取
        obligations = self.extractor.extract_obligations(clauses)
        
        return clauses, obligations
