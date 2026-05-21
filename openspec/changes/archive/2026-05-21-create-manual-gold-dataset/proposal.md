## Why

在合規知識編譯與推理系統中，我們不能依賴未經校驗的自動化生成數據來評估系統效能。為了避免垃圾進垃圾出（Garbage in, Garbage out），我們必須在實作自動化 Pipeline 之前，先由人工精準對齊法規條款、義務規則以及客戶風險畫像的正確決策輸出。
此黃金數據集將作為系統的「北極星」，定義了系統在完美狀態下應該產出的結構化數據，是進行持續整合（CI）與合規迴歸測試的絕對基礎。

## What Changes

*   **新增黃金數據目錄**：在專案根目錄下建立 `data/gold/` 存放人工編譯的結構化合規數據（YAML 格式），並在 `data/gold/concepts/` 中撰寫 Markdown 百科概念頁面。
*   **人工編譯合規對象**：
    *   **SourceDocument**：手動編譯 3 份源文件元數據（FATF Recommendation 10、MAS Notice 626 以及 1 份模擬的內部合規政策）。
    *   **Clause**：手動對前述源文件進行段落切分，建立至少 10 個核心法規條款。
    *   **Obligation**：從條款中抽取出至少 10 個機器可讀的合規義務規則，並保留條款級的雙向溯源連結（`source_clause_ids`）。
    *   **Conflict**：編寫至少 3 個法規與政策之間的時間性、特異性或流程衝突實例（例如：模擬政策與 MAS 626 的審查頻率衝突）。
    *   **CustomerContext**：手動編寫至少 5 個測試客戶情境（法人、個人、高風險國家、複雜多層股權與 PEP）。
    *   **CDDChecklist**：針對這 5 個客戶情境，手動演算出預期的 CDD 決策與文檔檢核表 Ground Truth 輸出。
*   **建立自動化校驗**：在 `tests/test_gold_dataset.py` 中實作自動化單元測試，對所有 YAML 檔案進行資料合約驗證與雙向關係完整性校驗。

## Capabilities

### New Capabilities
- `manual-gold-dataset`: 提供 CDD-GraphWiki 的人工黃金數據集 Ground Truth，作為衡量自動化合規推理系統正確性與置信度的核心基準。

### Modified Capabilities
<!-- 本階段沒有修改現有的 spec 需求行為 -->

## Impact

*   **系統無破壞性影響**：本變更僅新增靜態 YAML 數據集、Markdown 百科頁面與單元測試，不影響 `src/contracts/models.py` 的結構。
*   **解鎖後續 Pipeline 階段**：本階段產出的黃金數據將直接作為 Phase 3 (Source Parser) 的比對基準，以及 Phase 4 (Graph Engine) 的圖譜導入實體。
