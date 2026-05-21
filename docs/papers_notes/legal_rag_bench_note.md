# [論文筆記] Legal RAG Bench: an end-to-end benchmark for legal RAG

> **文獻簡稱**：[Butler 26]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)、第 4 層 (Rule Verification / Human Review Queue)  
> **關聯本專案路線圖**：Phase 8 (Verification Framework), Phase 9 (Evaluation Framework)

---

## 1. 論文基本資訊
- **標題**：Legal RAG Bench: an end-to-end benchmark for legal RAG (Legal RAG Bench：法律 RAG 的端到端評估基準與方法論)
- **作者**：Abdur-Rahman Butler, Umar Butler
- **年份/發表管道**：2026 年 3 月 2 日發表於 viXra (viXra:2603.0171v1 [cs.CL])
- **主辦機構/贊助商**：Isaacus
- **開源地址**：
  - 數據集 (Hugging Face)：[https://huggingface.co/datasets/isaacus/legal-rag-bench](https://huggingface.co/datasets/isaacus/legal-rag-bench)
  - 程式庫 (GitHub)：[https://github.com/isaacus-dev/legal-rag-bench](https://github.com/isaacus-dev/legal-rag-bench)
  - 部落格導讀：[https://isaacus.com/blog/legal-rag-bench](https://isaacus.com/blog/legal-rag-bench)

---

## 2. 核心研究命題與方法

### 2.1 解決的核心問題
在法律科技中，檢索增強生成（RAG）被廣泛用於為 LLM 注入法律語境以保證 Groundedness。然而，現有法律 RAG 評估存在嚴重弊端：
1. **非端到端**：大多數基準僅孤立地評估「向量檢索」或「LLM 生成推理」，忽略了兩者在完整系統中的協同效應與誤差傳播。
2. **標籤質量差與不切實際**：例如 MTEB 內嵌的 AILA 數據集，利用律師在起訴書中引用的歷史判例作檢索金標準。但在法理上，案件被引用可能僅是因為支持某個不相干的通用法律點（如 Donoghue v Stevenson 雖起源於「喝到有蝸牛的薑汁啤酒」，卻在全世界被引用於各種侵權法點），這與事實檢索脫節。
3. **任務過於簡單**：如 LegalBench 及 LegalBench-RAG 大多是低價值的 Yes/No 合約條款分類，無法評估複雜的長文本生成；HousingQA 和 BarExamQA 則被限制於選擇題，無法模擬真實生產環境中 LLM 自由生成時產生的混沌幻覺。

### 2.2 系統設計與實驗方法
為了解決上述痛點，本論文引入了 **Legal RAG Bench**，這是一套端到端的基準與錯誤診斷方法論：
- **數據集設計**：採用澳大利亞維多利亞州《刑事控告書 (Victorian Criminal Charge Book)》為語料庫，共 **4,876 個法律段落**。由法律專家手工編寫了 **100 個極具挑戰性的複雜刑事法律諮詢問題、黃金長答案以及唯一的支持證據段落 (Question-Answer-Evidence Triplets)**。條文採用 `semchunk` 進行語意分塊（限制在 512 tokens 內）。
- **全因子設計 (Full Factorial Design)**：對 3 種 Embedding（Kanon 2 Embedder、Google Gemini Embedding 001、OpenAI Text Embedding 3 Large）與 2 種 frontier LLM（Gemini 3.1 Pro、GPT-5.2）的 **所有 6 種排列組合** 進行了對齊評估，排除超參數干擾。
- **LLM-as-a-Judge 評估**：利用 GPT-5.2 (High Reasoning Mode) 擔任裁判，提供清晰的 Rubric 與 Binary Outcome（達 99% 的極高判定準確率），評估三個核心維度：
  1. **Correctness ($c$)**：LLM 生成的回答是否蘊含（entail）參考答案。
  2. **Groundedness ($g$)**：回答是否完全由檢索到的段落支持（不論這些段落是否真的與問題相關）。
  3. **Retrieval Accuracy ($r$)**：Embedding 模型是否成功檢索到黃金支持段落。

### 2.3 階層式錯誤分解分類法 (Hierarchical Error Decomposition Taxonomy)
這是本論文最核心的方法論貢獻。當系統出錯時，不只是記錄「回答錯誤」，而是按照下圖邏輯進行因果溯源：

```
                    RAG 回答 (RAG Response)
                             │
                  [ 是否 Grounded (g=1)? ]
                   /                  \
                (否)                 (是)
                 ▼                    ▼
          【 Hallucination 】    [ 是否 Correct (c=1)? ]
          生成模型編造了事實       /                  \
                               (否)                 (是)
                                ▼                    ▼
                    [ 是否檢索到黃金段落 (r=1)? ]       【 Correct 】
                       /                  \            回答正確且
                     (否)                 (是)          有證據支持
                      ▼                    ▼
             【 Retrieval Error 】   【 Reasoning Error 】
             檢索失敗導致LLM基於      檢索成功但LLM仍
             無關上下文回答錯誤       推理錯誤得出錯結論
```

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據與模型效能 (Table 1 & 2)
- **Kanon 2 Embedder（法律專用 Embedding）**：表現最優，平均 Correctness 達 **94.0%**，Groundedness 達 **96.0%**，Retrieval Accuracy 達 **86.0%**。
- **OpenAI Text Embedding 3 Large**：Correctness 驟降至 **76.5%**，Retrieval Accuracy 僅有 **52.0%**。
- **Google Gemini Embedding 001**：Correctness 降至 **74.0%**，Retrieval Accuracy 為 **53.0%**。
- **生成模型 averages (LLMs)**：
  - **Gemini 3.1 Pro**：Correctness 82.3%，Groundedness 94.3%
  - **GPT-5.2**：Correctness 80.7%，Groundedness 88.7%

### 3.2 統計學顯著性檢定與 Wald 檢定（極具參考價值）
論文通過對實驗數據擬合線性概率模型，並利用**基於問題分群的魯棒標準誤（Cluster-Robust SE）**進行 ANOVA-style Wald 檢定：
- **檢索是決定 legal RAG 效能的絕對瓶頸（主要效應主導）**：
  - Embedding 模型的 `Embedder main effect` 對於 Correctness 與 Groundedness 的 Wald 檢定均達到 **$p < 0.001$ 的極端顯著**。
  - 與之相反，LLM 的 `LLM main effect` 對於 Correctness 在統計上**完全不顯著 ($p = 0.499$)**。
  - **結論：在法律 RAG 中，檢索模型（Embedding）直接決定了系統的性能天花板，而 frontier LLM 之間的推理差距此時已不再是正確率的決定性因素。**
- **檢索失敗是幻覺的根本誘因**：
  - 實驗顯示，**低質量的檢索與幻覺率有極強的因果正相關**。相比於通用 Embedding，使用 Kanon 2 法律專用 Embedding 能讓 LLM 幻覺率平均降低 **6.75%**。因為**當提供正確且高度相關的上下文時，LLM 幾乎不會主動去編造事實**。
- **有趣的交互作用效應 (ANOVA Table 3 & 4)**：
  - `Groundedness` 是唯一表現出顯著交互作用的指標（$p=0.017$）。
  - 將 LLM 從 Gemini 3.1 Pro 切換到 GPT-5.2，在搭配 `Text Embedding 3 Large` 時，Groundedness 大幅下降 **9.0%**；搭配 `Gemini Embedding 001` 下降 **10.0%**。
  - 然而，當搭配 `Kanon 2 Embedder`（極高檢索率）時，切換 LLM 對 Groundedness **完全無統計學影響 (+2.0%, p=0.459)**！
  - **結論：GPT-5.2 在收到無關的「垃圾檢索上下文」時更容易被誤導而大肆產生幻覺；但若收到高度精確的法律上下文，GPT-5.2 與 Gemini 3.1 Pro 同樣穩定。**

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 檢索天花板與誤差轉移
論文指出，在引進高效的法律適應 Embedding（如 Kanon 2）後，RAG pipeline 中的錯誤結構會發生戲劇性轉移（見 Figure 2）：
- 在 `Text Embedding 3 L. x GPT-5.2` 組合中，總錯誤率為 30%，其中 **Retrieval Error 佔了絕大多數**。
- 在 `Kanon 2 x GPT-5.2` 中，總錯誤率降至 9%，此時 **Retrieval Error 被幾乎消滅，Reasoning Error（生成推理錯誤）與 Hallucination 成為主導**。
- **啟示：只有當檢索能力強大到一定程度後，LLM 的推理瓶頸才會顯露出來。在此之前，優化 LLM 推理對 RAG 整體正確率的邊際效益極低。**

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊 (Verification & Evaluation)
- **第 4 層 (Rule Verification / Human Review Queue)**：
  我們必須將本論文的**層次式錯誤分解分類法**作為我們 Phase 9 (Evaluation) 的核心流程。當我們的 CDD 引擎給出一個不合規判決時，評估模組應自動運行該決策樹，判斷這是：
  - 客戶上傳了無效證件但系統誤判（Retrieval Error）；
  - 客戶上傳了正確證件但 LLM 邏輯推理出錯（Reasoning Error）；
  - LLM 憑空捏造了外部 MAS 626 不存在的合規閾值（Hallucination）。
- **RegTech 第一黃金法則：可驗證性 (Verifiability) $\ge$ 正確性 (Veracity)**：
  本論文提出了一個極為深刻的法規科技觀點：
  > *"True but unverifiable conclusions can never be proven to be true."*  
  在 CDD-GraphWiki 中，**任何沒有具體法規 clause 以及客戶 Expression 證據鏈支持的 "PASSED" 判決，即使它事實上是正確的，也必須被判定為「幻覺 (Hallucination)」並送入 Human Review Queue**。合規系統必須保證決策鏈條的 100% 可追溯與可審計性。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **層次式錯誤診斷樹的 Python 實作**：
   在我們的測試框架中，編寫一個評估器，根據三個變數（Correctness, Groundedness, Retrieval Accuracy）對每一次合規問答生成錯誤分類標籤，作為日誌和儀表板的關鍵指標。
2. **語意分塊 (Semantic Chunking)**：
   我們在 Ingestion Pipeline (Phase 3) 中，應當採用論文提及的 `semchunk` 算法，限制 chunk 在 512 tokens 內，以保證檢索密度。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **對通用向量檢索 (Dense RAG) 保持警惕**：
   - *論文數據警告*：使用 OpenAI 通用向量模型會導致正確率下降 17.5%，檢索精度下降 34%。
   - *我們的改進*：在 CDD-GraphWiki 中，**絕不能僅依賴扁平的向量 RAG 來檢索 AML 法規**。我們必須採用混合檢索（Hybrid BM25 + Dense）並結合**知識圖譜關係鏈 (GraphRAG)** 來人為「抬高」檢索天花板，否則 downstream LLM 就會因為檢索垃圾而大量產生幻覺。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論可驗證性 (Verifiability) 在法律中的至高地位**：
  > *"Legal research and analysis is very much evidence-driven—the verifiability of legal conclusions is often just as important as the veracity of those conclusions, if not more so. Untrue but verifiable conclusions can always be proved to be false, yet true but unverifiable conclusions can never be proven to be true."* (Section 4, p. 5)

- **論檢索決定法律 RAG 系統的絕對天花板**：
  > *"Our results conclusively establish that across all evaluation dimensions, choice of embedding model dominates RAG performance... We observe that many errors attributed to hallucinations in legal RAG systems are in fact triggered by retrieval failures, concluding that retrieval sets the ceiling for the performance of many modern legal RAG systems."* (Section Abstract, p. 1)

- **論垃圾檢索對 LLM 幻覺的誘發效應**：
  > *"Our analysis finds conclusively that retrieval quality is the primary driver of end-to-end legal RAG performance and that most hallucinations in production legal RAG systems are induced by retrieval failures... generative models may potentially be aware of when they are hallucinating invented facts to answer questions to which they have no relevant facts."* (Section 1 & 6, p. 2 & p. 11)

- **論交互作用對 RAG 模型評估的挑戰**：
  > *"Differences in groundedness are not stable across embedding models, and should not be summarized by a single global LLM ranking. More generally, these results motivate reporting interaction tests alongside main effects when benchmarking RAG pipelines."* (Section 5.3, p. 10)
