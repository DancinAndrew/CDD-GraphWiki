# Phase 7: Explainable Reasoner and Provenance Engine Proposal

## Why

在反洗錢與客戶盡職調查 (AML/CDD) 合規審查中，合規判定與檢核表要求（例如：要求提供 Source of Funds、或者要求 Senior Management 審批）有著極高的嚴謹度與可審計性要求。

如果系統僅提供一個「黑盒」的 CDD 檢核清單，而無法向合規官員及金融審計人員清晰解釋「**為什麼這個客戶必須配備此項佐證文件**」或「**這個決策分級是如何依據具體客戶特徵與哪些法理條文推理出來的**」，這將無法獲得法規監管與業務部門的信任。

可解釋性與溯源引擎（Explainable Reasoner and Provenance Engine）旨在解決這個信任難題。藉由回溯鏈結 `CustomerContext`、`Obligation`、`Clause` 與 `SourceDocument` 的多維度關聯，自動為每一個決策與文件要求編譯出條款級雙向溯源（Clause-level Provenance）的結構化「合規解釋鏈」（Explanation Path），讓任何一項合規要求都有理有據、100% 可追溯。

## What Changes

1. **強型別解釋合約模型擴充**：
   在 `src/contracts/models.py` 中新增 `ProvenanceNode` 與 `ExplanationPath` 的強型別 Pydantic 資料合約。執行編譯腳本自動產出對應的 JSON Schema 契約，以保障資料傳輸的安全與高嚴謹性。
2. **實作合規解釋與溯源引擎**：
   在 `src/decision/provenance.py` 中實作 `ProvenanceEngine` 核心類。其核心方法能夠接受一個生成的 `CDDChecklist`，自動回溯關聯的 `CustomerContext` 屬性特徵、匹配適用義務、引述 `Clause` 原始文字明文與關聯 `SourceDocument` 元數據，組裝成強型別的樹狀「合規解釋鏈」。
3. **可追溯性審計軌跡報告生成 (Audit Trail Report)**：
   在 `ProvenanceEngine` 中實作 Markdown / YAML 格式的審計報告生成功能，能為合規人員自動產出條款級溯源清晰的人類可讀審計證明文件。
4. **自動化單元測試**：
   建立 `tests/test_explainable_provenance.py` 測試套件，針對 5 大經典客戶情境的解釋路徑進行精準度驗證，確保 citations 忠實度與 provenance 的無縫閉環。

## Capabilities

- **一鍵式決策溯源 (One-click Decision Provenance)**：針對 CDDChecklist 中的任何 required_documents 或 risk_triggers，能自動精確匹配並追溯至引發它的 customer 屬性、觸發 obligation 與對應的法源條款。
- **忠實的法理引述 (Faithful Legal Snippet Citations)**：自動引述 `Clause` 中 normalized_text 的原始法規文字明文，保證解釋的權威性與忠實度，杜絕 LLM 幻覺。
- **強型別審計系譜 (Structured Audit Trail & Lineage)**：支持輸出符合 Schema 約束的解釋鏈資料結構，能被 wiki 與 graph 元件直接讀取以進行可視化。

## Impact

- 標誌著 CDD-GraphWiki 專案從前面的「規則推理」向「可審計、高透明度、解釋有理有據的智慧型合規推理系統」的重大躍升。
- 為後續的 Regulatory Graph 視覺化查詢與 wiki 概念頁面提供底層溯源系譜的支持。
