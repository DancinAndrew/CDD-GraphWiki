你可以把這段想成：**不要把金融合規系統誤以為只是「把法規文件丟進 AI，讓它回答問題」**。真正能用的金融合規系統，至少要分成 4 層。

---

# **先講一句人話版**

你描述的 LLM-wiki 系統不是單純的 RAG chatbot，而是：

把一堆混亂的法規文件，整理成一套「人看得懂、機器也能判斷」的合規知識系統。

所以我才說它可以拆成 4 層。

---

# **第 1 層：LLM Wiki / Knowledge Compilation**

這一層做的是：

原始文件 → 整理後的知識頁面 → 初步規則

例如你丟進去：

FATF 建議  
MAS 626  
FCA AML 指引  
公司內部 KYC 手冊

LLM Wiki 會把它整理成類似這樣的頁面：

\# Beneficial Owner / 最終受益人

\#\# 定義  
最終受益人是指最終擁有或控制客戶的人。

\#\# 相關來源  
\- FATF Recommendation 10  
\- MAS Notice 626  
\- FCA AML Handbook

\#\# 相關概念  
\- UBO  
\- Controlling Party  
\- Customer Due Diligence  
\- Enhanced Due Diligence

這層主要是給**人類閱讀**的。

也就是說，它把法規從「一堆 PDF」變成「有組織的 wiki」。

---

# **第 2 層：Regulatory Knowledge Graph**

這層比較重要。

它不是給人看的，而是給系統判斷用的。

你可以把它想成一張「法規關係圖」。

例如：

MAS 626  
  └── 要求：辨識 Beneficial Owner  
        └── 適用對象：公司客戶  
        └── 需要文件：股權結構圖、身分證明文件  
        └── 風險條件：高風險國家、複雜股權結構

如果做成資料結構，大概像這樣：

obligation: identify\_beneficial\_owner  
source: MAS Notice 626  
jurisdiction: Singapore  
applies\_to: corporate\_customer  
required\_documents:  
  \- ownership\_structure\_chart  
  \- identity\_document  
risk\_triggers:  
  \- high\_risk\_country  
  \- complex\_ownership\_structure

這層的重點是：

系統不只是「知道 Beneficial Owner 是什麼」，而是知道「什麼情況下要查、誰要查、要查什麼文件、依據哪條法規」。

這就是普通 LLM Wiki 跟真正合規系統的差異。

---

# **第 3 層：Contradiction / Supersession Engine**

這層是處理「法規衝突」和「版本更新」。

金融合規最麻煩的地方不是沒資料，而是資料太多，而且會互相衝突。

例如：

FATF 說：高風險客戶需要加強盡職調查  
MAS 626 說：某些情境下必須做 enhanced due diligence  
公司內規說：每 12 個月更新一次高風險客戶資料  
新法規說：某些高風險客戶要每 6 個月更新一次

這時候系統不能直接亂回答：

高風險客戶每 12 個月更新一次。

因為可能已經有新規定要求 6 個月。

所以第 3 層要記錄：

A 條文跟 B 條文衝突  
B 條文取代 A 條文  
B 條文比 A 條文更嚴格  
這個地方需要人工審查

也就是我原本寫的：

conflicts\_with      \= 跟哪條規則衝突  
supersedes          \= 取代哪條舊規則  
narrower\_than       \= 比哪條規則更窄  
stricter\_than       \= 比哪條規則更嚴格  
requires\_review     \= 需要人類合規人員確認

這層很關鍵，因為金融合規不能只求「答案看起來合理」，它要能說明：

為什麼採用這條規則？  
為什麼沒有採用另一條規則？  
如果兩條規則衝突，誰優先？

---

# **第 4 層：CDD Decision Layer**

CDD 是 Customer Due Diligence，客戶盡職調查。

這一層是把前面整理好的知識，真正拿來做業務判斷。

例如使用者輸入：

客戶是一間新加坡註冊公司。  
股東結構有三層。  
其中一名最終受益人來自高風險國家。  
請問 onboarding 時需要哪些文件？

系統要輸出：

適用規則：  
\- MAS Notice 626  
\- FATF Recommendation 10  
\- 內部 AML Policy 第 X 條

需要文件：  
\- 公司註冊文件  
\- 股權結構圖  
\- 最終受益人身分證明  
\- 最終受益人地址證明  
\- 資金來源說明  
\- Enhanced Due Diligence 表單

需要人工審查：  
\- 因為涉及高風險國家  
\- 因為股權結構複雜

也就是：

客戶資料 → 找出適用法規 → 判斷需要文件 → 產生審查清單

這才是真的 CDD automation。

---

# **為什麼我說 GitHub 大多只做到第 1 層？**

因為很多 LLM-wiki 專案主要功能是：

丟文件進去  
AI 幫你整理成 wiki  
可以搜尋  
可以問答  
可以生成 summary

這很好，但它主要還是「知識整理」。

它通常還沒有完整做到：

這條法規適用於哪種客戶？  
哪個 jurisdiction 優先？  
哪條法規被新版取代？  
高風險客戶要哪些文件？  
如果 MAS 跟公司內規衝突，以誰為準？

這些才是金融合規真正值錢的地方。

---

# **為什麼不能只 clone 一個 LLM-wiki repo？**

因為那樣你大概只會得到：

一個比較聰明的法規筆記系統

但你要的是：

一個能輔助合規判斷的 CDD 系統

這兩個差很多。

普通 LLM Wiki 比較像：

「幫我整理 FATF、MAS 626、FCA 的內容」

真正金融合規系統要能回答：

「這個客戶情境下，我到底要做 standard CDD、simplified CDD，還是 enhanced due diligence？」

---

# **我那句話的意思**

原句：

用 LLM-wiki 當 human-readable knowledge layer，用 typed knowledge graph 當 machine-readable compliance layer，再用 RAG/GraphRAG 做 evidence retrieval，而不是只靠 Markdown wiki。

翻成人話：

---

## **1\. LLM-wiki 當 human-readable knowledge layer**

意思是：

LLM-wiki 負責把法規整理成人類看得懂的知識頁面。

例如：

\# Enhanced Due Diligence

\#\# 什麼時候需要 EDD？  
\- 高風險國家  
\- PEP  
\- 複雜股權結構  
\- 異常交易模式

\#\# 相關法規  
\- FATF Recommendation 10  
\- MAS Notice 626

這給合規人員看。

---

## **2\. Typed knowledge graph 當 machine-readable compliance layer**

意思是：

用結構化資料讓機器知道法規條件、適用對象、文件要求、風險觸發條件。

例如：

rule\_id: edd\_required\_for\_high\_risk\_country  
customer\_type: corporate  
trigger:  
  beneficial\_owner\_country: high\_risk  
action:  
  require: enhanced\_due\_diligence  
documents:  
  \- source\_of\_funds  
  \- source\_of\_wealth  
  \- senior\_management\_approval

這給系統判斷用。

---

## **3\. RAG / GraphRAG 做 evidence retrieval**

意思是：

當系統給出答案時，要能回頭找出原始依據。

例如系統回答：

這個客戶需要 Enhanced Due Diligence。

它不能只講結論，還要附：

依據：  
\- MAS Notice 626 第 X 條  
\- FATF Recommendation 10 第 Y 段  
\- 公司內部 AML Policy 第 Z 頁

RAG / GraphRAG 的用途就是幫它找證據。

---

# **最簡化架構圖**

PDF 法規文件  
    ↓  
LLM Wiki  
    ↓  
整理成人類看得懂的概念頁  
    ↓  
Knowledge Graph  
    ↓  
轉成機器可判斷的規則、條件、關係  
    ↓  
CDD Decision Engine  
    ↓  
根據客戶情境產生合規審查清單  
    ↓  
RAG / GraphRAG  
    ↓  
附上原始法規依據與引用

---

# **用一個例子完整串起來**

假設客戶是：

公司客戶  
註冊地：新加坡  
最終受益人：來自高風險國家  
股權結構：三層控股

系統要做的不是單純回答：

你可能需要做 EDD。

而是要這樣：

判斷結果：  
需要 Enhanced Due Diligence。

原因：  
1\. 客戶是 corporate customer。  
2\. 股權結構複雜。  
3\. 最終受益人來自高風險國家。  
4\. MAS 626 與 FATF 都要求此類情境加強審查。

需要文件：  
1\. 公司註冊證明  
2\. 股權結構圖  
3\. UBO 身分證明  
4\. UBO 地址證明  
5\. 資金來源  
6\. 財富來源  
7\. 高階管理層核准紀錄

需要人工審查：  
是，因為涉及高風險國家與複雜所有權結構。

這才叫 CDD automation。

---

# **你真正要記住的差異**

| 類型 | 能做什麼 | 問題 |
| ----- | ----- | ----- |
| 普通 RAG | 從文件找片段回答問題 | 容易抓到衝突條文，答案不穩 |
| LLM Wiki | 把文件整理成知識頁 | 人好讀，但機器不一定能精準判斷 |
| Knowledge Graph | 把規則、條件、關係結構化 | 建置成本較高 |
| CDD Decision Layer | 根據客戶情境產出審查要求 | 才是真正有業務價值的部分 |

---

# **最直白的結論**

你原本描述的金融合規 LLM-wiki 不是單一系統，而是至少 4 個東西疊在一起：

1\. 文件整理系統  
2\. 法規知識圖譜  
3\. 衝突與版本管理系統  
4\. CDD 判斷引擎

GitHub 上的 LLM-wiki repo 多半只幫你做到：

1\. 文件整理系統

部分專案可能碰到：

3\. 衝突偵測

但真正要讓它變成金融合規產品，你還要自己補：

2\. 法規知識圖譜  
4\. CDD 判斷引擎

所以我才說：**不要只靠 Markdown Wiki。那只是知識庫，不是合規自動化系統。**

—

可以。搜尋後的判斷是：**這套系統有研究基礎，而且方向正在成形**。但我要先把話講死：

目前沒有看到一篇論文完整等於你描述的「金融 CDD LLM-wiki 系統」。  
但有多篇論文分別覆蓋它的核心模組：**法規知識圖譜、義務抽取、GraphRAG、合規差距分析、情境判斷、矛盾偵測、可追溯引用**。

所以更好的做法不是找一篇「神論文」照抄，而是把下面幾篇拼成你的系統設計依據。

---

# **最值得參考的論文**

## **1\. ComplianceNLP: Knowledge-Graph-Augmented RAG for Multi-Framework Regulatory Gap Detection**

這篇最接近你要做的「企業級合規系統」。

它做的是：

監管法規更新  
→ 結構化義務抽取  
→ 法規 Knowledge Graph  
→ KG-Augmented RAG  
→ 跟企業內部政策做 gap analysis

這跟你的系統非常接近，因為你的 CDD 系統也需要：

FATF / MAS / FCA 法規  
→ obligation schema  
→ 內部 AML / KYC policy  
→ 找出衝突、缺口、適用要求

這篇的系統包含三個核心：KG-augmented RAG、multi-task obligation extraction，以及把 obligation 對齊到內部政策的 compliance gap analysis；它還報告了 87.7 F1 gap detection、94.2% grounding accuracy，以及四個月金融機構 parallel-run deployment 的數據。這是你整套系統裡「法規到內規 gap analysis」最值得參考的主幹。([arXiv](https://arxiv.org/abs/2604.23585))

**你可以抄的設計：**

Regulatory Sources  
→ Provision Extraction  
→ Obligation Extraction  
→ Regulatory Knowledge Graph  
→ Internal Policy Mapping  
→ Gap Scoring  
→ Evidence-grounded Answer

**你不能直接抄的地方：**  
它處理的是 SEC、MiFID II、Basel III，不是 FATF / MAS 626 / FCA AML / CDD。你要自己重建 AML/CDD ontology。

---

## **2\. GraphCompliance: Aligning Policy and Context Graphs for LLM-Based Regulatory Compliance**

這篇非常適合你的 **CDD Decision Layer**。

它的核心想法是：

Regulatory text → Policy Graph  
Runtime context → Context Graph  
然後把兩張圖對齊，判斷是否合規

這跟你的 CDD 場景幾乎一樣。因為 CDD 的問題不是單純問「MAS 626 說什麼」，而是：

這個客戶是公司戶  
UBO 來自高風險國家  
股權結構三層  
是否需要 EDD？  
需要哪些文件？

GraphCompliance 的 paper 明確把 regulatory texts 表成 Policy Graph，把 runtime contexts 表成 Context Graph，並用 structured graph alignment 輔助 judge LLM 做合規判斷；實驗上比 LLM-only 和 RAG baseline 高 4.1–7.2 個百分點 micro-F1。([arXiv](https://arxiv.org/abs/2510.26309))

**你可以抄的設計：**

Policy Graph:  
  MAS 626 / FATF / FCA 的義務、條件、例外、cross-reference

Context Graph:  
  客戶類型、註冊地、UBO、PEP、交易模式、國家風險

Compliance Gate:  
  判斷 standard CDD / simplified CDD / EDD

**這篇對你的價值：**  
它幫你把「法規知識」和「客戶情境」分開建模，這是很多普通 RAG chatbot 做不到的。

---

## **3\. AI Application in Anti-Money Laundering for Sustainable and Transparent Financial Systems**

這篇最貼近你講的 **KYC / CDD / EDD** 場景。

它提出把 Graph RAG 用在 KYC customer due diligence，整合銀行核心系統的 structured data，以及 customer documents / reports 這類 unstructured data；LLM 可以把 analyst query 轉成 Cypher，查詢 customer profiles、transaction relationships，並自動產生 due diligence reports。

它的第 7 節直接講 Graph RAG \+ KYC，提到：

structured data:  
  core banking relational database

unstructured data:  
  customer documents, reports

graph:  
  customers, accounts, transactions, relationships, sanctions, PEP links, alerts

LLM:  
  natural language query → Cypher → retrieve graph evidence → summarize due diligence report

這跟你要做的 CDD system 很近。它也提醒真實部署需要 persistent audit trails、human review、model risk controls，以及滿足 FATF / GDPR 等監管期待。

**但這篇有一個問題：**  
它比較像 AML/KYC 的 GraphRAG 系統，不是嚴格的「法規知識編譯系統」。也就是它比較關注 customer risk graph，不是 regulatory obligation graph。

所以你應該把它放在你的系統第 4 層：

CDD Decision Layer / Customer Risk Graph

而不是放在第 1、2 層。

---

## **4\. Approaching the AI Act... with AI: LLMs and Knowledge Graphs to Extract and Analyse Obligations**

這篇不是金融法規，但它對你的 **Obligation Extraction** 很有用。

它用 NLP \+ LLM 自動抽取 EU AI Act 裡面的 legal obligations，流程分成四階段：

1\. identification of obligations  
2\. filtering of deontic statements  
3\. analysis of deontic content  
4\. construction of searchable knowledge graphs

它用 LLaMA 3.3 70B，加上傳統 NLP 工具；專家評估結果顯示 obligation filtering precision 為 93%，obligation type / addressee / predicate classification 超過 99%。而且它有公開 code、data、prompts。([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2212473X25001026))

**你可以抄的地方：**

法規條文 → 找出 obligation  
obligation → 分析誰有義務  
obligation → 分析必須做什麼  
obligation → 分析適用條件  
obligation → 寫入 knowledge graph

套到你的金融 CDD：

obligation\_id: identify\_ubo  
source: MAS Notice 626  
addressee: financial\_institution  
subject: corporate\_customer  
predicate: identify\_and\_verify  
object: beneficial\_owner  
condition:  
  \- customer\_type \== corporate  
required\_evidence:  
  \- ownership\_structure\_chart  
  \- identity\_document

這篇是你做「法規轉 schema」最該讀的。

---

## **5\. RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA**

這篇適合參考你的 **LLM-wiki / GraphRAG 問答層**。

它做的是：

regulatory documents  
→ SPO triplet extraction  
→ clean / normalize / deduplicate / update KG  
→ triplet \+ original text \+ metadata 放進 enriched vector DB  
→ 用 agent pipeline 做 regulatory QA

它的重點不是金融，而是 regulated compliance QA。它明確指出 regulatory compliance QA 需要 precise、verifiable、domain-specific information；系統用 KG triplets \+ RAG 來降低 hallucination，並提高 traceability。([arXiv](https://arxiv.org/html/2508.09893v1))

**你可以抄的設計：**

Ingestion Agent:  
  解析法規文件

Triplet Extraction Agent:  
  MAS 626 requires FI to identify UBO

Normalization Agent:  
  UBO \= Beneficial Owner \= Controlling Party

Deduplication Agent:  
  合併同義概念

Retrieval Agent:  
  query → relevant triplets \+ source text

Answer Agent:  
  產生有 citation 的答案

這篇很適合補你原本說的 **Concept Deduplication**。

---

## **6\. Legal Requirements Translation from Law**

這篇對你最大的價值是：**不要只把法規整理成自然語言，而是轉成可執行的 canonical representation**。

它提出用 textual entailment \+ in-context learning，把 legal text 轉成可以 encoding / execution 的 Python code representation。作者認為 legal compliance 需要抽取 structural metadata 和 semantic metadata，例如：regulated entities、deontic modalities、pre-conditions、post-conditions，以及 clause interdependencies。([arXiv](https://arxiv.org/html/2507.02846v1))

這剛好可以支撐你系統裡的：

typed knowledge graph  
machine-readable compliance layer  
CDD decision engine

**你可以抄的設計：**

class Obligation:  
    source: str  
    actor: str  
    action: str  
    object: str  
    condition: list\[Condition\]  
    exception: list\[Exception\]  
    evidence\_required: list\[Evidence\]

這篇也有一個關鍵警告：LLM 在 long-range dependencies、logical consistency、negation、transitivity 上仍不可靠，所以高風險法規場景不能只靠自然語言回答，必須有 structured representation。([arXiv](https://arxiv.org/html/2507.02846v1))

這點非常重要。普通 RAG 在 CDD 會炸，就是因為它沒有形式化條件與例外。

---

## **7\. LegalWiz: A Multi-Agent Generation Framework for Contradiction Detection in Legal Documents**

這篇對你的 **Contradiction Log** 很有參考價值。

它做的是 legal document contradiction detection，用 multi-stage pipeline：

semantic filtering  
→ NLI contradiction classification  
→ LLM contradiction judgment  
→ confidence-weighted hybrid scoring  
→ human verification

它還把矛盾分成：

retrieval-verifiable:  
  可以靠可檢索證據判斷

retrieval-resistant:  
  需要更深推理或人工判斷

這個分類很適合你的金融合規系統，因為有些衝突是明確版本衝突，例如「12 個月更新」vs「6 個月更新」；但有些是法律解釋上的灰區，必須交給 compliance officer。([arXiv](https://arxiv.org/html/2510.03418v2))

**你可以抄的設計：**

contradiction:  
  id: conflict\_001  
  statement\_a: "High-risk customer review every 12 months"  
  statement\_b: "High-risk customer review every 6 months"  
  source\_a: "Internal AML Policy v3"  
  source\_b: "MAS Notice 626 update"  
  contradiction\_type: temporal  
  verifiability: retrieval\_verifiable  
  confidence: 0.87  
  status: pending\_human\_review

這篇要放進你的第 3 層：

Contradiction / Supersession Engine

---

## **8\. LegalBench-RAG / Legal RAG Bench**

這類不是直接做合規系統，而是幫你設計 evaluation。

LegalBench-RAG 專門評估 legal RAG 的 retrieval step，強調 retrieval 不應該只回傳大段 chunk，而要找出 minimal、highly relevant legal snippets，讓 LLM 可以產生精確 citation。它的資料集有 6,858 個 query-answer pairs，法律專家標註，並公開 repo。([arXiv](https://arxiv.org/abs/2408.10343?utm_source=chatgpt.com))

這對你的系統很重要，因為金融合規不是問答看起來順就好。你至少要評估：

retrieval precision  
retrieval recall  
citation correctness  
answer faithfulness  
obligation extraction accuracy  
contradiction detection precision  
CDD checklist correctness

另外 Legal RAG Bench 提出 end-to-end legal RAG 評估，並指出很多被稱為 hallucination 的錯誤，其實是 retrieval failure 造成的；這對你的設計很關鍵，因為 CDD 系統的上限很大程度由 retrieval / graph retrieval 決定。([arXiv](https://arxiv.org/abs/2603.01710?utm_source=chatgpt.com))

---

# **你這套系統應該怎麼對應論文**

| 你的系統模組 | 應該參考的論文 | 用途 |
| ----- | ----- | ----- |
| 法規 ingestion | RAGulating Compliance、Approaching the AI Act | 解析法規、抽 triplets、保留原文 metadata |
| 義務抽取 | ComplianceNLP、Approaching the AI Act、Legal Requirements Translation | 抽出 actor / action / object / condition / exception |
| 概念去重 | RAGulating Compliance | UBO / Beneficial Owner / Controlling Party 合併 |
| 法規 Knowledge Graph | ComplianceNLP、GraphCompliance、Knowledge Graph Representations for Policy Compliance | 建立可推理的 structured graph |
| 客戶情境建模 | GraphCompliance、AI Application in AML | 把 customer profile 轉成 context graph |
| CDD / EDD 判斷 | GraphCompliance、AI Application in AML | 判斷 standard CDD / EDD / 文件要求 |
| 矛盾日誌 | LegalWiz | 偵測 conflicting provisions / policy conflict |
| Gap analysis | ComplianceNLP | 法規 vs 內部 policy 差距 |
| Evidence retrieval | LegalBench-RAG、RAGulating Compliance | 精確引用來源條文 |
| Evaluation | LegalBench-RAG、Legal RAG Bench | 評估 retrieval、faithfulness、grounding |

---

# **我會建議你讀的順序**

## **第一輪：先讀「主架構」**

1. **ComplianceNLP**  
   先理解完整的 regulatory compliance monitoring system 怎麼拆。  
2. **GraphCompliance**  
   理解 policy graph / context graph alignment。這是 CDD decision layer 的核心。  
3. **AI Application in AML**  
   看 KYC / CDD / EDD GraphRAG 怎麼接 customer graph。

---

## **第二輪：補核心技術**

4. **Approaching the AI Act... with AI**  
   看 obligation extraction workflow。  
5. **Legal Requirements Translation from Law**  
   看如何把法律條文轉成 machine-readable / executable representation。  
6. **RAGulating Compliance**  
   看 multi-agent KG \+ RAG \+ triplet retrieval 架構。

---

## **第三輪：補可靠性**

7. **LegalWiz**  
   看 contradiction detection / human review queue。  
8. **LegalBench-RAG / Legal RAG Bench**  
   看 evaluation 怎麼設計，不然 demo 會很容易變成「看起來有用但無法證明」。

---

# **你的系統最合理的研究型架構**

我會把它改成這樣：

             ┌────────────────────┐  
              │ Regulatory Sources  │  
              │ FATF / MAS / FCA    │  
              └─────────┬──────────┘  
                        ↓  
              ┌────────────────────┐  
              │ Legal Parser        │  
              │ section / clause    │  
              │ version / citation  │  
              └─────────┬──────────┘  
                        ↓  
              ┌────────────────────┐  
              │ Obligation Extractor│  
              │ actor / action      │  
              │ object / condition  │  
              │ exception / evidence│  
              └─────────┬──────────┘  
                        ↓  
        ┌───────────────┴────────────────┐  
        ↓                                ↓  
┌────────────────────┐          ┌────────────────────┐  
│ Human-readable Wiki│          │ Regulatory KG       │  
│ concept pages      │          │ machine-readable    │  
│ explanation        │          │ obligations/rules   │  
└─────────┬──────────┘          └─────────┬──────────┘  
          ↓                               ↓  
┌────────────────────┐          ┌────────────────────┐  
│ Contradiction Log  │          │ CDD Decision Engine │  
│ conflict / version │          │ customer → checklist│  
│ stricter\_than      │          │ CDD / EDD decision  │  
└─────────┬──────────┘          └─────────┬──────────┘  
          ↓                               ↓  
          └──────────────┬────────────────┘  
                         ↓  
              ┌────────────────────┐  
              │ Evidence Layer      │  
              │ RAG / GraphRAG      │  
              │ citation / audit    │  
              └────────────────────┘

---

# **不要犯的錯**

## **錯誤做法**

把 FATF / MAS / FCA PDF 丟進 vector DB  
然後做一個 chatbot

這不是最佳解。這只會得到一個「會講法規的聊天機器人」，但無法穩定處理：

\- 條文衝突  
\- 不同 jurisdiction 優先級  
\- 新舊版本取代  
\- CDD / EDD 條件判斷  
\- 內規與外規 gap  
\- UBO / BO / controlling party 同義概念合併

## **更好的做法**

LLM-wiki 負責人類可讀知識層  
Knowledge Graph 負責機器可判斷規則層  
Contradiction Engine 負責衝突與版本層  
GraphRAG 負責 evidence retrieval  
CDD Engine 負責客戶情境決策  
Human Review Queue 負責高風險判斷

---

# **如果你要做成 side project / portfolio，我建議縮小 MVP**

不要一開始就做 FATF \+ MAS \+ FCA \+ HKMA \+ 內規。範圍太大，會變成爛尾。

**MVP 範圍：**

法規來源：  
\- FATF Recommendation 10  
\- MAS Notice 626 的 CDD / EDD 相關章節  
\- 一份你自己寫的 mock internal AML policy

客戶情境：  
\- individual customer  
\- corporate customer  
\- PEP  
\- high-risk jurisdiction  
\- complex ownership structure  
\- UBO unclear

核心功能：  
1\. 上傳法規文件  
2\. 抽取 obligation  
3\. 產生 concept wiki  
4\. 建立 regulatory KG  
5\. 偵測 MAS vs internal policy conflict  
6\. 輸入 customer profile  
7\. 產生 CDD / EDD checklist  
8\. 每個結論附 citation  
9\. 高風險或衝突 case 送 human review

---

# **最有論文價值的題目命名**

你可以把它包裝成：

Regulatory Knowledge Compilation for Customer Due Diligence:  
A Graph-Augmented LLM System for AML Compliance Reasoning

或更工程化一點：

CDD-GraphWiki:  
A Human-Readable and Machine-Reasonable Knowledge Compilation System for AML Compliance

這個題目比「金融合規 RAG chatbot」強很多。後者太普通，前者有架構差異。

---

# **最終判斷**

這套系統可以執行，而且有研究支撐。  
但正確方向不是「做 LLM-wiki」，而是：

LLM-wiki  
\+ regulatory obligation extraction  
\+ typed knowledge graph  
\+ customer context graph  
\+ contradiction detection  
\+ GraphRAG evidence retrieval  
\+ human-in-the-loop review

你真正要參考的不是單一 repo，而是這幾條研究線的組合：

ComplianceNLP       → regulatory gap analysis 主架構  
GraphCompliance     → policy graph / context graph 判斷架構  
AI AML GraphRAG     → KYC / CDD domain reference  
AI Act Obligation   → obligation extraction pipeline  
LegalWiz            → contradiction log  
LegalBench-RAG      → evaluation method

這樣做出來才不是普通 demo，而是有機會變成一個可以講得出研究貢獻與工程價值的系統。

