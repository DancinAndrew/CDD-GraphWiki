# [論文筆記] Approaching the AI Act... with AI: LLMs and Knowledge Graphs to Extract and Analyse Obligations

> **文獻簡稱**：[AIA-Extractor 25]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 3 (Ingestion), Phase 4 (Obligation Extraction)

---

## 1. 論文基本資訊
- **標題**：Approaching the AI Act... with AI: LLMs and Knowledge Graphs to Extract and Analyse Obligations (以 AI 處理 AI 法案：利用大語言模型與知識圖譜提取和分析法律義務)
- **作者**：(歐盟法律資訊學與法哲學研究團隊，如博洛尼亞大學 CIRSFID 團隊)
- **年份/發表管道**：2025 年發表於 ScienceDirect / Computer Law & Security Review (電腦法律與安全評論)
- **研究領域**：法律義務自動抽取 (Automated Obligation Extraction), 法規解構理論 (Deontic Modality Analysis)

---

## 2. 核心研究命題與方法
### 2.1 研究命題
歐盟《人工智慧法案》（AI Act, AIA）作為全球最全面的 AI 監管法規，遵循「風險基礎路徑 (Risk-based approach)」，但也對企業、 deployers 以及國家機構施加了極大的合規負擔。法規義務條款繁多、複雜且存在潛在交叉重疊。如何自動化地從法規文本中提取出「組織需要實施的具體義務 (obligations)」，並將其結構化呈現，是合規自動化的首要命題。

### 2.2 四模組法律文本處理解構工作流
本論文提出了一個嚴格契合**法律義務論理論 (Deontic Logic)** 的模組化四模組工作流（見下圖工作流）：
- **Module 1：義務檢測 (Obligations Detection)**
  - 使用關鍵字篩選法。基於歐盟法規起草規範，提取包含 deontic 情態動詞（如 `shall`, `must`, `should`, `has/have to`）的候選段落與句子，並保留段落的上下文關係與交叉引用條款。
- **Module 2：情態義務過濾 (Deontic Obligations Filtering)**
  - 即使條文包含 "shall"，也不一定代表它是「義務」。使用 LLaMA 3.3 70B 將候選句子分類為 6 類以過濾雜訊：
    1. `Deontic Obligation`：強制的行為義務或狀態義務。
    2. `Definition`：法律定義（如：shall be understood as...）。
    3. `Constitutive Statement`：法律事實的構成聲明（如：Article 6 規定 Annex III 條款應被視為高風險，屬於宣告而非處置行為）。
    4. `Entitlements`：賦予權利/資格。
    5. `Authorisations`：授權/許可。
    6. `Deontic Prohibition`：法律禁止事項（視為不作為義務）。
    - 設置 `Not Applicable` 作為安全過濾閥。
- **Module 3：義務要素分析 (Deontic Obligations Analysis)**
  - 將義務細分為「行為義務 (Obligation of Action)」與「狀態義務 (Obligation of Being)」，並提取 **6 個核心要素**：
    1. `Addressee` (義務人)：承擔主動責任的實體。**強調：義務人必須是具備行為能力的自然人或法人（如 provider），AI 系統、程序或措施本身不能作為義務人**。
    2. `Predicate` (謂語動詞)：要求的核心行為或狀態（如 shall perform, shall be resilient）。
    3. `Targets` (目標物)：被作用的對象（Action 義務中是賓語，Being 義務中是主語）。
    4. `Specifications` (規格說明)：標準、時間或方法（如 "in accordance with..."）。
    5. `Pre-conditions` (前置條件與例外)：觸發或豁免該義務的前提（如 "where applicable" 或特定例外）。
    6. `Beneficiary` (受益人)：履行義務時獲得利益的第三方。
  - **引進「提取來源標註」(Extraction Methods)**：要求模型分類要素來源是 Stated（條文直述）、Context（上下文推理）、Citation（引用推理）還是 Background Knowledge（先驗知識）。
- **Module 4：義務圖譜呈現 (Deontic Obligations Representation)**
  - 通過 Sentence Transformers（如 `all-MiniLM-L6-v2` 與 `nomic-ai/modernbert-embed-base`）進行語意聚類，映射到專家設計的法規本體（Ontology）中，並匯出為 GraphML 圖譜。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據 (基於 LLaMA 3.3 70B + Together AI API)
- **Module 2 Filtering 效能**：
  - 義務分類準確度達 **93%**， justification (理由生成) 準確度達 **90%**。
  - *主觀性評估*：專家評估的 inter-rater reliability (Krippendorff’s $\alpha$) 分類為 0.29，說明法規中分辨「定義、宣告與實質義務」在法學界本身就具有相當高的主觀性與釋法空間。
- **Module 3 Analysis 要素提取準確性**：
  - `Obligation Type` (義務類型分類)：**>99%** 準確度 (Krippendorff's $\alpha = 1.00$)。
  - `Addressees` (義務人價值提取)：**>99%** 準確度。
  - `Predicate` (謂語): **>99%** 準確度。
  - `Pre-Conditions` (前置條件與例外) & `Beneficiary` (受益人)：**97%** 準確度。
  - `Specifications` (規格基準): **94%** 準確度。
  - `Targets` (目標物): **89%** 準確度。
- **專家驗證協議**：採用 2 階段專家雙盲驗證（4 名獨立法律博士生審查，再由第 5 位法哲學博士後作為裁判進行仲裁），保證結果的學術嚴謹性。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 行為義務 (Action) 與狀態義務 (Being) 的本質差異
- **Obligation of Action（行為義務）**：要求主動採取特定行為以達成合規（例如："The provider shall perform a conformity assessment"）。
- **Obligation of Being（狀態義務）**：要求系統或實體維持在某種規定的屬性狀態，但不指定具體落實行為（例如："The high-risk AI system shall be accurate and transparent"）。
- *工程價值*：在 CDD 系統中，大多數 AML/KYC 法規是**行為義務**（例如：金融機構應收集身分證），這極易被形式化；但內部規章中常包含**狀態義務**（例如：客戶審查程序應是安全的），這需要合規官的主觀判定。

### 4.2 LLM 提取防幻覺機制：Source Meta-Classification
- 在 Module 3 中，論文指出：**強制 LLM 去判斷每個要素的「提取來源方法」(Extraction Method)**，能大幅減少模型在處理「隱性受益人」或「缺失主體」時的**幻覺 (Hallucinations)**。因為這強迫模型在輸出前，自證該 facts 是來源於條文 (Stated) 還是出於其自身背景知識 (Background Knowledge)。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 1 層 (Ingestion / Parsing)**：該論文為我們的法規條文解析與「義務淨化」提供了理論支持。在 MVP 的 Phase 3，我們可以實作關鍵字過濾器，僅保留 `shall`, `must` 等情態句。
- **第 2 層 (Regulatory KG / Data Contracts)**：論文的 6 Key Elements 直接昇華了我們的 `Obligation` Schema，為 Phase 1 提供了極具法學理論支撐的資料合約。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **防幻覺提取架構 (Extraction Source Meta-data)**：
   - 當我們的 LLM 在 Phase 4 提取 AML/CDD 義務時，我們的 Prompt 應強制 LLM 輸出 `{value: ..., source: "stated" | "context" | "citation"}` 結構。這樣可以極大程度遏制大模型無中生有地編造合規證據或適用對象。
2. **Deontic Filtering (情態義務過濾器) 的導入**：
   - 金融法規（如 MAS Notice 626）中充斥著大量的名詞定義（Definitions）和行政宣告。我們應借鑒 Module 2 的分類 prompt，在將法規寫入 RKG 前，排除所有 `Definition` 與 `Constitutive Statement`，**只保留實質性合規義務 (Obligations) 與禁止 (Prohibitions)**。這能防止垃圾資料污染我們的推理圖譜。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **主體概念 CDD 轉化**：
   - 論文的 `Addressee` (義務人) 在 AI Act 中是 provider。套用到我們系統中，`Addressee` 永遠是金融機構或 VASP，而我們的合規重心應放在 `Target` (例如客戶、最終受益人 UBO) 與其 `Pre-conditions` (適用門檻，如持有 25% 股份) 上。
2. **避免過度分類**：
   - 論文中的 `Beneficiary` (受益人) 在 AI Act 中非常重要（因為涉及隱私權益）。但在 AML 領域，受益人多數是隱性的（國家安全或反洗錢監管機構）。在我們的 MVP 中，**可以忽略 Beneficiary 提取**，將研發精力集中在 `Pre-conditions` (例外條件) 與 `Specifications` (證據文件要求) 上。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論義務解構與其 6 個核心要素的定義**：
  - > *"Our experiment... conceptualise obligations as deontic constructs with recurring elements... deontic modality, addressee, predicate, target, specifications, pre-conditions, beneficiary."* (Section 3, p. 3)

- **論義務人 (Addressee) 的主體資格限制（極重要）**：
  - > *"The addressee must individually or collectively possess the capacity to act, such as a natural or legal person. Consequently, entities like 'AI systems', 'a process', or 'adopted measures' cannot serve as addressees..."* (Section 3.3, p. 4)

- **論要求模型判定「提取來源」對抑制幻覺的顯著工程價值**：
  - > *"Technically, initial results showed that prompting the LLM to classify the extraction methods minimised the risk of hallucinations, especially when the information was not explicitly stated in the provision."* (Section 4.3, p. 5)

- **論區分「行為義務」與「狀態義務」的理論價值**：
  - > *"Obligations of action require an action to be taken in order to achieve compliance... Obligations of Being demand that an entity (a thing, a person, an organisation) meets certain requirements."* (Section 3.1, p. 4)
