# Phase 6: CDD Checklist Reasoning Engine Proposal

## Why

在反洗錢/客戶盡職調查 (AML/CDD) 合規審查中，將結構化客戶情境 (CustomerContext) 轉譯為最終可被合規官員與審計官員所信任的「客戶盡職調查檢核表」 (CDDChecklist) 是整個知識編譯項目的核心終局目標。

如果系統缺乏一個能夠載入 Obligations 與 Conflicts 並針對 CustomerContext 進行防禦性推理的決策引擎，下游的合規控管將無從依循，也無法量化地評估合規推理品質。本階段旨在實作一套自動化且精準的 `CDDChecklistEngine` 推理決策引擎原型，藉由精確的合規特徵推理與紅線控管，產出 100% 條款級溯源（Clause-level Provenance）、含風險觸發點與必備佐證文件清單的強型別合規決策檢核表，並與金標 expected checklists 完美對齊。

## What Changes

1. **實作 CDD 檢核與推理引擎核心**：
   在 `src/decision/engine.py` 中實作 `CDDChecklistEngine` 決策推理核心類，負責輸入客戶情境，依據合規規則對其進行分級、判定風險觸發點、比對適用義務與衝突，以及產出必備合規佐證文件清單。
2. **黃金數據比對評測工具**：
   在決策引擎中實作自動化比對與評鑑方法，將自動推理產出的 CDDChecklists 與 `data/gold/checklists.yaml` 的 Ground Truth 進行全面欄位級比對，計算並輸出 Precision, Recall 與 F1-score 指標。
3. **自動化測試套件**：
   建立 `tests/test_cdd_reasoning.py` 單元測試，針對 5 大經典客戶情境進行全面覆蓋驗證，確保引擎決策與金標 exact match。

## Capabilities

- **CDD 階層自動化分級 (Simplified / Standard / Enhanced CDD)**：根據客戶背景、地理、股權層級與 PEP 曝險特徵，進行精準分級。
- **動態合規證據包裝 (Dynamic Evidence Requirements)**：針對 Corporate、PEP 與高風險禁止 onboard 客戶，自動配備對應的「必備合規佐證/證據文件清單」。
- **風險紅線自動識別與觸發 (Risk Triggers & Action Controls)**：能動態輸出 `internal_ubo_threshold_triggered_10_percent`、`pep_from_high_risk_jurisdiction`、`onboarding_prohibited_by_policy` 等精細風險標記。
- **條款級溯源鏈結閉環 (Closed-loop Clause Citations)**：自動收集適用 obligations 對應的 raw clauses 人工友好引用，建立封閉的 Provenance Citations 鏈結。

## Impact

- 標誌著 CDD-GraphWiki 專案從前面的「合規知識編譯與衝突判定」正式進入「合規推理與可執行邏輯決策」的終局應用展示階段。
- 順利解鎖與黃金 expected checklists 的 perfect alignment。
