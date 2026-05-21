# regulatory-graph Specification

## Purpose

本規格定義了法規圖譜構建與可視化 (Regulatory Graph Construction & Visualization) 的核心行為與合規契約。系統旨在將結構化的合規知識（法規來源、條文、適用義務、核心概念、政策衝突、客戶 facts、CDD 決策檢核表與決策路徑）自動編譯、織入成一張機器可推理的有向知識圖譜，並將該圖譜導出為配備極致暗黑玻璃擬物美學 (Dark Glassmorphic UI) 的 D3.js 互動式 HTML 可視化網頁，提供 100% 透明且高互動性的多步溯源查詢與影響力分析體驗。

## ADDED Requirements

### Requirement: Regulatory Graph Contracts and JSON Schemas

系統 **MUST** 定義強型別圖譜資料模型，包括 `GraphNode`、`GraphEdge` 與 `RegulatoryGraph`。
* `GraphNode` **SHALL** 包含唯一 `node_id`、限定之 `node_type` 類型分類、人類可讀標籤 `label` 以及記錄任意元數據 payload 的 `properties` 字典。
* `GraphEdge` **SHALL** 包含唯一 `edge_id`、`source_id`、`target_id`、限定之語意化邊關係類型 `edge_type`、人類可讀標籤 `label` 以及 `properties` 屬性。
* `RegulatoryGraph` **SHALL** 以鄰接結構或點邊表的形式聚合所有點與有向邊。
* 系統 **SHALL** 支持將這些模型自動編譯並導出為獨立的 JSON Schemas，用於資料校驗。

#### Scenario: Graph Models Validation
* **GIVEN** 合規圖譜的強型別 `GraphNode`、`GraphEdge` 與 `RegulatoryGraph` 模型。
* **WHEN** 實例化包含多種節點（如 `Clause`、`Obligation` 等）與複雜關係邊（如 `requires_evidence`、`derived_from` 等）的 `RegulatoryGraph` 時。
* **THEN** Pydantic 校驗 **SHALL** 順利通過，且能正確序列化與反序列化為符合 Schema 的 JSON 結構。

---

### Requirement: Regulatory Graph Builder and Decision Weaving

系統 **SHALL** 提供 `GraphBuilder`，能夠將零散的合規實體（Documents, Clauses, Obligations, Concepts, Conflicts, Customers, Checklists）自動轉化並組裝成單一有向圖譜。
* `GraphBuilder` **SHALL** 根據實體間的關聯外鍵（例如 `Obligation` 對應多個 `Clause`）自動生成合規關係邊。
* `GraphBuilder` **MUST** 支援「決策織入 (Decision Weaving)」：當傳入 `ExplanationPath` 時，系統 **SHALL** 自動遍歷解釋路徑中的點與邊，並將其標記為 `decision_path` 屬性，用於高亮顯示 active 的決策傳導鏈。

#### Scenario: Building and Weaving CDD Decision Graph
* **GIVEN** 完整的金標數據集（包含 10 個 clauses、10 個 obligations）以及一個已決策的客戶 `CDDChecklist` 和對應的 `ExplanationPath`。
* **WHEN** 調用 `GraphBuilder.build_regulatory_graph(documents, clauses, obligations, concepts, conflicts, customers, checklists, paths)` 時。
* **THEN** 生成的 `RegulatoryGraph` **SHALL** 包含正確數量的節點與邊：
  * 對應的 `Clause` 節點 **MUST** 正確連接到對應的 `SourceDocument` 節點（邊類型為 `defines` 或 `derived_from`）。
  * 與 `ExplanationPath` 重合的節點與邊的 `properties` 中，`decision_path` 屬性 **MUST** 為 `True`。

---

### Requirement: Multi-hop Graph Traversal and Query

系統 **SHALL** 提供 `GraphQuery`，支援在 `RegulatoryGraph` 上進行高效的點邊遍歷與查詢。
* `GraphQuery` **SHALL** 實作 `find_multi_hop_paths` 方法，能以深度優先 (DFS) 或廣度優先 (BFS) 算法，查詢指定起始節點與目標節點間在限定深度（預設為 3 步）內的所有多步傳導路徑。
* `GraphQuery` **SHALL** 支持獲取指定節點的所有上游溯源節點 (`get_upstream_sources`) 與下游受影響節點 (`get_downstream_targets`)。

#### Scenario: Querying PEP Risk Evidence Lineage Path
* **GIVEN** 一個已構建好的包含 PEP 客戶事實的 `RegulatoryGraph`。
* **WHEN** 調用 `GraphQuery.find_multi_hop_paths` 查詢從特定客戶 Fact 節點出發，傳導至對應必備 EvidenceRequirement 節點的路徑時。
* **THEN** 系統 **SHALL** 返回一條或多條合規傳導鏈，且其路徑順序 **MUST** 為：`CustomerContext` ➔ `Obligation` ➔ `EvidenceRequirement`（或 `Clause` ➔ `Document`）。

---

### Requirement: Interactive Dark Glassmorphic HTML Visualization Export

系統 **SHALL** 提供 `GraphExporter`，能夠將構建好的 `RegulatoryGraph` 導出為一個單一、零依賴（除 D3.js CDN 外）的互動式 HTML 圖譜可視化網頁。
* 導出的 HTML 網頁 **MUST** 採用極致的暗黑色彩漸層背景，且節點應根據其 `node_type` 配備不同的柔和漸變霓虹 HSL 色彩與外發光陰影。
* 網頁中的資訊屬性側邊欄 **MUST** 使用 Vanilla CSS 實作磨砂玻璃擬物美學 (Glassmorphic Card UI)，配備 `backdrop-filter: blur(16px)` 與微細透明邊框。
* 網頁 **SHALL** 支援以下流暢的 D3.js 互動效果：
  * **點擊高亮 (Dynamic Focus Highlight)**：當點擊一個節點時，該節點本身、所有一度關聯（直接相連）與二度關聯（兩步相連）的節點與有向邊 **MUST** 保持 100% 亮度，其餘無關節點與邊 **SHALL** 淡出為極高透明度 (`opacity: 0.1`)。
  * **決策軌跡渲染**：被標記為 `decision_path` 的邊 **SHALL** 被繪製為具備霓虹流光動畫的紅色或金色高亮線條。
  * **屬性抽屜滑出**：點擊節點時，側邊欄抽屜 **SHALL** 以流暢過場動畫滑入並展示該節點的詳細屬性 payload（包含 PII 去敏感與法條明文 quote）。

#### Scenario: Visualizer HTML Integrity Verification
* **GIVEN** 一個包含 active 決策路徑的 `RegulatoryGraph` 實例。
* **WHEN** 調用 `GraphExporter.export_to_html(graph, output_path)` 時。
* **THEN** 在指定路徑生成的文件 **SHALL** 為有效的 HTML：
  * 其內部 **MUST** 含有 D3.js 的 CDN 引入腳本。
  * 其內部 **MUST** 含有完整的 D3.js 力導向布局控制邏輯與 CSS 暗黑玻璃美學樣式。
  * 其內部 **MUST** 將完整的點與邊數據編譯為 JSON 陣列並安全嵌入其中。
