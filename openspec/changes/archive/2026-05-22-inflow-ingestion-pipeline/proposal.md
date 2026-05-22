# Proposal: 真實法規 Inflow Ingestion Pipeline (真實法規導入管線)

本提案旨在 CDD-GraphWiki 系統中建立一個產品級的**真實法規 Inflow Ingestion Pipeline (法規導入管線)**，利用大語言模型 (LLM) 的強推理與結構化輸出能力，實現將真實的 PDF 格式法規（如完整的 *MAS Notice 626* 或是 *FATF 40條建議* 等）自動化解析、段落層級切割、語意識別，並高精度抽取為強型別的 `Clause` (條款) 與 `Obligation` (合規義務) 模型，從而徹底取代目前靜態手動編寫的金標數據集。

---

## 1. 動機與背景 (Motivation)

在第一階段和第二階段的開發中，我們成功建立了一個合規決策工作台，包含了 D3.js 力導向關係圖譜、Checklist 案件審查及鏈式防篡改審計日誌。然而，目前系統所依賴的法規知識庫（包含 `SourceDocument`、`Clause` 與 `Obligation` 節點）均是透過人工手動撰寫或基於正則表達式的靜態規則提取出來的「黃金數據集 MVP」（例如寫死特定 Clause ID 與正則特徵）。

這在真實的生產環境中面臨以下致命瓶頸：
* **擴展性低下**：若引入新的法規（如 MAS 的其他指引或新加坡以外的 CDD 規定），合規官必須手動對齊並編寫正則特徵，難以規模化。
* **PDF 格式處理困難**：法規文件多數以雙欄、包含頁首頁尾、目錄與腳註的 PDF 格式發布，傳統正則切片器無法正確解析層級樹狀關係。
* **合規語意缺失**：單純靠正則無法精準識別複雜的「事實觸發條件 (Conditions)」、「豁免例外 (Exceptions)」與「所需合規證據 (Required Evidence)」，這些必須依賴強推理 LLM 的法律語意識別。

因此，實作一個端到端的自動化 PDF 導入管道，將法規原文點石成金為「條款級溯源圖譜」，是邁向真實 AML 合規決策引擎的關鍵里程碑。

---

## 2. 系統能力 (Capabilities)

本變更將引入以下核心 kebab-case 系統能力：

* **`pdf-text-extraction`**：系統應具備解析上傳 PDF 的能力，能夠處理多頁 PDF、去除頁首頁尾與頁碼雜訊，保留完整的段落文字。
* **`llm-hierarchical-chunking`**：系統應利用 LLM 對提取的法規文字進行智能段落切割，將其階層化地解析為樹狀的 `Clause` 節點，並保留精確的章節引用（`section_ref`，如 `Section 6 > Paragraph 6.2 > (a) > (i)`）。
* **`llm-obligation-extraction`**：系統應使用 LLM 進行**強型別結構化輸出 (Structured Outputs)**，自動化精確提取每個 `Clause` 所隱含的 `Obligation` 實體，填補其 `actor`, `action`, `object`, `conditions`, `exceptions`, `required_evidence` 等關鍵欄位，並保證其 Clause-level 條款級溯源關聯。
* **`dashboard-ingest-ui`**：在合規官 Web Dashboard 前端提供直觀的「法規 PDF 導入面板」，允許合規官拖曳上傳 PDF，即時監控導入進度，並在導入完成後，將全新解析的法規點與邊實時動態追加載入至 D3.js 力導向圖譜中。

---

## 3. 影響範圍 (Impact)

* **數據儲存層**：
  * 原先的靜態 `data/sources/` 和 `data/processed/` 將做為 Ingestion 管道的起點或自動生成產物。系統圖譜將由原來的 67 點、74 邊，隨著新法規 PDF 的導入，動態增長並即時寫入圖譜資料結構中。
* **後端 API 服務 (`src/api/`)**：
  * 新增 PDF 檔案上傳與導入 Pipeline 觸發的 Endpoint：`/api/v1/ingest/pdf`。
  * 導入處理應採用非同步背景任務（FastAPI `BackgroundTasks`），避免長時間的 LLM 呼叫阻塞 API 主線程。
* **前端介面 (`frontend/`)**：
  * 前端新增一個法規導入面板，展示導入進度日誌，並在成功後自動刷新 D3 圖譜。
* **依賴套件 (Dependencies)**：
  * 需要引入輕量級、純 Python 的 PDF 提取套件 `pypdf>=4.0.0`。
  * 引入與大語言模型互動的客戶端套件（如 `google-genai` 或 `openai`），或直接使用環境變數配合標準 `httpx` 異步發送 POST 請求，保證輕量化。

---

## 4. 變更範圍 (What Changes)

1. **新建 PDF 導入解析器**：在 `src/ingestion/` 下新增基於純 Python 的 PDF 文本提取模組與 LLM 切片器。
2. **新建 LLM 結構化抽取引擎**：在 `src/extraction/` 下新增對接 LLM 結構化輸出（JSON Mode / Pydantic Structured Outputs）的義務提取器，取代原有的 rule-based 邏輯。
3. **擴展後端 API**：在 `src/api/` 新增上傳與非同步執行 Pipeline 的 API 路由。
4. **前端 UI 整合**：在 React Dashboard 中實作 Ingestion 控制台，與 D3 圖譜熱插拔式結合。
