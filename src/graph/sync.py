import logging
from typing import Dict, Any, List
from neo4j import Session

from src.contracts.models import (
    SourceDocument,
    Clause,
    Obligation,
    CustomerContext,
    Conflict
)

logger = logging.getLogger("cdd.graph.sync")

class GraphSyncEngine:
    """
    圖資料庫同步引擎，負責將 CDD-GraphWiki 的合規元模型知識庫與客戶事實
    轉譯為 Cypher 語句，並同步寫入正式的 Neo4j 圖資料庫中。
    """

    @staticmethod
    def sync_to_neo4j(session: Session, kb: Dict[str, Any]) -> None:
        """
        將合規知識庫同步至 Neo4j。為確保資料一致性與金標版本乾淨，同步前會清空舊有節點。
        """
        logger.info("開始執行 Neo4j 全量圖數據同步...")
        
        try:
            # 1. 為了確保每次同步數據乾淨，先清空圖資料庫（防禦性防重）
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("已清空 Neo4j 中所有現有節點與關係邊。")

            # 2. 同步 SourceDocument
            documents: List[SourceDocument] = kb.get("documents", [])
            for doc in documents:
                session.run(
                    """
                    MERGE (d:SourceDocument {source_document_id: $id})
                    SET d.title = $title,
                        d.issuer = $issuer,
                        d.jurisdiction = $jurisdiction,
                        d.version = $version,
                        d.local_path = $local_path
                    """,
                    id=doc.source_document_id,
                    title=doc.title,
                    issuer=doc.issuer,
                    jurisdiction=doc.jurisdiction,
                    version=doc.version,
                    local_path=doc.local_path
                )
            logger.info(f"已同步 {len(documents)} 個 SourceDocument 節點。")

            # 3. 同步 Clause
            clauses: List[Clause] = kb.get("clauses", [])
            for cl in clauses:
                session.run(
                    """
                    MERGE (c:Clause {clause_id: $id})
                    SET c.section_ref = $section_ref,
                        c.raw_text = $raw_text,
                        c.normalized_text = $normalized_text,
                        c.citations = $citations
                    """,
                    id=cl.clause_id,
                    section_ref=cl.section_ref,
                    raw_text=cl.raw_text,
                    normalized_text=cl.normalized_text,
                    citations=cl.citations
                )
                # 建立 Clause ➔ SourceDocument 關係
                session.run(
                    """
                    MATCH (c:Clause {clause_id: $clause_id})
                    MATCH (d:SourceDocument {source_document_id: $doc_id})
                    MERGE (c)-[:DERIVED_FROM]->(d)
                    """,
                    clause_id=cl.clause_id,
                    doc_id=cl.source_document_id
                )
                # 建立 nested parent Clause 關係
                if cl.parent_clause_id:
                    session.run(
                        """
                        MATCH (c:Clause {clause_id: $clause_id})
                        MATCH (p:Clause {clause_id: $parent_id})
                        MERGE (c)-[:SUBCLASSE_OF]->(p)
                        """,
                        clause_id=cl.clause_id,
                        parent_id=cl.parent_clause_id
                    )
            logger.info(f"已同步 {len(clauses)} 個 Clause 節點與關聯邊。")

            # 4. 同步 Obligation
            obligations: List[Obligation] = kb.get("obligations", [])
            for ob in obligations:
                session.run(
                    """
                    MERGE (o:Obligation {obligation_id: $id})
                    SET o.actor = $actor,
                        o.action = $action,
                        o.object = $object,
                        o.jurisdiction = $jurisdiction,
                        o.confidence = $confidence,
                        o.review_status = $review_status
                    """,
                    id=ob.obligation_id,
                    actor=ob.actor,
                    action=ob.action,
                    object=ob.object,
                    jurisdiction=ob.jurisdiction,
                    confidence=ob.confidence,
                    review_status=ob.review_status
                )
                # 建立 Obligation ➔ Clause 關係 (確保 clause-level provenance)
                for cl_id in ob.source_clause_ids:
                    session.run(
                        """
                        MATCH (o:Obligation {obligation_id: $ob_id})
                        MATCH (c:Clause {clause_id: $cl_id})
                        MERGE (o)-[:APPLIES_RULE_FROM]->(c)
                        """,
                        ob_id=ob.obligation_id,
                        cl_id=cl_id
                    )
            logger.info(f"已同步 {len(obligations)} 個 Obligation 節點與溯源關係。")

            # 5. 同步 CustomerContext
            customers: List[CustomerContext] = kb.get("customers", [])
            for cust in customers:
                # 區分法人與個人 Label，以完美對接 UBO Cypher 查詢
                label = "CustomerContext"
                if cust.customer_type == "individual":
                    label = "CustomerContext:Individual"
                
                session.run(
                    f"""
                    MERGE (c:CustomerContext {{customer_id: $id}})
                    SET c.customer_type = $type,
                        c.registration_jurisdiction = $jurisdiction,
                        c.ownership_layers = $ownership_layers,
                        c.ubo_status = $ubo_status,
                        c.pep_exposure = $pep_exposure,
                        c.ubo_country_risk = $ubo_country_risk
                    """,
                    id=cust.customer_id,
                    type=cust.customer_type,
                    jurisdiction=cust.registration_jurisdiction,
                    ownership_layers=cust.ownership_layers,
                    ubo_status=cust.ubo_status,
                    pep_exposure=cust.pep_exposure,
                    ubo_country_risk=cust.ubo_country_risk
                )
                # 如果是個人，加上 Individual Label
                if cust.customer_type == "individual":
                    session.run(
                        "MATCH (c:CustomerContext {customer_id: $id}) SET c:Individual",
                        id=cust.customer_id
                    )

            logger.info(f"已同步 {len(customers)} 個 Customer 基礎事實節點。")

            # 6. 同步 Conflict
            conflicts: List[Conflict] = kb.get("conflicts", [])
            for conf in conflicts:
                session.run(
                    """
                    MERGE (cf:Conflict {conflict_id: $id})
                    SET cf.conflict_type = $type,
                        cf.description = $description,
                        cf.adjudication_status = $status
                    """,
                    id=conf.conflict_id,
                    type=conf.conflict_type,
                    description=conf.description,
                    status=conf.adjudication_status
                )
                # 建立 Conflict 與 Clause 的關聯
                for cl_id in conf.source_clause_ids:
                    session.run(
                        """
                        MATCH (cf:Conflict {conflict_id: $cf_id})
                        MATCH (c:Clause {clause_id: $cl_id})
                        MERGE (cf)-[:REFERENCES_CLAUSE]->(c)
                        """,
                        cf_id=conf.conflict_id,
                        cl_id=cl_id
                    )
            logger.info(f"已同步 {len(conflicts)} 個 Conflict 衝突分析節點。")

            # =================================================================
            # 7. 注入實質受益人 (UBO) 極深股權穿透之測試實體與 OWNER_OF 控股邊
            # =================================================================
            # 建立多層級控股拓撲以驗證持股加乘大於等於 10% 的實質受益人 (Individual)
            
            # (A) UBO 測試用例主體：法人客戶 cust_corp_complex_cdd
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_corp_complex_cdd"})
                SET c.customer_type = "corporate",
                    c.registration_jurisdiction = "Singapore",
                    c.ownership_layers = 3,
                    c.ubo_status = "identified",
                    c.pep_exposure = false,
                    c.ubo_country_risk = "low"
                """
            )
            # 中間控股公司：cust_corp_holding_co_l1
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_corp_holding_co_l1"})
                SET c.customer_type = "corporate",
                    c.registration_jurisdiction = "British Virgin Islands",
                    c.ownership_layers = 2,
                    c.ubo_status = "identified",
                    c.pep_exposure = false,
                    c.ubo_country_risk = "medium"
                """
            )
            # 最上層控股公司：cust_corp_holding_co_l2
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_corp_holding_co_l2"})
                SET c.customer_type = "corporate",
                    c.registration_jurisdiction = "Cayman Islands",
                    c.ownership_layers = 1,
                    c.ubo_status = "identified",
                    c.pep_exposure = false,
                    c.ubo_country_risk = "medium"
                """
            )
            # UBO 1: 具備 PEP 曝險的個人股東 (直接持有最上層控股公司 60%)
            # 加乘持股：60% (L2) * 50% (L1) * 60% (Complex CDD) = 18% >= 10% ➔ 判定為 UBO
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_individual_pep_ubo"})
                SET c:Individual,
                    c.customer_type = "individual",
                    c.registration_jurisdiction = "Singapore",
                    c.ownership_layers = 0,
                    c.ubo_status = "identified",
                    c.pep_exposure = true,
                    c.ubo_country_risk = "low"
                """
            )
            # UBO 2: 一般個人股東 (直接持有 Complex CDD 12% ➔ 直接穿透 UBO)
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_individual_standard_ubo"})
                SET c:Individual,
                    c.customer_type = "individual",
                    c.registration_jurisdiction = "Singapore",
                    c.ownership_layers = 0,
                    c.ubo_status = "identified",
                    c.pep_exposure = false,
                    c.ubo_country_risk = "low"
                """
            )
            # 非 UBO 個人股東: 持有 L2 30%，加乘持股：30% * 50% * 60% = 9% < 10% ➔ 不符合 UBO 標準
            session.run(
                """
                MERGE (c:CustomerContext {customer_id: "cust_individual_minority_shareholder"})
                SET c:Individual,
                    c.customer_type = "individual",
                    c.registration_jurisdiction = "Singapore",
                    c.ownership_layers = 0,
                    c.ubo_status = "identified",
                    c.pep_exposure = false,
                    c.ubo_country_risk = "low"
                """
            )

            # 建立股權 OWNER_OF 邊關係並配置 share_pct 屬性
            # (1) 中間控股公司持有 Complex CDD 60%
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_corp_holding_co_l1"})
                MATCH (to:CustomerContext {customer_id: "cust_corp_complex_cdd"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.60
                """
            )
            # (2) 最上層控股公司持有中間控股公司 50%
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_corp_holding_co_l2"})
                MATCH (to:CustomerContext {customer_id: "cust_corp_holding_co_l1"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.50
                """
            )
            # (3) PEP 個人股東持有最上層控股公司 60%
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_individual_pep_ubo"})
                MATCH (to:CustomerContext {customer_id: "cust_corp_holding_co_l2"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.60
                """
            )
            # (4) 一般個人股東直接持有 Complex CDD 12%
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_individual_standard_ubo"})
                MATCH (to:CustomerContext {customer_id: "cust_corp_complex_cdd"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.12
                """
            )
            # (5) 少數個人股東持有最上層控股公司 30%
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_individual_minority_shareholder"})
                MATCH (to:CustomerContext {customer_id: "cust_corp_holding_co_l2"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.30
                """
            )

            # =================================================================
            # 8. 注入循環控股關係 (Circular Loop) 測試實體
            # =================================================================
            # 建立 A ➔ B ➔ C ➔ A 股權控制圈環路
            loop_nodes = ["cust_shell_a", "cust_shell_b", "cust_shell_c"]
            for i, name in enumerate(loop_nodes):
                session.run(
                    f"""
                    MERGE (c:CustomerContext {{customer_id: $id}})
                    SET c.customer_type = "corporate",
                        c.registration_jurisdiction = "Cayman Islands",
                        c.ownership_layers = 4,
                        c.ubo_status = "unclear",
                        c.pep_exposure = false,
                        c.ubo_country_risk = "high"
                    """,
                    id=name
                )
            
            # A ➔ B (40%)
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_shell_a"})
                MATCH (to:CustomerContext {customer_id: "cust_shell_b"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.40
                """
            )
            # B ➔ C (50%)
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_shell_b"})
                MATCH (to:CustomerContext {customer_id: "cust_shell_c"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.50
                """
            )
            # C ➔ A (60%) -- 構成閉環！
            session.run(
                """
                MATCH (from:CustomerContext {customer_id: "cust_shell_c"})
                MATCH (to:CustomerContext {customer_id: "cust_shell_a"})
                MERGE (from)-[r:OWNER_OF]->(to)
                SET r.share_pct = 0.60
                """
            )

            logger.info("成功寫入極深股權 UBO 穿透與循環控股環路之測試拓撲！")
            logger.info("✓ Neo4j 全量圖數據同步完成！")

        except Exception as e:
            logger.error(f"Neo4j 同步引擎出錯: {str(e)}")
            raise e
