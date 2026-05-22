import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.graph.sync import GraphSyncEngine
from src.graph.store import Neo4jStore, neo4j_store


@pytest.fixture(scope="module")
def client():
    """
    建立 TestClient 測試夾具，確保 startup_event 成功執行。
    """
    with TestClient(app) as c:
        yield c


def test_neo4j_store_singleton():
    """
    驗證 Neo4jStore 為單例模式，確保連線池唯一。
    """
    store1 = Neo4jStore()
    store2 = Neo4jStore()
    assert store1 is store2


@patch("src.graph.sync.logger")
def test_graph_sync_engine_mock(mock_logger):
    """
    使用 Mock 模擬 Neo4j Session，驗證 GraphSyncEngine.sync_to_neo4j 的 Cypher 呼叫流程。
    """
    mock_session = MagicMock()
    
    # 建立最小化的 Mock 知識庫
    mock_kb = {
        "documents": [],
        "clauses": [],
        "obligations": [],
        "customers": [],
        "conflicts": []
    }
    
    # 執行同步
    GraphSyncEngine.sync_to_neo4j(mock_session, mock_kb)
    
    # 驗證是否呼叫了清空數據庫的 Cypher
    mock_session.run.assert_any_call("MATCH (n) DETACH DELETE n")
    assert mock_logger.info.called


def test_ubo_penetration_api(client):
    """
    測試實質受益人 (UBO) 股權穿透 API 接口的強型別合約與回傳邏輯（包含對降級機制的覆蓋）。
    """
    # 針對 Complex CDD 測試用例進行穿透
    response = client.get("/api/v1/graph/ubo?customer_id=cust_corp_complex_cdd")
    assert response.status_code == 200
    ubos = response.json()
    
    # 不論是真實 Neo4j 或降級兜底，都應成功回傳高階 UBO 資訊
    assert len(ubos) >= 2
    
    # 驗證 UBO Pydantic 屬性合約
    ubo_pep = [u for u in ubos if u["ubo_id"] == "cust_individual_pep_ubo"]
    assert len(ubo_pep) == 1
    assert ubo_pep[0]["is_pep"] is True
    assert ubo_pep[0]["final_percentage"] == 0.18
    assert "cust_corp_complex_cdd" in ubo_pep[0]["holding_path"]
    
    ubo_std = [u for u in ubos if u["ubo_id"] == "cust_individual_standard_ubo"]
    assert len(ubo_std) == 1
    assert ubo_std[0]["is_pep"] is False
    assert ubo_std[0]["final_percentage"] == 0.12


def test_circular_loops_api(client):
    """
    測試循環控股自動環路檢測 API 接口，驗證強型別合約結構與去重邏輯。
    """
    response = client.get("/api/v1/graph/loops")
    assert response.status_code == 200
    loops = response.json()
    
    # 驗證至少檢測出一個循環控股閉環
    assert len(loops) >= 1
    
    # 驗證 Loop Pydantic 屬性合約
    first_loop = loops[0]
    assert "loop_nodes" in first_loop
    assert "loop_depth" in first_loop
    
    # 驗證環路包含預期節點
    assert "cust_shell_a" in first_loop["loop_nodes"]
    assert first_loop["loop_depth"] == 3
