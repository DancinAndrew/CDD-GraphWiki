# 第 15-21 頁報告逐字稿

用途：明天報告 PDF 第 15-21 頁，並包含新增架構圖與未來開發方向補充頁；時間可抓 8-10 分鐘。
語氣：繁中口語、課堂報告用。  
保守界線：這份稿只講 PDF 畫面與 repo 中已實作或已規格化的功能，不把 demo 說成正式上線的金融生產系統。

## 開場提醒

這一段不是介紹一般聊天機器人，而是介紹 CDD-GraphWiki。它的定位是 AML / CDD 法規知識編譯與合規推理系統，不是把 PDF 丟進向量資料庫後讓模型自由回答。論文 methodology 也把它定義成「機器可推理、人類可閱讀」的系統，所以我會用這個角度講第 15 到 21 頁。

## 名詞簡寫速查

這段是報告者自用，不一定要逐字念。遇到縮寫卡住時，可以用「中文意思 + 一句白話」快速帶過。

| 簡寫 / 名詞 | 中文意思 | 報告時可以怎麼理解 |
| --- | --- | --- |
| AML | Anti-Money Laundering，反洗錢 | 金融機構用來防止洗錢、資恐與可疑資金流動的一整套合規制度。 |
| CDD | Customer Due Diligence，客戶盡職調查 | 開戶或建立業務關係前，確認客戶身份、風險、實質受益人和需要文件。 |
| EDD | Enhanced Due Diligence，加強型盡職調查 | 客戶風險比較高時，比一般 CDD 要求更多文件、更多審查和人工核准。 |
| KYC | Know Your Customer，認識你的客戶 | 金融機構確認客戶身份與風險的實務流程；CDD 可以理解成 KYC 裡的核心合規步驟。 |
| FATF | Financial Action Task Force，防制洗錢金融行動工作組 | 國際反洗錢標準制定組織；這份 demo 用到 FATF Recommendation 10。 |
| MAS Notice 626 | 新加坡金融管理局 MAS 的反洗錢通知 | 新加坡銀行業 AML / CDD / EDD 的重要監管文件，是 demo 的主要法規來源之一。 |
| RAG | Retrieval-Augmented Generation，檢索增強生成 | 先找資料再讓模型回答；我們要強調本專案不是一般 PDF RAG chatbot。 |
| BM25 | 一種關鍵字檢索演算法 | 可以理解成比較傳統的「關鍵字相關度搜尋」，常拿來和向量檢索混合。 |
| Dense retrieval | 向量語意檢索 | 把文字轉成 embedding 向量，用語意相近程度找資料，不只看關鍵字有沒有一樣。 |
| GraphRAG | 圖譜輔助的 RAG | 檢索時不只找文字，也利用知識圖譜的節點和邊，把相關條文、義務、概念串起來。 |
| Minimal snippet | 最小必要引用片段 | 法律 RAG 評估裡，希望系統找到剛好足夠回答問題的短片段，而不是整大段 chunk。 |
| Character-span | 字元範圍 | 用精確的起訖字元標出引用位置，讓 citation 可以回到原文片段。 |
| LLM | Large Language Model，大型語言模型 | 例如 Llama、DeepSeek、Gemini；在這個系統裡主要用於切片與義務抽取，不直接做最後合規判斷。 |
| NLI | Natural Language Inference，自然語言推論 | 判斷兩段文字是支持、矛盾，還是無關；未來可用在法規衝突偵測。 |
| SPO triplets | Subject-Predicate-Object 三元組 | 把法規關係拆成「主體-關係-客體」，例如「金融機構-必須驗證-實質受益人」。 |
| Entity resolution | 實體解析 / 實體合併 | 把 UBO、Beneficial Owner、Controlling Party 這類可能指同一概念的詞彙對齊。 |
| IAA | Inter-Annotator Agreement，標註者一致率 | 多個人標金標資料時的一致程度；未來要讓 evaluation 更可信時會需要。 |
| Cypher | Neo4j 的圖查詢語言 | 類似 SQL 對資料庫查詢，但 Cypher 是用來查圖資料庫裡的節點與路徑。 |
| MVP | Minimum Viable Product，最小可行產品 | 可以展示核心價值的最小版本；報告時要把目前系統說成 demo / MVP，不要說成正式上線系統。 |
| Proof-of-concept | 概念驗證 | 證明方法可行的原型，不等於完整產品或生產級系統。 |
| PDF ingestion | PDF 導入流程 | 把新法規 PDF 放進系統，抽文字、切條文、抽義務，再更新 YAML / 圖譜 / checklist。 |
| Parser | 解析器 | 把 PDF 或 Markdown 轉成系統能處理的條文資料，不只是單純讀文字。 |
| Clause | 條文片段 | 法規中可被引用、抽取和審查的最小穩定單位。 |
| Provenance | 來源溯源 | 每個 checklist 或 obligation 都能追回原始法規條文，避免模型憑空回答。 |
| Citation | 引用依據 | 指向 MAS、FATF 或內部政策的具體條文，讓合規官可以核對。 |
| Obligation | 合規義務 | 從條文抽出的「誰在什麼情境下必須做什麼、需要什麼證據」。 |
| CustomerContext | 客戶情境資料結構 | 客戶不是自由文字 prompt，而是包含客戶類型、司法管轄區、UBO、PEP 等欄位的結構化資料。 |
| UBO | Ultimate Beneficial Owner，最終實質受益人 | 穿透公司股權後，真正擁有或控制公司的人；UBO 不明通常會提高風險。 |
| PEP | Politically Exposed Person，政治公眾人物 | 因職位或關係有較高貪腐、洗錢風險的人；通常會觸發 EDD 或人工審查。 |
| HITL | Human-in-the-loop，人機協作 / 人工覆核 | AI 先整理風險和建議，但高風險決策要交給合規官做最後判斷。 |
| Audit Trail | 審計軌跡 | 記錄系統初審、案件路由、人工覆寫等事件，方便事後稽核。 |
| Hash chain | 雜湊鏈 / 防篡改鏈 | 每筆 audit log 都連到上一筆 hash；中間被改過，後面整條鏈就會驗證失敗。 |
| SHA-256 | 一種雜湊演算法 | 用來把 audit log 算成固定長度指紋，支撐防篡改檢查。 |
| Evaluation Harness | 評估框架 | 用測試把錯誤拆成 retrieval、extraction、reasoning、citation 等類型，不只看模型回答好不好看。 |
| Dashboard | 工作台 | 前端 demo 介面，包含總覽、人工審查、audit timeline、圖譜、PDF 導入和使用手冊。 |
| API | Application Programming Interface，應用程式介面 | 前端向後端拿資料或送審查決策的接口，例如 `/api/v1/cases`。 |
| Pydantic | Python 資料驗證工具 | 用來限制 API 輸入和資料合約，避免送進不合法欄位。 |
| YAML | 一種結構化資料格式 | repo 用 YAML 保存法規條文、義務、客戶情境、checklist 等 demo 資料。 |
| Neo4j | 圖資料庫 | 用節點和邊保存條文、義務、客戶、股權穿透等多跳關係。 |
| D3 | 前端視覺化函式庫 | 用來把法規與決策圖譜畫成互動式節點關係圖。 |
| NVIDIA NIM | NVIDIA 的模型 API / 推論平台 | 後端支援用 NIM 呼叫 Llama 3.3 做切片、DeepSeek R1 做義務抽取，也保留 Gemini 和 mock fallback。 |
| Gemini / mock fallback | 備援模型 / 離線假資料模式 | 沒有 NIM key 或 API 失敗時，系統可以改用 Gemini；再不行就用 mock，確保 demo 和測試不中斷。 |
| NRIC | National Registration Identity Card | 新加坡身份證件；低風險個人 CDD 案例中要求的身份文件之一。 |
| SoF / SoW | Source of Funds / Source of Wealth，資金來源 / 財富來源 | EDD 常要求說明錢從哪裡來、財富怎麼累積。 |

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

## 第 15A 頁：系統建構架構圖

這一頁我會放在 demo 前面，先給大家一張鳥瞰圖。剛剛第 15 頁講的是解決方案方向，這一頁則把整個系統是怎麼做出來的，用 Phase 1 到 Phase 10 串起來。

最左邊是 Foundation。這代表我們不是先做 UI，而是先做資料合約、Parser 和義務抽取。也就是先定義 `SourceDocument`、`Clause`、`Obligation`、`CustomerContext`、`Conflict`、`CDDChecklist` 這些結構，再把 PDF 或 Markdown 法規切成 stable clause records，最後抽出 actor、action、condition、evidence 和 review flags。

中間是 Reasoning Core。這一層把前面的 clause 和 obligation 編成知識圖譜，加入衝突檢測，最後接到 CDD 推理引擎。重點是客戶資料不是 prompt，而是 `CustomerContext`；系統用它去對齊法規義務，產出 CDD 或 EDD checklist。

右邊是 Governance & Product。高風險或模糊案件會進 HITL 人工審查，所有推理和覆寫都寫進 SHA-256 hash-chain audit log；Evaluation Harness 用來拆開檢查 retrieval、extraction、reasoning 和 citation；Compliance Dashboard 則是後面 demo 會看到的工作台、審查、日誌、圖譜、導入與使用手冊。最後 NVIDIA NIM 整合是在 ingestion 階段使用 Llama 3.3 做智慧切片、DeepSeek R1 做義務抽取，同時保留 Gemini 和 mock fallback。

所以這張圖要表達的是：CDD-GraphWiki 不是單一模型，也不是 generic PDF RAG chatbot，而是一條從法規文件、結構化資料、圖譜推理，到人工覆核與審計治理的系統鏈。接下來第 16 到 21 頁的 demo，就是把這張圖右半邊的 Dashboard、HITL、Audit、Graph、Ingestion 和 Guide 展示出來。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| 圖檔 | `docs/assets/phase_1_10_architecture.png` 是可直接插入簡報的架構圖；`docs/assets/phase_1_10_architecture.svg` 是可編輯版本。 |
| README | `README.md:42-44` 說明報告用的 Phase 1-10 完成項目：資料合約、Parser、義務抽取、知識圖譜、衝突檢測、CDD 推理引擎、人工審查、Evaluation Harness、Compliance Dashboard、NVIDIA NIM 整合。 |
| Roadmap | `docs/system-build-roadmap.md:528-678` 定義 Data Contracts、Parser、Obligation Extraction、Regulatory Graph、Conflict、CDD Engine、Evaluation Harness 等 build path。 |
| 論文來源 | `docs/system-build-roadmap.md:311-324`、`docs/system-build-roadmap.md:326-508`、`docs/papers_notes/index.md:56-129` 說明這些架構不是單一論文，而是多篇論文對不同系統部件的映射。 |
| Dashboard | `openspec/changes/archive/2026-05-22-create-compliance-dashboard/design.md:7-34` 描述 FastAPI + React Dashboard、人工審查、D3 圖譜與 audit timeline。 |
| NVIDIA NIM | `openspec/changes/archive/2026-05-22-nvidia-nim-integration/design.md:17-20` 說明 Llama 3.3 chunker、DeepSeek R1 extractor 與環境變數覆寫；`backend/src/extraction/llm_client.py:48-82` 說明 NIM、Gemini、mock fallback。 |

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

## 第 21A 頁：未來開發方向

這一頁我會放在 demo 結束後，當作最後一張補充說明。剛剛第 16 到 21 頁展示的是目前已經跑通的 demo chain：從資料合約、Parser、義務抽取、知識圖譜、衝突 prototype、CDD 推理、人工審查、hash-chain audit，到 Dashboard、NVIDIA NIM fallback 和 Evaluation baseline。

但這裡要講得保守一點：目前 repo 比較像 proof-of-concept，也就是可以展示核心概念的 demo，不是完整 production-grade 法律判斷系統。所以這張未來開發方向主要回答一個問題：如果要從課堂 demo 往更嚴謹的 research-grade 或 production-grade 合規平台前進，還缺哪些能力？

第一個方向是 Evidence-grade Retrieval，也就是證據等級的檢索。現在 repo 裡有 evaluation harness，也有一個 vector RAG baseline simulator，可以把錯誤拆成 retrieval、extraction、reasoning 和 citation 這幾類；但它還不是完整的法律檢索系統。未來要補的是 hybrid BM25、dense retrieval 和 GraphRAG，並且做到 character-span minimal snippets。白話說，就是不要只說「我有引用 MAS Notice 626」，而是要精準指到最小必要文字片段，還要記錄檢索失敗的原因。

第二個方向是 True Graph Alignment。現在系統已經有法規圖譜，也能把 source document、clause、obligation、customer context、checklist 串成節點和邊；CDD engine 也能根據五個金標客戶情境產生 checklist。不過目前推理主要還是 deterministic branch logic，也就是針對客戶欄位做規則分支，還不是 GraphCompliance 論文講的完整 policy graph 對 context graph。未來要補的是更一般化的客戶風險圖、Context Graph，還有用 Cypher 查 UBO、PEP、制裁或高風險司法管轄區的多跳關係。

第三個方向是 Conflict & Gap Adjudication。現在 repo 的 conflict detector 可以處理幾種明確規則型衝突，例如 UBO 持股門檻 25% 和 10% 的差異、PEP onboarding 的政策差異、偶發交易金額門檻差異。但它還沒有做到 LegalWiz 那種 NLI 加 LLM 的 hybrid contradiction scoring，也還沒有完整的六類 conflict taxonomy。未來比較完整的做法，是先用檢索和 NLI 找出疑似衝突，再把 retrieval-verifiable 的衝突交給系統輔助判斷，把 retrieval-resistant 或需要法律解釋的衝突交給人工審查。

第四個方向是 Scale & Governance。現在的來源 corpus 是 MVP 等級，主要用 FATF、MAS 和 mock internal policy 做 demo；concept dedupe 也主要靠 fallback alias，把 UBO、Beneficial Owner、Controlling Party 這些詞對齊。未來如果要更接近真實金融機構，就要擴大到 FATF、MAS、FCA、HKMA 和多版本內規，加入 entity resolution、SPO triplets、標註者一致率 IAA、角色權限，以及法規更新後的人審發布流程。

所以這頁的收斂句可以這樣說：目前我們已經證明 AML / CDD 合規可以從「聊天式回答」改成「知識編譯、圖譜推理、人工覆核、審計留痕」的 demo。未來要做的，不是把畫面做得更像產品而已，而是把檢索證據、圖對齊、衝突裁決和治理規模化補起來，讓它從課堂原型往真正可驗證的合規平台前進。

### 來源證據

| 類型 | 來源 |
| --- | --- |
| 投影片 | `docs/future_development_direction.pptx` 是一頁未來開發方向 PPT；`docs/assets/future_development_direction_preview.png` 是預覽圖。 |
| Roadmap | `docs/system-build-roadmap.md:5-20` 定義系統核心流程：原始法規、條文切分、義務抽取、wiki、regulatory knowledge graph、gap tracking、CDD / EDD checklist、human review。 |
| Roadmap | `docs/system-build-roadmap.md:311-324` 把 ComplianceNLP、GraphCompliance、AI Application in AML、LegalWiz、LegalBench-RAG、Legal RAG Bench 等論文對應到系統部件。 |
| Roadmap | `docs/system-build-roadmap.md:528-678` 定義 Phase 1-9 的 build path，其中多個項目仍是未來可深化方向，例如 retrieval tests、conflict detection tests、citation faithfulness checks。 |
| Paper matrix | `docs/papers_notes/index.md:7-52` 把系統拆成 knowledge compilation、regulatory KG、contradiction / supersession、CDD decision layer 四層。 |
| Paper matrix | `docs/papers_notes/index.md:56-129` 將 10 個開發階段映射到 LegalBench-RAG、RAGulating Compliance、GraphCompliance、LegalWiz、Legal RAG Bench 等論文方法。 |
| Current implementation | `backend/src/evaluation/harness.py:16-23` 說明目前 evaluation harness 的目標；`backend/src/evaluation/baseline.py:5-13` 說明目前 vector RAG baseline 是模擬器。 |
| Current implementation | `backend/src/decision/engine.py:32-159` 顯示目前 CDD engine 主要以 customer features 做決策分支；`backend/src/graph/builder.py:18-35` 顯示目前已有將合規物件編成 graph 的 builder。 |
| Current implementation | `backend/src/association/conflict_detector.py:5-15` 說明目前是合規衝突自動偵測引擎原型；`backend/src/association/conflict_detector.py:18-102` 顯示目前處理的是幾種規則型衝突。 |
| Current implementation | `backend/src/association/concept_mapper.py:6-13` 顯示概念對齊目前依賴 fallback aliases；`backend/src/association/concept_mapper.py:88-146` 顯示目前是 normalization 與別名匹配，不是完整 entity resolution。 |

## 口頭收尾

所以第 15 到 21 頁，加上架構圖和未來開發方向，整體要表達的是：我們的解決方案不是單點模型，而是一條合規資料鏈。法規 PDF 變成 clause、obligation 和 graph；客戶資料變成 customer context 和 CDD / EDD checklist；高風險案件進人工審查；所有推理與覆寫都進 hash-chain audit log。目的就是降低幻覺與黑箱風險，保留來源可追溯、人工可覆核、稽核可驗證的治理能力。

如果時間不夠，優先講四句話：

1. CDD-GraphWiki 不是 PDF RAG chatbot，而是 AML / CDD 知識編譯與合規推理系統。
2. 它用結構化資料合約和圖譜，把法規條文、客戶情境、CDD / EDD checklist 串成可追溯決策鏈。
3. 它用 HITL 人工審查和 SHA-256 hash-chain audit log，把高風險 AI 輸出放回可治理、可覆核、可稽核的流程中。
4. 未來工作不是單純加更多 UI，而是補強 evidence-grade retrieval、graph alignment、conflict adjudication 和 governance scaling。

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
| 未來方向一：evidence-grade retrieval 尚需深化 | `docs/papers_notes/index.md:85-89`, `docs/papers_notes/index.md:123-129`, `backend/src/evaluation/harness.py:23-60`, `backend/src/evaluation/baseline.py:5-13` |
| 未來方向二：完整 policy graph / context graph alignment 尚需深化 | `docs/system-build-roadmap.md:350-367`, `docs/papers_notes/index.md:37-42`, `backend/src/decision/engine.py:32-159`, `backend/src/graph/builder.py:18-35` |
| 未來方向三：NLI + LLM hybrid conflict scoring 尚需深化 | `docs/papers_notes/index.md:111-115`, `docs/papers_notes/index.md:31-34`, `backend/src/association/conflict_detector.py:5-15`, `backend/src/association/conflict_detector.py:18-102` |
| 未來方向四：corpus scale、entity resolution、SPO triplets 與治理流程尚需深化 | `docs/system-build-roadmap.md:49-55`, `docs/papers_notes/index.md:99-109`, `backend/src/association/concept_mapper.py:6-13`, `backend/src/association/concept_mapper.py:88-146` |
