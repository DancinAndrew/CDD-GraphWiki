# Phase 8: Regulatory Graph Construction & Visualization Design

## Architectural Context & Decisions

本變更的技術設計嚴格對齊並依循以下架構決策紀錄 (ADRs)：
- **[ADR-0004: Schema 表示法與 Python Dataclass 策略](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0004-schema-representation-and-python-dataclass-strategy.md)**：我們將在 `src/contracts/models.py` 中使用強型別 Pydantic 模型定義 `GraphNode`、`GraphEdge` 與 `RegulatoryGraph`。隨後，利用現有的編譯指令碼自動將其導出為獨立的 JSON Schemas 契約，保持「具權威性的代碼模型」與「聲明式契約」的混合元模型策略。
- **[ADR-0002: Build compliance knowledge compilation before chat UI](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/docs/adr/0002-build-compliance-knowledge-compilation-before-chat-ui.md)**：本圖譜並不引入 Neo4j、RDF 或其他重型圖數據庫依賴，而是先在 Python 記憶體中使用鄰接結構進行高效推理與表達。透過將圖譜序列化為標準 JSON，結合輕量級 D3.js，輸出單一 HTML 即可實現極致可視化，既保持系統輕量，又具備強大的圖譜功能。

---

## Detailed Design

### 1. Data Contract Models

我們將在 `src/contracts/models.py` 中新增以下強型別模型，用於描述圖譜：

```python
class GraphNode(BaseModel):
    """
    圖譜中的單一合規知識或事實節點。
    """
    node_id: str = Field(..., description="Unique node ID, e.g. 'mas626_clause_04'")
    node_type: Literal[
        "SourceDocument", 
        "Clause", 
        "Concept", 
        "Obligation", 
        "CustomerContext", 
        "Conflict", 
        "CDDChecklist",
        "EvidenceRequirement",
        "RiskTrigger"
    ] = Field(..., description="Node classification type")
    label: str = Field(..., description="Human-readable node title/label")
    properties: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Factual metadata payload, e.g., raw_text, version, attributes"
    )

class GraphEdge(BaseModel):
    """
    圖譜中節點與節點之間的有向關係邊。
    """
    edge_id: str = Field(..., description="Unique edge identifier, e.g. 'nodeA_to_nodeB_requires'")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    edge_type: Literal[
        "defines",              # Concept defines Concept, Document defines Clause
        "requires",             # Obligation requires Evidence
        "applies_to",           # Obligation applies to CustomerType/CustomerContext
        "conditioned_on",       # Obligation conditioned on facts
        "except_when",          # Exception relation
        "requires_evidence",    # Obligation requires EvidenceRequirement
        "references_clause",    # Obligation references Clause, Conflict references Clause
        "same_as",              # Concept alias mapping
        "stricter_than",        # Conflict/Rule comparison
        "supersedes",           # Version superseding
        "conflicts_with",       # Conflict/Rule collision
        "derived_from",         # Provenance lineage relation
        "decision_path"         # Highlighted active decision path
    ] = Field(..., description="Relationship semantic type")
    label: str = Field(..., description="Human-readable edge label")
    properties: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Edge metadata payload, e.g., weight, reasoning_logic"
    )

class RegulatoryGraph(BaseModel):
    """
    大一統法規合規知識圖譜資料結構。
    """
    nodes: Dict[str, GraphNode] = Field(default_factory=dict, description="Fast access map of node ID to Node")
    edges: List[GraphEdge] = Field(default_factory=list, description="Collection of all relationship edges")
```

### 2. Graph Builder and Query Traversal (`src/graph/builder.py`)

* **`GraphBuilder`**：
  * 實作 `build_regulatory_graph(documents, clauses, obligations, concepts, conflicts, customers=None, checklists=None, paths=None) -> RegulatoryGraph` 方法。
  * 對於每一種類型的物件，自動映射為 `GraphNode`，並根據內部關聯（例如 `Obligation.source_clause_ids` 指向 `Clause.clause_id`）自動建立 `GraphEdge`。
  * **決策織入 (Decision Weaving)**：如果提供了 `paths` (`ExplanationPath` 列表)，`GraphBuilder` 會自動遍歷這些路徑，並在圖譜中為對應的節點與邊加上 `"decision_path"` 屬性標記，以便在可視化網頁中高亮顯示 active 決策鏈。
* **`GraphQuery`**：
  * 實作 `find_multi_hop_paths(graph: RegulatoryGraph, start_node_id: str, max_depth: int = 3) -> List[List[GraphNode]]` 深度優先或廣度優先搜尋方法，以支援多步關係查詢。
  * 實作 `get_upstream_sources(graph: RegulatoryGraph, node_id: str) -> List[GraphNode]` 與 `get_downstream_targets(graph: RegulatoryGraph, node_id: str) -> List[GraphNode]`，用於快速提取條款溯源和影響範圍分析。

### 3. Premium Interactive Visualization (`src/graph/visualization.py`)

為了符合極致美感與高級動態體驗，`GraphExporter` 將生成一個包含 D3.js 力導向布局的單一 HTML 頁面。

#### **設計美學規格 (Visual Design Spec - Vanilla CSS)**：
* **背景與調色盤 (Aesthetic Theme)**：
  * 採用極致的暗黑色彩方案：深黑渐變背景 `linear-gradient(135deg, #0a0e17 0%, #121824 100%)`。
  * 各類型節點配備專屬的柔和漸變霓虹色彩（利用 CSS HSL 控制，加上 `box-shadow` 與 `filter: drop-shadow` 營造發光霓虹感）：
    * `SourceDocument`：霓虹柔藍 (`hsl(210, 100%, 65%)`)
    * `Clause`：翡翠綠 (`hsl(150, 80%, 55%)`)
    * `Concept`：琥珀黃 (`hsl(45, 100%, 60%)`)
    * `Obligation`：魔幻紫 (`hsl(280, 90%, 65%)`)
    * `CustomerContext`：皇家橘 (`hsl(25, 100%, 60%)`)
    * `Conflict`：火山紅 (`hsl(10, 100%, 60%)`)
    * `CDDChecklist`：極光青 (`hsl(180, 100%, 50%)`)
* **磨砂玻璃側邊欄 (Glassmorphic Sidebar)**：
  * 側邊資訊面板使用現代玻璃擬物化風格：`background: rgba(255, 255, 255, 0.03)`，配備 `backdrop-filter: blur(16px)` 與極細透明邊框 `border: 1px solid rgba(255, 255, 255, 0.08)`，營造極致的高級感。
  * 點擊節點時，側邊欄會優雅地以 `transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)` 滑出，展示節點屬性，並以 markdown 風格排版展示法條明文。
* **D3.js 力導向力學與互動 (Interactive Force Mechanics)**：
  * D3 `d3.forceSimulation()` 設定柔和的彈簧力與碰撞力，支持流暢拖曳。
  * **滑鼠懸停 (Hover)**：節點放大 1.2 倍，並產生柔和的外發光陰影。
  * **點擊高亮 (Dynamic Focus / Click Interaction)**：點擊任一節點時，其餘無關節點與邊的透明度會降至 `0.1` (`opacity: 0.1`)，而該節點本身、所有一度關聯（直接相連）與二度關聯（兩步相連）的節點與邊會維持 100% 亮度並加粗亮起，呈現極富科技感的「決策流向」與「影響範圍」。
  * **決策路徑加亮 (Active Path Highlight)**：屬於 `decision_path` 的邊將繪製為帶有動態流光動畫的紅色或金色線條，展示決策傳導的軌跡。

---

## Files to be Added and Modified

```diff
  src/
    contracts/
+     __init__.py (Modify: export GraphNode, GraphEdge, RegulatoryGraph)
+     models.py (Modify: add GraphNode, GraphEdge, RegulatoryGraph models)
    graph/
+     __init__.py (New: export GraphBuilder, GraphQuery, GraphExporter)
+     builder.py (New: GraphBuilder with decision weaving, GraphQuery traversals)
+     visualization.py (New: GraphExporter exporting gorgeous dark glassmorphic D3 HTML)
  tests/
+   test_regulatory_graph.py (New: 100% coverage unit tests)
```

---

## Verification & Testing Plan

### Automated Tests
我們將建立 `tests/test_regulatory_graph.py` 測試套件，包含以下驗證場景：
1. **Model Validation**：驗證 `GraphNode`、`GraphEdge` 與 `RegulatoryGraph` 的 Pydantic 實例化與 JSON Schema 編譯。
2. **Graph Construction Verification**：使用金標數據（FATF 10, MAS 626, 內規），驗證 `GraphBuilder` 是否能無縫且正確地建立所有對應節點與邊，並且沒有丟失任何屬性。
3. **Decision Weaving Verification**：驗證將 `ExplanationPath` 織入圖譜後，對應節點與邊的 `decision_path` 屬性是否被正確標記為 `True`。
4. **Multi-hop Traversal Verification**：撰寫測試驗證 `GraphQuery` 是否能正確查詢多步關聯，例如：驗證從客戶事實 PEP 出發，可以多步遍歷到 `mas626_clause_04` 以及必須要求的證據文件。
5. **HTML Visualization Export Verification**：驗證 `GraphExporter` 生成的 HTML 內容，確保 d3.js 的導入、節點數據的 JSON 序列化嵌入以及 Vanilla CSS 的磨砂玻璃美學樣式均完整無缺。
6. **OpenSpec Change 驗證**：
   ```bash
   openspec validate create-regulatory-graph-construction --strict --no-interactive
   ```
7. **完整測試套件執行**：
   ```bash
   .venv/bin/python -m pytest tests/ -v
   ```

### Manual Verification
* 執行測試生成一個真實的 `regulatory_graph.html` 網頁檔。
* 使用 Chrome 瀏覽器打開此網頁，手動測試：
  - 拖曳節點、縮放畫布是否流暢。
  - 懸停與點擊節點是否正確觸發一度/二度高亮特效與玻璃側邊屬性面板的滑入。
  - 驗證 active 決策鏈（紅/金色霓虹流光線條）在圖中是否清晰可辨。
