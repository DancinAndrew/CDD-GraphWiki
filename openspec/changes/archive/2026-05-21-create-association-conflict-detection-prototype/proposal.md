# Phase 5: Association & Conflict Detection Prototype Proposal

## Why

在反洗錢/客戶盡職調查 (AML/CDD) 框架下，法規條文與內部合規政策對關鍵概念常有不同的同義別名表述（例如 "UBO"、"beneficial owner"、"controlling party"）。這容易導致下游的規則匹配或檢索產生遺漏，亟需同義詞同名化 (Alias Deduplication) 解析能力。

此外，不同管轄區的監管規定（如 FATF 建議與 MAS Notice 626）以及銀行內部的 CDD 政策，在針對同一風險場景時常存在實質性衝突。這些衝突包括數值閾值衝突（例如 UBO 判定門檻 10% vs 25%、偶發交易 SGD 20,000 vs USD 15,000）或政策限制衝突（例如 PEP 許可 EDD 對比特定高風險地區 PEP 禁止 Onboard）。為了提升系統合規推理的透明度，本階段旨在實作一套自動化同義別名映射與合規衝突偵測引擎原型。

## What Changes

1. **合約數據模型擴充**：
   在 `src/contracts/models.py` 中新增 `Concept` 的強型別強校驗 Pydantic 模型，滿足 CDD 5.2 合約規範。
2. **同義詞同名化模組**：
   實作 `src/association/concept_mapper.py`，實現對 aliases 的 canonical mapping，統一映射至標稱概念。
3. **衝突自動偵測引擎**：
   實作 `src/association/conflict_detector.py`，載入 Obligations 動態分析其屬性特徵，自動檢出金標中定義的 3 大合規衝突，並輸出 clause-level 溯源的 `Conflict` 實體。
4. **自動化測試套件**：
   建立 `tests/test_association_conflict.py` 單元測試，確保 Concept 映射與 Conflict 自動偵測的 100% 準確率。

## Capabilities

- **別名同名化 (Alias Deduplication)**：將同義表述準確對齊至 canonical 概念實體，保留 source references。
- **數值衝突自動偵測 (Numerical Conflict Detection)**：能自動比對 Obligation 中的 conditions 閾值，檢出不一致的數值型衝突並建檔。
- **政策反轉/禁止衝突自動偵測 (Policy Reversal Conflict Detection)**：自動比對 PEP EDD 授權與 PEP Prohibition 限制的政策邏輯衝突。
- **強型別衝突建檔**：產出 100% 通過 JSON Schema 驗證的 `data/processed/conflicts.yaml` 數據。

## Impact

- 確保 Phase 5 進度能完全滿足 `openspec validate` 與專案測試指標要求。
- 為 Phase 6: CDD Checklist Reasoning Engine 的動態衝突加載與 canonical checklist 生成提供堅實的數據基礎。
