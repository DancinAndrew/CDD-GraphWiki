# [論文筆記] Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning

> **文獻簡稱**：[Baldwin 26]  
> **關聯本專案架構**：第 1 層 (Knowledge Compilation / LLM Wiki)、第 2 層 (Regulatory KG)、我們的本地 MCP 機制  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 3 (Ingestion / Segmentation), Phase 5 (Concept Deduplication), Phase 8 (CDD Decision Engine)

---

## 1. 論文基本資訊
- **標題**：Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning (基於大語言模型的政策合規推理之知識圖譜呈現)
- **作者**：Wilder Baldwin, Sepideh Ghanavati (緬因大學 University of Maine)
- **年份/發表管道**：2026 年 4 月 30 日發表於 arXiv (arXiv:2604.27713v1 [cs.AI])
- **研究領域**：智能檢索代理 (Agentic Retrieval), 模型上下文協議 (Model Context Protocol, MCP), 跨監管法規推理 (Cross-Policy Compliance Reasoning)

---

## 2. 核心研究命題與方法
### 2.1 面臨的核心問題
AI 治理框架（如歐盟 AI Act、NIST AI RMF、OWASP Top 10 for LLM Applications）對軟體開發施加了大量重疊且高度交叉引用的合規義務。合規官和開發者需要在多個獨立且用詞不同的政策框架間進行對齊與合規判定（Cross-policy Compliance QA）。傳統單純依靠大模型先驗參數知識（parametric knowledge）無法輸出精確的條款原文引用，且極易產生幻覺。

### 2.2 基於 MCP 協議的智能代理合規推理框架
本論文提出了一個第一個**利用 Model Context Protocol (MCP) 協議提供圖譜檢索功能**的端到端智能合規推理框架（見下圖工作流）：
- **組件 1：Scan + Review 智能分塊代理 (Document Chunking)**
  - 法律與合規推理高度依賴法規條款的邏輯完整性。系統放棄了粗暴的固定字數切分，設計了雙階段分塊代理：
    - *Scan Phase*：以 6000 字符滑動窗口（400 字符重疊）推進，由 LLM 識別自然的條款關閉邊界（如 "end of Article 10"），並對齊到最近的段落或句子切分點。
    - *Review Phase*：若分塊大於 4000 字符，由 LLM 進行二次邏輯細分，確保分塊的語義高凝聚力。
- **組件 2：兩階段圖譜提取 (Two-pass KG Extraction)**
  - 為避免 LLM 一次性提取實體與關係時產生漏報，系統採用兩階段提取：第一階段只提取實體（Entities），第二階段依據已提取的實體 IDs 再提取關係（Relations）。
  - 對比了兩種本體（Ontology）：**AIRO Closed Ontology**（基於 AI 險境本體 AIRO 限定的 7 個實體類別與 6 個關係）與 **Open Emergent Ontology**（不設限制，讓 LLM 自由生成 `snake_case` 實體標籤）。
  - **跨框架關聯 (`CORRESPONDS_TO`)**：在不同監管文件提取的實體間，基於 `all-MiniLM-L6-v2` 密集向量相似度得分 $\ge 0.70$（或字面相似度 $\ge 0.80$）自動拉起 `CORRESPONDS_TO` 關係邊。
- **組件 3：適應性雙路徑檢索 (Adaptive Two-Path Retrieval & MCP)**
  - **複雜度路由器 (Complexity Router)** 判斷問題類型：
    - *Direct Path（適用於基礎查詢 T1-T3）*：向量檢索找出 Top-5 實體，自動展開其 1-hop 鄰近節點，將局部圖譜事實作為 Context 餵給生成 LLM。
    - *Agent Path（適用於複雜多步推理/跨法規 T4-T6）*：ReAct 檢索代理通過 5 個專屬圖譜工具（`keyword_search`, `semantic_search`, `neighbor_expansion`, `entity_detail`, `path_finding`）在 7 步限制內遍歷圖譜，收集最核心的證據鏈實體。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗結果 (跨五大模型評估，包含 Frontier 與 3B 小模型)
- **圖譜增強的普遍提升作用 (RQ1)**：
  - 知識圖譜（KG）的引入顯著提升了所有 5 個模型的合規答題 LLM-as-Judge 分數（提升幅度在 **+0.17 至 +0.55** 之間）。
  - **最大升幅體現在「需要精確條款引用 (verbatim citations)」的任務上**。沒有圖譜時，LLM 傾向於模稜兩可地「迴避 (hedging, 如回答 Partially compliant)」，而有圖譜精準提供證據時，LLM 能果斷地回答 "Yes/No" 並進行權威引用。
- **圖譜本體 Schema 對比 (RQ2)**：
  - 消融實驗表明，**Open (Emergent) Schema 在大模型上的表現與 Closed AIRO Schema 持平甚至更好**。因為 Open Schema 生成的具體描述性實體名稱（如 "Harmful Effects of AI Systems [Article 1(1)]"）比 AIRO 的通用本體標籤 "CONSEQUENCE" 與問題的語義重疊更好。
- **小模型 (granite4:micro 3B) 的性能臨界值瓶頸**：
  - 對於 3B 級別小模型，**ReAct 遍歷代理反而降低了其在複雜多步任務 (T4, T6) 上的分數**。因為小模型難以穩定執行多步 tool-calling 圖遍歷，容易在圖中迷失。小模型應直接使用 Direct Path（向量檢索 + 1-hop 鄰接展開）。
- **跨政策對齊的瓶頸 (Vocabulary Mismatch)**：
  - 跨政策推理 (T6) 的最大瓶頸是「詞彙不一致」（例如：OWASP 叫 "data poisoning"，AI Act 叫 "training data bias"）。這會導致向量檢索失效，需要強固的 entity alignment 技術。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 圖譜序列化最佳格式 (Serialization Strategies - Section 2.1)
- 論文研究了 5 種將圖譜數據序列化為 Prompt 的格式，證實：**關係優先的結構化 JSON (structured JSON in a relations-first serialization) 是最優解**。先列出關係邊（以 `source → relationship → target` 格式），再列出實體細節，比直接把圖譜翻譯成自然語言段落，更利於大模型提取事實。

### 4.2 本地 MCP Server 工具集設計 (Section 3)
本研究開源了一套完整的 Model Context Protocol (MCP) Server 實作，包含 16 個 tools, 7 個 resources, 8 個 prompts，是合規工程界將 MCP 協定與法律 GraphRAG 融合的首創。

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 1 層 (Ingestion / Segmentation)**：論文驗證的 **Scan + Review 雙階段代理分塊** 是我們實作 Ingestion 階段 Clause Segmentation (條文切分) 的黃金標準。
- **第 2 層 (Regulatory KG)**：本體同義詞映射與跨政策對齊直接啟發了我們對 FATF、MAS 626 和公司內規的圖譜關聯。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **Scan + Review 智能分塊器**：
   - 在 Ingestion 階段，我們應拋棄 recursive character chunker。我們應撰寫本地 LLM 提示，讓其執行雙階段「掃描 + 覆審」，自動在 `Article`、`Notice Section` 或 `Paragraph` 結尾切分，這能保證每條法規條文的邏輯完整度，極大地提升檢索召回。
2. **關係優先 JSON 序列化**：
   - 在生成 CDD 審查報告時，我們在 Prompt 中構造證據時，應採用其**關係優先的 JSON 結構**（分組列出 `OWNERSHIP`、`SHARES_ADDRESS` 關係），這能直接增強 LLM 在生成 checklist 時的邏輯精準度。
3. **跨政策自動關聯 (`CORRESPONDS_TO`)**：
   - 為了完成 Phase 5 的 Concept Deduplication（概念去重，如 `UBO` $\leftrightarrow$ `Beneficial Owner`），我們可以直接在不同來源的實體間運行 `all-MiniLM-L6-v2` 相似度計算，閾值設為 $\ge 0.70$，自動拉起關聯邊。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **避開小模型的多步 ReAct 遍歷**：
   - *警告*：在本地或生產環境中，**絕不能讓 LLaMA-3-8B 或類似小模型去執行 7 步 ReAct 遍歷 (Agent Path)**。小模型在這種合規檢索中會嚴重退化。小模型只適合 Direct Path（混合檢索後直接由系統展開 1-hop 節點）。複雜的多步 ReAct 圖遍歷應只賦能給頂級大模型。
2. **Open Schema 控制**：
   - 論文指出 Open Schema 容易導致類型增殖（Type Proliferation，如 Nemotron 產生了 47 種實體類型，導致檢索被稀釋）。我們在 CDD-GraphWiki 中，應採取**半開放的 Schema**：只允許生成特定的 snake_case 標籤，並通過強大的 validator 進行約束與合併。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論圖譜增強提供條文原文引用的壓倒性價值**：
  - > *"KG augmentation improves judge scores across all five models (+0.17 to +0.55), with the largest gains on tasks requiring verbatim policy citations, which LLMs cannot reliably produce from parametric knowledge alone."* (Section Abstract, p. 1)

- **論法律合規推理中，大模型從「推測」到「確信」的轉變**：
  - > *"This pattern—from hedging to grounded certainty—appears across models, suggesting that LLMs possess regulatory reasoning ability but lack the specific textual evidence to commit to a judgment; the KG's role is therefore evidential..."* (Section 5.1, p. 7)

- **論小模型在智能遍歷代理中的局限性**：
  - > *"We identify a model-capability threshold below which agentic graph traversal degrades rather than helps, suggesting that the retrieval strategy should be conditioned on the model that will use it."* (Section 6, p. 8)

- **論圖譜序列化中 JSON 的最優性**：
  - > *"An open question is how to represent graph-structured knowledge as text... evaluate five serialization strategies on KG comprehension tasks and find that structured JSON is optimal."* (Section 2.1, p. 2)
