# 提案：重構與優化專案資料夾結構

本提案旨在重構與清理 CDD-GraphWiki 專案的根目錄與代碼結構，使其符合現代 Web 開發（特別是前後端分離）的最佳實踐，同時讓專案目錄具備高可維護性、清晰度與專屬用途。

## 1. 動機 (Why)

目前 CDD-GraphWiki 專案的目錄結構存在以下管理與規範上的痛點：
1. **目錄結構不對稱**：前端代碼有獨立的 `frontend/` 資料夾，但後端 Python 代碼直接鋪在根目錄下的 `src/`，且測試代碼在 `tests/`，這對多套件/前後端分離的專案來說不夠對稱，難以直觀看清前後端界線。
2. **根目錄混亂**：根目錄充斥著已廢棄的 Demo 檔案（如 `audit_report_demo.html`, `regulatory_graph_demo.html`, `demo.py`）與佈署設定（`Dockerfile`, `docker-compose.yml`），缺乏統一規劃。
3. **規則檔案重疊**：存在 `AGENTS.md` 與 `gemini.md` 兩個作用相近的 AI 開發守則檔案，應該進行整合，以 Gemini 最憲法為尊。
4. **規格文件位置**：`SPEC.md` 目前位於根目錄，應該移入更合適的文件資料夾（如 `docs/`）中統一管理，保持根目錄的簡潔度。
5. **過時文件存留**：`HANDOVER.md` 是前一階段的交接文件，目前已完成階段任務，應該刪除或歸檔。

---

## 2. 變更範圍 (What Changes)

本變更將實施以下結構調整：
1. **後端代碼對稱化**：
   - 建立 `backend/` 目錄。
   - 將根目錄下的 `src/` 移動到 `backend/src/`，使後端主代碼位置對齊 `frontend/`。
   - 將根目錄下的 `tests/` 移動到 `backend/tests/`。
   - 將與後端專屬的配置（例如 `requirements.txt`）移入 `backend/` 目錄下。
2. **佈署設定模組化**：
   - 建立 `deployment/` 目錄。
   - 將 `Dockerfile` 與 `docker-compose.yml` 移動到 `deployment/` 中。
3. **規格與文檔集中化**：
   - 將 `SPEC.md` 移動到 `docs/SPEC.md`。
   - 更新所有系統文檔、OpenSpec 配置文件與 `gemini.md` 中對於 `SPEC.md` 的引用路徑。
4. **AI 規則文件合併**：
   - 將 `AGENTS.md` 中的專案約束、ECC 守則、運行規則等內容，完整合併到 `gemini.md` 底下。
   - 刪除根目錄下的 `AGENTS.md`。
5. **理清廢棄檔案**：
   - 完全刪除用不到的 `audit_report_demo.html`、`regulatory_graph_demo.html`、`demo.py` 以及 `demo_ingestion_nim.py`。
   - 完全刪除 `HANDOVER.md`。

---

## 3. 系統能力 (Capabilities)

本變更不會直接修改任何業務邏輯代碼，但將大幅提升專案的**可維護性 (Maintainability)** 與 **架構清晰度 (Architectural Clarity)**，為 Phase 2 以及後續的前後端協同開發奠定堅實的工程基礎。

---

## 4. 影響範圍 (Impact)

- **對開發流程**：所有 AI 與人類開發者在撰寫後端代碼時，工作目錄改為 `backend/src/`，測試執行範圍改為 `backend/tests/`。
- **對 OpenSpec 機制**：需更新 `openspec/config.yaml` 中對 `SPEC.md` 的路徑定義與對專案狀態的描述。
- **對 CI/CD 與運行設定**：`Dockerfile` 與 `docker-compose.yml` 移入 `deployment/` 後，後續構建與容器運行命令需調整 context 路徑。
