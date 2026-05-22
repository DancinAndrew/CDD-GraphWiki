# Spec: Graph Store Integration & UBO Penetration

本規格書定義了 CDD-GraphWiki 圖資料庫對接與極深股權 UBO 穿透、環路檢測的系統行為合約。

---

## ADDED Requirements

### Requirement: Graph Database Synchronization
系統 **SHALL** 支持將當前合規元模型與客戶事實圖譜自動同步至 Neo4j，以保持記憶體與實體圖數據庫的一致性。

#### Scenario: Startup Automatic Synchronization
GIVEN 當系統載入典型金標數據集並啟動 FastAPI 後端 API 時
WHEN 圖資料庫同步引擎啟動
THEN 系統 **SHALL** 自動將所有 `SourceDocument`, `Clause`, `Obligation`, `CustomerContext` 及關聯邊以 `MERGE` 陳述式同步寫入 Neo4j。

### Requirement: Multi-Layer UBO Penetration Query
系統 **SHALL** 通過 Cypher 語法執行遞迴穿透查詢，實時計算出所有實質受益人（UBO）的持股百分比。

#### Scenario: Corporate Customer Multi-Layer Ownership Chart
GIVEN 一個擁有多層複雜股權結構且股權路徑包含 PEP 的法人客戶
WHEN 合規官調用 UBO 穿透 API 接口時
THEN 系統 **SHALL** 執行 Cypher 穿透，計算並回傳有效持股加乘大於等於 10% 的所有實質受益人（UBO）個人，且回傳格式中 **MUST** 包含完整的穿透路徑 nodes 列表。

### Requirement: Circular Ownership Loop Detection
系統 **SHALL** 具備自動控股環路檢測能力，並提供及時合規警報。

#### Scenario: Identify Circular Holding Among Shell Companies
GIVEN 多個空殼公司之間存在交叉控股或循環控股的股權結構
WHEN 系統對其執行推理自檢或定時掃描時
THEN 系統 **SHALL** 自動偵測到此循環控制環路，並在 Checklist 推理結果中將 `human_review_required` 標記強制置為 `True`，同時標記該環路節點。
