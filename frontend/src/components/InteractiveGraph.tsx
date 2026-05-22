import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Network, Info, Eye, EyeOff } from 'lucide-react';

interface Node extends d3.SimulationNodeDatum {
  node_id: string;
  node_type: string;
  label: string;
  properties: Record<string, any>;
  x?: number;
  y?: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  edge_id: string;
  source: string | Node;
  target: string | Node;
  edge_type: string;
  label: string;
  properties: Record<string, any>;
}

export const InteractiveGraph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [legendVisible, setLegendVisible] = useState(true);
  const [dataStats, setDataStats] = useState({ nodes: 0, links: 0 });

  useEffect(() => {
    setLoading(true);
    fetch('http://localhost:8000/api/v1/graph')
      .then(res => res.json())
      .then((data: { nodes: any[]; links: any[] }) => {
        setDataStats({ nodes: data.nodes.length, links: data.links.length });
        renderGraph(data.nodes, data.links);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching graph data:', err);
        setLoading(false);
      });
  }, []);

  const renderGraph = (nodesData: any[], linksData: any[]) => {
    if (!svgRef.current) return;
    
    // 清除舊圖表
    d3.select(svgRef.current).selectAll('*').remove();

    const width = 800;
    const height = 550;
    const svg = d3.select(svgRef.current)
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('background', 'rgba(11, 12, 16, 0.4)');

    // 1. 添加 SVG Glow 發光濾鏡 (打造霓虹磨砂感)
    const defs = svg.append('defs');
    
    const filter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-30%')
      .attr('y', '-30%')
      .attr('width', '160%')
      .attr('height', '160%');

    filter.append('feGaussianBlur')
      .attr('stdDeviation', '4')
      .attr('result', 'coloredBlur');

    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    // 2. 定義關係連線箭頭
    defs.selectAll('marker')
      .data(['arrow-default', 'arrow-highlighted'])
      .enter().append('marker')
      .attr('id', d => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22) // 離節點圓心的距離，避免箭頭被圓遮住
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L10,0L0,4')
      .attr('fill', d => d === 'arrow-highlighted' ? 'var(--primary)' : 'rgba(255, 255, 255, 0.15)');

    // 建立畫布容器，支持 Zoom 縮放
    const g = svg.append('g').attr('class', 'graph-container');

    // 啟用 Zoom 縮放與拖拽畫布
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    svg.call(zoomBehavior);

    // 複製節點與邊數據以供 Simulation 使用
    const nodes: Node[] = nodesData.map(d => ({ ...d }));
    const links: Link[] = linksData.map(d => ({ ...d }));

    // 3. 建立 D3 力導向力學物理引擎
    const simulation = d3.forceSimulation<Node>(nodes)
      .force('link', d3.forceLink<Node, Link>(links).id(d => d.node_id).distance(120))
      .force('charge', d3.forceManyBody().strength(-180))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(25));

    // 4. 繪製邊 (Links)
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', 'rgba(255, 255, 255, 0.08)')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrow-default)')
      .style('transition', 'stroke 0.2s');

    // 5. 繪製邊文字標籤
    const linkText = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(links)
      .enter().append('text')
      .attr('font-size', '7px')
      .attr('fill', 'rgba(255, 255, 255, 0.25)')
      .attr('text-anchor', 'middle')
      .text(d => d.label);

    // 6. 繪製節點圓圈組 (Nodes)
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('.node-group')
      .data(nodes)
      .enter().append('g')
      .attr('class', 'node-group')
      .call(d3.drag<SVGGElement, Node>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
      );

    // 歸一化節點類型 (相容後端強型別與大小寫)
    const normalizeType = (type: string) => {
      if (!type) return '';
      const t = type.toLowerCase();
      if (t.includes('document')) return 'document';
      if (t.includes('clause')) return 'clause';
      if (t.includes('obligation')) return 'obligation';
      if (t.includes('conflict')) return 'conflict';
      if (t.includes('customer')) return 'customer';
      if (t.includes('checklist')) return 'checklist';
      return t;
    };

    // 節點配色系統 (和 CSS 設計相容，採用高相容性十六進位色碼)
    const getNodeColor = (type: string) => {
      const normalized = normalizeType(type);
      switch (normalized) {
        case 'document': return '#4facfe';   // 法規文件 (藍)
        case 'clause': return '#00f2fe';     // 法規條款 (青)
        case 'obligation': return '#a855f7'; // 合規義務 (紫)
        case 'conflict': return '#ff1744';   // 義務衝突 (紅)
        case 'customer': return '#ffb300';   // 客戶個案 (黃)
        case 'checklist': return '#00e676';  // 推理決策 (綠)
        default: return '#8b9bb4';           // 預設 (灰)
      }
    };

    // 繪製節點圓形與發光
    node.append('circle')
      .attr('r', d => {
        const norm = normalizeType(d.node_type);
        return norm === 'document' || norm === 'customer' ? 14 : 10;
      })
      .attr('fill', d => getNodeColor(d.node_type))
      .attr('stroke', 'rgba(255, 255, 255, 0.15)')
      .attr('stroke-width', 1.5)
      .style('cursor', 'pointer')
      .style('filter', d => {
        const norm = normalizeType(d.node_type);
        return norm === 'conflict' || norm === 'checklist' ? 'url(#glow)' : 'none';
      });

    // 繪製節點文字
    node.append('text')
      .attr('dy', d => {
        const norm = normalizeType(d.node_type);
        return norm === 'document' || norm === 'customer' ? 22 : 18;
      })
      .attr('text-anchor', 'middle')
      .attr('fill', '#e2e8f0')
      .attr('font-size', '8px')
      .attr('font-weight', d => {
        const norm = normalizeType(d.node_type);
        return norm === 'document' || norm === 'customer' ? 'bold' : 'normal';
      })
      .style('pointer-events', 'none')
      .text(d => d.label.length > 12 ? `${d.label.slice(0, 10)}...` : d.label);

    // 7. 實現點擊與 Hover 高亮路徑功能 (WOW Visuals)
    node.on('click', function(event, d) {
      setSelectedNode(d);

      // 高亮關聯節點與邊
      const connectedNodeIds = new Set<string>();
      connectedNodeIds.add(d.node_id);

      links.forEach(l => {
        const sourceId = typeof l.source === 'object' ? (l.source as Node).node_id : l.source;
        const targetId = typeof l.target === 'object' ? (l.target as Node).node_id : l.target;
        
        if (sourceId === d.node_id) connectedNodeIds.add(targetId);
        if (targetId === d.node_id) connectedNodeIds.add(sourceId);
      });

      // 虛擬化非關聯邊與高亮關聯邊
      link.attr('stroke', (l: any) => {
        const sourceId = l.source.node_id;
        const targetId = l.target.node_id;
        if (sourceId === d.node_id || targetId === d.node_id) {
          return 'var(--primary)';
        }
        return 'rgba(255, 255, 255, 0.02)';
      })
      .attr('stroke-width', (l: any) => {
        const sourceId = l.source.node_id;
        const targetId = l.target.node_id;
        return (sourceId === d.node_id || targetId === d.node_id) ? 2.5 : 1;
      })
      .attr('marker-end', (l: any) => {
        const sourceId = l.source.node_id;
        const targetId = l.target.node_id;
        return (sourceId === d.node_id || targetId === d.node_id) ? 'url(#arrow-highlighted)' : 'url(#arrow-default)';
      });

      // 虛擬化非關聯節點
      node.style('opacity', (n: any) => connectedNodeIds.has(n.node_id) ? 1 : 0.15);
      
      // 阻止事件冒泡到 SVG 背景上
      event.stopPropagation();
    });

    // 點擊 SVG 背景時，重置所有高亮
    svg.on('click', () => {
      setSelectedNode(null);
      link.attr('stroke', 'rgba(255, 255, 255, 0.08)')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrow-default)');
      node.style('opacity', 1);
    });

    // 8. 力學物理引擎迭代 Tick 運算更新點邊坐標
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as Node).x || 0)
        .attr('y1', d => (d.source as Node).y || 0)
        .attr('x2', d => (d.target as Node).x || 0)
        .attr('y2', d => (d.target as Node).y || 0);

      linkText
        .attr('x', d => {
          const s = d.source as Node;
          const t = d.target as Node;
          return ((s.x || 0) + (t.x || 0)) / 2;
        })
        .attr('y', d => {
          const s = d.source as Node;
          const t = d.target as Node;
          return ((s.y || 0) + (t.y || 0)) / 2 - 4;
        });

      node.attr('transform', d => `translate(${d.x || 0}, ${d.y || 0})`);
    });

    // 拖曳控制元件
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 className="display-title" style={styles.title}>法規與決策可視化圖譜</h1>
          <p style={styles.subtitle}>穿透法規條款節點、客戶實體與決策推理 Checklists 之間的拓撲關係鏈路圖</p>
        </div>
      </header>

      {loading ? (
        <div style={styles.loadingWrapper}>載入 D3 力導向關係圖譜中...</div>
      ) : (
        <div style={styles.mainLayout}>
          {/* 左側：圖譜畫布與工具欄 */}
          <div className="glass-card" style={styles.canvasCard}>
            <div style={styles.canvasHeader}>
              <div style={styles.canvasTitleWrap}>
                <Network size={16} color="var(--primary)" />
                <span style={styles.canvasTitle}>D3.js 力導向關係圖 (共 {dataStats.nodes} 點，{dataStats.links} 邊)</span>
              </div>
              <button 
                onClick={() => setLegendVisible(!legendVisible)}
                style={styles.legendToggle}
              >
                {legendVisible ? <EyeOff size={14} /> : <Eye size={14} />}
                {legendVisible ? '隱藏圖例' : '顯示圖例'}
              </button>
            </div>

            <div style={styles.canvasWrapper}>
              <svg ref={svgRef} style={styles.svg} />
              
              {/* 圖例 */}
              {legendVisible && (
                <div style={styles.legend}>
                  {[
                    { type: 'document', label: '法規文件', color: '#4facfe' },
                    { type: 'clause', label: '法規條款', color: '#00f2fe' },
                    { type: 'obligation', label: '合規義務', color: '#a855f7' },
                    { type: 'conflict', label: '義務衝突', color: '#ff1744' },
                    { type: 'customer', label: '客戶個案', color: '#ffb300' },
                    { type: 'checklist', label: '推理決策', color: '#00e676' }
                  ].map(item => (
                    <div key={item.type} style={styles.legendItem}>
                      <span style={{ ...styles.legendDot, backgroundColor: item.color }} />
                      <span style={styles.legendText}>{item.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div style={styles.canvasFooter}>
              💡 提示：可使用滑鼠滾輪縮放、拖曳畫布；點擊節點可高亮其決策通路，右側面板將同步呈現條款級溯源資訊。
            </div>
          </div>

          {/* 右側：條款級溯源細節展示卡片 (Provenance Drawer) */}
          <div className="glass-card" style={styles.detailCard}>
            {selectedNode ? (
              <div style={styles.detailWrapper}>
                <div style={styles.detailHeader}>
                  <span style={styles.detailTypeBadge}>
                    {selectedNode.node_type.toUpperCase()}
                  </span>
                  <h3 style={styles.detailNodeLabel}>{selectedNode.label}</h3>
                </div>

                <div style={styles.divider} />

                <div style={styles.detailBody}>
                  {/* 核心條款級文字展示 (Provenance) */}
                  {selectedNode.properties.raw_text && (
                    <div style={styles.detailSec}>
                      <h4 style={styles.detailSecTitle}>📜 原始條文文字內容</h4>
                      <p style={styles.detailSecText}>{selectedNode.properties.raw_text}</p>
                    </div>
                  )}

                  {/* 引用 citations */}
                  {selectedNode.properties.citations && (
                    <div style={styles.detailSec}>
                      <h4 style={styles.detailSecTitle}>🔗 法規合規條文引用</h4>
                      <div style={styles.citationList}>
                        {selectedNode.properties.citations.map((cit: string, idx: number) => (
                          <span key={idx} style={styles.citationTag}>{cit}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 其它通用 Metadata */}
                  <div style={styles.detailSec}>
                    <h4 style={styles.detailSecTitle}>⚙️ 節點元數據載荷</h4>
                    <div style={styles.metadataGrid}>
                      <div style={styles.metaRow}>
                        <span style={styles.metaKey}>節點 ID:</span>
                        <code style={styles.metaVal}>{selectedNode.node_id}</code>
                      </div>
                      {Object.entries(selectedNode.properties).map(([key, val]) => {
                        if (key === 'raw_text' || key === 'citations') return null;
                        return (
                          <div key={key} style={styles.metaRow}>
                            <span style={styles.metaKey}>{key}:</span>
                            <span style={styles.metaVal}>{String(val)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={styles.emptyDetail}>
                <Info size={32} color="var(--text-muted)" style={{ marginBottom: '12px' }} />
                <h4 style={styles.emptyTitle}>點擊節點查看溯源</h4>
                <p style={styles.emptyDesc}>點擊左側力導向圖中的任意法規、客戶或決策節點，此處將實時解析呈現條款級來源、法律責任說明與合規元數據。</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '32px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: '2.2rem',
    marginBottom: '8px',
  },
  subtitle: {
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  loadingWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '500px',
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  mainLayout: {
    display: 'grid',
    gridTemplateColumns: '1fr 340px',
    gap: '24px',
    alignItems: 'stretch',
  },
  canvasCard: {
    padding: '20px',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  canvasHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  canvasTitleWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  canvasTitle: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '1rem',
  },
  legendToggle: {
    background: 'none',
    border: 'none',
    color: 'var(--primary)',
    cursor: 'pointer',
    fontSize: '0.8rem',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  canvasWrapper: {
    position: 'relative' as const,
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    height: '550px',
    background: 'rgba(0,0,0,0.3)',
    overflow: 'hidden',
  },
  svg: {
    width: '100%',
    height: '100%',
  },
  legend: {
    position: 'absolute' as const,
    bottom: '16px',
    left: '16px',
    background: 'rgba(18, 20, 30, 0.85)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '8px',
    padding: '12px',
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px 16px',
    backdropFilter: 'blur(8px)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  legendDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  legendText: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  canvasFooter: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    marginTop: '12px',
    textAlign: 'center' as const,
  },
  detailCard: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  emptyDetail: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center' as const,
    flex: 1,
    padding: '20px',
  },
  emptyTitle: {
    fontSize: '1rem',
    fontWeight: 700,
    marginBottom: '8px',
  },
  emptyDesc: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    lineHeight: '1.5',
  },
  detailWrapper: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
  },
  detailHeader: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  detailTypeBadge: {
    fontSize: '0.65rem',
    fontWeight: 700,
    background: 'rgba(0, 242, 254, 0.1)',
    color: 'var(--primary)',
    border: '1px solid rgba(0, 242, 254, 0.2)',
    padding: '2px 8px',
    borderRadius: '4px',
    width: 'fit-content',
    letterSpacing: '0.05em',
  },
  detailNodeLabel: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#ffffff',
  },
  divider: {
    height: '1px',
    background: 'rgba(255,255,255,0.06)',
    width: '100%',
  },
  detailBody: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
  },
  detailSec: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  detailSecTitle: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-display)',
  },
  detailSecText: {
    fontSize: '0.85rem',
    lineHeight: '1.5',
    color: '#e2e8f0',
    background: 'rgba(255, 255, 255, 0.02)',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.04)',
  },
  citationList: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '6px',
  },
  citationTag: {
    fontSize: '0.75rem',
    fontWeight: 600,
    background: 'rgba(168, 85, 247, 0.1)',
    color: '#c084fc',
    border: '1px solid rgba(168, 85, 247, 0.2)',
    padding: '4px 10px',
    borderRadius: '6px',
    fontFamily: 'monospace',
  },
  metadataGrid: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
    background: 'rgba(0,0,0,0.2)',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(255,255,255,0.02)',
  },
  metaRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
  },
  metaKey: {
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  metaVal: {
    color: '#ffffff',
    fontFamily: 'monospace',
  }
};
