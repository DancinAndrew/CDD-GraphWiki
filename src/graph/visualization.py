import json
import html
from typing import Dict, Any
from src.contracts.models import RegulatoryGraph


class GraphExporter:
    """
    法規合規圖譜高級可視化導出器，負責將圖譜編譯導出為極致暗黑玻璃擬物美學 (Dark Glassmorphic UI) 的 D3.js 互動 HTML 網頁。
    """

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDD-GraphWiki - 法規合規知識圖譜可視化</title>
    <!-- 引入 D3.js V7 CDN -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        /* 極致暗黑美學 Vanilla CSS 設計 */
        :root {
            --bg-gradient: linear-gradient(135deg, #0a0e17 0%, #121824 100%);
            --panel-bg: rgba(20, 26, 38, 0.4);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            
            /* HSL 霓虹調色盤 */
            --color-document: hsl(210, 100%, 65%);     /* 柔藍 */
            --color-clause: hsl(150, 80%, 55%);        /* 翡翠綠 */
            --color-concept: hsl(45, 100%, 60%);       /* 琥珀黃 */
            --color-obligation: hsl(280, 90%, 65%);     /* 魔幻紫 */
            --color-evidence: hsl(320, 100%, 65%);     /* 亮粉紅 */
            --color-risk: hsl(0, 100%, 65%);           /* 亮紅 */
            --color-conflict: hsl(15, 100%, 60%);      /* 火山橘 */
            --color-customer: hsl(35, 100%, 60%);      /* 皇家黃 */
            --color-checklist: hsl(180, 100%, 50%);    /* 極光青 */
        }

        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: var(--bg-gradient);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans TC", sans-serif;
            color: var(--text-primary);
            overflow: hidden;
        }

        /* 頂級背景網格效果 */
        #canvas-container {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            background-image: 
                radial-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 0),
                radial-gradient(rgba(255, 255, 255, 0.01) 2px, transparent 0);
            background-size: 20px 20px, 40px 40px;
            z-index: 1;
        }

        svg {
            width: 100%;
            height: 100%;
            cursor: grab;
        }
        svg:active {
            cursor: grabbing;
        }

        /* 玻璃擬物標題與控制面板 (Glassmorphic Header Panel) */
        .glass-panel {
            position: fixed;
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            z-index: 10;
        }

        .header-panel {
            top: 20px;
            left: 20px;
            padding: 16px 24px;
        }

        .header-panel h1 {
            margin: 0;
            font-size: 1.4rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            background: linear-gradient(90deg, #58a6ff 0%, #bc8cff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-panel p {
            margin: 4px 0 0 0;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* 左下角圖例說明面板 (Legend Panel) */
        .legend-panel {
            bottom: 20px;
            left: 20px;
            padding: 16px;
            font-size: 0.75rem;
            max-width: 260px;
        }

        .legend-title {
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 4px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin: 6px 0;
        }

        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            box-shadow: 0 0 8px currentColor;
        }

        /* 磨砂玻璃側邊欄屬性抽屜 (Glassmorphic Drawer Sidebar) */
        .sidebar {
            position: fixed;
            top: 20px;
            right: -420px; /* 初始隱藏 */
            width: 380px;
            height: calc(100vh - 40px);
            padding: 24px;
            overflow-y: auto;
            box-sizing: border-box;
            transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 100;
        }

        .sidebar.active {
            transform: translateX(-440px); /* 滑入顯示 */
        }

        .close-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.2rem;
            cursor: pointer;
            transition: color 0.2s;
        }

        .close-btn:hover {
            color: var(--text-primary);
        }

        .sidebar h2 {
            margin: 0 0 16px 0;
            font-size: 1.25rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
        }

        .node-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 16px;
            box-shadow: 0 0 10px currentColor;
        }

        .property-group {
            margin-bottom: 16px;
        }

        .property-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .property-value {
            font-size: 0.85rem;
            line-height: 1.5;
            background: rgba(0, 0, 0, 0.2);
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.04);
            white-space: pre-wrap;
            word-break: break-word;
        }

        /* D3 圖譜節點與邊的 SVG 樣式 */
        .node circle {
            stroke-width: 2px;
            transition: stroke-width 0.2s, filter 0.2s;
            cursor: pointer;
        }

        .node text {
            font-size: 10px;
            font-weight: 600;
            fill: #c9d1d9;
            pointer-events: none;
            text-anchor: middle;
            transition: opacity 0.2s, font-size 0.2s;
        }

        /* 邊關係樣式 */
        .link {
            fill: none;
            stroke: rgba(255, 255, 255, 0.12);
            stroke-width: 1.5px;
            transition: stroke 0.3s, stroke-width 0.3s, opacity 0.3s;
        }

        /* 決策路徑 (Decision Path) 高亮流光動畫樣式 */
        .link.decision-path {
            stroke: #ff7b72;
            stroke-width: 3.5px !important;
            stroke-dasharray: 8 5;
            animation: linkFlow 25s linear infinite;
        }

        @keyframes linkFlow {
            to {
                stroke-dashoffset: -1000;
            }
        }

        /* 重置按鈕 */
        .reset-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--panel-bg);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 10px 16px;
            border-radius: 8px;
            font-size: 0.8rem;
            cursor: pointer;
            backdrop-filter: blur(10px);
            z-index: 10;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            transition: background 0.2s, border-color 0.2s;
        }

        .reset-btn:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.2);
        }

        /* PII 敏感數據去敏感展示 */
        .redacted {
            color: #ff7b72;
            font-family: monospace;
            background: rgba(255, 123, 114, 0.1);
            padding: 2px 4px;
            border-radius: 4px;
        }
    </style>
</head>
<body>

    <!-- 頂端標題 -->
    <div class="glass-panel header-panel">
        <h1>CDD-GraphWiki</h1>
        <p>法規合規知識圖譜與決策傳導網路 (Interactive Force-Directed Graph)</p>
    </div>

    <!-- 圖例說明 -->
    <div class="glass-panel legend-panel">
        <div class="legend-title">合規圖譜圖例</div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-document); background: var(--color-document)"></div><span>SourceDocument (法規文件)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-clause); background: var(--color-clause)"></div><span>Clause (法條條款)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-concept); background: var(--color-concept)"></div><span>Concept (核心概念)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-obligation); background: var(--color-obligation)"></div><span>Obligation (合規義務)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-evidence); background: var(--color-evidence)"></div><span>EvidenceRequirement (佐證證據)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-risk); background: var(--color-risk)"></div><span>RiskTrigger (風險條件)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-conflict); background: var(--color-conflict)"></div><span>Conflict (政策衝突)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-customer); background: var(--color-customer)"></div><span>CustomerContext (客戶情境)</span></div>
        <div class="legend-item"><div class="legend-color" style="color: var(--color-checklist); background: var(--color-checklist)"></div><span>CDDChecklist (決策結果)</span></div>
    </div>

    <!-- 側邊欄屬性面版 -->
    <div id="sidebar-panel" class="glass-panel sidebar">
        <button class="close-btn" onclick="closeSidebar()">&times;</button>
        <span id="node-badge" class="node-badge">Clause</span>
        <h2 id="node-label">節點名稱</h2>
        
        <div class="property-group">
            <div class="property-label">唯一識別碼 (ID)</div>
            <div id="node-id" class="property-value">id</div>
        </div>
        
        <div id="properties-container">
            <!-- 動態插入節點屬性 -->
        </div>
    </div>

    <!-- 重置視角按鈕 -->
    <button class="reset-btn" onclick="resetZoom()">重置圖譜視角</button>

    <!-- D3 畫布容器 -->
    <div id="canvas-container">
        <svg id="graph-svg"></svg>
    </div>

    <script>
        // 嵌入的圖譜 JSON 數據
        const graphData = %GRAPH_DATA%;

        // HSL 配色查找表
        const typeColors = {
            "SourceDocument": "var(--color-document)",
            "Clause": "var(--color-clause)",
            "Concept": "var(--color-concept)",
            "Obligation": "var(--color-obligation)",
            "EvidenceRequirement": "var(--color-evidence)",
            "RiskTrigger": "var(--color-risk)",
            "Conflict": "var(--color-conflict)",
            "CustomerContext": "var(--color-customer)",
            "CDDChecklist": "var(--color-checklist)"
        };

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph-svg");
        const g = svg.append("g");

        // 設置有向邊的箭頭標記 (Arrow Markers)
        svg.append("defs").selectAll("marker")
            .data(["normal", "decision"])
            .enter().append("marker")
            .attr("id", d => `arrow-${d}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 22) // 箭頭相對於節點圓心的距離
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-4L9,0L0,4")
            .attr("fill", d => d === "decision" ? "#ff7b72" : "rgba(255, 255, 255, 0.25)");

        // 設置縮放與平移 (Zoom & Drag Canvas)
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });
        svg.call(zoom);

        // 建立力導向物理引擎 (Force Simulation)
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.node_id).distance(130))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(35));

        // 繪製關係邊
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links)
            .enter().append("line")
            .attr("class", d => d.properties.decision_path ? "link decision-path" : "link")
            .attr("marker-end", d => d.properties.decision_path ? "url(#arrow-decision)" : "url(#arrow-normal)");

        // 建立節點容器群組
        const node = g.append("g")
            .selectAll(".node")
            .data(graphData.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("click", handleNodeClick);

        // 繪製節點圓圈
        node.append("circle")
            .attr("r", d => d.properties.decision_path ? 14 : 12)
            .attr("fill", d => typeColors[d.node_type] || "#999")
            .attr("stroke", d => d.properties.decision_path ? "#ff7b72" : "rgba(255,255,255,0.2)")
            .style("filter", d => d.properties.decision_path ? "drop-shadow(0 0 10px #ff7b72)" : "none");

        // 繪製節點文字標籤 (下方文字)
        node.append("text")
            .attr("dy", 24)
            .attr("font-size", "10px")
            .text(d => d.label);

        // 物理引擎 Tick 更新坐標
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("transform", d => `translate(${d.x}, ${d.y})`);
        });

        // 點擊節點高亮特效 (Dynamic Focus / Click Interaction)
        let selectedNode = null;

        function handleNodeClick(event, d) {
            event.stopPropagation();
            selectedNode = d;

            // 1. 滑出側邊屬性面版
            showSidebar(d);

            // 2. 尋找與該點直接相連的一度、二度節點與邊
            const connectedNodeIds = new Set([d.node_id]);
            const connectedEdgeIds = new Set();

            // 一度關聯
            graphData.links.forEach(l => {
                if (l.source.node_id === d.node_id) {
                    connectedNodeIds.add(l.target.node_id);
                    connectedEdgeIds.add(l.edge_id);
                } else if (l.target.node_id === d.node_id) {
                    connectedNodeIds.add(l.source.node_id);
                    connectedEdgeIds.add(l.edge_id);
                }
            });

            // 二度關聯 (多步傳導 Multi-hop Trace)
            graphData.links.forEach(l => {
                const s = l.source.node_id;
                const t = l.target.node_id;
                if (connectedNodeIds.has(s) && !connectedNodeIds.has(t)) {
                    // 若起點已是一度，終點歸入二度
                    if (s !== d.node_id) { // 避免重複加入
                        connectedNodeIds.add(t);
                        connectedEdgeIds.add(l.edge_id);
                    }
                } else if (connectedNodeIds.has(t) && !connectedNodeIds.has(s)) {
                    if (t !== d.node_id) {
                        connectedNodeIds.add(s);
                        connectedEdgeIds.add(l.edge_id);
                    }
                }
            });

            // 3. 高亮變色：無關點與邊變淡為 0.1 透明度
            node.transition().duration(300)
                .style("opacity", n => connectedNodeIds.has(n.node_id) ? 1.0 : 0.08)
                .select("circle")
                .attr("r", n => n.node_id === d.node_id ? 16 : (n.properties.decision_path ? 14 : 12))
                .style("filter", n => n.node_id === d.node_id ? "drop-shadow(0 0 12px currentColor)" : (n.properties.decision_path ? "drop-shadow(0 0 8px #ff7b72)" : "none"));

            link.transition().duration(300)
                .style("opacity", l => connectedEdgeIds.has(l.edge_id) ? 1.0 : 0.08)
                .style("stroke-width", l => connectedEdgeIds.has(l.edge_id) ? 3.0 : 1.5);
        }

        // 點擊畫布空白處重置高亮狀態
        svg.on("click", () => {
            selectedNode = null;
            closeSidebar();

            node.transition().duration(300)
                .style("opacity", 1.0)
                .select("circle")
                .attr("r", n => n.properties.decision_path ? 14 : 12)
                .style("filter", n => n.properties.decision_path ? "drop-shadow(0 0 8px #ff7b72)" : "none");

            link.transition().duration(300)
                .style("opacity", 1.0)
                .style("stroke-width", l => l.properties.decision_path ? 3.5 : 1.5);
        });

        // 展示側邊欄，對 PII 數據做去敏感 (PII Redaction)
        function showSidebar(nodeData) {
            const sidebar = document.getElementById("sidebar-panel");
            sidebar.classList.add("active");

            // 設置標題與 Badge
            const badge = document.getElementById("node-badge");
            badge.innerText = nodeData.node_type;
            badge.style.color = typeColors[nodeData.node_type];
            badge.style.borderColor = typeColors[nodeData.node_type];
            
            document.getElementById("node-label").innerText = nodeData.label;
            document.getElementById("node-id").innerText = nodeData.node_id;

            // 填充屬性內容
            const container = document.getElementById("properties-container");
            container.innerHTML = "";

            const props = nodeData.properties;
            const skipKeys = ["node_id", "node_type", "label", "decision_path"];

            for (let key in props) {
                if (skipKeys.includes(key)) continue;

                let val = props[key];
                if (val === null || val === undefined) continue;

                // 若是複雜物件/陣列，轉為 JSON 字串
                if (typeof val === 'object') {
                    val = JSON.stringify(val, null, 2);
                }

                // 進行 PII 去敏感過濾（例如若為 customer_id 或包含身分證字號等）
                let displayVal = val.toString();
                if (key.includes("customer_id") || key.includes("customer_name") || key.includes("identity_number")) {
                    if (displayVal.length > 4) {
                        displayVal = displayVal.substring(0, 3) + "****" + displayVal.substring(displayVal.length - 2);
                        displayVal = `<span class="redacted">${displayVal} (敏感去識別)</span>`;
                    }
                }

                // 若 properties 裡有決策高亮路徑，給予特殊展示
                if (key === "explained_items") {
                    displayVal = JSON.parse(val).map(item => `🎯 ${item}`).join("<br/>");
                }

                const propGroup = document.createElement("div");
                propGroup.className = "property-group";
                propGroup.innerHTML = `
                    <div class="property-label">${formatKeyLabel(key)}</div>
                    <div class="property-value">${displayVal}</div>
                `;
                container.appendChild(propGroup);
            }
        }

        function formatKeyLabel(key) {
            // 轉換底線命名的欄位為人類易讀格式
            return key.replace(/_/g, " ").toUpperCase();
        }

        function closeSidebar() {
            document.getElementById("sidebar-panel").classList.remove("active");
        }

        // 重置縮放視角 (Reset Zoom Viewport)
        function resetZoom() {
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }

        // 拖曳物理引擎控制
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // 自動響應瀏覽器視窗大小調整
        window.addEventListener("resize", () => {
            const w = window.innerWidth;
            const h = window.innerHeight;
            svg.attr("width", w).attr("height", h);
            simulation.force("center", d3.forceCenter(w / 2, h / 2)).restart();
        });
    </script>
</body>
</html>
"""

    @classmethod
    def export_to_html(cls, graph: RegulatoryGraph, output_path: str) -> None:
        """
        將 RegulatoryGraph 圖譜數據編譯並寫入至一個漂亮的互動式 HTML 網頁。
        
        Args:
            graph: 要導出的 RegulatoryGraph 物件
            output_path: 目標 HTML 檔案的絕對輸出路徑
        """
        # 1. 將圖譜轉換為 D3.js 期待的 nodes 與 links 數據結構
        d3_nodes = []
        for nid, node in graph.nodes.items():
            d3_nodes.append({
                "node_id": node.node_id,
                "node_type": node.node_type,
                "label": node.label,
                "properties": node.properties
            })

        d3_links = []
        for edge in graph.edges:
            d3_links.append({
                "edge_id": edge.edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "edge_type": edge.edge_type,
                "label": edge.label,
                "properties": edge.properties
            })

        graph_payload = {
            "nodes": d3_nodes,
            "links": d3_links
        }

        # 2. 序列化為 JSON 字串
        graph_json_str = json.dumps(graph_payload, indent=2, ensure_ascii=False)

        # 3. 填充進入 HTML 模版中
        final_html = cls.HTML_TEMPLATE.replace("%GRAPH_DATA%", graph_json_str)

        # 4. 寫入目標檔案
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_html)

        print(f"Successfully exported interactive graph visualizer to {output_path}")
