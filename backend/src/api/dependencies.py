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
from src.paths import find_data_dir

# 定義本地持久化路徑（皆可用環境變數覆寫，測試會把它們指到暫存目錄）
DATA_DIR = find_data_dir()
GOLD_DIR = os.environ.get("CDD_GOLD_DIR", os.path.join(DATA_DIR, "gold"))
PROCESSED_DIR = os.environ.get("CDD_PROCESSED_DIR", os.path.join(DATA_DIR, "processed"))
ADJUDICATIONS_FILE = os.environ.get(
    "CDD_ADJUDICATIONS_FILE", os.path.join(DATA_DIR, "reviews", "conflict_adjudications.yaml")
)
AUDIT_LOG_FILE = os.environ.get("CDD_AUDIT_LOG_FILE", os.path.join(PROCESSED_DIR, "audit_log.json"))

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


def check_referential_integrity(kb: dict) -> None:
    """
    確認每個義務、衝突的出處條文都存在於條文庫中；有懸空引用就直接報錯，
    不讓圖譜或解釋路徑默默漏掉邊。
    """
    clause_ids = {c.clause_id for c in kb["clauses"]}
    dangling = [
        (ob.obligation_id, cid) for ob in kb["obligations"] for cid in ob.source_clause_ids if cid not in clause_ids
    ] + [
        (cf.conflict_id, cid) for cf in kb["conflicts"] for cid in cf.source_clause_ids if cid not in clause_ids
    ]
    if dangling:
        raise ValueError(f"Knowledge base has references to unknown clauses: {dangling[:5]}")


def load_knowledge_base():
    """
    加載法規知識數據庫。
    若 data/processed 已有完整的四個檔案（來源文件、條文、義務、衝突），整組從 processed 讀取，
    避免和 data/gold 混用；否則整組改用 data/gold。客戶情境是輸入資料，固定從 data/gold 讀取。
    """
    global _cached_documents, _cached_clauses, _cached_obligations, _cached_customers, _cached_conflicts

    if not _cached_documents:
        kb_files = ["source_documents.yaml", "clauses.yaml", "obligations.yaml", "conflicts.yaml"]
        has_full_processed = all(os.path.exists(os.path.join(PROCESSED_DIR, name)) for name in kb_files)
        base_dir = PROCESSED_DIR if has_full_processed else GOLD_DIR

        def read(dir_path: str, filename: str):
            with open(os.path.join(dir_path, filename), "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or []

        # 先全部讀進區域變數並驗證，成功後才寫入快取，失敗時不會留下半套快取
        documents = [SourceDocument(**doc) for doc in read(base_dir, "source_documents.yaml")]
        clauses = [Clause(**cl) for cl in read(base_dir, "clauses.yaml")]
        obligations = [Obligation(**ob) for ob in read(base_dir, "obligations.yaml")]
        conflicts = [Conflict(**conf) for conf in read(base_dir, "conflicts.yaml")]
        customers = [CustomerContext(**c) for c in read(GOLD_DIR, "customer_contexts.yaml")]
        check_referential_integrity({"clauses": clauses, "obligations": obligations, "conflicts": conflicts})

        _cached_documents, _cached_clauses, _cached_obligations = documents, clauses, obligations
        _cached_conflicts, _cached_customers = conflicts, customers

    return {
        "documents": _cached_documents,
        "clauses": _cached_clauses,
        "obligations": _cached_obligations,
        "customers": _cached_customers,
        "conflicts": _cached_conflicts
    }
