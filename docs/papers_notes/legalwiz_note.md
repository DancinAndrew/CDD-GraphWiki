# [論文筆記] LegalWiz: A Multi-Agent Generation Framework for Contradiction Detection in Legal Documents

> **文獻簡稱**：[LegalWiz 26]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 3 層 (Contradiction / Supersession Engine)、第 4 層 (Human-in-the-loop Wiki)  
> **關聯本專案路線圖**：Phase 5 (Dynamic Conflict Resolver), Phase 8 (Wiki / Revision Interface), Phase 10 (Adjudication Queue)

---

## 1. 論文基本資訊
- **標題**：LegalWiz: A Multi-Agent Generation Framework for Contradiction Detection in Legal Documents (LegalWiz: 用於法律文件矛盾偵測的多智能體生成框架)
- **作者**：Ananya Mantravadi, Shivali Dalmia, Abhishek Mukherji, Nand Dave, Anudha Mittal (Centific), Olga Pospelova (Amazon)
- **年份/發表管道**：2026 年發表於 The First Workshop on Generative and Protective AI for Content Creation
- **主要特徵**：提出一個多智能體（Multi-Agent）框架，用於受控生成包含 6 種結構化矛盾（Self- & Pairwise Contradictions）的法律風格文件，並結合 NLI 與 LLM 進行混合置信度衝突挖掘（Contradiction Mining），最後區分檢索驗證性（Retrieval-verifiable）與檢索抗性（Retrieval-resistant）衝突。

---

## 2. 核心研究命題與方法
### 2.1 解決的核心問題
在法律與合規（GRC）場景中，RAG 管道檢索出的多個證據段落往往存在法規更新、司法管轄區衝突或政策修正帶來的「隱性矛盾」。若未加識別，LLM 生成器會直接「融合（Merge）」這些矛盾，產生語意混亂或法理錯誤的幻覺（無檢索時法律問答幻覺率達 69%-88%，使用 RAG 仍有 17% 以上的幻覺率）。
然而，現有的矛盾偵測基準（如 SNLI, MNLI）多為單句配對，缺乏法律文本特有的複雜句式與跨文件（Cross-document）結構。本論文旨在：
1. **可控注入矛盾**：生成具有真實法律風格、包含受控矛盾的合成數據集，用於壓力測試。
2. **多階段精準挖掘**：設計高效的雙階段 NLI 與 LLM 混合矛盾偵測流程，避免 $\mathcal{O}(n^2)$ 的暴力比對。
3. **矛盾可驗證性分類**：首次區分「檢索能解決的衝突」與「需要法理推理/人工裁決的衝突」。

### 2.2 系統架構與核心技術
系統由三個協調的智能體組成（見工作流）：
1. **Contradiction-Aware Content Generation Agent (矛盾感知內容生成智能體)**：
   - 根據組織畫像（如 Aerodyne Systems）和 5 大法律領域元數據生成基礎文件（Assertive, Policy-oriented style）。
   - **流暢度感知控制 (Perplexity-Based Fluency Control)**：使用預訓練 GPT-2 計算注入矛盾前后的相對困惑度變化率 $\Delta_{\text{rel}}$，若絕對困惑度超過門檻或變化率超標則予以拒絕並重試，確保矛盾自然融入而不破壞法規語法結構。
2. **Contradiction Mining Agent (矛盾挖掘智能體)**：
   - **Semantic Filtering**：使用 `msmarco-distilbert-base-v3` 對句子進行 Top-5 語意過濾，消除短句、數字，減少搜尋空間。
   - **NLI Classification**：利用 `facebook/bart-large-mnli` 進行三分類預測。凡標記為 `contradiction` 或置信度 $p_{\text{NLI}} \le 0.7$ 的模糊邊界對，皆送入 LLM 裁決。
   - **LLM Judge**：由 GPT-4o 扮演法官，輸出二分類 `contradiction`、文字理由及置信度 $p_{\text{LLM}}$。
   - **Confidence-Weighted Hybrid Scoring**：動態計算 NLI 與 LLM 的置信度權重得分 $s_{\text{hybrid}}$，判定最終衝突。
3. **Retrieval Verifiability Agent (檢索可驗證性智能體)**：
   - 區分內部衝突的本質，為 RAG 系統診斷提供清晰的故障定位（例如是檢索漏了法規，還是 LLM 推理失敗）。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據 (Table 5)
評估 NLI-only、LLM Judge-only 與 Hybrid 模型在 **Self-contradiction (單文件內自身矛盾)** 與 **Pairwise contradiction (跨文件成對矛盾)** 的表現：

| 評估維度 / 模型 | NLI-only (BART-MNLI) | LLM-only (GPT-4o) | Hybrid (NLI + LLM) |
| :--- | :---: | :---: | :---: |
| **Self (自身矛盾) - Accuracy** | - | - | **92.0%** |
| **Self (自身矛盾) - Precision** | 37.3% | 74.4% | **高精準 (減少 False Positives)** |
| **Self (自身矛盾) - Recall** | 81.6% | 76.3% | **89.5% F1-score (最佳平衡)** |
| **Pairwise (跨文件) - Accuracy**| - | - | **89.5%** |
| **Pairwise (跨文件) - Precision**| 16.0% | 傾向過度預測 (F1 46.9%) | **顯著提升** |
| **Pairwise (跨文件) - Recall** | 66.7% | - | **70.9% F1-score (最佳平衡)** |

> [!IMPORTANT]
> 數據表明，**跨文件矛盾 (Pairwise Contradictions) 的偵測難度遠高於單文件內部矛盾**。NLI-only 在跨文件場景中 Precision 僅有 16.0%（產生大量虛警），而 Hybrid 混合模型透過置信度權重（Confidence-weighted）將其校正至 70.9% F1。

### 3.2 人工評估與標記一致性 (Human-in-the-Loop)
- **生成的法律文本質量 (5-point Likert Scale)**：
  - Fluency (流暢度): **4.2**
  - Specificity (具體度): **4.7**
  - Coherence (連貫性): **4.5**
  - Legitimacy (法律權威度): **3.5** (說明合成文本在權威感上略遜於真實法規，但流暢與連貫度極佳)。
  - 隱蔽性測試：僅有 **43%** 的注入矛盾被人類初審員直接發現，證明注入極具隱蔽性與真實性。
- **標記一致性 (IAA)**：
  - Self-contradiction: 一致率 **96.0%** (Cohen's $\kappa = 0.914$, Krippendorff's $\alpha = 0.915$)。
  - Pairwise-contradiction: 一致率 **94.8%** (Cohen's $\kappa = 0.828$, Krippendorff's $\alpha = 0.828$)。
  - 低於 90% 一致性的樣本由領域專家 (Subject Matter Expert, SME) 最終仲裁。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 六大矛盾分類法 (Taxonomy of Contradiction Types - Table 2)
在 CDD-GraphWiki 中，這 6 類矛盾可直接映射到我們的 `Contradiction Engine` 偵測規則：
1. **Temporal (時間衝突, 佔比最高 - 30對)**：日期、期限、通知期或生效窗口衝突。
   * *例如*："Termination requires 30 days' notice" vs. "Termination requires 90 days' notice".
2. **Numerical (數值衝突, 6對)**：金額、比例、合規閾值衝突。
   * *例如*："Exemption threshold is $50,000" vs. "Exemption threshold is $10,000".
3. **Specificity (特異度衝突, 20對)**：通用原則與具體例外、或條款範疇定義的衝突。
   * *例如*："All cloud storage is prohibited" vs. "Cloud storage is permitted for non-confidential marketing data".
4. **Policy Reversal (政策翻轉, 26對)**：合規指令或義務模態的直接逆轉。
   * *例如*："The Compliance Officer must approve all transactions" vs. "The Finance Director has sole approval authority".
5. **Authority (權限/管轄權衝突, 7對)**：決策主體或監管法規的層級不一致。
6. **Process (流程/步驟衝突, 15對)**：工作流、申報渠道或審核程序的衝突。

### 4.2 Perplexity (PPL) 流暢度控制公式
為防止矛盾注入導致句子語法畸變，必須滿足以下流暢度門檻限制：
$$\Delta_{\text{rel}}^{\text{self}} = \frac{PPL_{\text{contr}} - PPL_{\text{base}}}{PPL_{\text{base}}} \le 0.05 \quad (\text{Self-contradiction})$$
$$\Delta_{\text{rel}}^{\text{pair}} = \frac{PPL_{\text{contr}} - PPL_{\text{base}}}{PPL_{\text{base}}} \le 0.075 \quad (\text{Pairwise-contradiction})$$
$$PPL_{\text{contr}} \le 22.0 \quad (\text{絕對流暢度上限限制})$$

### 4.3 混合置信度評分公式 (Confidence-Weighted Scoring)
$$\ell_{\text{NLI}}, \ell_{\text{LLM}} \in \{0, 1\} \quad (1 = \text{Contradiction}, 0 = \text{Otherwise})$$
$$w_{\text{NLI}} = \frac{p_{\text{NLI}}}{p_{\text{NLI}} + p_{\text{LLM}}}, \quad w_{\text{LLM}} = \frac{p_{\text{LLM}}}{p_{\text{NLI}} + p_{\text{LLM}}}$$
$$s_{\text{hybrid}} = w_{\text{NLI}} \cdot \ell_{\text{NLI}} + w_{\text{LLM}} \cdot \ell_{\text{LLM}}$$
當 $s_{\text{hybrid}} > \tau$ (部署閾值 $\tau = 0.5$) 時，觸發矛盾警告。

### 4.2 檢索可驗證性分類 (Retrieval Verifiability Schema)
- **Retrieval-verifiable (可檢索驗證的)**：
  - *定義*：衝突可透過引進外部客觀法規（例如 FATF Rec 10 或 MAS 626 條文）來得到唯一正確解答。
  - *處置*：觸發「檢索增強」，重新檢索最新版本的法規庫進行自動覆蓋（Supersession）。
- **Retrieval-resistant (檢索抗性的)**：
  - *定義*：衝突源於內部模糊政策、不同管轄區重疊或合規條款字面無解，必須依賴情境推論或人工仲裁。
  - *處置*：路由至「人工審查隊列（Human Review Queue）」，在 CDD-GraphWiki 界面中標註為 `PENDING_ADJUDICATION`。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 3 層 (Contradiction Engine)**：我們不能只做簡單的關鍵字比對。應直接實作 LegalWiz 的 **Semantic Filtering + NLI + LLM Judge 三階段混合挖掘算法**。
- **第 4 層 (Human-in-the-loop Wiki)**：設計「法理衝突仲裁隊列（Adjudication Queue）」。針對 `Retrieval-resistant` 的法律衝突，提供兩側對比視窗，讓合規官手動決定是「覆蓋（Supersede）」、「共存並設例外（Exemption）」還是「修改草案」。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **6 大矛盾分類元數據 (Taxonomy Metadata)**：在 Ingestion 階段抽取義務時，就將其打上標籤。當發生衝突時，自動向合規官展示衝突類型（例如：「發現時間線衝突（Temporal Conflict），生效期重疊 2 個月」）。
2. **混合置信度加權得分公式**：結合輕量型模型（本地部署的 NLI 模型）與大語言模型（如 GPT-4/Claude），以降低全量調用大模型帶來的 API 昂貴成本，這非常符合我們實用主義的架構設計。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **避免在沒有元數據篩選的情況下進行跨文件全局比對**：
   - 跨文件矛盾偵測（Pairwise Contradictions）的搜尋空間是 $\mathcal{O}(n^2)$。如果我們把 FATF 所有條款與內部政策所有句子進行交叉配對，計算成本將呈爆炸式增長。
   - *改進策略*：必須像論文一樣，**第一步使用 Semantic Filtering (msmarco) 或 2.1 節中的 RKG 關係路徑（例如屬於同一個 `OBLIGATION` 或指向同一個 `ENTITY` 的 Provision）進行窄化**，僅對高度關聯的子圖 (Sub-graph) 進行矛盾挖掘。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論 RAG 對證據矛盾的脆弱性**：
  - > *"Retrieval-Augmented Generation (RAG) integrates large language models (LLMs) with external sources, but unresolved contradictions in retrieved evidence often lead to hallucinations and legally unsound outputs."* (Abstract, p. 1)

- **論跨文件矛盾偵測的難度**：
  - > *"Pairwise contradiction detection proves substantially more challenging... cross-document contradiction detection remains challenging due to contextual shifts and fragmented evidence."* (Section 5, p. 6)

- **論區分檢索可驗證性對 RAG 系統診斷的價值**：
  - > *"Labeling contradictions this way [retrieval-verifiable vs. retrieval-resistant] localizes errors, making evaluation actionable for improving legal RAG systems."* (Section 3.3, p. 5)

- **論 LLM 在面對衝突證據時的「融合」缺陷**：
  - > *"When contradictions in input evidence go unresolved, generation models often merge them, producing legally unsound and potentially risky outputs."* (Section 1, p. 1)
