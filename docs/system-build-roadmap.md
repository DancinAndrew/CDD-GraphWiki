# CDD-GraphWiki 系統建構與論文閱讀路線圖

Last updated: 2026-05-12

## 一句話方向

CDD-GraphWiki 要做的是 **AML / CDD 法規知識編譯與合規推理系統**，不是把 PDF 丟進 vector database 後讓 LLM 問答的 generic RAG chatbot。

核心流程應該是：

```text
原始法規與內規文件
-> 條文切分與 provenance
-> 義務 / 條件 / 例外 / 證據需求抽取
-> 人類可讀的 wiki concept pages
-> 機器可推理的 regulatory knowledge graph
-> 矛盾 / 版本取代 / 內外規 gap tracking
-> 有 citation 的 CDD / EDD checklist
-> 高風險或模糊案例交給 human review
```

## 產品核心命題

這套系統的價值不是「會回答法規問題」，而是把 FATF、MAS、FCA、內部 AML / KYC policy 這些複雜文件，轉成一套 **人看得懂、機器也能判斷** 的知識系統。

普通 RAG chatbot 可能可以回答：

- FATF Recommendation 10 在說什麼？
- MAS Notice 626 對 CDD 有哪些要求？
- Beneficial Owner 是什麼？

但它通常無法穩定回答真正有業務價值的問題：

- 這個 customer profile 到底觸發 standard CDD 還是 EDD？
- 哪一條 obligation 適用於 corporate customer？
- 哪個 jurisdiction 或 policy version 優先？
- 內部 AML policy 是否比外部 regulation 寬鬆？
- 新版條文是否取代舊版內規？
- 這份 checklist 的每個文件要求依據哪一條 source clause？

所以這個 project 不能從「聊天介面」開始，而要從「知識編譯 pipeline」開始。

## 目標架構

### 1. Raw Regulatory Sources

目的：保存原始權威來源、版本、引用位置與 provenance。

MVP 來源：

- FATF Recommendation 10
- MAS Notice 626 的 CDD / EDD 相關章節
- FCA AML / financial crime guidance 的部分章節
- 一份 mock internal AML / KYC policy

要建的東西：

- `SourceDocument`
- `Clause`
- `Citation`
- `SourceVersion`

每個 clause 至少要保留：

- source id
- issuer
- jurisdiction
- document version
- effective date
- retrieval date
- section / clause / paragraph id
- raw text
- source URL 或 local file path

判斷標準：任何後續 wiki page、obligation、conflict、CDD checklist，都要能回到原始 clause。

### 2. Clause Segmentation / Legal Parsing

目的：把長文件切成可以 citation、抽取、比較、review 的穩定單位。

不要只用固定 token chunk。法規文件的 hierarchy 很重要，因為例外、定義、cross-reference 通常依賴 parent clause。

要建的東西：

- section parser
- clause id generator
- hierarchy representation
- cross-reference placeholder
- extraction-ready clause records

對應論文：

- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1)：看 ingestion agent、triplet extraction、source-linked triplets。
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1)：看 sections、subsections、references、rule relationships 如何被表示。
- [LegalBench-RAG](https://arxiv.org/abs/2408.10343)：看 retrieval evaluation 為什麼要找 minimal legal snippets，而不是大段 chunk。

### 3. Obligation Extraction Layer

目的：把法律或內規條文轉成 structured obligation，不只是摘要。

建議的 canonical obligation 格式：

```yaml
obligation_id: identify_beneficial_owner
source_clause_id: mas626_cdd_001
jurisdiction: Singapore
issuer: MAS
actor: financial_institution
action: identify_and_verify
object: beneficial_owner
applies_to:
  customer_type: corporate_customer
conditions:
  - customer_type == corporate
exceptions: []
required_evidence:
  - ownership_structure_chart
  - identity_document
review_flags:
  - ubo_unclear
  - complex_ownership_structure
confidence: 0.82
review_status: pending_human_review
```

要抽取的欄位：

- actor / addressee：誰有義務
- action / predicate：必須做什麼
- object：作用對象
- condition：什麼情境下適用
- exception：什麼情境下不適用
- evidence required：需要什麼文件或證據
- timing / frequency / threshold：時間、頻率、門檻
- review trigger：什麼情境要人工審查

對應論文：

- [Approaching the AI Act... with AI](https://www.sciencedirect.com/science/article/pii/S2212473X25001026)：主讀 obligation identification、deontic filtering、addressee / predicate classification、searchable KG construction。
- [ComplianceNLP](https://arxiv.org/abs/2604.23585)：看 multi-task obligation extraction 和 external regulation 對 internal policy 的 gap detection。
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1)：看 legal text 如何變成 canonical / executable representation。

### 4. Human-Readable Wiki Layer

目的：讓 compliance officer 能讀懂概念，但每個概念都要連回 source clauses 和 structured obligations。

初期 wiki pages：

- Beneficial Owner / UBO
- Customer Due Diligence
- Enhanced Due Diligence
- Politically Exposed Person
- High-Risk Jurisdiction
- Source of Funds / Source of Wealth

每頁應包含：

- 定義
- aliases / equivalent terms
- related concepts
- applicable jurisdictions
- source references
- linked obligations
- known ambiguities
- human review notes

重要原則：wiki page 是人類閱讀層，不是 compliance reasoning 的唯一資料結構。

對應論文：

- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1)：看 triplets + original text 如何支撐可追溯 regulatory QA。
- [Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713)：看 KG-augmented policy QA 以及 ontology schema 選擇。

### 5. Machine-Readable Regulatory Graph

目的：把概念、義務、條件、例外、證據、jurisdiction、風險 trigger 和來源條文做成 typed graph，讓系統可以判斷。

建議 node types：

- `SourceDocument`
- `Clause`
- `Concept`
- `Obligation`
- `Condition`
- `Exception`
- `EvidenceRequirement`
- `Jurisdiction`
- `CustomerType`
- `RiskTrigger`
- `InternalPolicyRule`
- `Conflict`
- `ReviewCase`

建議 edge types：

- `defines`
- `requires`
- `applies_to`
- `conditioned_on`
- `except_when`
- `requires_evidence`
- `references_clause`
- `same_as`
- `broader_than`
- `narrower_than`
- `stricter_than`
- `supersedes`
- `conflicts_with`
- `derived_from`

對應論文：

- [ComplianceNLP](https://arxiv.org/abs/2604.23585)：看 regulatory KG + KG-augmented RAG 如何處理 cross-reference-heavy compliance task。
- [GraphCompliance](https://arxiv.org/abs/2510.26309)：看 policy graph / context graph alignment。
- [Knowledge Graph Representations for LLM-Based Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713)：看 formal ontology vs open schema 的取捨。
- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1)：看 ontology-free triplet graph、normalization、deduplication、evidence-linked retrieval。

### 6. Contradiction / Supersession Layer

目的：不要讓系統把衝突條文默默混在一起。

要記錄：

- statement A
- statement B
- source A
- source B
- conflict type
- 是明確衝突還是推理衝突
- 是否 supersedes / stricter_than / narrower_than
- 是否 retrieval-verifiable
- 是否需要 human review
- 最終 resolution

建議 conflict record：

```yaml
conflict_id: conflict_001
statement_a: "High-risk customer review every 12 months"
statement_b: "High-risk customer review every 6 months"
source_a: internal_aml_policy_v3
source_b: mas626_update_x
conflict_type: temporal_or_frequency
relationship: stricter_than
preferred_rule: mas626_update_x
verifiability: retrieval_verifiable
status: pending_human_review
```

對應論文：

- [LegalWiz](https://arxiv.org/html/2510.03418v2)：主讀 contradiction taxonomy、NLI + LLM hybrid scoring、retrieval-verifiable vs retrieval-resistant、human validation。
- [ComplianceNLP](https://arxiv.org/abs/2604.23585)：看 external regulations 和 institutional policies 的 gap analysis。
- [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1)：看 exceptions、dependencies、rule relationships 的 representation。

### 7. CDD Decision Layer

目的：根據 customer profile 產出 CDD / EDD checklist，而不是讓 LLM 自由生成。

customer context 應該先變成 structured object 或 context graph：

```yaml
customer_id: example_customer_001
customer_type: corporate
registration_jurisdiction: Singapore
ownership_layers: 3
ubo_status: identified
ubo_country_risk: high
pep_exposure: false
source_of_funds_available: false
source_of_wealth_available: false
```

系統輸出應包含：

- CDD / EDD decision
- applicable obligations
- required documents
- risk triggers
- unresolved conflicts
- human review flags
- source citations

對應論文：

- [GraphCompliance](https://arxiv.org/abs/2510.26309)：主讀 policy graph 和 context graph 如何 alignment，這就是 CDD decision layer 的理論核心。
- [AI Application in Anti-Money Laundering for Sustainable and Transparent Financial Systems](https://arxiv.org/abs/2512.06240)：看 KYC / CDD / EDD Graph RAG、customer relationship graph、audit trail、human review。
- [ComplianceNLP](https://arxiv.org/abs/2604.23585)：看 evidence-grounded monitoring 和 internal policy mapping。

### 8. Evidence Retrieval / Audit Layer

目的：每個 answer、wiki page、obligation、conflict、checklist item 都要能引用 source clause。

要建的能力：

- clause-level retrieval
- graph-based retrieval
- minimal supporting snippet retrieval
- citation attachment
- answer faithfulness check
- retrieval failure logging

重要原則：retrieval failure 不是小問題。法律 / 合規 RAG 中，很多 hallucination 其實是 retrieval failure 導致的。

對應論文：

- [LegalBench-RAG](https://arxiv.org/abs/2408.10343)：主讀 legal retrieval step evaluation，尤其 minimal relevant snippets。
- [Legal RAG Bench](https://arxiv.org/abs/2603.01710)：主讀 end-to-end legal RAG evaluation 和 retrieval / reasoning error decomposition。
- [RAGulating Compliance](https://arxiv.org/html/2508.09893v1)：看 retrieved triplets + source text sections 如何支撐 traceable answer。

## 論文對應到哪個架構部件

| 論文 | 閱讀時機 | 對應系統部件 | 你要學什麼 |
| --- | --- | --- | --- |
| [ComplianceNLP](https://arxiv.org/abs/2604.23585) | 第一輪 | 整體 compliance architecture、obligation extraction、regulatory KG、policy gap analysis | 法規更新 -> 義務抽取 -> KG -> 內規 mapping -> gap detection -> grounded answer 的主架構 |
| [GraphCompliance](https://arxiv.org/abs/2510.26309) | 第一輪 | CDD Decision Layer | policy graph 和 context graph 要分開建模；customer profile 不是 prompt，而是 context graph |
| [AI Application in AML](https://arxiv.org/abs/2512.06240) | 第一輪 | Customer risk graph、KYC / CDD / EDD workflow | AML / KYC domain grounding、customer relationship graph、due diligence report、audit / human review |
| [Approaching the AI Act... with AI](https://www.sciencedirect.com/science/article/pii/S2212473X25001026) | 第二輪 | Obligation Extraction Layer | obligation identification、deontic filtering、addressee / predicate classification、KG construction |
| [Legal Requirements Translation from Law](https://arxiv.org/html/2507.02846v1) | 第二輪 | Machine-readable rule representation | legal text 如何變成 canonical / executable representation，並保留 conditions、exceptions、references |
| [RAGulating Compliance](https://arxiv.org/html/2508.09893v1) | 第二輪 | Ingestion、concept dedupe、GraphRAG QA | ingestion agent、SPO triplets、normalization、deduplication、evidence-grounded retrieval |
| [Knowledge Graph Representations for Policy Compliance Reasoning](https://arxiv.org/abs/2604.27713) | 第二輪 | KG schema design、retrieval strategy | formal ontology vs open schema，還有從 lookup 到 cross-policy reasoning 的 task taxonomy |
| [LegalWiz](https://arxiv.org/html/2510.03418v2) | 第三輪 | Contradiction / Supersession Layer | conflict taxonomy、hybrid contradiction scoring、retrieval-verifiable vs retrieval-resistant、human validation |
| [LegalBench-RAG](https://arxiv.org/abs/2408.10343) | 第三輪 | Evidence retrieval evaluation | 怎麼評估 legal RAG 的 retrieval step，尤其 minimal citation-ready snippets |
| [Legal RAG Bench](https://arxiv.org/abs/2603.01710) | 第三輪 | End-to-end evaluation | 怎麼把 retrieval failure 和 reasoning failure 拆開看 |

## 建議閱讀順序

### 第一輪：先建立整體架構感

#### 1. ComplianceNLP

你現在讀這篇，是在讀 CDD-GraphWiki 的 **主幹架構**。

對應部件：

- Raw Regulatory Sources
- Obligation Extraction
- Regulatory Knowledge Graph
- Internal Policy Mapping
- Gap Analysis
- Evidence-grounded Answer

讀完要產出：

- 第一版 `Obligation` schema
- 第一版 `InternalPolicyRule` schema
- external regulation 對 internal policy 的 mapping 方式
- 一張 end-to-end architecture diagram

#### 2. GraphCompliance

你現在讀這篇，是在讀 CDD-GraphWiki 的 **CDD Decision Layer**。

對應部件：

- Policy Graph
- Customer Context Graph
- Compliance Gate
- CDD / EDD decision logic

讀完要產出：

- 第一版 `CustomerContext` schema
- 5 個 customer profiles
- 5 個 expected CDD / EDD outcomes
- 第一個問題：「這個 customer profile 是否觸發 EDD？」

#### 3. AI Application in AML

你現在讀這篇，是在讀 CDD-GraphWiki 的 **AML / KYC domain grounding**。

對應部件：

- Customer risk graph
- KYC / CDD / EDD report generation
- Audit trail
- Human review expectations

讀完要產出：

- customer risk graph 的 node / edge 草稿
- 區分哪些 facts 屬於 regulatory reasoning，哪些屬於 financial crime risk analysis
- 決定 MVP 是否只做 CDD checklist，不做 transaction monitoring

### 第二輪：學會把法規編譯成資料

#### 4. Approaching the AI Act... with AI

你現在讀這篇，是在讀 **obligation extraction pipeline**。

對應部件：

- Clause -> obligation
- deontic statement filtering
- addressee / predicate extraction
- searchable KG construction

讀完要產出：

- actor / action / object / condition / exception 的 extraction prompt 或 rule
- 10 條 FATF / MAS 手動標註 obligation gold examples
- low-confidence obligation 的 review queue 規則

#### 5. Legal Requirements Translation from Law

你現在讀這篇，是在讀 **machine-readable canonical representation**。

對應部件：

- Legal rule object
- Section hierarchy
- Cross-reference
- Condition / exception / dependency
- Executable or schema-validatable representation

讀完要產出：

- 5 條 obligation 的 YAML / Python typed representation
- clause hierarchy 的資料格式
- exception 與 cross-reference 的表示方式

#### 6. RAGulating Compliance

你現在讀這篇，是在讀 **ingestion + concept deduplication + GraphRAG QA**。

對應部件：

- Ingestion Agent
- Triplet Extraction Agent
- Normalization Agent
- Deduplication Agent
- Retrieval Agent
- Answer Agent

讀完要產出：

- 第一版 alias map：UBO / Beneficial Owner / Controlling Party
- source-linked triplet format
- 判斷哪些 triplets 可以進 wiki，哪些可以進 regulatory KG

#### 7. Knowledge Graph Representations for Policy Compliance Reasoning

你現在讀這篇，是在讀 **KG schema strategy**。

對應部件：

- Formal ontology vs open schema
- Graph retrieval strategy
- KG QA task taxonomy

讀完要產出：

- MVP graph ontology
- strict relation types 與 exploratory relation types 的分界
- 5 種 graph QA test：definition lookup、relation enumeration、attribute retrieval、multi-hop reasoning、compliance check

### 第三輪：讓系統可驗證、可審計、可被信任

#### 8. LegalWiz

你現在讀這篇，是在讀 **contradiction / supersession layer**。

對應部件：

- Conflict schema
- Contradiction taxonomy
- Hybrid NLI + LLM contradiction scoring
- Retrieval-verifiable vs retrieval-resistant
- Human review queue

讀完要產出：

- 第一版 `Conflict` schema
- AML / CDD conflict types：temporal、threshold、jurisdiction、authority、procedure、specificity、policy reversal
- 3 個 mock conflicts，例如 high-risk customer review 12 個月 vs 6 個月

#### 9. LegalBench-RAG

你現在讀這篇，是在讀 **evidence retrieval evaluation**。

對應部件：

- Clause retrieval
- Minimal legal snippet retrieval
- Citation precision / recall

讀完要產出：

- 20 個 query -> supporting clause test cases
- retrieval precision / recall 評估方式
- citation correctness check

#### 10. Legal RAG Bench

你現在讀這篇，是在讀 **end-to-end evaluation**。

對應部件：

- Retrieval failure analysis
- Reasoning failure analysis
- Groundedness
- Checklist correctness

讀完要產出：

- 評估分類：retrieval correctness、obligation extraction accuracy、graph consistency、conflict detection precision、checklist correctness、citation faithfulness
- error taxonomy，讓每個錯誤都能歸因到 retrieval、extraction、graph modeling、conflict handling 或 final reasoning

## MVP Build Path

### Phase 0：Project Skeleton and Spec

目標：先把 project 說清楚，再寫 code。

Deliverables：

- `docs/system-build-roadmap.md`
- `docs/note.md`
- `docs/spec.md` 或等價產品規格
- MVP scope：FATF Recommendation 10、MAS Notice 626 CDD / EDD clauses、一份 mock internal AML policy

Done when：

- project anti-goal 清楚：不是 generic RAG chatbot
- 每個 module 的邊界清楚
- 每篇 paper 都知道對應哪個系統部件

### Phase 1：Data Contracts

目標：先定義資料結構，再做 extraction。

Deliverables：

- `SourceDocument`
- `Clause`
- `Concept`
- `Obligation`
- `EvidenceRequirement`
- `CustomerContext`
- `Conflict`
- `CDDChecklist`

Done when：

- 每個 object 都有 JSON / YAML example
- 每個 object 都有 provenance 和 review status
- 可以手動用 structured objects 寫出一份 CDD checklist

### Phase 2：Manual Gold Dataset

目標：先做小而可信的人工標註集，不要一開始就全自動。

Deliverables：

- 10 個 manually segmented clauses
- 10 個 manually extracted obligations
- 5 個 concept pages
- 5 個 customer profiles
- 5 個 expected CDD / EDD checklist outputs
- 3 個 conflict examples

Done when：

- 每個 output 都能回到 source clause
- 覆蓋 individual customer、corporate customer、PEP、high-risk jurisdiction、complex ownership、UBO unclear

### Phase 3：Ingestion and Clause Segmentation

目標：讓原始文件變成可引用、可抽取、可比對的 clause records。

Deliverables：

- source parser
- clause segmentation output
- source metadata / version metadata
- stable clause ids

Done when：

- 每個 clause 都能回到 source document、section、page / paragraph、raw text
- rerun 後 clause id 不會任意漂移

### Phase 4：Obligation Extraction Prototype

目標：把 clauses 轉成 structured obligations。

Deliverables：

- extraction prompt 或 rule pipeline
- obligation schema validation
- low-confidence human review queue
- manual gold dataset comparison

Done when：

- extracted obligation 包含 actor、action、object、condition、exception、required evidence、source clause
- extraction failure 有分類，而不是只說模型答錯

### Phase 5：Wiki and Concept Deduplication

目標：產生人類可讀 concept pages，並處理同義詞 / 近義詞。

Deliverables：

- concept page generator
- alias map
- related concept links
- source-backed ambiguity notes

Done when：

- Beneficial Owner 頁面能顯示 aliases、definitions、obligations、related concepts、source clauses、ambiguity notes
- UBO / BO / Beneficial Owner / Controlling Party 不會無審查地變成四個孤立概念

### Phase 6：Regulatory Graph

目標：建立第一個 machine-reasonable graph。

Deliverables：

- graph schema
- clauses / concepts / obligations / evidence / risk triggers / jurisdictions nodes
- typed edges
- JSON / RDF / graph database import export

Done when：

- 可以查詢：`corporate_customer + high_risk_jurisdiction + complex_ownership_structure` 觸發哪些 obligations
- 每個 graph answer 都能回 source clauses

### Phase 7：Contradiction and Supersession Log

目標：讓系統顯示衝突，而不是默默選一個答案。

Deliverables：

- conflict schema
- supersedes / stricter_than / narrower_than relationships
- human review status
- mock internal policy conflicts

Done when：

- 系統能記錄 internal policy 比 external regulation 寬鬆或衝突
- CDD checklist 能顯示 unresolved conflicts

### Phase 8：CDD Decision Engine

目標：從 customer profile 產生 evidence-grounded CDD / EDD checklist。

Deliverables：

- customer profile schema
- rule matching logic
- checklist generator
- human review flags
- citation attachment

Done when：

- corporate customer + complex ownership + high-risk UBO jurisdiction 會輸出 EDD、required documents、applicable obligations、risk triggers、conflicts、citations

### Phase 9：Evaluation Harness

目標：證明它比普通 RAG chatbot 更可靠。

Deliverables：

- retrieval tests
- obligation extraction tests
- conflict detection tests
- checklist correctness tests
- citation faithfulness checks

Done when：

- 每個錯誤能被歸因到 retrieval、extraction、graph modeling、conflict handling 或 final reasoning
- 有 simple vector-RAG chatbot baseline 可以比較

## 建議 MVP Repo 結構

```text
CDD-GraphWiki/
  docs/
    note.md
    system-build-roadmap.md
    spec.md
  data/
    sources/
    processed/
    gold/
  knowledge/
    wiki/
    graph/
    conflicts/
  schemas/
    source_document.schema.json
    clause.schema.json
    obligation.schema.json
    customer_context.schema.json
    conflict.schema.json
    cdd_checklist.schema.json
  src/
    ingestion/
    extraction/
    graph/
    decision/
    evaluation/
  tests/
```

## 現在不要先做的事

先不要做：

- 漂亮 chatbot UI
- 以 vector database 作為核心架構
- 一次吃 FATF + MAS + FCA + HKMA + 多份內規
- live financial institution integration
- 全自動 legal judgment

先做：

- 小範圍 source set
- stable clause ids
- manual gold examples
- structured obligations
- tiny regulatory graph
- evidence-backed checklist
- explicit conflict handling

## 最適合的 Portfolio / Research Framing

工程型 title：

> CDD-GraphWiki: A Human-Readable and Machine-Reasonable Knowledge Compilation System for AML Compliance

研究型 title：

> Regulatory Knowledge Compilation for Customer Due Diligence: A Graph-Augmented LLM System for AML Compliance Reasoning

這個 project 的貢獻不是「做一個合規聊天機器人」，而是：

> 把法規文字編譯成 human-readable wiki pages 和 machine-readable compliance objects，並用 graph reasoning、conflict tracking、evidence retrieval 產生可審計的 CDD / EDD decision。
