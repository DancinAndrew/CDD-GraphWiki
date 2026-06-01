# 第 15-21 頁報告逐字稿

用途：明天報告 PDF 第 15-21 頁，時間抓 6-8 分鐘。  
語氣：繁中口語、課堂報告用。  
保守界線：這份稿只講 PDF 畫面與 repo 中已實作或已規格化的功能，不把 demo 說成正式上線的金融生產系統。

## 開場提醒

這一段不是介紹一般聊天機器人，而是介紹 CDD-GraphWiki。它的定位是 AML / CDD 法規知識編譯與合規推理系統，不是把 PDF 丟進向量資料庫後讓模型自由回答。論文 methodology 也把它定義成「機器可推理、人類可閱讀」的系統，所以我會用這個角度講第 15 到 21 頁。

## 第 15 頁：解決方案與防禦技術

第 15 頁是章節轉場。前面我們講金融業導入 AI 的風險，包括黑箱、幻覺、資料偏差和監理要求；從這頁開始，我們要回答：如果 AI 真的要進入高風險合規流程，系統架構要怎麼設計，才不會變成不可追溯的聊天系統？

我們的答案是 CDD-GraphWiki。它不讓模型直接決定客戶能不能開戶，而是先把法規編譯成結構化物件，再把客戶情境結構化，最後由決策引擎產出有來源依據的 CDD 或 EDD checklist。接下來幾頁會依序看到五個模組：智能合規工作台、人工審查、hash-chain audit trail、法規決策圖譜，以及法規 PDF ingestion。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 15 頁，章節標題為「4. 解決方案與防禦技術」。 |
| 論文 | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組.md:48-62` 說明 CDD-GraphWiki、知識編譯、雙圖對齊與人工審查路由。 |
| Repo | `README.md:3-8` 說明本專案不是一般 RAG chatbot，而是 wiki concept pages、regulatory knowledge graph、CDD / EDD checklist、human review log。 |
| Repo | `docs/SPEC.md:10-12` 定義 product thesis，明確排除 generic upload PDFs and chat RAG app。 |

## 第 16 頁：智能合規工作台

第 16 頁是智能合規工作台。畫面左邊是 5 個典型客戶情境，右邊是某個客戶的 checklist 推理結果。這裡的重點是：輸入不是任意自然語言，而是結構化的 `CustomerContext`，包含客戶類型、司法管轄區、股權層級、UBO 狀態、PEP 曝險、資金來源和財富來源證據。

畫面中的 `cust_individual_low_risk` 是低風險個人，所以系統產出 standard CDD，要求 NRIC 和地址證明，並列出 MAS Notice 626 Paragraph 6.2、6.6 這類 citation。後端 `CDDChecklistEngine` 會依客戶特徵分支：低風險個人走標準 CDD，PEP 升級 EDD，UBO 不明或高風險企業進人工審查。

所以這頁要講的是：我們把「模型自由判斷」改成「資料合約加規則推理」。5 個客戶情境也是 spec 和 gold data 裡定義的測試情境，不是臨時編出來的畫面資料。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 16 頁，畫面為「智能合規工作台」，展示 5 個客戶情境、Checklist 推理結果、文件清單與 Provenance。 |
| Spec | `docs/SPEC.md:37-49` 要求 primary output 是 evidence-backed CDD / EDD checklist，包含 decision category、obligations、required evidence、risk triggers、human review flags、source citations。 |
| Spec | `docs/SPEC.md:96-107` 要求 manual gold dataset 至少包含 5 個 customer profiles 與 5 個 checklist outputs。 |
| Data | `data/gold/customer_contexts.yaml:1-64` 定義 5 個典型客戶情境。 |
| Data | `data/gold/checklists.yaml:1-15` 定義低風險個人客戶的 standard CDD 文件與 citations。 |
| Code | `backend/src/decision/engine.py:12-159` 實作從 `CustomerContext` 產生 `CDDChecklist` 的推理分支。 |
| Code | `backend/src/api/main.py:66-142` API startup 載入知識庫、產生 checklist，並自動路由人工審查案件。 |
| Frontend | `frontend/src/pages/DashboardHome.tsx:61-90` 從 API 讀取 customers 與 checklist；`frontend/src/pages/DashboardHome.tsx:240-313` 呈現推理結論、文件清單與 provenance。 |

## 第 17 頁：人工審查工作台 HITL

第 17 頁是 Human-in-the-loop 人工審查工作台。這頁的重點是：我們沒有讓系統在高風險合規情境下自動做最後法律判斷。只要碰到 UBO 不明、PEP 曝險、股權層級太深，或其他需要覆核的風險，系統就會建立 review case，交給合規官。

畫面中的案例是 `rev_corp_unclear_ubo`，對應到 `cust_corp_unclear_ubo`。這個客戶是企業、註冊在 Cayman Islands、股權有 5 層，而且 UBO unclear。後端因此判斷為 enhanced due diligence，並在 review case 裡留下 `unclear_ubo_layers`、`excessive_ownership_layers` 這類觸發理由。

合規官在前端可以核准、要求補件或拒絕，也可以覆寫 CDD 等級，並留下 reviewer ID 和 notes。後端有 Pydantic 欄位限制，避免送出不合法狀態。所以這頁不是說 AI 取代合規官，而是 AI 把高風險案件和原因整理好，再交給人做最後判斷。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 17 頁，畫面為「人工審查工作台 (HITL)」，展示 pending review case、觸發理由、approval status、CDD 等級覆寫、reviewer ID 與 notes。 |
| 論文 | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組.md:61-62` 說明高風險、衝突、缺乏證據鏈的決策會觸發人工審查路由。 |
| Spec | `docs/SPEC.md:115-119` 要求涉及 regulatory thresholds、risk classification、required evidence 或 escalation rules 的輸出需人工審查。 |
| Data | `data/gold/customer_contexts.yaml:53-64` 定義 `cust_corp_unclear_ubo`，包含 Cayman Islands、5 層股權、UBO unclear。 |
| Data | `data/gold/checklists.yaml:73-90` 定義 `cust_corp_unclear_ubo` 的 enhanced due diligence、risk triggers、human review required 與 citations。 |
| Code | `backend/src/audit/manager.py:20-62` 建立 `ReviewCase` 並寫入 audit log；`backend/src/audit/manager.py:64-128` 實作合規官覆寫與審查事件紀錄。 |
| Code | `backend/src/api/main.py:52-64` 定義 review decision request 的白名單與欄位限制；`backend/src/api/main.py:178-226` 提供案件列表與人工審查 API。 |
| Frontend | `frontend/src/pages/ReviewQueue.tsx:162-245` 呈現案件隊列與觸發理由；`frontend/src/pages/ReviewQueue.tsx:247-347` 呈現核准、補件、拒絕、CDD 等級覆寫與送出按鈕。 |

## 第 18 頁：防篡改日誌審計稽核

第 18 頁是防篡改 Audit Trail。這頁要回答的是：系統做了初審、建立人工案件、合規官覆寫決策之後，事後要怎麼證明紀錄沒有被改過？

我們的做法是 hash chain。每一筆 audit log 都有 `previous_hash` 和 `current_hash`。寫入事件時，系統會把 log id、timestamp、event type、operator、customer id、payload 和前一筆 hash 串起來，用 SHA-256 算出 current hash。只要有人回頭修改歷史 payload，重新驗證時 hash 就會對不上。

畫面右邊是時間線，能看到引擎初審、案件路由、人工覆寫等事件。前端也呼叫 verify API 檢查整條鏈。這裡要保守講：PDF 截圖顯示約 250 筆紀錄，但 repo 目前是 268 筆，所以不要把 250 說成固定 benchmark；比較準確是說 demo 已累積數百筆可驗證紀錄。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 18 頁，畫面為「防篡改日誌審計稽核」，展示完整性狀態、Audit Trail、事件類型與 hash。 |
| Code | `backend/src/audit/logger.py:8-12` 說明 AuditLogger 是 tamper-evident hash chain；`backend/src/audit/logger.py:29-39` 定義 hash 計算資料；`backend/src/audit/logger.py:41-85` 寫入新事件並串接 previous hash；`backend/src/audit/logger.py:87-115` 驗證完整性。 |
| Code | `backend/src/api/main.py:233-254` 提供 `/api/v1/audit/logs` 與 `/api/v1/audit/verify`。 |
| Frontend | `frontend/src/pages/AuditTimeline.tsx:32-63` 抓取 logs 與 verify API；`frontend/src/pages/AuditTimeline.tsx:92-214` 顯示時間線、event badge、hash、payload。 |
| Data | `data/processed/audit_log.json` 目前共有 268 筆；最後一筆為 `log_20260531080958_000267`。 |
| Tests | `backend/tests/test_human_in_the_loop_audit.py:11-53` 測試 hash chain、持久化載入與手動篡改 payload 會讓完整性驗證失敗。 |

## 第 19 頁：法規與決策可視化圖譜

第 19 頁是法規與決策可視化圖譜。這頁把資料合約變成圖：source document、clause、obligation、customer context、conflict、checklist 都是節點，references clause、requires evidence、applies to、conflicts with 則是關係。

它的價值是可追溯。系統不是只顯示「這個客戶要 standard CDD」，而是可以往上追：decision 來自哪個 customer context，套用了哪些 obligations，obligations 引用哪些 clauses，clauses 又來自哪份 source document。這就是論文裡 policy graph 和 context graph 的概念。

畫面右側選到 `chk_corp_standard` 時，可以看到 MAS Notice 626 Paragraph 6.13、Global Bank Policy Section 3.2.1，以及 required documents、risk triggers、human review required 等 payload。後端除了產生 D3 圖，也有 Neo4j sync 和 UBO penetration API，可以查 1 到 10 層 ownership path，所以它不只是視覺化，而是把多跳合規關係放進 graph structure。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 19 頁，畫面為「法規與決策可視化圖譜」，展示 D3 力導向圖與右側 decision payload。 |
| 論文 | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組.md:54-59` 說明政策圖譜、客戶情境圖與圖對齊決策。 |
| Code | `backend/src/contracts/models.py:148-207` 定義 `GraphNode`、`GraphEdge`、`RegulatoryGraph` 與 edge types。 |
| Code | `backend/src/graph/builder.py:18-49` 定義圖譜構建器；`backend/src/graph/builder.py:53-237` 將 documents、clauses、obligations、conflicts、customers、checklists 組成圖節點與邊。 |
| Code | `backend/src/api/main.py:261-302` 提供 `/api/v1/graph` 給 D3 前端。 |
| Code | `backend/src/graph/sync.py:21-190` 將 source documents、clauses、obligations、customers、conflicts 同步至 Neo4j；`backend/src/graph/sync.py:191-367` 注入 UBO 穿透與循環控股測試拓撲。 |
| Code | `backend/src/api/main.py:321-396` 實作 UBO penetration API，使用 Neo4j `OWNER_OF*1..10` 路徑與 effective share 計算。 |
| Frontend | `frontend/src/components/InteractiveGraph.tsx:30-43` 抓取 graph API；`frontend/src/components/InteractiveGraph.tsx:107-280` 用 D3 force simulation 繪圖；`frontend/src/components/InteractiveGraph.tsx:357-409` 顯示 provenance drawer 與 metadata。 |

## 第 20 頁：真實法規 Inflow Ingestion 工作台

第 20 頁是 Inflow Ingestion，也就是新法規 PDF 怎麼進入系統。合規官上傳 PDF，填入 title、issuer、jurisdiction、version、effective date、source URL 等 metadata 後，後端會建立新的 `SourceDocument`，再啟動 ingestion pipeline。

管線分四步：先用 `PDFTextParser` 和 pypdf 抽文字並清理頁碼、頁首頁尾、跨行斷字；再用 LLM chunker 切成有層級和 citation 的 `Clause`；接著用 structured extractor 抽出 `Obligation`，包含 actor、action、conditions、required evidence 和 source clause ids；最後合併回 YAML，清除快取，重新推理 checklist，並嘗試同步到 Neo4j。

模型名稱要保守講。畫面文案提到 NVIDIA NIM 和 DeepSeek V4 Pro，但後端 `LLMClient` 實際支援 NVIDIA NIM、Gemini 和 mock fallback；預設 extractor model 是 `deepseek-ai/deepseek-r1`，可用環境變數覆寫。所以這頁展示的是「PDF -> Clause -> Obligation -> YAML / Neo4j -> checklist 熱更新」這條可審計編譯流程，不是宣稱已經是正式監理抽取系統。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 20 頁，畫面為「真實法規 Inflow Ingestion 工作台」，展示 PDF 上傳、metadata、pipeline logs、progress 與導入成功狀態。 |
| 論文 | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組.md:52-53` 說明 knowledge compilation pipeline、資料合約、條款切分與義務抽取。 |
| Code | `backend/src/api/main.py:466-623` 實作 ingestion worker：PDF parsing、clause extraction、obligation extraction、YAML merge、Neo4j sync、cache clear、checklist 熱更新。 |
| Code | `backend/src/api/main.py:624-709` 實作 PDF 上傳 endpoint 與 task polling endpoint。 |
| Code | `backend/src/ingestion/pdf_parser.py:9-38` 實作 PDF text extraction；`backend/src/ingestion/pdf_parser.py:40-72` 實作清洗、頁首頁尾過濾與跨行斷字修補。 |
| Code | `backend/src/extraction/llm_extractor.py:15-58` 實作 LLM hierarchical clause chunker；`backend/src/extraction/llm_extractor.py:59-143` 實作 section-level structured obligation extraction；`backend/src/extraction/llm_extractor.py:145-168` 串成二階段 pipeline。 |
| Code | `backend/src/extraction/llm_client.py:48-82` 支援 NVIDIA NIM、Gemini、mock fallback；`backend/src/extraction/llm_client.py:94-212` 實作 structured generation、JSON schema prompt、重試與 fallback。 |
| Frontend | `frontend/src/components/IngestionConsole.tsx:123-176` 送出 PDF ingestion request；`frontend/src/components/IngestionConsole.tsx:51-79` 輪詢 task status；`frontend/src/components/IngestionConsole.tsx:238-536` 呈現上傳表單、progress、logs 與成功/失敗狀態。 |

## 第 21 頁：系統使用教學手冊

第 21 頁是系統使用手冊，可以當成第 15 到 21 頁的總結。它把整套系統整理成五個模組：法規 PDF 導入、大模型智慧切片、條款與義務抽取、人機核准邊界，以及圖譜與安全日誌。

我們的核心設計哲學是 compiled compliance，也就是「編譯型合規」。傳統 RAG 常常只做到文本切片和檢索，但金融合規有條款引用、例外、門檻、風險升級和人工覆核規則。CDD-GraphWiki 的做法是先把法規編成 clause 和 obligation，再把客戶資料編成 customer context，最後生成 checklist，並用 review queue 和 hash chain 做治理。

所以這套 demo 想回答的不是「AI 能不能取代合規官」，而是「AI 要怎麼被放進可治理流程」。它目前不是正式法律判斷自動化系統，但展示了來源可追溯、人工可覆核、稽核可驗證的落地架構。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| PDF | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組 (1).pdf` 第 21 頁，畫面為「系統使用教學手冊」，展示 compiled compliance、data compilation pipeline 與各分頁模組。 |
| 論文 | `/Users/hushsueh/Downloads/AI在金融業的導入風險與監理治理框架_第12組.md:48-62` 對應 CDD-GraphWiki、knowledge compilation、dual-graph alignment、review routing 與 governance。 |
| Spec | `docs/SPEC.md:61-71` 明確列出 non-goals，包括不以 chatbot UI 為 primary product、不做 production legal judgment automation、不做 automatic policy updates without human review。 |
| Frontend | `frontend/src/components/UserGuide.tsx:144-155` 說明核心設計哲學為 compiled compliance，不是一般 PDF RAG；`frontend/src/components/UserGuide.tsx:158-192` 展示 data compilation pipeline。 |
| Frontend | `frontend/src/components/UserGuide.tsx:39-129` 定義 dashboard、review queue、audit timeline、regulatory graph、ingestion console 五個模組的用途與技術說明。 |
| Frontend | `frontend/src/App.tsx:49-80` 將 dashboard、review、timeline、graph、ingestion、guide 對應到不同前端頁面。 |

## 口頭收尾

所以第 15 到 21 頁整體要表達的是：我們的解決方案不是單點模型，而是一條合規資料鏈。法規 PDF 變成 clause、obligation 和 graph；客戶資料變成 customer context 和 CDD / EDD checklist；高風險案件進人工審查；所有推理與覆寫都進 hash-chain audit log。目的就是降低幻覺與黑箱風險，保留來源可追溯、人工可覆核、稽核可驗證的治理能力。

如果時間不夠，優先講三句話：

1. CDD-GraphWiki 不是 PDF RAG chatbot，而是 AML / CDD 知識編譯與合規推理系統。
2. 它用結構化資料合約和圖譜，把法規條文、客戶情境、CDD / EDD checklist 串成可追溯決策鏈。
3. 它用 HITL 人工審查和 SHA-256 hash-chain audit log，把高風險 AI 輸出放回可治理、可覆核、可稽核的流程中。

## 總來源索引

| 主張 | 來源 |
| --- | --- |
| 不是一般 RAG，而是法規知識編譯與推理 | `README.md:3-8`, `docs/SPEC.md:10-12`, 論文 Markdown `:48-49` |
| MVP 有小型來源 corpus 與 5 個金標情境 | `docs/SPEC.md:16-24`, `docs/SPEC.md:96-107`, `data/gold/customer_contexts.yaml:1-64` |
| checklist 必須包含 decision、required evidence、risk triggers、human review、citations | `docs/SPEC.md:37-49`, `backend/src/contracts/models.py:96-110` |
| 決策引擎將 customer context 轉成 CDD / EDD checklist | `backend/src/decision/engine.py:12-159` |
| 高風險與模糊案例進人工審查 | `backend/src/api/main.py:118-140`, `backend/src/audit/manager.py:20-62`, `frontend/src/pages/ReviewQueue.tsx:162-347` |
| audit log 使用 SHA-256 hash chain | `backend/src/audit/logger.py:29-39`, `backend/src/audit/logger.py:87-115`, `frontend/src/pages/AuditTimeline.tsx:92-214` |
| 法規與決策以圖譜展示 | `backend/src/graph/builder.py:53-237`, `frontend/src/components/InteractiveGraph.tsx:107-280` |
| PDF ingestion 經過 parsing、clause chunking、obligation extraction、YAML merge、Neo4j sync、checklist 熱更新 | `backend/src/api/main.py:466-623`, `backend/src/ingestion/pdf_parser.py:9-72`, `backend/src/extraction/llm_extractor.py:15-168` |
| LLM provider 保守說法 | `backend/src/extraction/llm_client.py:48-82`, `backend/src/extraction/llm_client.py:94-212` |
