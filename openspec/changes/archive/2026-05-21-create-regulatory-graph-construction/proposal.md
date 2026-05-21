# Phase 8: Regulatory Graph Construction & Visualization Proposal

## Why

在反洗錢與客戶盡職調查 (AML/CDD) 合規審查中，合規規則、來源法條、適用義務、事實證據與潛在內外規衝突並非孤立存在，而是交織成一張錯綜複雜的網狀結構。

雖然 Phase 7 實作的線性解釋路徑 (Explanation Path) 為特定決策提供了局部的可追溯性，但合規官員與審計人員依然缺乏一種「全局鳥瞰」的視野。他們無法直觀、動態地觀察到合規條款在不同實體間的傳導關係，亦無法輕易進行多步圖遍歷 (Multi-hop Query) 來發掘潛在的合規盲點與政策衝突。

**Regulatory Graph Construction & Visualization** 旨在將編譯好的合規知識物件（包括 `SourceDocument`、`Clause`、`Obligation`、`CustomerContext`、`Concept` 與 `Conflict`）構建成一張機器可推理、人類可交互的「法規合規知識圖譜」(Regulatory Compliance Knowledge Graph)。透過實作強型別圖譜合約、多步遍歷查詢，以及輸出配備極致暗黑玻璃擬物美學 (Dark Glassmorphic UI) 的 D3.js 互動式 HTML 可視化網頁，能將複雜的合規判斷過程以具備高度視覺衝擊力、可互動、可追溯的方式展現給使用者，大幅提升 CDD 決策的透明度與可信賴感。

## What Changes

1. **強型別圖譜資料合約定義**：
   在 `src/contracts/models.py` 中新增 `GraphNode`、`GraphEdge` 與 `RegulatoryGraph` 的 Pydantic 資料模型，並將其自動編譯導出為 JSON Schemas 契約，保障圖譜序列化與跨系統互操作性的嚴謹性。
2. **實作法規圖譜構建與查詢引擎**：
   建立 `src/graph/builder.py` 模組，實作 `GraphBuilder` 與 `GraphQuery`。
   * `GraphBuilder` 支援載入已解析的法源條文、金標義務、客戶事實、關聯概念以及 CDD 決策，將它們對應映射並編譯為圖譜中的節點與有向關係邊。
   * 支持動態將 Phase 7 產出的 `ExplanationPath` 織入 (weave) 圖譜，以便高亮顯示該決策路徑。
   * `GraphQuery` 支援多步遍歷與檢索，能從特定節點出發進行關聯傳導查詢（例如：「從高風險客戶事實出發，經過哪些義務，最終關聯到哪些證據要求與法源條文？」）。
3. **極致美感互動 HTML 圖譜導出器**：
   建立 `src/graph/visualization.py` 模組，實作 `GraphExporter`。它能將 `RegulatoryGraph` 動態編譯並嵌入到一個單一、零依賴（除 D3.js CDN 外）的互動式 HTML 圖譜網頁中。
   * 網頁採用頂尖的 **Vanilla CSS** 進行排版與設計（完全不依賴 Tailwind，遵循 `gemini.md` 最高憲法）。
   * 具備 Rich Aesthetics：使用極致的深色漸層背景、磨砂玻璃擬物化 (Glassmorphic) 屬性面板、霓虹漸層節點色彩與柔和發光陰影。
   * 配備 D3.js 力導向布局與流暢互動：點擊節點會觸發動態的焦點高亮，將其鄰近的一度與二度關聯路徑加粗亮起，而無關節點則優雅淡出 (fade-out)。同時側邊欄會滑出該節點的詳細屬性與法規條文明文 quote。
4. **全自動單元測試套件**：
   建立 `tests/test_regulatory_graph.py`，針對圖譜組裝完整性、圖遍歷查詢精確度、邊關係方向性以及 HTML 導出內容進行 100% 覆蓋測試。

## Capabilities

- **Unified Compliance Knowledge Graph**：將所有零散的法規、條款、概念、內規與事實，融合為單一可推理的有向圖譜，消除合規信息孤島。
- **Interactive Multi-hop Discovery**：允許合規官員以圖遍歷方式查詢任何實體，一鍵發掘「事實 ➔ 義務 ➔ 條文 ➔ 證據」的多步關聯。
- **Premium Dynamic Visualization**：生成免安裝、高度流暢、極致美觀的互動式力導向圖可視化 HTML，提供極具專業感的演示與審計體驗。

## Impact

- 使 CDD-GraphWiki 具備成熟的「圖譜合規推理 (Graph-augmented Compliance Reasoning)」與「合規可視化」能力。
- 奠定了未來進行多源法規 Gap 分析、政策版本更迭追蹤等高階圖譜應用的底層基礎。
