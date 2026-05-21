# [論文筆記] Legal Requirements Translation from Law

> **文獻簡稱**：[Singhal 25]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)、第 4 層 (Rule Verification / Defeasible Logic Engine)  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 3 (Ingestion), Phase 4 (Obligation Extraction), Phase 7 (Compliance Reasoning), Phase 8 (Verification Framework)

---

## 1. 論文基本資訊
- **標題**：Legal Requirements Translation from Law (從法律中進行法律需求的代碼翻譯)
- **作者**：Anmol Singhal, Travis Breaux (卡內基梅隆大學 Carnegie Mellon University)
- **年份/發表管道**：2025 年發表於 IEEE International Requirements Engineering Conference (RE 2025)
- **程式庫與數據庫**：[https://doi.org/10.5281/zenodo.15794182](https://doi.org/10.5281/zenodo.15794182)

---

## 2. 核心研究命題與方法

### 2.1 解決的核心問題
軟體系統必須遵守司法管轄區的法律法規，但這對於缺乏專職法務的小型企業和新創公司來說是極大的資源消耗。自動化法律合規的第一步是從法規中提取結構化和語義元數據，然而由於法律文本的冗長和複雜性，這是一項極其繁瑣的任務。
過去的方法存在兩大局限：
1. **遺失關聯性**：將結構與語義元數據割裂開來獨立抽取（例如單獨抽取義務或條款），未能保留條款間的層次結構、嵌套關係及交叉引用（如 A 條款的豁免受制於 B 條款）。
2. **泛化力極差**：依賴人工手動標記或基於啟發式規則（Heuristics）的機器學習，難以推廣至未見過的新法規。

### 2.2 系統架構與核心技術
本論文提出了一種基於**文本蘊含（Textual Entailment）**與**上下文學習（In-Context Learning, ICL）**的自動化方法，將法律文本自動翻譯成**可運作、可執行的中間表示（Canonical Representation），並以實例化 Python 代碼形式呈現**。

系統包含三個核心步驟：
1. **領域特定元模型設計（Domain Metamodel Design）**：
   人工設計一組 Python 類（Class）結構來表示法律元數據，保留條款的層次結構（Sections, Subsections）、語義義務（Rules, Definitions, Exemptions）以及它們之間的依賴關係邊（Relationships，如精確化 refines、例外 exception、先行 follows 等）。
2. **演示選擇策略（Demonstration Selection Strategy）**：
   由於法律翻譯高度依賴上下文，本論文設計了「兩階段範例檢索」：
   - **第一階段（Zero-shot Tagging）**：利用零樣本提示詞，讓 LLM 先為待處理的段落分配語義標籤（例如 `#definition`, `#obligation`, `#exception`）。
   - **第二階段（Hybrid Similarity Retrieval）**：計算測試段落標籤與開發集（150 個已手動翻譯為 Python 代碼的黃金段落）標籤的交集得分（匹配一個標籤加 1 分），並結合 `text-embedding-3-large` 計算文本餘弦相似度，最終檢索出 3 個最優 Few-shot 演示（Demonstrations）。
3. **結構化代碼生成（Code-gen Prompting）**：
   將 Python 元模型宣告與檢索出的 3 個 Few-shot 演示作為 Context 傳入 GPT-4o，生成目標條款的實例化 Python 代碼。隨後通過 Python 解譯器進行語法檢驗，並進行結構序列化。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據
評估基於美國 13 個州的個人數據洩露通知法（共 332 個法律段落），其中 150 段做開發，182 段做盲測：
- **代碼編譯通過率 (Compilation Test)**：在測試集上達到 **99.2%** 的極高成功率，證明 LLM 在強大元模型類的引導下，生成符合語意語法的可執行代碼能力極其穩定。
- **整體結構準確性 (Structural Test Accuracy)**：達到 **82.0%**，確認生成的類實例符合元模型最小要求。
- **語義準確性 (Semantic Test Accuracy)**：達到 **89.4%**（經清洗 stop-words 與標點符號的 Exact Match）。
- **屬性級別精準率與召回率 (Attribute Precision & Recall)**：在未見過的測試集上，達到 **82.2% Precision** 與 **88.7% Recall**。
- **Pass@k 指標（Pass@3）**：對於極其嚴苛的「整段 22 個單元測試必須全部通過才算成功」的評估，在 $k=3$（生成 3 次候選）時，達到了 **62.1% 的 Pass@3 得分**，顯著超越基線。

### 3.2 不同方案之對比 (Table II)
- **JSON 提取基線 (Text-gen JSON baseline)**：
  如果讓 LLM 直接按照 JSON Schema 提取屬性（這也是目前最常用的 RAG 方案），其 **Semantic Accuracy 僅為 54.2%**，**Pass@3 僅有 31.2%**。
- **元模型代碼翻譯 (Code-gen + Class + Demo)**：
  通過 Python class 的強約束，將 **Semantic Accuracy 提升至 89.4%**，**Pass@3 提升至 62.1%**（整整提升了約 **30% 的絕對百分點**）。
- **消融實驗 (Ablation Studies)**：
  - `Code-gen + Class` (移除檢索策略，改為隨機挑選 Few-shot 範例)：Pass@3 降至 **38.0%**。
  - `Code-gen + Demo` (移除元模型 Class 定義，僅憑範例生成)：Pass@3 降至 **42.1%**，且 Compilation Rate 降至 **85.7%**。
  - 結論：**元模型 Class 聲明的硬性語意約束**與**基於語意標籤的演示檢索策略**缺一不可，對提升 LLM 代碼生成的精確性具有最高的邊際效益。

### 3.3 屬性層面的效能差異與瓶頸分析 (Table III)
- **高準確率屬性**：
  - `Definition term`（定義詞）：Accuracy 97.6%, Precision 100%, Recall 93.4%
  - `Definition meaning`（定義含義）：Accuracy 95.2%, Precision 100%, Recall 92.8%
  - 結論：實體與術語定義具有固定的法規 drafting 結構（如 "...means..."），極易被 LLM 完美捕獲。
- **低準確率屬性 (合規推理瓶頸)**：
  - `Exemption`（豁免條款）：Accuracy 85.9%, Precision 37.5%, Recall 37.5%
  - `References`（法規參照）：Accuracy 74.8%, Precision 58.3%, Recall 100%（召回率高，但精準率低，容易產生過度提取）
  - `Relationship type`（關係類型，如 follows, refines）：Precision 33.1%, Recall 45.8%
  - 結論：**法律條文中的「豁免例外」和「多跳嵌套引用的關係判斷」是目前 Legal LLM 的重大錯誤源頭**，必須依靠後端符號引擎或人機協作進行校對與修補。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 領域特定元模型設計 (UML Schema)
論文將法規條文拆解為以下 Python Class：
- `Section`：代表法律層次結構（例如 `Section("14-3504")` 內含 `Section("(d)")` 再內含 `Section("(1)")`）。
- `Expression`：表示最基礎的文本片段（ smallest textual unit），用於追溯精確文字。
- `Statement`：語義聲明的基類，可跨越多個巢狀段落。
- `Rule`：繼承自 `Statement`，包含 `rule_type`（可為 `Rule.OBLIGATION` 義務, `Rule.PERMISSION` 許可, `Rule.PROHIBITION` 禁止）、`entity`（主體實體）、`description`（規則行為）以及 `conditions`（條件 Expression 列表）。
- `Definition`：用於定義法律術語，包含 `defined_term`（被定義術語）、`meaning`（定義含義列表）和 `exclusions`（排除適用列表）。
- `Exemption`：繼承自 `Statement`，代表豁免規則。
- `Reference`：表示跨條款參照，並標註指向的 target (另一個 `Expression` 或 `Statement`) 及 `relationship`（關係類型）。

```
Section ────> subSections[*]
   │
   ├─> expressions[*] ────> text: str
   └─> statements[*]  ────> Statement (Base)
                              │
             ┌────────────────┴───────────────┐
             ▼                                ▼
           Rule                           Definition
             ├─> rule_type (Int)             ├─> defined_term
             ├─> entity                      ├─> meaning[*]
             ├─> description                 └─> exclusions[*]
             └─> conditions[*]
```

### 4.2 基於 conformance 檢測的單元測試設計
論文提出了一種評估結構化表示的新方法：**不運行代碼邏輯，而是利用 unit testing 框架對生成的對象圖（Object Graph）與黃金標準進行 conformance 比對**：
- **Compilation Test (1 個)**：代碼是否無錯運行並實例化。
- **Structural Tests (5 個)**：檢查生成類是否具有規定的最小屬性（例如 Definition 必須被給予定義詞）。
- **Semantic Tests (16 個)**：經由字串正則化（ lowercase, 移除 stop-words 如 means、if）後，進行對象屬性值的 Exact Match。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 1 層 (Knowledge Compilation / LLM Wiki)**：
  我們不能只把 AML 法規（例如 FATF Rec 10, MAS 626）作為文本塊進行向量檢索，而應該採用本論文的 **Metamodel（元模型）代碼實例** 作為我們的**中間表示法 (Canonical Intermediate Representation, CIR)**。
- **第 2 層 (Regulatory KG)**：
  Python 類結構中的 `Reference` 對象以及 `refines`, `exception`, `follows` 關係類型，直接為我們的合規知識圖譜中的**關係邊（Edges）**定義了本體架構（Ontology Schema）。
- **第 4 層 (Rule Verification / Defeasible Logic Engine)**：
  `Rule` 類包含 `rule_type: OBLIGATION / PERMISSION / PROHIBITION`，這直接對應我們 CDD 決策規則引擎中的可執行斷言。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **中間表示法代碼約束提示 (Code-gen Constraints)**：
   提示詞中加入硬性 Python Class 定義。實驗證明，**程式碼的語法嚴謹度能大幅減少 LLM 的幻覺與胡言亂語（Compilation Rate 達 99.2%）**，遠優於鬆散的 JSON。
2. **兩階段 Few-shot 演示檢索**：
   我們應實作「Tag-based score + Dense embedding cosine similarity」的範例挑選器。在處理某個 AML 條款（例如「對政治曝露人物 (PEP) 的加強盡職調查 (EDD) 義務」）時，系統能自動匹配具有相同 `#EDD_obligation` 標籤且語意相似的黃金代碼範例。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **警惕關係（Relationships）和豁免（Exemptions）的 LLM 生成錯誤**：
   - *論文數據警告*：關係類型的 Precision 僅 33.1%，Exemption 的 Precision 僅 37.5%。
   - *我們的改進*：**CDD-GraphWiki 在處理複雜的豁免邏輯（如「若客戶為政府機構，則免除識別受益人義務」）與多跳參照時，不能完全信任 LLM 的直出代碼**。系統必須建立一個**人機協作審核界面 (Human-in-the-loop Wiki)**，將這些低精準度屬性特別標紅，交由合規專家進行人工校對和確認。
2. **AML/CDD 領域特化元模型（AML-Metamodel）**：
   - 論文的元模型是基於資料洩露通知法。我們需要將其特化為 CDD/KYC 領域模型：
     - 在 `Rule` 的 `conditions` 中，增加實體類型（如 `NaturalPerson`, `LegalEntity`, `Trust`）。
     - 增加 `EvidenceRequirement`（如身份證、地址證明、股權架構圖）作為可執行實體驗證鏈接。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論代碼表示法優於 JSON（長距離依賴丟失問題）**：
  > *"Our method shows a significant improvement over the JSON baseline. This finding is consistent with prior work, which shows that flattening structured representations into text tends to reduce task accuracy... because: (1) serialized structures are underrepresented in pre-training data compared to free-form text, and (2) flattening a structured graph often separates semantically related nodes... across distant positions in a flat string."* (Section VI-B, p. 9)

- **論 ICL 在合規更新中的敏捷性與低樣本優勢**：
  > *"In-context learning leverages a small set of carefully selected demonstrations, thus diminishing the need for large, manually labeled datasets. In settings where domain experts (e.g., legal counsel) are scarce, this approach lowers the overhead of preparing corpora... when new regulations arise, only a few additional exemplars are needed for the model to adapt, rather than retraining an entire pipeline."* (Section VI-C, p. 10)

- **論使用代碼強語法約束來消除幻覺**：
  > *"By encoding legal statements as Python objects, our approach enforces rigorous formatting and data-typing constraints in the narrower vocabulary of code. The near-perfect compilation rate suggests that the structured prompt and class definitions improve task selection at inference time, reducing free-form text errors like hallucinations..."* (Section VI-B, p. 9)

- **論 conformance-based 測試的本質**：
  > *"Our conformance-based unit testing approach ensures that the generated representation is well-formed, complete, and semantically aligned with the source text, even though it does not simulate rule execution... to verify correct API usage, structural properties, or data flow conformance before execution-level behaviors are modeled."* (Section VI-B, p. 9)
