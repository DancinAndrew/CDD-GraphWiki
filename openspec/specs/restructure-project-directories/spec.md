# restructure-project-directories Specification

## Purpose
TBD - created by archiving change restructure-project-directories. Update Purpose after archive.
## Requirements
### Requirement: Structured Directory Separation

CDD-GraphWiki 專案目錄 SHALL 保持整潔、有條理且對稱。所有系統模組必須具備清晰的職責分離 (separation of concerns)。

- 後端 Python 源碼與測試檔案 SHALL 收納於 `backend/` 目錄下（即 `backend/src/` 與 `backend/tests/`）。
- 系統環境設定與佈署相關的基礎設施程式碼（例如 `Dockerfile` 與 `docker-compose.yml`） SHALL 收納於 `deployment/` 目錄下。
- 所有產品規格文件 (Spec)、架構決策紀錄 (ADR) 以及其他說明文檔 SHALL 收納於 `docs/` 目錄下，確保專案根目錄的乾淨與整潔。
- 已廢棄的舊 Demo 檔案與過時的階段交接文檔 SHALL 自工作區完全移除。

#### Scenario: Verify Clean Workspace Structure

Given 專案目錄結構已重構完成，
When 列出專案根目錄下的檔案與資料夾，
Then 根目錄 MUST NOT 包含任何已廢棄檔案（如 `demo.py`、`demo_ingestion_nim.py`、`audit_report_demo.html`、`regulatory_graph_demo.html`、`HANDOVER.md`），
And 後端核心程式碼目錄 `src/` 與測試目錄 `tests/` MUST 位於 `backend/` 目錄內，
And 佈署設定檔 `Dockerfile` 與 `docker-compose.yml` MUST 位於 `deployment/` 目錄內，
And 頂層核心規格書 `SPEC.md` MUST 位於 `docs/` 目錄內。

### Requirement: Unified AI Agent Rulebook

所有 AI 代理程式的指令檔、開發守則與專案專屬限制 SHALL 統一整合至專案根目錄的單一規則書 `gemini.md` 中，以確保合規與避免指令衝突。

- `AGENTS.md` 的所有精華內容與專案約束 SHALL 被合併至 `gemini.md` 成為獨立的「CDD-GraphWiki 專案專屬約束與運作規則」小節。
- 獨立的 `AGENTS.md` 檔案 SHALL 被完全刪除，確保 `gemini.md` 作為唯一且最高效力的 AI 規則書。

#### Scenario: Verify Unified Agent Instruction

Given `AGENTS.md` 已被合併至 `gemini.md` 中，
When 檢查專案根目錄，
Then 檔案 `AGENTS.md` MUST NOT 存在，
And 檔案 `gemini.md` MUST 包含合併後的專案專屬運作約束、ECC 守則與 SOP 流程之繁體中文描述。

