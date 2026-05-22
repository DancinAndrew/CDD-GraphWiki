import os
import yaml
from src.contracts.models import (
    CustomerContext,
    Obligation,
    Clause,
    SourceDocument,
    Conflict
)
from src.decision.engine import CDDChecklistEngine
from src.audit.logger import AuditLogger
from src.audit.manager import ReviewCaseManager
from src.graph.store import get_neo4j_session

# 定義本地持久化路徑
GOLD_DIR = "data/gold"
PROCESSED_DIR = "data/processed"
AUDIT_LOG_FILE = os.path.join(PROCESSED_DIR, "audit_log.json")

# 單例模式實體
_engine = None
_logger = None
_manager = None

# 金標法規知識庫緩存，避免每次 API 調用都重新讀取檔案
_cached_documents = []
_cached_clauses = []
_cached_obligations = []
_cached_customers = []
_cached_conflicts = []


def get_engine() -> CDDChecklistEngine:
    global _engine
    if _engine is None:
        _engine = CDDChecklistEngine()
    return _engine


def get_logger() -> AuditLogger:
    global _logger
    if _logger is None:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        # 如果日誌檔案不存在，會自動初始化 Hash Chain
        _logger = AuditLogger(filepath=AUDIT_LOG_FILE)
    return _logger


def get_manager() -> ReviewCaseManager:
    global _manager
    if _manager is None:
        logger = get_logger()
        _manager = ReviewCaseManager(logger=logger)
    return _manager


def clear_knowledge_base_cache():
    """
    清除緩存，以便在 Ingestion 導入新法規後實施熱加載。
    """
    global _cached_documents, _cached_clauses, _cached_obligations, _cached_customers, _cached_conflicts
    _cached_documents = []
    _cached_clauses = []
    _cached_obligations = []
    _cached_customers = []
    _cached_conflicts = []
    print("🧹 已清除法規知識庫記憶體緩存")


def load_knowledge_base():
    """
    加載法規知識數據庫（優先從 data/processed 載入以支持增量 Ingestion，否則 fallback 至 data/gold）。
    """
    global _cached_documents, _cached_clauses, _cached_obligations, _cached_customers, _cached_conflicts
    
    if not _cached_documents:
        # 決定各類別檔案的路徑
        doc_file = os.path.join(PROCESSED_DIR, "source_documents.yaml") if os.path.exists(
            os.path.join(PROCESSED_DIR, "source_documents.yaml")
        ) else os.path.join(GOLD_DIR, "source_documents.yaml")

        clause_file = os.path.join(PROCESSED_DIR, "clauses.yaml") if os.path.exists(
            os.path.join(PROCESSED_DIR, "clauses.yaml")
        ) else os.path.join(GOLD_DIR, "clauses.yaml")

        obs_file = os.path.join(PROCESSED_DIR, "obligations.yaml") if os.path.exists(
            os.path.join(PROCESSED_DIR, "obligations.yaml")
        ) else os.path.join(GOLD_DIR, "obligations.yaml")

        cust_file = os.path.join(PROCESSED_DIR, "customer_contexts.yaml") if os.path.exists(
            os.path.join(PROCESSED_DIR, "customer_contexts.yaml")
        ) else os.path.join(GOLD_DIR, "customer_contexts.yaml")

        conflict_file = os.path.join(PROCESSED_DIR, "conflicts.yaml") if os.path.exists(
            os.path.join(PROCESSED_DIR, "conflicts.yaml")
        ) else os.path.join(GOLD_DIR, "conflicts.yaml")

        # 讀取檔案
        with open(doc_file, "r", encoding="utf-8") as f:
            raw_docs = yaml.safe_load(f) or []
        with open(clause_file, "r", encoding="utf-8") as f:
            raw_clauses = yaml.safe_load(f) or []
        with open(obs_file, "r", encoding="utf-8") as f:
            raw_obs = yaml.safe_load(f) or []
        with open(cust_file, "r", encoding="utf-8") as f:
            raw_custs = yaml.safe_load(f) or []
        with open(conflict_file, "r", encoding="utf-8") as f:
            raw_confs = yaml.safe_load(f) or []

        # 轉化為強型別 Pydantic 模型
        _cached_documents = [SourceDocument(**doc) for doc in raw_docs]
        _cached_clauses = [Clause(**cl) for cl in raw_clauses]
        _cached_obligations = [Obligation(**ob) for ob in raw_obs]
        _cached_customers = [CustomerContext(**c) for c in raw_custs]
        _cached_conflicts = [Conflict(**conf) for conf in raw_confs]

    return {
        "documents": _cached_documents,
        "clauses": _cached_clauses,
        "obligations": _cached_obligations,
        "customers": _cached_customers,
        "conflicts": _cached_conflicts
    }

