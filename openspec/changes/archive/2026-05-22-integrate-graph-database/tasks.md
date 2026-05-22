# Tasks: Neo4j 圖資料庫對接與極深股權 UBO 關係鏈穿透

本文件列出了本階段開發任務的 checkbox 進度。所有標題與格式均嚴格依循 OpenSpec Parser 規範。

---

## 1. Neo4j Docker Container Configuration
- [ ] 1.1 在 `docker-compose.yml` 中配置 `neo4j` 容器服務，設置持久化 Volumes 與環境變數。
- [ ] 1.2 在 `requirements.txt` 中引入後端官方依賴包 `neo4j>=5.18.0`。
- [ ] 1.3 啟動 Neo4j 容器並手動登入 `http://localhost:7474` 驗證資料庫通訊正常。

## 2. Neo4j Store & Driver Integration
- [ ] 2.1 創建 `src/graph/store.py`，編寫 Neo4j 圖資料庫驅動管理器，實作單例 Bolt 連線管理。
- [ ] 2.2 在 `src/api/dependencies.py` 中引入 Neo4j 驅動依賴注入，支持運行時 Session 池調用。
- [ ] 2.3 編寫防禦性錯誤重試機制，當 Neo4j 容器尚未完全啟動時自動重試連線。

## 3. Graph Sync Engine
- [ ] 3.1 創建 `src/graph/sync.py`，開發 `GraphSyncEngine` 圖同步器。
- [ ] 3.2 實作對合規元模型物件（如 Clause, Obligation, CustomerContext）的 Cypher `MERGE` 寫入轉換器。
- [ ] 3.3 在 API 啟動（FastAPI Startup Event）中自動執行初始同步，將金標數據同步寫入 Neo4j。

## 4. Cypher UBO Penetration & Loop Detection
- [ ] 4.1 實作多層股權穿透 Cypher 查詢，提取加權持股比大於等於 10% 的 UBO 節點。
- [ ] 4.2 實作自動環路檢測 Cypher 查詢，動態尋找交叉持股或循環股權控股圈。
- [ ] 4.3 於後端 API 增設 `/api/v1/graph/ubo` 與 `/api/v1/graph/loops` 接口，回傳強型別強校驗 JSON 數據。

## 5. Verification & Walkthrough
- [ ] 5.1 撰寫整合測試 `tests/test_graph_db.py`，測試 Neo4j 圖同步、UBO 穿透與環路檢測邏輯。
- [ ] 5.2 執行全量 `pytest` 單元測試，確保專案整體通過率達 100% 且無向下相容破壞。
- [ ] 5.3 執行 `openspec validate integrate-graph-database --strict --no-interactive` 通過規格驗證。
- [ ] 5.4 封存歸檔變更並更新 `walkthrough.md` 呈報。
