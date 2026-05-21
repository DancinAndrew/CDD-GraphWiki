# [論文筆記] ComplianceNLP: Knowledge-Graph-Augmented RAG for Multi-Framework Regulatory Gap Detection

> **文獻簡稱**：[ComplianceNLP 26]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)、第 3 層 (Contradiction / Supersession Engine)  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 3 (Ingestion), Phase 4 (Obligation Extraction), Phase 6 (Regulatory Graph)

---

## 1. 論文基本資訊
- **標題**：ComplianceNLP: Knowledge-Graph-Augmented RAG for Multi-Framework Regulatory Gap Detection (知識圖譜增強的 RAG 用於多框架監管合規缺口偵測)
- **作者**：Dongxin Guo (香港大學), Jikun Wu (星辰天合 Stellaris AI), Siu Ming Yiu (香港大學)
- **年份/發表管道**：2026 年 4 月 26 日發表於 arXiv (arXiv:2604.23585v1 [cs.CL])
- **代碼倉庫**：[https://github.com/bettyguo/ComplianceNLP](https://github.com/bettyguo/ComplianceNLP)

---

## 2. 核心研究命題與方法
### 2.1 解決的核心問題
金融機構每年必須應對跨司法管轄區的 60,000 多個監管更新。手動比對外部新法規與內部政策規定的「合規缺口（Compliance Gaps）」成本極高且容易遺漏。現有的 Legal NLP 系統大多隻能處理單一法規框架，且多假設輸入已是結構化數據。本論文提出 **COMPLIANCENLP**，這是第一個**端到端**自動化監控新法規、抽取結構化義務、並與內部政策進行多級缺口對齊的生產級系統。

### 2.2 系統架構與核心技術
系統整合了三大核心組件（見下圖工作流）：
1. **RKG 增強的 RAG 管道 (RKG-Augmented RAG)**：將 12,847 條法規條款（涵蓋 SEC, MiFID II, Basel III）解析並建立為「監管知識圖譜 (Regulatory Knowledge Graph, RKG)」。在檢索時結合了 Dense（密集向量）與 Sparse（BM25）混合分數，並基於 RKG 節點間的距離（KG Proximity）進行重排序。
2. **多任務義務抽取 (Multi-task Obligation Extraction)**：使用共享的 `LEGAL-BERT` 編碼器，同時處理三個核心任務：
   - 領域命名實體識別 (Regulatory NER)：識別角色、金額、時間、金融工具等 23 種實體。
   - 義務模態分類 (Deontic Classification)：在句子級別分類為 `OBLIGATION`（義務）、`PERMISSION`（許可）、`PROHIBITION`（禁止）和 `RECOMMENDATION`（建議）。
   - 跨引用解析 (Cross-Reference Resolution)：解析條文中嵌套的「參照其他條款」關係，將其連接到 RKG。
3. **合規缺口分析 (Compliance Gap Analysis)**：將抽取的結構化義務 $\langle \text{entity, action, modality, condition, source\_provision} \rangle$ 與內部政策條款進行語意對齊，通過 Dense 相似度與實體類型權重匹配函數 $f_{\text{type}}$ 計算得分，低於閾值（部署為 $0.45$）者標記為潛在缺口，再經由 LLaMA-3 生成器細分為三類：`COMPLIANT`（合規）、`PARTIAL GAP`（部分缺口）、`FULL GAP`（完全缺口）。最後通過 MiniCheck 進行 Grounding 驗證。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據
- **Gap Detection 效能**：在 GapBench 評估基準上達到 **87.7 F1**，超越 GPT-4o + 傳統 RAG (+3.5 F1)。
- **Grounding 準確性**：使用 MiniCheck 進行回答的幻覺過濾，達到了 **94.2% 的 Grounding 準確率**，與人類專家的判斷高度一致 (Pearson $r=0.83$)。
- **真實端到端誤差傳播下的效能**：在考慮到抽取階段錯誤傳播的真實情況下，系統仍能維持 **83.4 F1** 的端到端效能。
- **KG 重排序邊際貢獻**：消融實驗（Ablation）表明，**移除圖譜重排序 (RKG Re-ranking) 會導致 F1 得分下降 4.6%**（在未更新同步的 Blind spot 期間僅用向量檢索作為 Fallback，F1 下降 4.6%），證明結構化的圖譜關係對處理高度交叉引用的法規至關重要。

### 3.2 生產環境部署指標
- **並行運行實績**：在某金融機構進行為期 4 個月的並行實戰（處理了 9,847 個監管更新），系統達到了 **96.0% 的生產召回率 (Production Recall)** 與 **90.7% 的精準度 (Production Precision)**。
- **效率提升**：使合規分析師的工作效率大幅提升 **3.1 倍**，單個監管更新的審核時間從 47 分鐘降至 15 分鐘以下（Month 4 降至 12 分鐘）。
- **推理加速 (Distillation + Medusa)**：將微調後的 LLaMA-3-70B 知識蒸餾至 8B 模型，並結合 Medusa 投機解碼（Speculative Decoding），獲得了 **2.8 倍的推理加速**（p50 延遲從 1,847 ms 縮短至 **659 ms**）。

### 3.3 錯誤分析 (Error Analysis) 與未被發現的缺口 (False Negatives)
- **漏報的合規缺口 (Missed Gaps) 主因分析**：
  1. **隱性義務 (Implicit Obligations, 35%)**：法規中沒有明顯的義務情態助動詞（如 shall, must），而是隱性暗示。
  2. **多跳交叉引用 (Multi-hop Cross-References, 29%)**：義務的判定高度依賴解析 3 層或以上的嵌套參照（如 A 參照 B，B 參照 C）。
  3. **特定司法管轄區的細微差別 (Jurisdiction-Specific Nuance, 21%)**：特定的國家或地區實施細則所帶來的獨特缺口。
- **端到端誤差傳播影響 (Table 12)**：
  - 從 Gold Obligations（人工黃金標準）換成 Predicted Obligations（預測義務），端到端 Gap F1 下降了 **4.3 點**。
  - 其中 **NER 邊界錯誤** 是最大元兇（貢獻了 -2.9 F1 下降），其次是 **交叉引用解析失敗** (-1.0 F1) 與 **Deontic 模態誤分類** (-0.4 F1)。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 監管知識圖譜模式 (RKG Schema - Appendix D)
本論文提出了一個極具參考價值的法規/合規領域特定知識圖譜設計：
- **5 種節點類型 (Node Types)**：
  1. `PROVISION`：法規中的具體條款、條目或段落（例如 SEC Section 402, Basel III d424 Paragraph 50）。
  2. `ENTITY`：被監管實體或相關角色（如 `REGULATED_ENTITY`, `REPORTING_ENTITY`, `SUPERVISORY_AUTHORITY` 等共 23 種）。
  3. `OBLIGATION`：抽取出的結構化義務對象。
  4. `THRESHOLD`：定量合規指標（例如 "Basel III CET1 $\ge$ 4.5%"）。
  5. `ENFORCEMENT`：已記錄的合規執法行動歷史（包含處罰金額、日期、對象）。
- **5 種關係邊類型 (Edge Types)**：
  1. `AMENDS`：條款修正關係。
  2. `SUPERSEDES`：條款取代關係（適用於新舊版本）。
  3. `CROSSREFERENCES`：條款間的參照關係 (`PROVISION` $\to$ `PROVISION`)。
  4. `IMPLEMENTS`：特定條款落實了某個義務 (`PROVISION` $\to$ `OBLIGATION`)。
  5. `APPLIESTO`：義務作用於特定實體對象 (`OBLIGATION` $\to$ `ENTITY`)。

### 4.2 檢索與重排序演算法 (Algorithm 1 & Section 3.1)
檢索分為兩階段：
1. **第一階段：混合檢索 (Hybrid Retrieval)**
   使用密集向量（Dense encoder 微調自 `all-MiniLM-L6-v2`）與 BM25 的權重融合：
   $$s(q, d) = \alpha \cdot \text{sim}_{\text{dense}}(q, d) + (1 - \alpha) \cdot \text{BM25}(q, d)$$
   （論文推薦預設 $\alpha = 0.7$，檢索出前 $k=5$ 個候選段落）
2. **第二階段：KG 增強重排序 (KG Re-ranking)**
   利用知識圖譜中檢索段落與源條款的圖距 (Graph Distance) 進行分數調整：
   $$s_{KG}(q, d) = \beta \cdot \text{KGScore}(q, d, \mathcal{G}) + (1 - \beta) \cdot s(q, d)$$
   （預設 $\beta = 0.3$。$\text{KGScore}$ 通過計算圖譜中兩個條款節點間的最短路徑跳數來衡量相關度。）

### 4.3 缺口判定與對齊比對
- 義務表示法：使用五元組 $\langle \text{entity, action, modality, condition, source\_provision} \rangle$。
- 比對相似度公式：
  $$a(o_j, p_k) = \text{sim}_{\text{dense}}(o_j, p_k) \cdot f_{\text{type}}(o_j, p_k)$$
  其中 $f_{\text{type}}$ 是一個機器學習訓練的「模糊類型比對函數」，用於解決同義詞但命名習慣不同（如 "credit institution" 與 "bank"）的名稱對齊。
- 缺口觸發：當最大對齊相似度小於預設門檻 $\delta=0.6$（評估）或 $0.45$（部署）時，將該義務標記為潛在 Gap，送入 LLaMA-3 分析具體缺口類型。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 1 層 (LLM-Wiki)**：論文中的 multi-task 義務抽取（Deontic Classification + NER）為我們的 Ingestion/Extraction Pipeline 提供了標準。
- **第 2 層 (Regulatory KG)**：論文的 5 Nodes + 5 Edges Schema 直接為我們的 `Regulatory Knowledge Graph` 提供了藍圖。
- **第 3 層 (Contradiction/Supersession)**：論文中的 `SUPERSEDES` 邊與 $f_{\text{type}}$ 對齊算法，可以用來實作我們的政策更新與同義詞消除 (Concept Deduplication)。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **RKG 的 Schema 設計**：特別是 `CROSSREFERENCES` 邊的引入，極佳地解決了金融法規「看一條要參照另外三條」的痛點。
2. **混合檢索 + KG Proximity Reranking**：這個雙階段公式簡單明瞭，卻能帶來 +4.6 F1 的顯著提升，應作為我們 CDD-GraphWiki 檢索模組的基礎算式。
3. **實體特化 NER**：論文跳脫了常規的（人名/地名/機構名）NER，設計了合規特異的實體類別（如 `SUPERVISORY_AUTHORITY`, `THRESHOLD_VALUE`, `COMPLIANCE_PERIOD`）。我們也應該在 AML 領域定義類似的 `BENEFICIAL_OWNER`, `PEP_STATUS` 等實體。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **避免對生成器進行端到端微調（極重要警告！）**：
   - *論文踩坑紀錄 (Appendix O)*：全量微調 LLaMA-3-70B 來做 Gap Analysis 反而導致效能下降（F1 從 86.3 降到 81.7）。因為**微調使模型產生了「災難性遺忘」，傾向於走捷徑進行簡單模式匹配，喪失了在複雜跨引用鏈條上的多步推理能力**。
   - *我們的決策*：**CDD-GraphWiki 絕不能試圖微調 LLM 進行推理**，應專注於 In-Context Learning (RAG/GraphRAG) 以及結構化代碼規則匹配的混合路徑。
2. **實體類別 AMR/CDD 本地化**：
   - 論文的 NER 是基於 SEC/Basel III，我們需要將其實體定義替換為符合 FATF Recommendation 10 與 MAS 626 的 KYC 概念（如身分證明、股權結構圖等 `EvidenceRequirement`）。
3. **繞開複雜的 GRC 整合**：
   - 論文提到與 15 年歷史的舊 GRC 系統整合耗費了 40% 的開發週期。我們的專案 MVP 應該**徹底繞開外部 GRC 平台的對齊**，先以純 JSON/YAML 和人機協作 Wiki 頁面的形式輸出。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論 KG 的結構化知識價值**：
  > *"Ablations show that knowledge-graph re-ranking contributes the largest marginal gain (+4.6 F1), confirming that structural regulatory knowledge is critical for cross-reference-heavy tasks."* (Section Abstract, p. 1)

- **論模型微調的負面效果（災難性遺忘）**：
  > *"Full fine-tuning of LLaMA-3-70B on our regulatory corpus degraded general reasoning capabilities needed for gap analysis (gap F1: 86.3→81.7)... the fine-tuned model frequently 'shortcut' to pattern-matched outputs rather than synthesizing cross-reference chains."* (Appendix O, p. 15)

- **論實施 Grounding 驗證 (MiniCheck) 的重要性**：
  > *"MiniCheck removal has minimal F1 impact but degrades grounding accuracy from 94.2% to 86.7%, since it filters unfaithful justifications without changing gap classification."* (Section 6, p. 5)

- **論 GRC 系統整合工程量（前車之鑑）**：
  > *"Integrating COMPLIANCENLP into the institution's existing GRC platform... consumed roughly three months of engineering, comparable to the entire model development cycle. We recommend that future deployments budget at least 40% of total project timeline for GRC integration..."* (Appendix O, p. 15)
