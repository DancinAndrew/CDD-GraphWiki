# 設計說明書：對接 NVIDIA NIM 平台模型與多模型任務配置 (nvidia-nim-integration)

本文件描述了 CDD-GraphWiki 對接 NVIDIA NIM 平台大語言模型 API 的技術設計，包含環境變數配置、多模型任務規劃、API 呼叫與結構化 JSON 解析架構，以及與現行系統的整合方式。

---

## 1. 深度面試對齊之核心決策設計 (/grill-me 共識)

> [!IMPORTANT]
> 本小節記錄了與使用者進行 `/grill-me` 深度面試後達成的核心技術設計決策共識：
>
> 1. **NVIDIA NIM API 的 JSON Schema 強約束策略**：
>    - **共識決策**：**混合約束策略**。在調用 API 時，我們不僅會在參數中啟用 `response_format={"type": "json_object"}` 模式，還會自動在 Prompt/System Instruction 中將 Pydantic 結構轉化為明確的 JSON Schema 注入，雙重保障欄位 100% 匹配。
> 2. **模型錯誤降級與 Mock Fallback 邏輯**：
>    - **共識決策**：**雙層容錯**。首層進行最多 3 次的指數退避重試（應對短暫的網路超時或波動），如果重試全部失敗，再優雅降級回 Mock 模式並寫入詳細錯誤日誌，保障合規 Pipeline 整體流程不中斷。
> 3. **多任務模型適配規劃**：
>    - **共識決策**：**預設混合配置，並支援環境變數自訂**。
>      - **智慧切片** 預設配置：`meta/llama-3.3-70b-instruct` (在長文本理解與層次梳理上表現優秀)。
>      - **義務抽取** 預設配置：`deepseek-ai/deepseek-r1` (具備極強思維鏈推理能力，完美演繹複雜合規義務條件與例外)。
>      - 系統將完全依循 `.env` 中的 `NIM_CHUNKER_MODEL` 與 `NIM_EXTRACTOR_MODEL` 配置，支援無縫切換。

---

## 2. NVIDIA NIM 平台模型任務選型規劃

根據對 CDD-GraphWiki 合規導入任務特性的評估與對 NVIDIA NIM 上可用模型的分析，我們為不同子任務規劃了以下模型配置：

### 2.1 任務一：LLMHierarchicalChunker (智慧切片)
- **任務特性**：
  - 需要在長文本中精確找出法律條文之間的樹狀階層結構（父子條款關係）。
  - 需要對條款編號、層級序列（如 `Section 6.1 -> 6.1(a) -> 6.1(a)(i)`）進行邏輯歸納與層次化排序。
  - 需要較大的上下文窗口，以保證打包導入時不遺失長程相依上下文。
- **配置模型**：**`meta/llama-3.3-70b-instruct`**（推薦首選）
- **選型理由**：Llama-3.3-70B 具有 128K 的強大上下文窗口，且在複雜推理、邏輯劃分與長文本歸納方面極為優異，能穩定梳理法規的深層層級結構。

### 2.2 任務二：LLMStructuredExtractor (強型別義務抽取)
- **任務特性**：
  - 需要高精度的強型別 Schema 遵循（必須回傳符合 Pydantic 定義的 JSON 結構）。
  - 需要 100% 準確抓取 `source_clause_ids` 以維持條款級溯源（Clause-level Provenance）。
  - 需要對 actor、action、object、applies_to、conditions、exceptions 等多個合規維度進行極度細緻的語義提煉。
- **配置模型**：**`deepseek-ai/deepseek-r1`**（推薦首選）
- **選型理由**：DeepSeek-R1 具備卓越的推理（COT）能力，對於合規義務中極其複雜的「觸發事實（conditions）」與「豁免條件（exceptions）」能夠進行精準的演繹推理與提煉。

---

## 3. 技術架構與實現細節

### 3.1 安全憑證與環境變數管理 (.env)
我們將在專案根目錄下建立 `.env` 檔案（該檔案已被列入 `.gitignore`，防止憑證洩漏），包含以下配置：
```bash
# NVIDIA NIM API 密鑰
NVIDIA_API_KEY=your_nvidia_api_key_placeholder

# 子任務一：智慧切片模型配置
NIM_CHUNKER_MODEL=meta/llama-3.3-70b-instruct

# 子任務二：義務抽取模型配置
NIM_EXTRACTOR_MODEL=deepseek-ai/deepseek-r1

# API 基本 URL (NVIDIA NIM 平台標準)
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 3.2 NVIDIA NIM API 連接層 (LLMClient 擴展)
我們將修改 `src/extraction/llm_client.py`，主要改動如下：
1. **載入 dotenv**：使用標準 `os.getenv` 載入上述配置，並保留原有 `GEMINI` 變數以維持雙引擎相容性。
2. **優先級調度**：
   - 當檢測到 `NVIDIA_API_KEY` 時，`LLMClient` 底層採用 `httpx` 來對接 NVIDIA NIM 平台。
   - 當未檢測到 `NVIDIA_API_KEY` 但有 `GEMINI_API_KEY` 時，使用 Gemini 引擎。
   - 兩者皆無或呼叫失敗時，優雅降級至離線 Mock 模式。
3. **OpenAI-Compatible 呼叫封裝**：
   - 由於 NVIDIA NIM 平台提供標準的 OpenAI-Compatible Chat Completions API。我們將使用現有的 `httpx` 發送 POST 請求至 `{NIM_BASE_URL}/chat/completions`。
   - 封裝請求時，若存在 `response_schema`，我們將藉由 Prompt 引導，並在請求中設定 `response_format={"type": "json_object"}`（如果模型支援）來強制要求結構化回傳。
   - 接收到 API 響應後，利用 Pydantic 模型的 `model_validate_json` 方法進行嚴格的型別校驗與轉換。

```python
# httpx 調用偽代碼範例
headers = {
    "Authorization": f"Bearer {self.nvidia_api_key}",
    "Content-Type": "application/json"
}
payload = {
    "model": model_name,
    "messages": [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.1,
    "response_format": {"type": "json_object"}
}
response = httpx.post(f"{self.nim_base_url}/chat/completions", json=payload, headers=headers)
```

---

## 4. 變更檔案列表 (What Will Change)

- `[NEW]` [test_nim_connection.py](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/scripts/test_nim_connection.py) —— 驗證 NVIDIA NIM API 連通性與 JSON 輸出的測試腳本。
- `[NEW]` [demo_ingestion_nim.py](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/demo_ingestion_nim.py) —— 供使用者跑一次真實使用流程的實作演示入口。
- `[MODIFY]` [llm_client.py](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/src/extraction/llm_client.py) —— 擴展 `LLMClient` 整合 NVIDIA NIM API，提供多模型分發。
- `[MODIFY]` [llm_extractor.py](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/src/extraction/llm_extractor.py) —— 讓 Chunker 和 Extractor 能動態從 `LLMClient` 獲取個別指定的 NIM 模型名稱。
- `[MODIFY]` [.env](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/.env) —— 建立環境配置，寫入 API key。

---

## 5. 驗證與測試策略

### 5.1 自動化驗證
- **連通性驗證**：運行 `scripts/test_nim_connection.py`，確保能夠與 NVIDIA NIM 平台順暢通訊，並且成功獲得強型別的 JSON 物件。
- **單元測試**：運行 `pytest tests/test_extraction.py`，確認在 mock 模式下功能不受影響，且在真實 NVIDIA 憑證下單元測試通過。
- **OpenSpec 校驗**：運行 `openspec validate nvidia-nim-integration --strict --no-interactive`，必須保證輸出為 valid。

### 5.2 手動驗證流程
- 運行 `python demo_ingestion_nim.py`。
- 該腳本將會：
  1. 載入位於 `.env` 的真實 NVIDIA NIM 憑證。
  2. 讀取 `data/sources/mas_notice_626.md` 的一部分實體文字（或測試文字）。
  3. 呼叫 `meta/llama-3.3-70b-instruct` 進行樹狀條款分割（第一階段）。
  4. 呼叫模型進行合規義務結構化提取，並產出強型別 Obligation 對象（第二階段）。
  5. 打印產出的 Clause 與 Obligation 成果，並展示 Clause-level Provenance (條款溯源 ID) 的完整鏈路。
