from typing import List, Dict, Any, Optional, Set
from collections import deque
from src.contracts.models import (
    SourceDocument,
    Clause,
    Obligation,
    CustomerContext,
    Conflict,
    CDDChecklist,
    Concept,
    ExplanationPath,
    GraphNode,
    GraphEdge,
    RegulatoryGraph
)


class GraphBuilder:
    """
    法規合規知識圖譜構建器，負責將零散的合規知識與決策物件編譯成點邊圖譜。
    """

    @staticmethod
    def build_regulatory_graph(
        documents: List[SourceDocument],
        clauses: List[Clause],
        obligations: List[Obligation],
        concepts: List[Concept],
        conflicts: List[Conflict],
        customers: Optional[List[CustomerContext]] = None,
        checklists: Optional[List[CDDChecklist]] = None,
        paths: Optional[List[ExplanationPath]] = None
    ) -> RegulatoryGraph:
        """
        將合規條文、義務、概念、衝突、客戶事實與決策等物件對應組裝成一個 RegulatoryGraph。
        
        Args:
            documents: 原始法規文件列表
            clauses: 條款列表
            obligations: 合規義務列表
            concepts: 核心概念列表
            conflicts: 政策衝突列表
            customers: 客戶情境列表（可選）
            checklists: CDD 檢核表決策結果列表（可選）
            paths: 決策溯源解釋路徑列表（可選，用於織入決策路徑高亮）
            
        Returns:
            RegulatoryGraph 實例
        """
        nodes: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []

        # 1. 映射 SourceDocument 節點
        for doc in documents:
            nodes[doc.source_document_id] = GraphNode(
                node_id=doc.source_document_id,
                node_type="SourceDocument",
                label=doc.title,
                properties=doc.model_dump()
            )

        # 2. 映射 Clause 節點與邊
        for cl in clauses:
            nodes[cl.clause_id] = GraphNode(
                node_id=cl.clause_id,
                node_type="Clause",
                label=f"條款 {cl.clause_id}",
                properties=cl.model_dump()
            )
            # 建立連接至 SourceDocument 的邊
            edge_id = f"{cl.clause_id}_derived_from_{cl.source_document_id}"
            edges.append(GraphEdge(
                edge_id=edge_id,
                source_id=cl.clause_id,
                target_id=cl.source_document_id,
                edge_type="derived_from",
                label="發源自"
            ))

            # 如果有 parent_clause_id，建立連接至 parent Clause 的邊
            if cl.parent_clause_id and cl.parent_clause_id in [c.clause_id for c in clauses]:
                p_edge_id = f"{cl.clause_id}_derived_from_{cl.parent_clause_id}"
                edges.append(GraphEdge(
                    edge_id=p_edge_id,
                    source_id=cl.clause_id,
                    target_id=cl.parent_clause_id,
                    edge_type="derived_from",
                    label="隸屬於"
                ))

        # 3. 映射 Concept 節點與邊
        for cp in concepts:
            nodes[cp.concept_id] = GraphNode(
                node_id=cp.concept_id,
                node_type="Concept",
                label=cp.name,
                properties=cp.model_dump()
            )
            # 建立 Concept 與定義 Clauses 之間的引用邊
            for cl_id in cp.source_clause_ids:
                if cl_id in nodes:
                    edge_id = f"{cp.concept_id}_references_clause_{cl_id}"
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source_id=cp.concept_id,
                        target_id=cl_id,
                        edge_type="references_clause",
                        label="定義於"
                    ))

        # 4. 映射 Obligation 節點與邊
        for ob in obligations:
            nodes[ob.obligation_id] = GraphNode(
                node_id=ob.obligation_id,
                node_type="Obligation",
                label=ob.obligation_id,
                properties=ob.model_dump()
            )
            # 建立與來源 Clauses 的關係邊
            for cl_id in ob.source_clause_ids:
                if cl_id in nodes:
                    edge_id = f"{ob.obligation_id}_references_clause_{cl_id}"
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source_id=ob.obligation_id,
                        target_id=cl_id,
                        edge_type="references_clause",
                        label="引用條文"
                    ))

            # 建立 Obligation ➔ EvidenceRequirement 節點與邊
            for ev in ob.required_evidence:
                if ev not in nodes:
                    nodes[ev] = GraphNode(
                        node_id=ev,
                        node_type="EvidenceRequirement",
                        label=ev,
                        properties={}
                    )
                edge_id = f"{ob.obligation_id}_requires_evidence_{ev}"
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source_id=ob.obligation_id,
                    target_id=ev,
                    edge_type="requires_evidence",
                    label="要求佐證證據"
                ))

            # 建立 Obligation ➔ RiskTrigger (Review Flags) 節點與邊
            for rf in ob.review_flags:
                if rf not in nodes:
                    nodes[rf] = GraphNode(
                        node_id=rf,
                        node_type="RiskTrigger",
                        label=rf,
                        properties={}
                    )
                edge_id = f"{ob.obligation_id}_conditioned_on_{rf}"
                edges.append(GraphEdge(
                    edge_id=edge_id,
                    source_id=ob.obligation_id,
                    target_id=rf,
                    edge_type="conditioned_on",
                    label="觸發條件"
                ))

        # 5. 映射 Conflict 節點與邊
        for cf in conflicts:
            nodes[cf.conflict_id] = GraphNode(
                node_id=cf.conflict_id,
                node_type="Conflict",
                label=cf.conflict_id,
                properties=cf.model_dump()
            )
            # 建立 Conflict ➔ Clause 關係邊
            for cl_id in cf.source_clause_ids:
                if cl_id in nodes:
                    edge_id = f"{cf.conflict_id}_references_clause_{cl_id}"
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source_id=cf.conflict_id,
                        target_id=cl_id,
                        edge_type="references_clause",
                        label="衝突條款"
                    ))

        # 6. 映射 CustomerContext 節點（若提供）
        if customers:
            for cust in customers:
                nodes[cust.customer_id] = GraphNode(
                    node_id=cust.customer_id,
                    node_type="CustomerContext",
                    label=f"客戶 {cust.customer_id}",
                    properties=cust.model_dump()
                )

        # 7. 映射 CDDChecklist 節點與邊（若提供）
        if checklists:
            for chk in checklists:
                nodes[chk.checklist_id] = GraphNode(
                    node_id=chk.checklist_id,
                    node_type="CDDChecklist",
                    label=f"決策 {chk.checklist_id}",
                    properties=chk.model_dump()
                )
                # 連結 CDDChecklist ➔ CustomerContext
                if chk.customer_id in nodes:
                    edge_id = f"{chk.checklist_id}_derived_from_{chk.customer_id}"
                    edges.append(GraphEdge(
                        edge_id=edge_id,
                        source_id=chk.checklist_id,
                        target_id=chk.customer_id,
                        edge_type="derived_from",
                        label="決策源自客戶"
                    ))
                # 連結 CDDChecklist ➔ Obligation
                for ob_id in chk.applicable_obligations:
                    if ob_id in nodes:
                        edge_id = f"{chk.checklist_id}_applies_to_{ob_id}"
                        edges.append(GraphEdge(
                            edge_id=edge_id,
                            source_id=chk.checklist_id,
                            target_id=ob_id,
                            edge_type="applies_to",
                            label="適用義務"
                        ))
                # 連結 CDDChecklist ➔ Conflict
                for cf_id in chk.unresolved_conflicts:
                    if cf_id in nodes:
                        edge_id = f"{chk.checklist_id}_conflicts_with_{cf_id}"
                        edges.append(GraphEdge(
                            edge_id=edge_id,
                            source_id=chk.checklist_id,
                            target_id=cf_id,
                            edge_type="conflicts_with",
                            label="存在未解衝突"
                        ))

        # 8. 織入決策解釋路徑 (Decision Weaving)
        if paths:
            for path in paths:
                # 8.1 高亮解釋鏈上的節點
                path_node_ids = [pn.node_id for pn in path.path_nodes]
                for p_node in path.path_nodes:
                    if p_node.node_id in nodes:
                        nodes[p_node.node_id].properties["decision_path"] = True
                        # 也順便把 properties 裡的 target_item 存進去
                        if "explained_items" not in nodes[p_node.node_id].properties:
                            nodes[p_node.node_id].properties["explained_items"] = []
                        if path.target_item not in nodes[p_node.node_id].properties["explained_items"]:
                            nodes[p_node.node_id].properties["explained_items"].append(path.target_item)

                # 8.2 高亮已存在的邊關係，或動態建立決策邊
                for i in range(len(path_node_ids) - 1):
                    src_id = path_node_ids[i]
                    tgt_id = path_node_ids[i + 1]

                    # 在已存在的邊中尋找連接這兩個點的有向關係（不限方向）
                    found_edge = False
                    for edge in edges:
                        is_forward = (edge.source_id == src_id and edge.target_id == tgt_id)
                        is_backward = (edge.source_id == tgt_id and edge.target_id == src_id)
                        if is_forward or is_backward:
                            edge.properties["decision_path"] = True
                            edge.properties["decision_target"] = path.target_item
                            found_edge = True
                    
                    # 若在圖中尚未有邊相連，則建立一個特定的決策路徑邊
                    if not found_edge:
                        d_edge_id = f"decision_{src_id}_to_{tgt_id}"
                        edges.append(GraphEdge(
                            edge_id=d_edge_id,
                            source_id=src_id,
                            target_id=tgt_id,
                            edge_type="decision_path",
                            label="決策路徑傳導",
                            properties={
                                "decision_path": True,
                                "decision_target": path.target_item
                            }
                        ))

        return RegulatoryGraph(nodes=nodes, edges=edges)


class GraphQuery:
    """
    法規合規圖譜遍歷與檢索引擎。
    """

    @staticmethod
    def find_multi_hop_paths(
        graph: RegulatoryGraph,
        start_node_id: str,
        max_depth: int = 3,
        ignore_direction: bool = True
    ) -> List[List[GraphNode]]:
        """
        深度優先搜尋 (DFS) 圖譜中從起點開始且長度不超過 max_depth 的所有關係路徑。
        
        Args:
            graph: 目標 RegulatoryGraph
            start_node_id: 起始節點 ID
            max_depth: 最大遍歷深度
            ignore_direction: 是否忽略有向邊的方向（進行雙向遍歷）
            
        Returns:
            符合條件的節點路徑列表，每條路徑是一組 GraphNode 列表
        """
        if start_node_id not in graph.nodes:
            return []

        # 構建鄰接表
        adj: Dict[str, Set[str]] = {nid: set() for nid in graph.nodes}
        for edge in graph.edges:
            if edge.source_id in adj and edge.target_id in adj:
                adj[edge.source_id].add(edge.target_id)
                if ignore_direction:
                    adj[edge.target_id].add(edge.source_id)

        results: List[List[GraphNode]] = []

        def dfs(curr_id: str, path: List[str]):
            # 若路徑長度超過深度限制，停止
            if len(path) > max_depth + 1:
                return

            # 將當前路徑記錄進結果中 (長度大於 1 代表有移動)
            if len(path) > 1:
                results.append([graph.nodes[nid] for nid in path])

            for neighbor in adj[curr_id]:
                if neighbor not in path:  # 避免環路
                    dfs(neighbor, path + [neighbor])

        dfs(start_node_id, [start_node_id])
        return results

    @staticmethod
    def get_upstream_sources(graph: RegulatoryGraph, node_id: str) -> List[GraphNode]:
        """
        追溯指定節點的所有直接上游源頭節點。
        例如：Obligation ➔ upstream Clause ➔ upstream SourceDocument
        
        Args:
            graph: 目標 RegulatoryGraph
            node_id: 目標節點 ID
            
        Returns:
            上游節點列表
        """
        if node_id not in graph.nodes:
            return []

        upstream_ids = set()
        # 尋找 target_id == node_id 且屬於溯源關係的邊 (例如 clause ➔ document)
        for edge in graph.edges:
            if edge.source_id == node_id and edge.edge_type in ["derived_from", "references_clause"]:
                upstream_ids.add(edge.target_id)
            # 部分關係可能反向記錄，在此做容錯比對
            elif edge.target_id == node_id and edge.edge_type in ["applies_to", "requires_evidence", "conditioned_on"]:
                upstream_ids.add(edge.source_id)

        return [graph.nodes[nid] for nid in upstream_ids if nid in graph.nodes]

    @staticmethod
    def get_downstream_targets(graph: RegulatoryGraph, node_id: str) -> List[GraphNode]:
        """
        檢索指定節點的所有直接下游受影響節點。
        例如：SourceDocument ➔ downstream Clause ➔ downstream Obligation
        
        Args:
            graph: 目標 RegulatoryGraph
            node_id: 目標節點 ID
            
        Returns:
            下游節點列表
        """
        if node_id not in graph.nodes:
            return []

        downstream_ids = set()
        for edge in graph.edges:
            if edge.target_id == node_id and edge.edge_type in ["derived_from", "references_clause"]:
                downstream_ids.add(edge.source_id)
            elif edge.source_id == node_id and edge.edge_type in ["applies_to", "requires_evidence", "conditioned_on"]:
                downstream_ids.add(edge.target_id)

        return [graph.nodes[nid] for nid in downstream_ids if nid in graph.nodes]
