# [論文筆記] RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA

> **文獻簡稱**：[RAGulating Compliance 26]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)、第 3 層 (Contradiction / Supersession Engine)  
> **關聯本專案路線圖**：Phase 2 (Schema Design), Phase 3 (Ingestion), Phase 6 (Regulatory Graph), Phase 7 (GraphRAG Integration)

---

## 1. 論文基本資訊
- **標題**：RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA (合規監管：用於監管問答的多智能體知識圖譜)
- **作者**：Bhavik Agarwal, Hemant Sunil Jomraj, Simone Kaplunov, Jack Krolick, Viktoria Rojkova (MasterControl AI Research)
- **年份/發表管道**：2026 年發表於 arXiv
- **主要特徵**：提出一個將「無本體知識圖譜 (Ontology-Free KG / Schema-light)」與「檢索增強生成 (RAG)」雙向融合的多智能體框架。核心思想是將抽取的 SPO 三元組與其原始文本段落（Provenance）統一存儲在同一個向量庫中，通過三元組語意檢索拉動原始文本，最後交給 LLM 生成高度可靠且可追溯的合規答覆。

---

## 2. 核心研究命題與方法
### 2.1 解決的核心問題
在生命科學、金融合規等高風險監管問答 (Regulatory QA) 領域，傳統大語言模型 (LLMs) 有顯著的幻覺風險。儘管傳統 RAG 可以提供非結構化段落，但在處理高度互聯、參照關係錯綜複雜的法規（例如「多個不同條款收斂到同一個 15 天申訴期」）時，純文本检索往往會漏掉關鍵鏈條，且缺乏結構化的法理關聯性，不利於審計 (Auditing)。
本論文旨在：
1. **擺脫死板的本體定義**：針對快速變更的法規，提出「Ontology-Free」自底向上抽取法，免去傳統知識圖譜 (KG) 高昂的 Schema 設計與維護成本。
2. **三元組與非結構化文本的一體化存儲**：解決傳統 GraphRAG 需要同時維護獨立的「圖數據庫 (e.g. Neo4j)」與「向量數據庫」的架構冗餘問題，將兩者在單一向量數據庫中關聯。
3. **優化交叉引用的導航能力**：透過三元組建立段落間的隱性聯繫，使系統能在相關條款間快速尋址。

### 2.2 系統架構與核心技術
系統整合了兩個互聯的多智能體系統（見下圖）：
1. **Ontology-Free KG Construction Agent Pipeline (圖譜構建管道)**：
   - *Document Ingestion Agent*：切分原始段落，捕獲層級元數據。
   - *Triplet Extraction Agent*：利用微調 LLM 自底向上提取 `Subject-Predicate-Object (SPO)` 三元組（例如 $\langle \text{FDA, requires, submission} \rangle$）。
   - *Normalization & Cleaning Agent*：進行實體對齊 (Entity Resolution) 與概念去重，處理同義詞。
   - *Indexing Agent*：拼接三元組為文字片段 $f(t_i) = \text{concat}(s_i, p_i, o_i)$ 並生成向量嵌入，存入富向量庫。
2. **Agentic RAG QA System (問答檢索管道)**：
   - *Retrieval Agent*：利用自定義 eCFR 嵌入模型，檢索與 query 語意最接近的 Top-$k$ 個三元組 $\mathcal{T}_Q$。
   - *Story-building Agent*：根據追蹤字典，拉出這些三元組背後的原始文本段落 $\mathcal{X}_Q$，並將其編排為連貫的故事背景（Story）。
   - *Generation Agent*：將 $\langle Q, \mathcal{T}_Q, \mathcal{X}_Q \rangle$ 組合輸入 LLM（如 Qwen-2.5 或 GPT-o1），生成最終答案，並輔以交互式子圖可視化。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據 (Table 1)
比較傳統無三元組 RAG (Without Triplets) 與三元組增強 RAG (With Triplets) 的系統性能表現：

| 評估指標 (Metric) | Without Triplets (純文本 RAG) | With Triplets (本專案方法) | 關鍵結論與洞察 |
| :--- | :---: | :---: | :--- |
| **Section Overlap (相似度閾值 0.50)** | **0.0812** | 0.0745 | 低門檻下，三元組過濾掉了雜訊，覆蓋率略低。 |
| **Section Overlap (相似度閾值 0.60)** | **0.2700** | 0.2143 | 中門檻下，純文本檢索引入了較多不精準的關聯段落。 |
| **Section Overlap (嚴格閾值 0.75)** | 0.1684 | **0.2888** | **在嚴格的高精度匹配下，三元組增強顯著勝出 (+71.4%)**，說明三元組精確定位了真正相關的段落。 |
| **Average Answer Accuracy (1-5分)** | 4.71 | **4.73** | 結合 SPO 三元組的 LLM 答案在事實正確性上更穩健，消除了長尾幻覺。 |
| **Average Degree (平均圖節點度數)** | 1.2939 | **1.6080** | **圖譜連通性顯著增強**，單個實體能關聯更多相關法規條款。 |
| **Unconnected Sections Linked** | 5014 個孤立段落 | **5011 個已建立連通** | 成功將先前在文本層面孤立的段落，透過三元組關係串聯起來。 |
| **Avg. Shortest Path (平均最短路徑)** | 2.0167 | **1.3300** | **知識傳遞路徑縮短 34%**，大幅提升跨引用檢索效率。 |

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 富向量數據庫元數據 Schema (Enriched Vector Index $\mathcal{V}$)
本論文的一大工程突破是**在一個向量數據庫中同時存儲結構化三元組與非結構化文本**。這可以直接作爲 CDD-GraphWiki 的數據庫設計藍圖：
- **存儲三元組**：$t_i = (s_i, p_i, o_i) \in \mathcal{T}$
- **短語化變換函數 (Textual representation)**：
  $$f(t_i) = \text{concat}(s_i, \text{ ' ' }, p_i, \text{ ' ' }, o_i)$$
- **向量嵌入**：$\mathbf{e}_{t_i} = E(f(t_i)) \in \mathbb{R}^d$（嵌入模型微調自 BERT 結構，並在 eCFR 監管數據集上進行領域自適應預訓練）。
- **雙向 Provenance 鏈接函數 (Linking Function)**：
  $$\Lambda: \mathcal{T} \to 2^{\mathcal{X}}$$
  其中 $\Lambda(t_i) = \{x_j, x_k\}$ 表示抽取該三元組的原始段落。
- **最終數據庫索引**：
  $$\mathcal{V} = \{(\mathbf{e}_{t_i}, t_i, \Lambda(t_i)) \mid 1 \le i \le N\}$$

### 4.2 檢索與生成工作流 (Algorithmic Pipeline)
1. **Query Embedding**：$\mathbf{e}_Q = E(Q)$。
2. **Triplet Retrieval**：
   $$\mathcal{T}_Q = \text{TopK}(\text{sim}(\mathbf{e}_Q, \mathbf{e}_{t_i}))$$
   （依據 Cosine Similarity 檢索最相關的三元組集合）。
3. **Text Evidence Fetching (回溯非結構化證據)**：
   透過 Provenance 字典將檢索到的三元組集映射回原始段落集合：
   $$\mathcal{X}_Q = \bigcup_{t_i \in \mathcal{T}_Q} \Lambda(t_i)$$
4. **Context Synthesis & LLM Generation**：
   將 Query、三元組、以及原始段落以高度結構化的 Context 餵給生成 LLM：
   $$A = \Gamma(Q, \mathcal{T}_Q, \mathcal{X}_Q)$$

### 4.3 三元組導航指標 (Navigational Metric)
為了量化在交叉引用網絡中的「知識尋址效率」，論文提出了導航 facility 計算公式：
$$\text{Nav}(\mathcal{S}') = \frac{1}{k} \sum_{j=1}^k \frac{\sum_{s_{m_\ell} \in M(s_{i_j})} \bigl| \mathcal{T}(s_{i_j}) \cap \mathcal{T}(s_{m_\ell}) \bigr|}{\sum_{s_{m_\ell} \in M(s_{i_j})} \bigl| \mathcal{T}(s_{i_j}) \cup \mathcal{T}(s_{m_\ell}) \bigr|}$$
一個高 $\text{Nav}$ 值代表相關段落之間有高比例的共用或順序關聯三元組，能確保圖譜檢索時的「多跳尋路 (Multi-hop Pathfinding)」不會偏離主題。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 2 層 (Regulatory KG)**：本專案的 KYC/CDD 圖譜應採取 **Ontology-Free / Schema-light** 的 bottom-up 提取哲學。不要嘗試在一開始就設計一套完美的「AML/CDD 本體」，應讓 LLM 自底向上提取 SPO 三元組，隨後利用 Entity Resolution 模組在運行時自然形成關聯網絡。
- **第 7 階段 (GraphRAG Integration)**：直接落地論文的 **Enriched Vector Database 架構**。我們的向量數據庫（如 Chroma / Pinecone）中的單個 Document Payload 不僅應存儲原始條款 Chunk，還應把從該 Chunk 中抽取出來的多個 SPO 三元組（短語化後）一起存入 Metadata，並實現雙向 provenance 回溯。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **三元組短語化嵌入 (Triplet Phrase Embedding)**：這是一種極為實用的 GraphRAG 簡化手段。將三元組 `concat(s, p, o)` 變成一段文字進行密集向量嵌入檢索，可以完全繞開複雜的圖機器學習，直接在標準向量庫中實現高精度圖語意檢索。
2. **Triplet-driven Story Builder**：當檢索到法規條款時，不只餵給 LLM 密密麻麻的文字 Chunk，應同時拼接一個結構化的 **SPO Triplet Facts** 段落。這能讓 LLM 生成時的邏輯線極度清晰，杜絕代名詞混淆（如 "The agency" 指代不明）。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **實體規範化 (Canonicalization) 的缺失將導致圖譜崩塌**：
   - *論文警告 (Section 8.1)*：無本體 (Ontology-free) 最大的致命傷是「詞彙碎片化 (Vocabulary Fragmentation)」。例如 LLM 在條款 A 中提取了 `(CDD, is required for, customer)`，在條款 B 中提取了 `(Customer Due Diligence, applies to, clients)`。如果沒有實體規範化，這兩個節點將徹底孤立，導致 `Average Shortest Path` 指標大幅惡化。
   - *我們的決策*：**CDD-GraphWiki 必須配備一個極為強大的「實體對齊與規範化 Agent」**。在寫入向量庫前，透過 LLM 對 `CDD` / `Customer Due Diligence`、`Customer` / `Client` 進行別名消除與合併。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論無本體自底向上知識圖譜的靈活性**：
  - > *"An alternative 'schema-light' approach defers rigid schemas in favor of flexible bottom-up extraction... making it especially valuable in regulatory settings where rules evolve rapidly, data formats vary, and open-ended queries can reveal hidden legal connections."* (Section 3, p. 2)

- **論三元組如何提升高精度檢索效果**：
  - > *"Triplets yield highest accuracy at higher threshold [similarity threshold = 0.75]. Triplets network significantly enhances connectivity and navigation, shortening the shortest path from 2.0167 to 1.3300."* (Section 7.3, p. 5)

- **論三元組與原始文本 Provenance 關聯的必要性**：
  - > *"Because each triplet links back to its source text, users or downstream models can verify and clarify relationships by referring to the original regulatory language, thus mitigating ambiguities not fully captured by the triplet alone."* (Section 4.6, p. 4)

- **論無本體 KG 的缺陷與解決方案**：
  - > *"An ontology-free approach facilitates rapid ingestion... but can lead to vocabulary fragmentation; canonicalization and entity resolution help unify concepts."* (Section 8.1, p. 6)
