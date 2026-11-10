"""
測試隔離設定：在任何 src.api 模組被 import 之前執行。

- 用管線（src.pipeline）把知識庫重建到暫存目錄，API 測試只讀這份新產生的資料。
- 稽核日誌寫到暫存檔，不會追加到 repo 裡的 data/processed/audit_log.json。
- Neo4j 指向不存在的位址並只試一次，測試不會等待重試，也不會清空本機正在跑的資料庫。
"""
import os
import sys
import tempfile
import contextlib
import io
import atexit
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

_TMP_ROOT = tempfile.mkdtemp(prefix="cdd_graphwiki_tests_")
atexit.register(shutil.rmtree, _TMP_ROOT, ignore_errors=True)
TEST_PROCESSED_DIR = os.path.join(_TMP_ROOT, "processed")

os.environ["CDD_PROCESSED_DIR"] = TEST_PROCESSED_DIR
os.environ["CDD_AUDIT_LOG_FILE"] = os.path.join(_TMP_ROOT, "audit_log.json")
os.environ["CDD_NEO4J_RETRIES"] = "1"
os.environ["CDD_NEO4J_RETRY_DELAY"] = "0"
os.environ["NEO4J_URI"] = "bolt://127.0.0.1:1"
for key in ("NVIDIA_API_KEY", "GEMINI_API_KEY"):
    os.environ.pop(key, None)

from src import pipeline  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    PIPELINE_SUMMARY = pipeline.run(
        sources_dir=os.path.join(REPO_ROOT, "data", "sources"),
        gold_dir=os.path.join(REPO_ROOT, "data", "gold"),
        out_dir=TEST_PROCESSED_DIR,
        adjudications_path=os.path.join(REPO_ROOT, "data", "reviews", "conflict_adjudications.yaml"),
    )
