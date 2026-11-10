# CDD-GraphWiki

[![CI](https://github.com/DancinAndrew/CDD-GraphWiki/actions/workflows/ci.yml/badge.svg)](https://github.com/DancinAndrew/CDD-GraphWiki/actions/workflows/ci.yml)

**What it is:** a proof-of-concept anti-money laundering (AML) customer due diligence (CDD) workflow. It parses verbatim excerpts of FATF Recommendation 10 and MAS Notice 626, plus a fictional bank policy, into 54 schema-validated clauses and links them in a knowledge graph with obligations, conflicts and customer contexts. A rule-based extractor finds all 12 obligations in my hand-labelled gold set, with the right source clauses. The system flags 3 conflicts between sources, such as 25% versus 10% beneficial ownership thresholds. It generates CDD/EDD checklists that cite their source clauses for 5 synthetic customer profiles, and routes high-risk cases to human review with a SHA-256 hash chain audit log.

**Held-out test:** to see whether the rules generalise, the full official MAS Notice 626 (167 paragraphs, 419 clause records) was converted from the PDF, and the 157 paragraphs not used to write the rules were labelled against a written guideline. The labels were committed before the rules were run on them. On those paragraphs the rules found 1 of 18 labelled obligations (paragraph level, precision 0.14). A local open-weight LLM (qwen3.5:9b, temperature 0) given the same guideline found 16 of 18 but with precision 0.40. The keyword rules overfit their development text and the LLM over-labels neighbouring duties, so neither replaces the human review step.

**My role:** individual final project for the IT Risk Management course at National Central University (May–June 2026). I designed and built the data contracts, gold dataset, extraction and decision rules, evaluation, API and dashboard.

**How to run:** `docker compose -f deployment/docker-compose.yml up --build` starts the dashboard at `http://localhost:3000`. `PYTHONPATH=backend python -m src.pipeline` rebuilds `data/processed` and prints every number below. `PYTHONPATH=backend pytest backend/tests` runs the 89 tests. `PYTHONPATH=backend python -m src.heldout.evaluate` and `PYTHONPATH=backend python -m src.heldout.llm_compare score` recompute the held-out scores.

| Number | Where it comes from |
| --- | --- |
| 54 clauses with text, plus 5 section-heading records (59 records: FATF 17, MAS 28, fictional bank policy 14) | [`data/processed/clauses.yaml`](data/processed/clauses.yaml), parsed from [`data/sources/`](data/sources/) |
| 12/12 gold obligations found, each with the right anchor clause, jurisdiction and full set of source clauses | [`data/processed/evaluation_report.txt`](data/processed/evaluation_report.txt) |
| 3 conflicts: ownership 25% vs 10%, occasional transactions USD/EUR 15,000 vs S$20,000, PEPs allowed vs prohibited | [`data/processed/conflicts.yaml`](data/processed/conflicts.yaml) |
| 5 checklists for 5 synthetic profiles, 4 routed to human review | [`data/processed/checklists.yaml`](data/processed/checklists.yaml) |
| All numbers in one file | [`data/processed/summary.json`](data/processed/summary.json) |
| Held-out (157 MAS Notice 626 paragraphs not used to write the rules): rules find 1/18 labelled obligations, precision 0.14 | [`data/heldout/results/rules_report.txt`](data/heldout/results/rules_report.txt) |
| Same paragraphs, local LLM qwen3.5:9b: 16/18, precision 0.40; all 108 clause IDs it returned exist | [`data/heldout/results/llm_qwen3_5_9b_report.txt`](data/heldout/results/llm_qwen3_5_9b_report.txt) |

The development gold set in [`data/gold/`](data/gold/) is my own annotation of these sources and the rules were written against it, so 12/12 shows that the rules cover the annotated obligations; the held-out rows show they do not generalise. The LLM chose clause IDs from the one paragraph it was sent, so its valid citations do not show it would cite correctly without that list. The MAS texts are checked line by line against the official PDF in [`data/sources/official/`](data/sources/official/) by the test suite.

![Demo: pick a synthetic customer, read the checklist and the clauses it cites, open the review queue, then trace the checklist in the knowledge graph](images/00-demo.gif)

---

CDD-GraphWiki 是一個為「科技風險管理」課程開發的專案，結合了 AI 輔助的風險工作流程，以及以圖（graph）為基礎的知識組織方式。

它探討的是：如何把合規文件、風險義務、客戶／實體資訊、審查決策、稽核證據，組織成一條可追溯的工作流程，而不是做成一個通用的「上傳 PDF 然後聊天」的應用。

## 30 秒摘要

- **這是什麼：** 一個概念驗證（proof-of-concept）的合規工作流程系統，針對 AML／CDD 盡職調查情境。
- **它展示了什麼：** 結構化的合規知識萃取、以圖為基礎的關係對應、CDD／EDD 檢查清單生成、人工審查路由，以及防篡改的稽核日誌。
- **為什麼重要：** 風險與合規工作仰賴大量零散的文件、要求、實體、證據、簽核和歷史決策。這個專案示範了一種做法——讓 AI 與知識圖譜支援這套流程，同時保持「人的判斷」與「來源出處」清楚可見。
- **目前狀態：** 課程期末專案／可運作的原型，不是正式的法律或合規決策系統。

## 問題

風險與合規審查經常需要在零散的文件、政策、實體紀錄、義務和歷史審查決策之間翻找。這帶來幾個實際的問題：

- 資訊散落在不同的文件和系統裡
- 實體、文件、風險、義務和證據之間的關係很難追蹤
- 人工查找拖慢了合規審查與盡職調查的流程
- 團隊需要的是可解釋、可追溯的檢索，而不是模型給出的黑箱答案
- 高風險的決策仍然需要人工審查、上呈與可稽核性

## 解法

CDD-GraphWiki 把合規知識組織成結構化的物件與圖的關係，再用這套結構去支援風險審查流程。

原型的處理流程如下：

1. 匯入法規或政策來源。
2. 把來源切分成穩定的條文（clause）紀錄。
3. 萃取合規義務與證據要求。
4. 建立一張法規知識圖譜，連結文件、條文、義務、客戶、衝突和檢查清單。
5. 從結構化的客戶情境（customer context）生成 CDD／EDD 檢查清單。
6. 把高風險案件路由到人工介入（human-in-the-loop）的審查。
7. 用防篡改的 SHA-256 雜湊鏈，記錄推理過程、案件路由和審查者的決策。

目標不是取代合規判斷，而是讓資訊檢索、關係對應、審查路由和稽核證據更容易被檢視。

## 與合規／風險管理的關聯

示範的領域是 AML／CDD，但這套設計模式同樣適用於更廣的風險與合規工作流程，包含產品合規的情境。

產品合規團隊通常需要管理：

- 法規要求與標準
- 產品需求與測試證據
- 認證或核可紀錄
- 風險發現與緩解決策
- 文件與產品之間的關聯
- 跨部門的審查歷史

CDD-GraphWiki 展示了在這些情境中可以轉移套用的工作流程概念：

- 文件與需求的檢索
- 風險證據的組織
- 實體／文件／義務之間的關係對應
- 可追溯的 AI 輔助審查支援
- 高風險決策的人工簽核邊界
- 供日後查閱的稽核日誌

## 主要功能

- **結構化的合規資料契約：** 以 JSON Schema 和 Pydantic 模型定義來源文件、條文、義務、客戶情境、衝突、檢查清單、圖節點和稽核日誌。
- **規則式義務萃取：** 規則比對條文與它的上層段落，持股與金額門檻直接從條文文字解析（例如 `25%`、`USD/EUR 15,000`、`S$20,000`），不依賴特定條文 ID。評估同時檢查義務是否對應到正確的條文與管轄區。
- **衝突偵測：** 比較不同來源對同一類義務的門檻或立場，目前涵蓋三類（持股門檻、偶發交易門檻、PEP 允許與禁止）。衝突會引用實際寫出數字或禁止字樣的條文。如何調和衝突是人的決定，記錄在 [`data/reviews/conflict_adjudications.yaml`](data/reviews/conflict_adjudications.yaml)；沒有裁決紀錄的衝突會讓相關檢查清單送人工審查。
- **CDD／EDD 決策：** 以規則為基礎，從結構化的客戶情境生成檢查清單，包含所需文件、風險觸發條件、引用出處、衝突，以及人工審查標記。引用一律是適用義務的錨點條文 ID，可以在圖譜上一路追回原文。
- **人工介入審查：** 針對高風險或不明確的案件提供審查佇列，審查者的決策與註記都透過 FastAPI 驗證後記錄下來。
- **防篡改稽核軌跡：** 用 SHA-256 雜湊鏈記錄推理過程、案件路由和審查者的覆寫。
- **法規圖譜視覺化：** 以 D3 製作的互動式圖，連結來源文件、條文、義務、衝突、客戶和生成的檢查清單。
- **Neo4j 圖資料庫支援：** 可選的圖資料庫同步，以及用 Cypher 進行 UBO 股權穿透追蹤／循環偵測。
- **PDF 匯入工作流程：** PDF 上傳、文字萃取、LLM 輔助的條文切塊、結構化義務萃取、YAML 合併、快取刷新，以及圖譜／檢查清單更新。若沒有接上真實 LLM（或呼叫失敗退回 mock 模式），匯入會失敗，不會把合成資料寫進知識庫。
- **評估與治理產出物：** 黃金資料集（gold dataset）、評估工具（evaluation harness）、未用於開發的 held-out 測試與 LLM 對照、OpenSpec 需求、ADR，以及系統路線圖文件。評估工具內的 `ScriptedRAGBaseline` 是刻意寫入錯誤的測試 fixture，用來確認評估工具抓得到錯判與幻覺引用，不是真實系統的分數。

## Demo 與視覺素材

在本機跑起應用後，即可使用線上 demo：

- 前端儀表板：`http://localhost:3000`
- 後端 API 文件：`http://localhost:8000/docs`
- Neo4j Browser：`http://localhost:7474`

既有的視覺素材：

![Phase 1-10 Architecture](docs/assets/phase_1_10_architecture.png)

- 架構圖：[`docs/assets/phase_1_10_architecture.png`](docs/assets/phase_1_10_architecture.png)
- 未來發展方向預覽：[`docs/assets/future_development_direction_preview.png`](docs/assets/future_development_direction_preview.png)
- 投影片／第 15-21 頁的 demo 解說：[`docs/presentation_script_pages_15_21.md`](docs/presentation_script_pages_15_21.md)

專案投影片包含更完整的儀表板導覽，涵蓋儀表板、審查佇列、稽核時間軸、圖譜檢視、匯入主控台和使用者指南。

## 畫面截圖

以下是實際運作 demo 的截圖。每個頁面負責合規審查流程中的一個步驟。

### 1. 合規儀表板（Compliance Dashboard）

![合規儀表板](images/01-dashboard.png)

首頁。最上方顯示一個快速摘要（有多少客戶、有多少案件需要人來看、有多少已經處理完）。你從左邊的清單挑一個客戶，系統就會自動產生一份檢查清單——列出這個客戶需要哪些文件和檢查，並列出這份清單依據的條文（官方法規或銀行內部政策）。

### 2. 人工審查佇列（Human Review Queue）

![人工審查佇列](images/02-review-queue.png)

當案件有風險或不明確時，系統不會自己下決定，而是把案件送到這裡讓真人來審查。審查者讀完案件後，挑一個決定（核准、要求更深入的查核，或駁回），寫下說明理由的註記，然後送出。這讓重要的決定始終由人來掌控。

### 3. 稽核軌跡（Audit Trail）

![防篡改稽核軌跡](images/03-audit-trail.png)

一份完整的歷史紀錄——所有發生過的事、每一個決定、每一次審查，按順序排列。每一筆紀錄都用數位「指紋」（雜湊）鏈鎖在一起，所以如果有人想偷偷竄改舊紀錄，馬上就會被發現。這就是你日後可以拿出來證明「流程確實有照規矩走」的依據。

### 4. 知識圖譜檢視（Knowledge Graph View）

![法規知識圖譜](images/04-graph-view.png)

一張互動式的地圖，呈現所有東西怎麼連在一起——法規、文件、客戶、要求和生成的檢查清單都畫成圓點，再用線標出彼此的關係。你不必在一堆分散的檔案裡翻找，就能看到全貌，並追溯任何一項要求是從哪裡來的。

### 5. 法規匯入主控台（Regulation Ingestion Console）

![PDF 匯入主控台](images/05-ingestion.png)

把新法規加進系統的地方。你上傳一份官方法規文件（PDF），系統會讀取它、把它切成一條條條文，並自動抽出其中的義務。右邊的面板會即時顯示處理檔案的進度。

## 系統架構

```text
Source PDFs / Markdown / Policies
        |
        v
PDF parser and source document records
        |
        v
Clause segmentation and structured obligation extraction
        |
        v
YAML gold / processed datasets + JSON Schema / Pydantic contracts
        |
        v
Regulatory graph: documents, clauses, obligations, conflicts, customers, checklists
        |
        v
CDD / EDD checklist generation
        |
        v
Human review queue + tamper-evident audit log
        |
        v
React dashboard, D3 graph view, FastAPI endpoints, optional Neo4j queries
```

重要的設計邊界：系統把客戶輸入當成結構化的 `CustomerContext` 來處理，而不是當成不受限制的 prompt。高風險的決策一律路由到人工審查。

## 技術堆疊

- **前端：** React 18、TypeScript、Vite、D3、lucide-react
- **後端：** Python、FastAPI、Pydantic、PyYAML、jsonschema
- **匯入：** pypdf、PDF 文字萃取、結構化的條文與義務萃取
- **圖：** 記憶體內的法規圖建構器、D3 視覺化、可選的 Neo4j Community Edition
- **AI／LLM：** 支援 NVIDIA NIM、Gemini 後備方案；mock 模式只供測試，產出不會寫入知識庫
- **資料：** YAML 黃金資料集、處理後資料集、JSON Schema 契約
- **測試：** pytest 後端測試、評估工具、範例 schema
- **部署：** Docker、Docker Compose
- **治理：** OpenSpec 規格／變更，以及 ADR 決策紀錄

## 專案資料

- 論文／書面報告：[Google Docs](https://docs.google.com/document/d/18sSEPHwYYoJUjvCJkYucqSJ-gF9ndiVysm-VFIubL8g/edit?tab=t.0)
- 簡報投影片：[Google Slides](https://docs.google.com/presentation/d/1fYlCTjPTBb8Kf8QJfHVWZ1CbFYJCz8LnEv-pMoTzKeQ/edit?slide=id.g3ec91351360_1_53#slide=id.g3ec91351360_1_53)
- 產品／規格論述：[`docs/SPEC.md`](docs/SPEC.md)
- 系統路線圖：[`docs/system-build-roadmap.md`](docs/system-build-roadmap.md)
- 架構決策：[`docs/adr/`](docs/adr/)
- OpenSpec 契約：[`openspec/`](openspec/)

## 如何執行

### 方式 A：用 Docker Compose 執行

```bash
git clone https://github.com/DancinAndrew/CDD-GraphWiki.git
cd CDD-GraphWiki
cp .env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

接著打開：

- 前端：`http://localhost:3000`
- 後端 API 文件：`http://localhost:8000/docs`
- Neo4j Browser：`http://localhost:7474`
  - 帳號：`neo4j`
  - 密碼：`testpassword123`

預設的 `.env.example` 裡放的是佔位用的 AI 金鑰。即使沒有真正的模型金鑰，核心 demo 資料和所有規則式流程都能執行；只有 PDF 匯入（含 LLM 萃取）需要設定好的供應商金鑰。

### 方式 B：後端與前端分開執行

後端：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn src.api.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

基本 demo 不一定要 Neo4j。如果 Neo4j 不可用，API 會在數個圖工作流程上退回（fallback）到記憶體內的行為。

### 重現所有數字與測試

```bash
PYTHONPATH=backend python -m src.pipeline
PYTHONPATH=backend pytest backend/tests

# 未用於開發的測試（held-out）：規則與 LLM 在 MAS Notice 626 全文上的表現
PYTHONPATH=backend python -m src.heldout.evaluate          # 規則式萃取器
PYTHONPATH=backend python -m src.heldout.llm_compare score # 用快取的 LLM 回答重新計分，不需要模型
ollama pull qwen3.5:9b && PYTHONPATH=backend python -m src.heldout.llm_compare run  # 重新呼叫模型（選用）
```

GitHub Actions 每次 push 都會跑全部測試、重跑管線與 held-out 評估，並確認輸出和 commit 的檔案完全相同。

管線會依序執行：解析來源 → 萃取義務並與金標比對 → 偵測衝突並套用人工裁決 → 為 5 個合成客戶產生檢查清單，把結果寫進 `data/processed/` 並印出摘要。輸出是確定性的，重跑兩次檔案內容完全相同。測試會先把管線跑到暫存目錄，稽核日誌也寫到暫存檔，不會改動 repo 裡的資料。

## 未用於開發的測試（held-out）

12/12 是在寫規則時看過的資料上得到的，不能說明規則能不能用在新的條文上。為了檢驗這點：

1. **全文：** 用 [`backend/src/heldout/convert.py`](backend/src/heldout/convert.py) 把官方 MAS Notice 626 PDF 轉成 Markdown，共 167 個編號段落、419 筆條文紀錄。測試會逐行比對 PDF 原文，跨頁的段落也一樣。
2. **切出測試資料：** 寫規則時用過的 10 個段落（6.3、6.5、6.6、6.9、6.13、6.14、6.14B、6.35、8.2、8.3）整段排除，剩下的 157 段是測試資料。
3. **先標註、先 commit：** 依 [`標註準則`](data/heldout/ANNOTATION_GUIDELINE.md) 標出哪些條文屬於系統建模的 8 種義務類型，標註（[`gold_labels.yaml`](data/heldout/gold_labels.yaml)）在規則跑這些段落之前就 commit 了，git 歷史可以看到順序。共 16 段、42 筆條文帶有類型。
4. **原封不動地跑規則**，再用同一份準則讓本機的開源模型 qwen3.5:9b（Ollama，temperature 0，固定 seed）逐段標註；模型的原始回答都存在 [`data/heldout/llm_runs/`](data/heldout/llm_runs/)，沒有模型也能重新計分。

| | 段落層級：找到 | 段落層級：精確率 | 條文層級：精確率／召回率 |
| --- | --- | --- | --- |
| 規則式萃取器 | 1／18 | 0.14 | 0.41／0.32 |
| qwen3.5:9b | 16／18 | 0.40 | 0.30／0.56 |

**規則為什麼失準**（細節見 [`rules_report.txt`](data/heldout/results/rules_report.txt)）：
- 規則綁定開發段落的句型。例如 CDD 觸發規則要找「measures as required by paragraphs … when」，6.31 寫成「shall – (a) perform CDD measures as if …」就漏掉；10.3 的代理銀行條款剛好含有這個句型，反而誤判。
- 規則依管轄區設定。禁止匿名帳戶只有 FATF 的設定，所以 MAS 第 6.1 段明明寫著禁止，也抓不到。
- 規則不處理否定與放寬。第 6.16 段「shall not be required to inquire」（豁免查詢受益人）被判成要查詢受益人，一段就多出 10 筆誤判。
- 每筆條文最多只給一種類型，所以第 6.32 段「同時驗證客戶與受益人」最多只能對一半。

**LLM 的問題在另一邊**（[`llm_qwen3_5_9b_report.txt`](data/heldout/results/llm_qwen3_5_9b_report.txt)）：它找得到大部分義務，但會把相近的責任也標進來。例如代表客戶行事的人（6.10）被當成客戶身分驗證、關聯方（6.8）被當成受益人識別；名單篩檢的時點（6.40）被當成 CDD 觸發；非 PEP 的高風險客戶加強審查（8.7）也被當成 PEP 義務。

結論：關鍵字規則可以解釋，但只對寫規則時看過的文字有效；小型 LLM 召回率高，但精確率不到一半。兩者都需要人工審查把關，這也是系統把高風險清單送人工審查的理由。

這個測試的限制：標註只有一位標註者，沒有測量標註者間的一致性；段落層級只有 18 項，數字的波動會很大；LLM 只測了一個 9B 的本機模型，沒有測更大的託管模型；LLM 回傳的條文 ID 只能從送給它的那一段裡選，所以 0 筆無效 ID 不代表它在開放情境下不會捏造引用。

## 專案目錄導覽

- [`backend/`](backend/) - FastAPI 服務、資料契約、決策引擎、稽核管理器、圖建構器、匯入、評估和測試
- [`frontend/`](frontend/) - React 儀表板，包含合規總覽、審查佇列、稽核時間軸、法規圖譜、匯入主控台和使用者指南
- [`data/sources/`](data/sources/) - 管線讀取的三份來源：FATF R.10 與 MAS Notice 626 的官方原文逐字摘錄，以及虛構的銀行內部政策；[`official/`](data/sources/official/) 放 MAS Notice 626 官方 PDF
- [`data/gold/`](data/gold/) - 人工標註的黃金資料集：條文（parser 輸出經人工檢查後凍結）、義務、衝突、客戶情境與預期檢查清單
- [`data/reviews/`](data/reviews/) - 衝突的人工裁決紀錄
- [`data/heldout/`](data/heldout/) - 未用於開發的測試：MAS Notice 626 全文（由官方 PDF 轉出）、標註準則、先於規則執行 commit 的金標、規則與 LLM 的評估結果，以及 LLM 的原始回答
- [`data/processed/`](data/processed/) - `python -m src.pipeline` 產生的結果與 `summary.json`，以及只能追加的稽核日誌 `audit_log.json`
- [`schemas/`](schemas/) - JSON Schema 契約與範例
- [`docs/`](docs/) - 產品規格、路線圖、ADR、論文筆記、簡報支援素材和視覺素材
- [`openspec/`](openspec/) - 需求規格與封存的實作變更
- [`deployment/`](deployment/) - Docker 與 Docker Compose 設定

## 範例工作流程

1. 打開儀表板，檢視可用的客戶情境。
2. 選一個客戶，查看生成的 CDD／EDD 檢查清單。
3. 檢視所需文件、風險觸發條件、適用義務和引用出處。
4. 打開審查佇列，查看需要人工簽核的案件。
5. 送出審查者的決策與註記。
6. 確認稽核時間軸有記錄下推理過程與審查事件。
7. 打開圖譜檢視，檢視文件、條文、義務、客戶、衝突和檢查清單之間的關係。
8. （選用）透過匯入主控台上傳一份法規 PDF，並監看萃取進度。

## 目前的限制

- 這是課程專案的原型，不是正式的法律意見，也不是已部署的合規平台。
- 主要的 demo 語料偏向 AML／CDD，不是產品合規的語料。
- 決策用的語料只是 FATF R.10 與 MAS Notice 626 的部分段落摘錄，加上一份虛構的銀行政策；規則是對照這份金標寫的。在 MAS Notice 626 其餘 157 段上，規則只找到 18 項義務中的 1 項（見上方 held-out 測試）。
- 衝突偵測目前只涵蓋三類衝突（持股門檻、偶發交易門檻、PEP 允許與禁止）。
- CDD 決策層刻意設計得受限且以規則驅動，以換取可解釋性：決策分支是寫好的規則，引用則由義務的出處推導。
- PDF 匯入用 LLM 切條文，條文 ID 格式和 parser 不同；重跑管線會以 `data/sources/` 重建知識庫，透過匯入主控台加入的文件不會保留。
- 真正的 PDF 匯入時，LLM 萃取仰賴設定好的供應商金鑰。
- 在真正用於合規之前，還需要更嚴謹的檢索評估、人工標註、存取控制和正式的治理機制。

## 未來改進

- 把語料從 AML／CDD 範例擴展到產品合規標準、產品需求文件、認證證據和測試報告。
- 加入證據等級的檢索，結合 BM25、密集檢索（dense retrieval）、GraphRAG，以及字元級（character-span）的引用支援。
- 擴展圖推理，支援產品對需求、需求對測試、風險對證據的可追溯性。
- 強化衝突與落差的裁決，導入 NLI、LLM 輔助的矛盾偵測，以及明確的人工解決流程。
- 加入角色式存取控制（RBAC）、審查者權限，以及正式部署的強化。
- 建立更豐富的截圖／demo 素材資料夾，方便招募者與用人主管快速檢視。

## 修訂紀錄

- **2026-11（課程結束後的修補）：** 移除兩條 PDF 匯入時 LLM 退回 mock 模式產生的合成條文；把 MAS 與 FATF 來源改成官方原文的逐字摘錄（修正 SGD 5,000 應為 S$20,000，以及 25% 門檻出自 FATF 而非 MAS Notice 626）；補上 MAS 第 6.14B 段（驗證受益人）與第 6.35 段（無法完成 CDD 時不得建立業務關係），銀行政策的 PEP 禁令與核准要求拆成兩條義務；萃取規則改成依文字判斷、不再指定條文 ID；衝突與檢查清單的引用改由解析出的條文推導，人工裁決只套用在當時裁決的條文上；評估加入出處檢查；PDF 匯入先驗證再寫檔；新增一鍵重建管線，測試不再改寫 repo 資料。課程繳交版本見 git 歷史中 2026-06 的 commit。
- **2026-11（held-out 測試）：** 把官方 MAS Notice 626 全文轉成可解析的 Markdown；在規則沒看過的 157 段上先標註、先 commit，再跑規則，並用本機開源 LLM 做對照；新增 GitHub Actions，每次 push 都重跑測試、管線與評估並比對輸出；README 加上示範動畫；評估工具裡手寫的對照組改名為 `ScriptedRAGBaseline`，避免被誤認為真實系統。

## 免責聲明

CDD-GraphWiki 是一個學習與原型專案，目的是示範 AI 輔助的合規工作流程設計、以圖為基礎的知識組織，以及可稽核性的模式。它不應被當作法律、法規、財務或正式合規的建議使用。
