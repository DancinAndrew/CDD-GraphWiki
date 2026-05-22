# Tasks for Project Directory Restructuring

## 1. Merge Rules and Configs

- [x] 1.1 將 `AGENTS.md` 的精華內容合併至 `gemini.md` 中，並補強專案硬約束與運作限制
- [x] 1.2 更新 `gemini.md` 內部的檔案引用路徑（例如將所有 `SPEC.md` 的參考路徑修正為 `docs/SPEC.md`）
- [x] 1.3 更新 `openspec/config.yaml` 中對 `SPEC.md` 的路徑設定，並更新當前工程狀態描述
- [x] 1.4 修改 `README.md`，更新專案目錄結構與相關檔案指引的描述

## 2. Restructure Project Directory

- [x] 2.1 建立全新的後端目錄結構 `backend/` 
- [x] 2.2 將根目錄下的後端源碼 `src/` 移動至 `backend/src/`
- [x] 2.3 將根目錄下的測試目錄 `tests/` 移動至 `backend/tests/`
- [x] 2.4 將後端依賴檔案 `requirements.txt` 移動至 `backend/requirements.txt`
- [x] 2.5 建立佈署設定目錄 `deployment/`，並將 `Dockerfile` 與 `docker-compose.yml` 移入其中
- [x] 2.6 將產品規格書 `SPEC.md` 移動至 `docs/SPEC.md`

## 3. Clean Legacy Files

- [x] 3.1 完全刪除已被合併且過時的 `AGENTS.md` 以及階段交接檔案 `HANDOVER.md`
- [x] 3.2 完全刪除用不到的舊 Demo 檔案：`audit_report_demo.html`、`regulatory_graph_demo.html`、`demo.py` 以及 `demo_ingestion_nim.py`

## 4. Verification and Validation

- [x] 4.1 執行 OpenSpec 語法校驗指令：`openspec validate restructure-project-directories --strict --no-interactive`
- [x] 4.2 切換至 `backend/` 目錄執行本地單元測試，確保 Python 後端測試執行路徑依然 100% 正確
- [x] 4.3 驗證 Docker 佈署設定的路徑指針與 context 正確性

