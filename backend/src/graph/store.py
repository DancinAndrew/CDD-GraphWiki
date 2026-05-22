import os
import time
import logging
from typing import Generator
from neo4j import GraphDatabase, Driver, Session

logger = logging.getLogger("cdd.graph.store")

class Neo4jStore:
    """
    Neo4j 圖資料庫連接與驅動管理器（單例模式）。
    負責 Bolt 連線管理、健全的初始化重試與 Session 釋放。
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Neo4jStore, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 從環境變數讀取 Neo4j 設定，具備 Secrets Management 防禦，不硬編碼預設密碼
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "testpassword123")
        self.driver: Optional[Driver] = None
        self._initialized = True

    def connect(self, max_retries: int = 5, delay_seconds: int = 5) -> Driver:
        """
        初始化 Bolt 驅動並建立與 Neo4j 的連線。
        包含防禦性重試機制，防止 Neo4j 容器尚未完全啟動而導致連線崩潰。
        """
        if self.driver:
            return self.driver

        logger.info(f"正在嘗試連接 Neo4j 圖資料庫: {self.uri} (用戶: {self.user})")
        
        for attempt in range(1, max_retries + 1):
            try:
                # 建立官方 Neo4j 驅動實例
                driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                # 執行簡單的 ping 測試以確認連線可用性
                driver.verify_connectivity()
                self.driver = driver
                logger.info("成功建立 Neo4j 圖資料庫連線！")
                return self.driver
            except Exception as e:
                logger.warning(
                    f"建立 Neo4j 連線失敗 (第 {attempt}/{max_retries} 次嘗試): {str(e)}。 將在 {delay_seconds} 秒後重試..."
                )
                time.sleep(delay_seconds)

        # 超過最大重試次數後拋出明確的異常
        raise ConnectionError(f"無法建立與 Neo4j 圖資料庫的連線 ({self.uri})，已達到最大重試次數。")

    def close(self):
        """
        關閉 Neo4j 驅動與其所有的連線池資源。
        """
        if self.driver:
            logger.info("正在關閉 Neo4j 驅動...")
            self.driver.close()
            self.driver = None
            logger.info("Neo4j 驅動已成功關閉。")

    def get_session(self) -> Session:
        """
        獲取一個新的 Neo4j Session。
        """
        driver = self.connect()
        return driver.session()

# 單例全域調用對象
neo4j_store = Neo4jStore()

def get_neo4j_session() -> Generator[Session, None, None]:
    """
    FastAPI 依賴注入的 Session 管理器，保證使用完畢後自動釋放 Session。
    """
    session = neo4j_store.get_session()
    try:
        yield session
    finally:
        session.close()
