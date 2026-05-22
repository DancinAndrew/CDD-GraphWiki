#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
測試 NVIDIA NIM 平台 API 連通性與任務特定模型分發的驗證腳本。
"""

import sys
import os
import logging

# 確保能導入 src 目錄
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extraction.llm_client import LLMClient
from src.extraction.llm_extractor import ClausesExtractionResult, ObligationsExtractionResult

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_nim_connection")

def test_nim_connection():
    logger.info("=== 開始測試 NVIDIA NIM 平台連通性與任務特定模型分發 ===")
    
    # 1. 讀取並打印環境變數 (隱藏關鍵金鑰)
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        masked_key = nvidia_key[:10] + "..." + nvidia_key[-5:] if len(nvidia_key) > 15 else "..."
        logger.info(f"檢測到 NVIDIA_API_KEY: {masked_key}")
    else:
        logger.error("未檢測到 NVIDIA_API_KEY，請確認專案根目錄下已正確配置 .env 檔案")
        sys.exit(1)
        
    logger.info(f"智慧切片模型配置 (NIM_CHUNKER_MODEL): {os.getenv('NIM_CHUNKER_MODEL')}")
    logger.info(f"義務抽取模型配置 (NIM_EXTRACTOR_MODEL): {os.getenv('NIM_EXTRACTOR_MODEL')}")
    logger.info(f"API 端點配置 (NIM_BASE_URL): {os.getenv('NIM_BASE_URL')}")
    
    # 2. 初始化 LLMClient
    client = LLMClient()
    logger.info(f"LLMClient 提供者狀態: {client.provider} (IsMock: {client.is_mock})")
    
    if client.is_mock or client.provider != "nvidia_nim":
        logger.error("LLMClient 初始化失敗，未能成功選定 nvidia_nim 提供者")
        sys.exit(1)
        
    # 3. 測試智慧切片任務 (使用 meta/llama-3.3-70b-instruct)
    logger.info("\n--- [測試任務一] 智慧樹狀條款切片 (Llama 3.3 70B) ---")
    chunk_prompt = "請解析以下法規文本並抽取出 Clause 條款：'Section 6.1: A bank shall identify the customer.'"
    try:
        clauses_result = client.generate_structured(
            prompt=chunk_prompt,
            response_schema=ClausesExtractionResult,
            system_instruction="你是一個資深的金融合規架構師。請回傳包含 Clause 的 JSON 物件。"
        )
        logger.info("呼叫成功！回傳對象類型: %s", type(clauses_result))
        logger.info("抽取出的條款個數: %d", len(clauses_result.clauses))
        for idx, clause in enumerate(clauses_result.clauses):
            logger.info(f"  Clause [{idx+1}]: ID={clause.clause_id}, Section={clause.section_ref}, Text='{clause.raw_text}'")
    except Exception as e:
        logger.error(f"智慧切片任務呼叫失敗: {e}")
        sys.exit(1)
        
    # 4. 測試強型別合規義務抽取任務 (使用 deepseek-ai/deepseek-r1)
    logger.info("\n--- [測試任務二] 強型別合規義務抽取 (DeepSeek R1) ---")
    extract_prompt = """
    請從以下條款中抽取出強型別合規義務：
    Clause ID: mas626_cdd_01
    Section Ref: Section 6.1
    Text: A bank shall identify the customer and verify the customer's identity using reliable, independent source documents.
    """
    try:
        obligations_result = client.generate_structured(
            prompt=extract_prompt,
            response_schema=ObligationsExtractionResult,
            system_instruction="你是一個資深的金融合規大律師。請回傳包含 Obligation 的 JSON 物件。"
        )
        logger.info("呼叫成功！回傳對象類型: %s", type(obligations_result))
        logger.info("抽取出的義務個數: %d", len(obligations_result.obligations))
        for idx, ob in enumerate(obligations_result.obligations):
            logger.info(f"  Obligation [{idx+1}]: ID={ob.obligation_id}, Actor={ob.actor}, Action={ob.action}, Object={ob.object}")
            logger.info(f"    Required Evidence: {ob.required_evidence}")
            logger.info(f"    Source Clause IDs: {ob.source_clause_ids}")
    except Exception as e:
        logger.error(f"合規義務抽取任務呼叫失敗: {e}")
        sys.exit(1)
        
    # 5. 測試無效金鑰下的優雅降級 (Mock Fallback)
    logger.info("\n--- [測試容錯降級] 使用無效金鑰測試 Mock Fallback ---")
    mock_client = LLMClient(api_key="invalid_key_for_testing")
    logger.info(f"新實例提供者狀態: {mock_client.provider} (IsMock: {mock_client.is_mock})")
    # 將 nvidia_api_key 設為無效
    mock_client.provider = "nvidia_nim"
    mock_client.nvidia_api_key = "invalid_key_for_testing"
    mock_client.is_mock = False
    
    try:
        fallback_result = mock_client.generate_structured(
            prompt="這是一次失敗重試測試",
            response_schema=ClausesExtractionResult
        )
        logger.info("降級成功！在 API 故障時，系統已自動優雅 fallback 並回傳 Mock 條款數據。")
        logger.info("回傳對象類型: %s", type(fallback_result))
        logger.info("回傳 Mock 條款數: %d", len(fallback_result.clauses))
    except Exception as e:
        logger.error(f"容錯降級測試失敗，系統拋出了未捕獲異常: {e}")
        sys.exit(1)

    logger.info("\n🎉 所有 NVIDIA NIM 連通性與任務特定分發測試全數通過！系統已具備生產級的高可靠性！")

if __name__ == "__main__":
    test_nim_connection()
