## Context

在 Phase 1 (資料合約) 中，我們已實作了符合 ADR-0004 (混合元模型) 的強型別 Pydantic 模型與導出的 JSON Schema。
目前專案急需建立一套高品質的「人工黃金數據集 (Manual Gold Dataset)」來作為合規推理的 Ground Truth。為了使人工編譯更為直觀、好維護，我們必須設計一套靜態 YAML 數據結構、Markdown 百科目錄，並配合嚴格的單元測試，在編譯器與測試層面自動校驗資料合約與外鍵關係完整性。

## Goals / Non-Goals

**Goals:**
*   在 `data/gold/` 下手動編譯 3 份源文件、至少 10 個核心條款、10 個合規義務、3 個法規衝突、5 個客戶畫像與 5 個預期 CDD 決策檢核表。
*   在 `data/gold/concepts/` 下建立 5 個核心 Wiki 百科 Markdown 概念頁面（UBO、PEP、EDD、CDD、SOFW）。
*   在 `tests/test_gold_dataset.py` 中實現雙層校驗（Pydantic 合約解封裝驗證 + 關係完整性外鍵校驗）。

**Non-Goals:**
*   實作自動化解析 PDF 的代碼（這是 Phase 3 的工作）。
*   實作圖引擎與推理算法（這是 Phase 4 的工作）。
*   實作 Web UI 或 CLI 界面（這是後續 Phase 的工作）。

## Decisions

### Decision: YAML 格式作為結構化數據存儲
為了兼顧人工編寫的便利性、可讀性，我們選擇 YAML 作為結構化數據的儲存格式，而不是 JSON。
*   **理由**：YAML 支援行內註釋，這能讓我們在手動編譯條款與義務時，隨時加上解釋性背景。同時，YAML 對多行文本（如法規原始文字 `raw_text`）的支援比 JSON 更佳。
*   **替代方案**：JSON (缺乏註釋、多行文字格式繁瑣，不便人工維護)。

### Decision: Pydantic 物件雙層驗證與關係校驗
在 `tests/test_gold_dataset.py` 中，載入 YAML 檔案後，直接利用 Phase 1 建立好的 Pydantic 模型進行解封裝，並實作外鍵參考完整性檢查。
*   **理由**：我們引進了 `Literal` 枚舉約束，使用 Pydantic 載入能自動校驗枚舉合法性。此外，必須確保所有 `source_clause_ids`、`customer_id` 等指向的實體在全局是存在的，防止出現「懸空參考 (Dangling References)」，保證數據集是閉環且邏輯無缺陷的。
*   **替代方案**：僅使用 `jsonschema` 進行靜態驗證 (無法方便地進行外鍵完整性與圖譜關係深度校驗)。

## Risks / Trade-offs

*   **[Risk] 人工編寫錯誤** $\to$ [Mitigation] 在 CI 中加入 `pytest tests/test_gold_dataset.py`，一旦有人工漏填、型別錯誤或外鍵指向不合法，測試會立刻失敗，攔截不合規變更。
*   **[Risk] 百科概念頁面無結構化合約限制** $\to$ [Mitigation] 將概念百科頁面定位為人可讀的 Wiki Markdown 文件，儲存於獨立目錄 `data/gold/concepts/` 中，以保持最大靈活性，只對結構化對象實施強合約。
