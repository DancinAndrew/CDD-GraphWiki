# [論文筆記] AI Application in Anti-Money Laundering for Sustainable and Transparent Financial Systems

> **文獻簡稱**：[Nie 25]  
> **關聯本專案架構**：第 4 層 (CDD Decision Layer / Customer Graph)  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 8 (CDD Decision Engine)

---

## 1. 論文基本資訊
- **標題**：AI Application in Anti-Money Laundering for Sustainable and Transparent Financial Systems (人工智慧在反洗錢中的應用以建構永續且透明的金融系統)
- **作者**：Chuanhao Nie (喬治亞理工學院), Yunbo Liu (杜克大學), Chao Wang (萊斯大學)
- **年份/發表管道**：2025 年發表於 arXiv / 金融犯罪分析技術研究
- **研究領域**：KYC 客戶畫像與風險評級 (KYC Risk Profiling), 基於 GraphRAG 的端到端合規推理與自動化調查助手

---

## 2. 核心研究命題與方法
### 2.1 傳統金融合規監控系統的致命缺陷
1. **極高的誤報率 (Excessive False Positives)**：傳統系統嚴重依賴基於靜態閾值與规则（Rule-based CRM）的警報（例如：單筆存提款超過 $10,000 或跨境匯款超過預設值）。這種系統不具備隨著洗錢手段演進而動態變化的能力，導致**誤報率常年高達 95% 以上**，淹沒了合規調查員。
2. **數據庫架構的查詢效能瓶頸**：傳統 AML 系統依賴關聯式資料庫 (RDBMS)。然而，洗錢行為是網絡化的（資金在複雜的多個賬戶層級間轉移）。在 RDBMS 中進行多步多 hops 交易追蹤需要頻繁進行大表的跨表 Join，在計算上極其昂貴且難以直觀呈現。
3. **客戶畫像靜態且更新緩慢**：傳統 KYC 客戶盡職調查 (CDD) 只在 Onboarding（客戶開戶）時收集靜態資料（如護照、國籍、職業等），風險評分可能數年不變，無法動態捕捉客戶行為的突然轉變。

### 2.2 基於 Graph RAG 的端到端 KYC/CDD 調查助手
為解決上述瓶頸，論文提出了一個結合 **Graph RAG (基於 Neo4j)** 與 **大語言模型** 的端到端 KYC 智能調查助手（見下圖工作流）：
- **組件 1：RAG Graph Core**
  - 使用圖資料庫 (Neo4j) 作為底層存儲。將結構化的核心銀行數據（賬戶、金流、警報）與非結構化的客戶文件（背景報告、審查資料）全部建模為圖中的節點與邊。
- **組件 2：合規特定 MCP Server (Tooling Layer)**
  - 提供 12 個專門的合規調查 API 作為中間層，供 LLM 自動調用。包括 `get_customer_risk_summary`、`find_customer_rings`（自動識別共享電話/地址的潛在洗錢團夥環）、`trace_shared_accounts`（追蹤共用賬戶）與 `summarize_customer_risk_profile`（自動綜合客戶所有合規事實以生成摘要）。
- **組件 3：LLM 推理環節 (LLM Reasoning Loop)**
  - 大模型（以 GPT-4o-mini 為大腦）扮演受約束的 KYC 調查專員。系統通過精心設計的 System Prompt 強制模型**「只使用工具返回的事實，明示缺失資料，禁止推測」**，並採用固定的審計格式輸出：`Direct Answer -> Supporting Details -> Key Findings`。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心評估數據（基於 10,000 節點 KYC 合成圖譜基準）
- **混合檢索在圖數據上的壓倒性優勢 (Table 2)**：
  - 論文使用 RAGAS 框架（Faithfulness 忠實度、Relevancy 相關性、Context Precision 精準度、Context Recall 召回率）評估。
  - **Level 1 (基礎單點查詢)**：GraphRAG 表現完美（Faithfulness: 0.951, Relevancy: 0.977, Recall: 1.000），而**傳統向量檢索 (Vector RAG) 表現崩塌**（Relevancy: 0.042, Recall: 0.025）。證明將關聯式圖數據扁平化為純文字段落後進行向量相似度检索是徹底失效的。
  - **Level 3 (多跳圖推理，如查關聯制裁人物)**：GraphRAG 依舊穩健（Faithfulness: 0.830, Relevancy: 0.957），而 Vector RAG 徹底崩潰（Relevancy: 0.030, Recall: 0.080）。
  - **Level 5 (敘事綜合與複雜風險詮釋)**：GraphRAG 依然維持高準確度（Faithfulness: 0.865, Relevancy: 0.726, Precision: 0.789, Recall: 0.653）。
- **傳統 ML 混合模型效能 (Section 3.1 & 4)**：
  - 將 XGBoost、LSTM 與 Isolation Forest 結合的混合異常檢測模型能達到 **0.91 的 F1 得分**，並將誤報率控制在 **3% 以下**（rule-based 系統誤報率常 >95%）。
  - GNN 結合 RAG 模型（Regulatory Graphs and GenAI [15]）在 Elliptic Bitcoin 測試集上達到了 **F1 = 98.2%, Precision = 97.8%, Recall = 97.0%**，並能自動產出合規解釋。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 KYC Graph Schema 設計 (Figure 3)
論文展示了生產級 KYC Graph 完整的 Schema 設計：
- **核心節點 (Nodes)**：
  - `Customer`（客戶畫像：ID, Nationality, Risk Level等）
  - `Account`（賬戶資訊）
  - `Transaction`（交易事實）
  - `Address`（物理地址）
  - `Sanction`（制裁名單事實）
  - `PEP`（政治敏感人物標籤）
  - `Alert`（風險警報）
  - `Document`（客戶提供的非結構化文件）
  - `Investigation`（合規官歷史調查案件記錄）
- **核心關係邊 (Edges)**：
  - `OWNERSHIP`：客戶與賬戶的所有權關係。
  - `PERFORMED/RECEIVED`：金流向關係（與 `Transaction` 關聯）。
  - `SHARES_ADDRESS/PHONE`：共用地址或電話事實（對於反洗錢團夥偵測極為關鍵）。
  - `MATCHED`：與制裁或 PEP 名單的對齊關係。

### 4.2 調查員 Agent System Prompt 約束範式 (Figure 4)
```text
SYSTEM_PROMPT = """You are an expert KYC (Know Your Customer) investigation agent...
1. ALWAYS directly answer the question first - State the answer clearly and concisely.
2. Use only information from tool results - Do not make assumptions or add info not in the retrieved data.
3. Cite specific data points - Reference exact values.
4. Structure your response: Start with direct answer, then provide supporting details, and conclude with Key Findings.
5. If data is missing - Explicitly state what information is not available rather than inferring.
"""
```

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 4 層 (CDD Decision Layer)**：本論文直接啟發了我們在 onboarding 客戶背景事實與風險關係上的建模。**我們不應僅把客戶當作一個純文字檔案輸入模型，而應在 neo4j 中為其建立 `Customer Graph`（包含 Customer, Account, Transaction, Address, Sanction 節點）**。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **KYC Graph Schema 設計**：
   - 論文設計的 `SHARES_ADDRESS` 和 `SHARES_PHONE` 關係是偵測 CDD 中「股權結構隱形關聯」的絕佳方式。我們可以直接借鑒其 Schema 來設計我們的 CDD 客戶背景事實圖（Context Graph）。
2. **合規特定的 Python 工具 (MCP Functions)**：
   - 我們可以實作類似 `summarize_customer_risk_profile` 和 `get_customer_risk_summary` 的 Python 函數，作為合規引擎的後端提取器，將復雜的 Neo4j 關係過濾整理後，以高度濃縮的形式餵給決策 LLM。
3. **審計友善的調查報告生成格式**：
   - 採用其 `Direct Answer -> Supporting Details -> Key Findings` 的結構化輸出 Prompt 約束，這能直接優化我們 onboarding 產生合規報告的格式。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **避免過早實作 GNN 實時異常金流監控**：
   - *原因*：論文中提及了使用 EvolveGCN 或 GraphSAGE 進行動態交易模式的洗錢偵測。這屬於**交易監控 (Transaction Monitoring)** 範疇，對我們以 **「法規知識編譯與 onboarding 合規判定 (KYC/CDD)」** 為核心的專案而言是 Anti-Goal。我們應專注於靜態與動態合規要求的比對（如：該客戶是否要提供資金來源證明？），而非洗錢特徵建模。
2. **MCP 機制簡化**：
   - 在 MVP 開發中，我們不需要建立複雜的網絡 MCP Server，直接將這 12 個工具實作為專案本地的 Python 函數（Local Python Tools），並由主 Agent 直接調用即可。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論傳統 Rule-based 系統的極端低效**：
  > *"Traditional rule-based systems often generated false positive rates exceeding 95%, overwhelming investigators and diverting resources away from genuine threats."* (Section 4, p. 5)

- **論向量檢索 (Vector RAG) 在圖結構數據上的徹底失效**：
  > *"This indicates that even simple factual retrieval is difficult for embedding-only retrieval when the underlying data originates from a relational graph structure... Vector RAG cannot reliably reconstruct multi-entity relationships..."* (Section 7.3.3, p. 14)

- **論基於 Graph RAG 建構自動化 KYC 助手的願景**：
  > *"This integration automates the generation and summarization of due diligence reports, reducing manual workload while improving consistency, traceability, and investigative efficiency."* (Section 7, p. 8)
