# RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA

Bhavik Agarwal, Hemant Sunil Jomraj, Simone Kaplunov, Jack Krolick, Viktoria Rojkova  
MasterControl AI Research  
{bagarwal,hjomraj,skaplunov, jkrolick,vrojkova}@mastercontrol.com

###### Abstract

Report issue for preceding element

Regulatory compliance question answering (QA) requires precise, verifiable information, and domain-specific expertise, posing challenges for Large Language Models (LLMs). In this work, we present a novel multi-agent framework that integrates a Knowledge Graph (KG) of Regulatory triplets with Retrieval-Augmented Generation (RAG) to address these demands. First, agents build and maintain ontology-free KG by extracting subject–predicate–object (SPO) triplets from regulatory documents and systematically cleaning, normalizing, deduplicating, and updating them. Second, these triplets are embedded and stored along with their corresponding textual sections and metadata in a single enriched vector database, allowing for both graph-based reasoning and efficient information retrieval. Third, an orchestrated agent pipeline leverages triplet-level retrieval for question answering, ensuring high semantic alignment between user queries and the factual ’who-did-what-to-whom’ core captured by the graph. Our hybrid system outperforms conventional methods in complex regulatory queries, ensuring factual correctness with embedded triplets, enabling traceability through a unified vector database, and enhancing understanding through subgraph visualization, providing a robust foundation for compliance-driven and broader audit-focused applications.

Report issue for preceding element

## 1 Introduction

Report issue for preceding element

The growing regulatory complexities in healthcare, pharmaceuticals, and medical devices shape market access and patient care \[[HCB24](https://arxiv.org/html/2508.09893v1#bib.bibx15)\]. The extensive guidance and rules of the FDA \[[FDA25](https://arxiv.org/html/2508.09893v1#bib.bibx8)\] require strict compliance with approvals, post-market surveillance, and quality systems \[[CDW22](https://arxiv.org/html/2508.09893v1#bib.bibx5)\]. Meanwhile, LLMs such as GPT-o1 \[[Z<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx36)\], Qwen-2.5 \[[Y<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx33)\] and Pi-4 \[[A<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx1)\] excel in text tasks but face unique challenges in precision, verifiability, and domain specialization in high-stakes regulatory contexts \[[WZ24](https://arxiv.org/html/2508.09893v1#bib.bibx31)\]. Hallucination risks and limited contextual understanding underscore the need for robust guardrails, particularly in safety-critical applications \[[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24a](https://arxiv.org/html/2508.09893v1#bib.bibx12)\], \[[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24b](https://arxiv.org/html/2508.09893v1#bib.bibx22)\]. How can we ensure the domain specificity and reliability required for compliance?

Report issue for preceding element

Our work proposes a three-fold innovation for regulated compliance: first, we construct and refine triplet graphs from regulatory documents, building on knowledge graph research \[[N<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>15](https://arxiv.org/html/2508.09893v1#bib.bibx23)\]; second, we integrate these graphs with RAG techniques, inspired by open-domain QA \[[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx20)\] and healthcare question-answering \[[Y<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>25](https://arxiv.org/html/2508.09893v1#bib.bibx34)\], to reduce hallucinations \[[J<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx16)\]; and third, a multi-agent architecture oversees graph construction, RAG database enrichment, and the final question-answering process, ultimately grounding responses in factual relationships to enhance precision, reliability, and verifiability—key for demonstrating compliance to regulators and stakeholders.

Report issue for preceding element

## 2 Relevant Work

A line of research tackles hallucination and domain-specific gaps by integrating language models with knowledge graphs (KGs), which encode domain knowledge for semantic linking, inference, and consistency checks \[[H<sup><span>+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx11), [N<sup><span>+</span></sup>15](https://arxiv.org/html/2508.09893v1#bib.bibx23), [C<sup><span>+</span></sup>20](https://arxiv.org/html/2508.09893v1#bib.bibx2)\]. In regulatory settings, KGs capture complex relationships among rules and guidelines \[[C<sup><span>+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx3)\], and when combined with retrieval-augmented generation (RAG) \[[L<sup><span>+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx20)\], reduce factual errors by putting outputs in authoritative data \[[L<sup><span>+</span></sup>24a](https://arxiv.org/html/2508.09893v1#bib.bibx21)\]. Although RAG has excelled in open-domain QA \[[L<sup><span>+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx20), [K<sup><span>+</span></sup>20](https://arxiv.org/html/2508.09893v1#bib.bibx17)\], its application in regulatory compliance, particularly synthesizing structured (KG) and unstructured text, remains underexplored. Multi-agent systems \[[SLB08](https://arxiv.org/html/2508.09893v1#bib.bibx27), [Woo09](https://arxiv.org/html/2508.09893v1#bib.bibx30)\] offer autonomous agents for data ingestion, KG construction, verification, and inference, enabling modularity and scalability \[[Wei00](https://arxiv.org/html/2508.09893v1#bib.bibx29), [Z<sup><span>+</span></sup>13](https://arxiv.org/html/2508.09893v1#bib.bibx35)\]. This approach is well suited to dynamic regulatory environments that require constant updates.

### 2.1 Knowledge Graphs in Regulatory Compliance

Report issue for preceding element

Knowledge graphs excel at representing complex regulatory information, facilitating semantic relationships \[[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx11)\]. Notable examples include enterprise KGs for market regulations \[[Ers23](https://arxiv.org/html/2508.09893v1#bib.bibx7)\] and frameworks for medical device policies \[[C<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24](https://arxiv.org/html/2508.09893v1#bib.bibx3)\], while \[[X<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>25](https://arxiv.org/html/2508.09893v1#bib.bibx32)\] underscores KG reasoning techniques that bridge structured and unstructured data.

Report issue for preceding element

### 2.2 Retrieval-Augmented Generation in Regulatory Compliance

Report issue for preceding element

RAG \[[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx20)\] integrates retrieval mechanisms with generative language models, improving the factual accuracy \[[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24b](https://arxiv.org/html/2508.09893v1#bib.bibx13)\]. In the pharmaceutical domain, a chatbot that uses RAG successfully navigated complex guidelines by retrieving and storing responses in relevant documents \[[KM24](https://arxiv.org/html/2508.09893v1#bib.bibx18)\].

Report issue for preceding element

### 2.3 Multi-Agent Systems and Their Application

Report issue for preceding element

Multi-agent systems enable specialized agents to coordinate complex tasks \[[SLB08](https://arxiv.org/html/2508.09893v1#bib.bibx27), [Woo09](https://arxiv.org/html/2508.09893v1#bib.bibx30)\], facilitating robust data integration and knowledge engineering \[[Z<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>13](https://arxiv.org/html/2508.09893v1#bib.bibx35)\]—a key advantage in rapidly evolving regulatory contexts.

Report issue for preceding element

## 3 Ontology Free Knowledge Graph

Report issue for preceding element

Knowledge graphs often rely on predefined ontologies (e.g. DBpedia \[[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>15](https://arxiv.org/html/2508.09893v1#bib.bibx19)\], YAGO \[[SKW07](https://arxiv.org/html/2508.09893v1#bib.bibx26)\]), yet an alternative ’schema-light’ approach defers rigid schemas in favor of flexible bottom-up extraction \[[EFC<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>11](https://arxiv.org/html/2508.09893v1#bib.bibx6), [FSE14](https://arxiv.org/html/2508.09893v1#bib.bibx9)\]. This method quickly adapts to new data domains \[[CBK<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>10](https://arxiv.org/html/2508.09893v1#bib.bibx4)\], reduces initial overhead \[[EFC<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>11](https://arxiv.org/html/2508.09893v1#bib.bibx6)\], and allows partial schemas to emerge naturally \[[HBC<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21](https://arxiv.org/html/2508.09893v1#bib.bibx14)\], making it especially valuable in regulatory settings where rules evolve rapidly, data formats vary \[[PEK06](https://arxiv.org/html/2508.09893v1#bib.bibx24)\], and open-ended queries can reveal hidden legal connections \[[FSE14](https://arxiv.org/html/2508.09893v1#bib.bibx9)\]. In order to demonstrate how the _schema-light_ strategy operates in practice, we extracted triplets from the data from the Electronic Code of Federal Regulations, focusing on specific sections that share references and time constraints. The resulting relationships form a small subgraph that illustrates both shallow hierarchical structures (_e.g._, parts, and subparts) and interlinked regulatory requirements. As seen in Figure [1](https://arxiv.org/html/2508.09893v1#S3.F1 "Figure 1 ‣ 3 Ontology Free Knowledge Graph ‣ RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA"), these extracted triplets reveal how different sections converge on the same 15-day appeal timeframe, underscoring the flexibility of an ontology-free approach in capturing cross-references and shared procedural deadlines.

Report issue for preceding element

[⬇](data:text/plain;base64,KHBhcnRPZikKQ0hBUFRFUiBJICA8LS0tLS0tLS0tLS0tLSAgU1VCQ0hBUFRFUiBCCl4gICAgICAgICAgICAgICAgICAgICAgICAgXgp8IChwYXJ0T2YpICAgICAgICAgICAgICAgIHwKUEFSVCAxMTcgIC0tLS0tLS0tLS0tLS0tICBTVUJQQVJUIEUgKFdpdGhkcmF3YWwgb2YgUUYgRXhlbXB0aW9uKQpeICAgICAgICAgICAgICAgICAgICAgICAgIF4KfCAoaW5TdWJwYXJ0KSAgICAgICAgICAgICB8IChpblN1YnBhcnQpCsKnwqcgMTE3LjI1NywgMTE3LjI2MCwgMTE3LjI2NCwgMTE3LjI2Nwp8ICAgICAgXiAgICAgICAgXiAgICAgICAgXgp8IChyZWZlcmVuY2VzKSAocmVmZXJlbmNlcykgKHJlZmVyZW5jZXMpCnwgICAgICBcXCQxMTcuMjY0IFxcJDExNy4yNjcgXFwkMTE3LjI2NAp8Clt0aW1lZnJhbWU6IDE1IGRheXMgdG8gYXBwZWFsIHRoZSBvcmRlcl0=)

(partOf)

CHAPTER I <------------- SUBCHAPTER B

^ ^

| (partOf) |

PART 117 \-------------- SUBPART E (Withdrawal of QF Exemption)

^ ^

| (inSubpart) | (inSubpart)

§§ 117.257, 117.260, 117.264, 117.267

| ^ ^ ^

| (references) (references) (references)

| \\\\$117.264 \\\\$117.267 \\\\$117.264

|

\[timeframe: 15 days to appeal the order\]

Figure 1: Independent sections converge on a single requirement, only discernible through triplet-driven interconnections.

Report issue for preceding element

## 4 Triplet-Based Embeddings for Regulatory QA with Textual Evidence

In this section, we introduce a formulation for leveraging embedded triplets to enable precise, fact-centric retrieval in a regulatory question-answering system. Unlike purely text-based approaches, our method not only encodes concise Subject-Predicate-Object relationships, but also links each triplet to the original text sections from which it was extracted. At query time, the system retrieves both the relevant triplets and corresponding text evidence, feeding them into an LLM for the final generation of the answer.

### 4.1 Corpus, Sections, and Triplet Extraction

Let $\mathcal{C}$ be a corpus of regulatory documents. We partition $\mathcal{C}$ into atomic text sections —- for instance, paragraphs, clauses, or semantically coherent fragments —-using a function

Report issue for preceding element

|  | Ω:𝒞→𝒳,\Omega:\mathcal{C}\;\to\;\mathcal{X}, |  |
|-----|-----------------------------------------------|-----|

where $\mathcal{X}$ is the set of all text fragments $\{\,x_{1},\,x_{2},\,\dots,\,x_{m}\}$.

Report issue for preceding element

We then apply an information extraction pipeline $\Phi$ to each section $x_{j}$. The pipeline identifies the subject-predicate-object relationships of that section, thus producing triplets:

Report issue for preceding element

|  | Φ(Ω(𝒞))={ti∣ti=(si,pi,oi)}.\Phi\bigl{(}\Omega(\mathcal{C})\bigr{)}\;=\;\bigl{\{}\,t_{i}\;\mid\;t_{i}=(s_{i},\;p_{i},\;o_{i})\bigr{\}}. |  |
|-----|---------------------------------------------------------------------------------------------------------------------------------------|-----|

We define a linking function $\Lambda$ such that each triplet $t_{i}$ is associated with one or more text sections $x_{j}$. Formally,

Report issue for preceding element

|  | Λ:𝒯→ 2𝒳,\Lambda:\mathcal{T}\;\to\;2^{\mathcal{X}}, |  |
|-----|------------------------------------------------------|-----|

where $\mathcal{T}$ is the set of all extracted triplets, and $\Lambda\bigl{(}t_{i}\bigr{)}$ yields the subset of sections from which $t_{i}$ was extracted. Hence, each triplet $t_{i}$ has _provenance_—a reference to its original textual source(s).

Report issue for preceding element

### 4.2 Embedding Triplets

For each triplet $t_{i}=(s_{i},\,p_{i},\,o_{i})$, we create a short textual representation $f(t_{i})$. A typical choice is a concatenation of S-P-O, for example:

Report issue for preceding element

|  | f(ti)=concat(si,pi,oi).f(t_{i})=\mathrm{concat}(s_{i},\;p_{i},\;o_{i}). |  |
|-----|-----------------------------------------------------------------------|-----|

We then define an embedding function

Report issue for preceding element

|  | E:𝒳∪𝒯→ℝd,E:\mathcal{X}\cup\mathcal{T}\;\to\;\mathbb{R}^{d}, |  |
|-----|---------------------------------------------------------------|-----|

where $d$ is the dimensionality of the embedding space. Specifically, for any triplet $t_{i}$,

Report issue for preceding element

|  | 𝐞ti=E(f(ti))∈ℝd\mathbf{e}_{t_{i}}=E\bigl{(}f(t_{i})\bigr{)}\;\in\;\mathbb{R}^{d} |  |
|-----|-----------------------------------------------------------------------------------|-----|

We also embed queries and (optionally) text sections themselves via the same or a compatible model. The resulting vectors are stored in a vector index $\mathcal{V}$ such that:

Report issue for preceding element

|  | 𝒱={(𝐞ti,ti,Λ(ti))| 1≤i≤N},\mathcal{V}=\bigl{\{}\,(\mathbf{e}_{t_{i}},\,t_{i},\,\Lambda(t_{i}))\;\bigm{|}\;1\,\leq\,i\,\leq\,N\bigr{\}}, |  |
|-----|----------------------------------------------------------------------------------------------------------------------------------------|-----|

where $\mathbf{e}_{t_{i}}$ is the triplet embedding and $\Lambda(t_{i})$ is the set of associated text sections.

Report issue for preceding element

### 4.3 Embedding Function

Report issue for preceding element

To enhance query processing and retrieval, we developed an embedding model based on Transformer’s methodology, specifically leveraging transformer-based architectures such as BERT. This embedding model was trained on textual data extracted from the eCFR, capturing semantic nuances specific to the regulatory language. The embedding process involves encoding cleaned textual chunks into high-dimensional vector representations, which enable efficient semantic search and retrieval in downstream tasks, significantly improving the precision and relevance of responses to regulatory queries.

Report issue for preceding element

### 4.4 Query Embedding and Retrieval

Given a user query $Q\in\mathcal{Q}$ —- for example, “Which agency is responsible for Regulation 2025-X?” —- we embed $Q$ as

Report issue for preceding element

|  | 𝐞Q=E(Q).\mathbf{e}_{Q}=E(Q). |  |
|-----|--------------------------------|-----|

We perform a $k$\-nearest neighbor search in $\mathcal{V}$ using a similarity measure $\mathrm{sim}(\cdot,\cdot)$, typically cosine similarity. We obtain:

Report issue for preceding element

|  | 𝒯Q=TopK(sim(𝐞Q,𝐞ti))\mathcal{T}_{Q}=\mathrm{TopK}\Bigl{(}\mathrm{sim}\bigl{(}\mathbf{e}_{Q},\;\mathbf{e}_{t_{i}}\bigr{)}\Bigr{)} |  |
|-----|-----------------------------------------------------------------------------------------------------------------------------------|-----|

which yields the top-$k$ triplets most relevant to the query. For each retrieved triplet $t_{i}\in\mathcal{T}_{Q}$, we can also retrieve its associated text sections through $\Lambda(t_{i})$. Formally:

Report issue for preceding element

|  | 𝒳Q=⋃ti∈𝒯QΛ(ti)\mathcal{X}_{Q}=\bigcup_{t_{i}\,\in\,\mathcal{T}_{Q}}\Lambda\bigl{(}t_{i}\bigr{)} |  |
|-----|------------------------------------------------------------------------------------------------|-----|

so $\mathcal{X}_{Q}$ is the set of sources’ text sections that support the discovered triplets.

### 4.5 LLM-Based QA with Triplets and Text

To finalize the answer, we define a function

Report issue for preceding element

|  | Γ:𝒬× 2𝒯× 2𝒳→𝒜,\Gamma:\mathcal{Q}\;\times\;2^{\mathcal{T}}\;\times\;2^{\mathcal{X}}\;\to\;\mathcal{A}, |  |
|-----|-----------------------------------------------------------------------------------------------------------|-----|

where $\mathcal{A}$ is the set of possible answers. Essentially, $\Gamma$ is an LLM that accepts: User query $Q$, Retrieved triplets $\mathcal{T}_{Q}$, Relevant Text Sections $\mathcal{X}_{Q}$. The LLM then produces an answer $A\in\mathcal{A}$. In symbolic form:

Report issue for preceding element

|  | A=Γ(Q,𝒯Q,𝒳Q).A=\Gamma\bigl{(}Q,\;\mathcal{T}_{Q},\;\mathcal{X}_{Q}\bigr{)}. |  |
|-----|------------------------------------------------------------------------------|-----|

In practice, the LLM input might be a prompt that includes the user question plus concatenated or selectively summarized triplets and text sections. By examining both structured (triplet) facts and verbatim textual evidence, the LLM generates a more accurate and explainable response.

Report issue for preceding element

### 4.6 Theoretical Considerations

Report issue for preceding element

Completeness and Consistency: $\mathcal{T}$ is complete if every relevant statement in $\mathcal{C}$ is represented by at least one SPO triplet and consistent if $\Phi$ does not introduce contradictory or spurious triplets.

Report issue for preceding element

Report issue for preceding element

Retrieval Sufficiency: With $\mathrm{sim}\bigl{(}\mathbf{e}_{Q},\mathbf{e}_{t_{i}}\bigr{)}$ as a semantic relatedness measure and an embedding function $E$ that preserves factual relationships, the top-$k$ triplets in $\mathcal{T}_{Q}$ should suffice to answer $Q$.

Report issue for preceding element

Report issue for preceding element

Text Sections as Evidence: Because each $t_{i}$ links back to its source text, users or downstream models can verify and clarify relationships by referring to the original regulatory language, thus mitigating ambiguities not fully captured by the triplet alone.

Report issue for preceding element

## 5 Multi Agents System

We use a multiagent system to orchestrate ingestion, extraction, cleaning, and query-answering in a modular, scalable manner. Each agent specializes in a core function, such as document ingestion, triplet extraction, or final answer generation, so they can run independently and be refined without disrupting the rest.

![Refer to caption](https://arxiv.org/html/Agent_KG.png)

Figure 2: Multi Agents High Level Architecture

### 5.1 Agents for ontology free knowledge graph constructions

Report issue for preceding element

The document ingestion agent segments raw regulatory text, captures metadata, and outputs structured fragments. The extraction agent uses an LLM to detect subject-predicate-object triplets (e.g., ’FDA requires submission within 15 days’). Normalization and Cleaning Agent merges duplicates, standardizes entities, and resolves synonyms to produce clean triplets. Triplet Store and Indexing Agent embeds and stores triplets in a vector database for easy retrieval.

Report issue for preceding element

### 5.2 Agentic Retrieval-Augmented Generation System

Report issue for preceding element

Our second agentic system utilizes the custom embedding model to retrieve semantically similar triplets from the knowledge graph. Initially, the retrieval agent identifies relevant triplets based on semantic proximity to user queries. Subsequently, the story-building agent compiles and synthesizes the textual chunks associated with these triplets into a coherent narrative. Finally, the generation agent processes this cohesive story to formulate precise and contextually relevant responses. This approach ensures that responses to regulatory inquiries are accurate, traceable, and grounded in verified regulatory content.

Report issue for preceding element

## 6 Retrieved Subgraph Visualization

Report issue for preceding element

Additionally, we supplement the responses with an interactive visual of the relevant subgraphs of the retrieved triplets. This visual aid significantly improves user comprehension and provides greater contextual clarity, facilitating informed decision making in regulatory compliance tasks.

Report issue for preceding element

![Refer to caption](https://arxiv.org/html/2508.09893v1/KGRAG.png)

Figure 3: Navigational Facility of triplets

Report issue for preceding element

## 7 Evaluation

In this section, we outline our methodology for evaluating the system’s ability to (1) retrieve the correct sections of a regulatory corpus, (2) generate factually accurate answers and (3) demonstrate flexibility of navigation through the interconnection of triplets in related sections. We detail our sampling procedure, the construction of queries, the measurement of section-level overlap, the assessment of factual correctness, and the analysis of triplet-based navigation.

![Refer to caption](https://arxiv.org/html/Eval.png)

Figure 4: Evaluation Methodology

### 7.1 Sampling and Ground Truth Construction

##### Random Sampling of Sections.

Let $\mathcal{S}=\{\,s_{1},\,s_{2},\,\dots,\,s_{N}\}$ be the full set of sections of the regulatory corpus. We draw a random subset

Report issue for preceding element

|  | 𝒮′={si1,si2,…,sik}⊂𝒮,\mathcal{S}^{\prime}\;=\;\bigl{\{}\,s_{i_{1}},\,s_{i_{2}},\,\dots,\,s_{i_{k}}\bigr{\}}\subset\mathcal{S}, |  |
|-----|----------------------------------------------------------------------------------------------------------------------------|-----|

where each $s_{i_{j}}$ is considered a _target section_ for evaluation, and $k\ll N$.

Report issue for preceding element

##### Identifying All Ground Truth Mentions.

For each sampled section $s_{i_{j}}$, we locate all other sections in the corpus that reference or expand upon the same regulatory ideas or entities. Formally, let

Report issue for preceding element

|  | M(sij)={sm1,sm2,…}M(s_{i_{j}})\;=\;\bigl{\{}\,s_{m_{1}},\,s_{m_{2}},\,\dots\bigr{\}} |  |
|-----|---------------------------------------------------------------------------------|-----|

denote the set of sections that contain overlaps or references relevant to $s_{i_{j}}$. We then create a _re-told story_ by concatenating $s_{i_{j}}$ with all sections in $M(s_{i_{j}})$:

Report issue for preceding element

|  | s~ij=(sij‖sm1‖sm2∥…).\widetilde{s}_{i_{j}}\;=\;\bigl{(}\,s_{i_{j}}\;\|\;s_{m_{1}}\;\|\;s_{m_{2}}\;\|\;\dots\bigr{)}. |  |
|-----|----------------------------------------------------------------------------------------------------------------|-----|

This concatenated text $\widetilde{s}_{i_{j}}$ is treated as the ground truth context for the focal section $s_{i_{j}}$.

Report issue for preceding element

### 7.2 LLM-Generated Questions and Answers

We employ a Large Language Model, denoted $\mathrm{LLM}_{\text{gen}}$, to produce a set of questions and corresponding reference answers based on each concatenated text $\widetilde{s}_{i_{j}}$. Formally,

Report issue for preceding element

|  | (𝒬ij,𝒜ij)=LLMgen(s~ij),(\mathcal{Q}_{i_{j}},\,\mathcal{A}_{i_{j}})\;=\;\mathrm{LLM}_{\text{gen}}\bigl{(}\,\widetilde{s}_{i_{j}}\bigr{)}, |  |
|-----|-------------------------------------------------------------------------------------------------------------------------------------|-----|

where $\mathcal{Q}_{i_{j}}=\{q_{1},q_{2},\dots,q_{m}\}$ and $\mathcal{A}_{i_{j}}=\{a_{1},a_{2},\dots,a_{m}\}$. Each pair $(q_{r},a_{r})$ is presumed to be responsible via the original information in $\widetilde{s}_{i_{j}}$.

Report issue for preceding element

### 7.3 System Inference and Evaluations

#### 7.3.1 Section-Level Overlap

To answer each question $q_{r}\in\mathcal{Q}_{i_{j}}$, our system retrieves a set of sections $\mathcal{R}_{i_{j},r}$ deemed relevant (based on embedding retrieval, triplet matching, or both). We measure the level of overlap between the recovered sections $\mathcal{R}_{i_{j},r}$ and the ground truth target section $s_{i_{j}}$ (along with its reference set $M(s_{i_{j}})$).

##### Definition: Overlap score.

Let $\mathcal{G}_{i_{j}}=\{s_{i_{j}}\}\cup M(s_{i_{j}})$ be the set of ground truth sections. Suppose that the system returns $\mathcal{R}_{i_{j},r}=\{r_{1},r_{2},\dots,r_{\ell}\}$. We define the overlap score $\mathcal{O}$ for question $q_{r}$ as

|  | 𝒪(ℛij,r,𝒢ij)=|ℛij,r∩𝒢ij||ℛij,r|.\mathcal{O}\bigl{(}\mathcal{R}_{i_{j},r},\,\mathcal{G}_{i_{j}}\bigr{)}\;=\;\frac{\bigl{|}\mathcal{R}_{i_{j},r}\,\cap\,\mathcal{G}_{i_{j}}\bigr{|}}{\bigl{|}\mathcal{R}_{i_{j},r}\bigr{|}}. |  |
|-----|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|

Thus,

-   •
    
    if $\mathcal{R}_{i_{j},r}\cap\mathcal{G}_{i_{j}}=\emptyset$, then $\mathcal{O}=0$;
    
    Report issue for preceding element
    
-   •
    
    if $\mathcal{R}_{i_{j},r}$ returns exactly one section, $r_{1}$, and $r_{1}=s_{i_{j}}$, then $\mathcal{O}=1$;
    
    Report issue for preceding element
    
-   •
    
    if, for instance, the system returns three sections, only one of which matches any in $\mathcal{G}_{i_{j}}$, then $\mathcal{O}=1/3$.
    
    Report issue for preceding element
    

We can further refine this measure by applying a similarity threshold $\theta$ for the equivalence between the retrieved sections and the ground truth sections (e.g., if the sections partially overlap or are highly similar). In that case,

Report issue for preceding element

|  | |ℛij,r∩𝒢ij|=∑r∈ℛij,r𝟏[sim(r,sg)≥θfor somesg∈𝒢ij].\bigl{|}\mathcal{R}_{i_{j},r}\,\cap\,\mathcal{G}_{i_{j}}\bigr{|}\;=\;\sum_{r\in\mathcal{R}_{i_{j},r}}\mathbf{1}\Bigl{[}\mathrm{sim}\bigl{(}r,\,s_{g}\bigr{)}\,\geq\,\theta\;\text{for some}\;s_{g}\in\mathcal{G}_{i_{j}}\Bigr{]}. |  |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|

#### 7.3.2 Factual Correctness of Answers

Once the system retrieves relevant sections and processes them through the QA pipeline (with or without associated triplets), it produces an answer $a_{r}^{\star}$. We compare $a_{r}^{\star}$ with the reference answer $a_{r}$ from $\mathrm{LLM}_{\text{gen}}$.

##### LLM-Based Fact Checking.

We use a secondary evaluation model $\mathrm{LLM}_{\text{eval}}$ or a domain expert to assess whether $a_{r}^{\star}$ is _factually correct_ with respect to the original text $\widetilde{s}_{i_{j}}$. We denote:

|  | F(ar⋆,ar)={1,if ar⋆ is factually correct and consistent with ar,0,otherwise.F(a_{r}^{\star},\;a_{r})\;=\;\begin{cases}1,&\text{if $a_{r}^{\star}$ is factually correct and consistent with $a_{r}$},\\ 0,&\text{otherwise}.\end{cases} |  |
|-----|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|

We measure correctness with two conditions:

1.  1.
    
    With Triplets: The system’s answer is grounded in the set of triplets that directly link to the retrieved sections.
    
    Report issue for preceding element
    
2.  2.
    
    Without Triplets: The system response is derived purely from the retrieval of raw text, without referencing the triplet data structure.
    
    Report issue for preceding element
    

By comparing the correctness scores for these two conditions, we quantify the _impact of structured triplets_ in factual precision.

#### 7.3.3 Navigational Facility of Triplets

We also investigate how _triplet interconnections_ facilitates follow-up questions. In many regulatory contexts, a concept from one section leads to further questions about a related section. To do this, we define the following.

##### Triplet Overlap Across Sections.

Let $\mathcal{T}$ be the global set of extracted triplets. For sections $s_{i_{j}}$ and $s_{m_{\ell}}\in M(s_{i_{j}})$, we look at triplets that are shared or linked between these sections:

Report issue for preceding element

|  | 𝒯(sij)={t∈𝒯∣tis extracted from sectionsij},\mathcal{T}(s_{i_{j}})\;=\;\{\,t\in\mathcal{T}\mid t\ \text{is extracted from section}\ s_{i_{j}}\}, |  |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------|-----|

|  | 𝒯(smℓ)={t∈𝒯∣tis extracted from sectionsmℓ}.\mathcal{T}(s_{m_{\ell}})\;=\;\{\,t\in\mathcal{T}\mid t\ \text{is extracted from section}\ s_{m_{\ell}}\}. |  |
|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----|

We then analyze:

Report issue for preceding element

|  | 𝒯(sij)∩𝒯(smℓ),\mathcal{T}(s_{i_{j}})\,\cap\,\mathcal{T}(s_{m_{\ell}}), |  |
|-----|------------------------------------------------------------------------|-----|

which denotes shared triplets that link the heads / tail entities in sections. A single triplet may appear in multiple sections if those sections refer to the same entity relationships; or it may connect a head entity in $s_{i_{j}}$ to a tail entity in $s_{m_{\ell}}$.

Report issue for preceding element

##### Navigational Metric.

We define a metric $\mathrm{Nav}(\mathcal{S}^{\prime})$ to capture _average fraction of shared or sequentially linked triplets_ among sections that mention the same ground-truth concepts. Let

Report issue for preceding element

|  | Nav(𝒮′)=1k∑j=1k∑smℓ∈M(sij)|𝒯(sij)∩𝒯(smℓ)|∑smℓ∈M(sij)|𝒯(sij)∪𝒯(smℓ)|.\mathrm{Nav}(\mathcal{S}^{\prime})\;=\;\frac{1}{k}\,\sum_{j=1}^{k}\frac{\sum_{\,s_{m_{\ell}}\in M(s_{i_{j}})}\bigl{|}\mathcal{T}(s_{i_{j}})\,\cap\,\mathcal{T}(s_{m_{\ell}})\bigr{|}}{\sum_{\,s_{m_{\ell}}\in M(s_{i_{j}})}\bigl{|}\mathcal{T}(s_{i_{j}})\,\cup\,\mathcal{T}(s_{m_{\ell}})\bigr{|}}. |  |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|

A higher value indicates stronger overlap (and thus _navigational facility_), suggesting that triplets help the system move seamlessly between related sections.

Report issue for preceding element

By integrating section-level overlap analysis, factual correctness checks, and a triplet interconnection navigation metric, this evaluation framework measures retrieval accuracy, answer precision, and knowledge connectivity - ensuring robust compliance support, domain-specific Q&A, and effective scalability in real-world regulatory settings.

Table 1: Evaluation Results for Section Overlap, Answer Accuracy, and Navigation Metrics

|                  Metric                   |             Without Triplets              |               With Triplets               |
|-------------------------------------------|-------------------------------------------|-------------------------------------------|
| 1. Section Overlap (Similarity Threshold) | 1. Section Overlap (Similarity Threshold) | 1. Section Overlap (Similarity Threshold) |
|                   0.50                    |                  0.0812                   |                  0.0745                   |
|                   0.60                    |                  0.2700                   |                  0.2143                   |
|              0.75 (stricter)              |                  0.1684                   |         0.2888 (highest accuracy)         |
|      2. Answer Accuracy (Scale: 1-5)      |      2. Answer Accuracy (Scale: 1-5)      |      2. Answer Accuracy (Scale: 1-5)      |
|             Average Accuracy              |                   4.71                    |                   4.73                    |
|           3. Navigation Metrics           |           3. Navigation Metrics           |           3. Navigation Metrics           |
|              Average Degree               |       1.2939 (less interconnected)        |       1.6080 (more interconnected)        |
|        Unconnected Sections Linked        |         5014 unconnected section          |          5011 connected sections          |
|            Avg. Shortest Path             |     2.0167 (slower information flow)      |     1.3300 (faster information flow)      |

The table compares system performance with and without triplets across three evaluation criteria: retrieval accuracy (section overlap at varying similarity thresholds), factual correctness of generated answers, and efficiency of navigation through related regulatory sections. Triplets yield highest accuracy at higher threshold. Triplets network significantly enhances connectivity and navigation.

Report issue for preceding element

## 8 Discussion

Throughout this work, we presented a multi-agent system that uses triplet-based knowledge graph construction and retrieval-augmented generation (RAG) to enable transparent, verifiable question-answering on a regulatory corpus. By delegating ingestion, triplet extraction, KG maintenance, and query orchestration to specialized agents, unstructured text becomes a structured data layer for precise retrieval. The synergy of KG and RAG provides high-confidence, explainable facts alongside fluent responses to the large language model, as Section 7 demonstrates through accurate section retrieval, factual correctness and navigational queries (Figure 3). Grounding answers with triplets reduces LLM hallucinations, and provenance links enable robust auditing.

### 8.1 Challenges

Report issue for preceding element

An ontology-free approach facilitates rapid ingestion and incremental refinement but can lead to vocabulary fragmentation; canonicalization and entity resolution \[[GTHS14](https://arxiv.org/html/2508.09893v1#bib.bibx10), [SWLW14](https://arxiv.org/html/2508.09893v1#bib.bibx28)\] help unify concepts, and advanced reasoning tasks may still benefit from partial or emergent schemas \[[RYM13](https://arxiv.org/html/2508.09893v1#bib.bibx25)\]. Extraction quality directly affects the integrity of the KG, as domain-specific jargon or ambiguous references can produce missing or erroneous triples, and deeper inferences or temporal constraints may require additional rule-based or symbolic logic. Large-scale RAG pipelines also require careful optimization for embedding, indexing, and retrieval.

Report issue for preceding element

### 8.2 Future Directions

Report issue for preceding element

Looking ahead, we see multiple avenues for enhancing and extending the system: although our current pipeline supports factual lookups, more complex regulatory questions demand deeper logical reasoning or chaining of evidence, and integration with advanced reasoning LLMs can address multistep analysis and domain-specific inference needs. By including user feedback or expert annotations, we could iteratively refine triplet quality and reduce extraction errors. Active learning or weakly supervised methods may help identify ambiguous relationships, prompting relabeling or model retraining. Over time, such feedback loops would yield higher-precision knowledge graphs. Regulatory corpora often change rapidly (e.g., new guidelines, amendments). We aim to develop _incremental update mechanisms_ that re-ingest altered documents and regenerate only those triples affected by the changes, minimizing downtime and ensuring continuous compliance coverage. Although we focus on _health life science regulatory compliance_, the underlying architecture of multi–agent ingestion, knowledge graph construction, and RAG QA—can be generalized to other domains with high stakes factual queries (e.g., clinical trials, financial regulations, or patent law). Tailoring the extraction logic and graph schema of each agent to domain-specific requirements would enable a larger impact.

Report issue for preceding element

## References

Report issue for preceding element

-   \[A<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24\]↑ Marah Abdin et al. Phi-4 technical report. arXiv preprint, 2024.
-   \[C<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>20\]↑ Xiaojun Chen et al. A review: Knowledge reasoning over knowledge graph. Expert Systems with Applications, 2020.
-   \[C<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24\]↑ Subhankar Chattoraj et al. Semantically rich approach to automating regulations of medical devices. Technical report, UMBC, 2024.
-   \[CBK<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>10\]↑ Andrew Carlson, Justin Betteridge, Bryan Kisiel, Burr Settles, Estevam Hruschka, and Tom Mitchell. Toward an architecture for never-ending language learning. In Proceedings of the 24th AAAI Conference on Artificial Intelligence (AAAI), pages 1306–1313, 2010.
-   \[CDW22\]↑ Joseph J. Cordes, Susan E. Dudley, and Layvon Washington. Regulatory compliance burden. GW Regulatory Studies Center, 2022.
-   \[EFC<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>11\]↑ Oren Etzioni, Anthony Fader, Janara Christensen, Stephen Soderland, and Mausam. Open information extraction: The second generation. In Proceedings of the 22nd International Joint Conference on Artificial Intelligence (IJCAI), pages 3–10, 2011.
-   \[Ers23\]↑ Vladimir Ershov. A case study for compliance as code with graphs and language models. arXiv preprint, 2023.
-   \[FDA25\]↑ FDA. Fda guidance documents. FDA Regulatory Information, 2025.
-   \[FSE14\]↑ Anthony Fader, Stephen Soderland, and Oren Etzioni. Open information extraction for the web. Communications of the ACM, 57(9):80–86, 2014.
-   \[GTHS14\]↑ Luis Galárraga, Christina Teflioudi, Klaus Hose, and Fabio Suchanek. Canonicalizing open knowledge bases. In Proceedings of the 23rd ACM International Conference on Information and Knowledge Management (CIKM), pages 1679–1688, 2014.
-   \[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21\]↑ Aidan Hogan et al. Knowledge graphs. arXiv preprint, 2021.
-   \[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24a\]↑ Joe B. Hakim et al. The need for guardrails with large language models in medical safety-critical settings: An artificial intelligence application in the pharmacovigilance ecosystem. arXiv preprint, 2024.
-   \[H<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24b\]↑ Lars Hillebrand et al. Advancing risk and quality assurance: A rag chatbot for improved regulatory compliance. [https://ieeexplore.ieee.org/document/10825431](https://ieeexplore.ieee.org/document/10825431), 2024.
-   \[HBC<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21\]↑ Aidan Hogan, Eva Blomqvist, Michael Cochez, et al. Knowledge graphs. Synthesis Lectures on Data, Semantics, and Knowledge, 12(2):1–257, 2021.
-   \[HCB24\]↑ Yu Han, Aaron Ceross, and Jeroen Bergmann. More than red tape: exploring complexity in medical device regulatory affairs. BMJ Innovations, 2024.
-   \[J<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24\]↑ Ziwei Ji et al. Survey of hallucination in natural language generation. arXiv preprint, 2024.
-   \[K<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>20\]↑ Vladimir Karpukhin et al. Dense passage retrieval for open-domain question answering. arXiv preprint, 2020.
-   \[KM24\]↑ Jaewoong Kim and Moohong Min. From rag to qa-rag: Integrating generative ai for pharmaceutical regulatory compliance process. arXiv preprint, 2024.
-   \[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>15\]↑ Jens Lehmann et al. Dbpedia – a large-scale, multilingual knowledge base extracted from wikipedia. Semantic Web, 2015.
-   \[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>21\]↑ Patrick Lewis et al. Retrieval-augmented generation for knowledge-intensive nlp tasks. arXiv preprint, 2021.
-   \[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24a\]↑ Jiarui Li et al. Enhancing llm factual accuracy with rag to counter hallucinations: A case study on domain-specific queries in private knowledge-bases. arXiv preprint, 2024.
-   \[L<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24b\]↑ Chen Ling et al. Domain specialization as the key to make large language models disruptive: A comprehensive survey. arXiv preprint, 2024.
-   \[N<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>15\]↑ Maximilian Nickel et al. A review of relational machine learning for knowledge graphs. arXiv preprint, 2015.
-   \[PEK06\]↑ Florian Probst, Sascha Eck, and Werner Kuhn. Scalable semantics: A case study on ontology-driven geographic information integration. International Journal of Geographical Information Science, 20(5):563–583, 2006.
-   \[RYM13\]↑ Sebastian Riedel, Limin Yao, and Andrew McCallum. Relation extraction with matrix factorization and universal schemas. In Proceedings of NAACL-HLT 2013, pages 74–84, 2013.
-   \[SKW07\]↑ Fabian M. Suchanek, Gjergji Kasneci, and Gerhard Weikum. Yago: A core of semantic knowledge unifying Wikipedia and WordNet. Proceedings of the 16th International Conference on World Wide Web, 2007.
-   \[SLB08\]↑ Yoav Shoham and Kevin Leyton-Brown. Multiagent systems: Algorithmic, game-theoretic, and logical foundations. [https://www.eecs.harvard.edu/cs286r/courses/fall08/files/SLB.pdf](https://www.eecs.harvard.edu/cs286r/courses/fall08/files/SLB.pdf), 2008.
-   \[SWLW14\]↑ Wei Shen, Jianyong Wang, Ping Luo, and Min Wang. A survey on entity linking: Methods, techniques, and applications. IEEE Transactions on Knowledge and Data Engineering, 27(2):443–460, 2014.
-   \[Wei00\]↑ Gerhard Weiss. Multiagent systems: A modern approach to distributed artificial intelligence. [https://ieeexplore.ieee.org/book/6267355](https://ieeexplore.ieee.org/book/6267355), 2000.
-   \[Woo09\]↑ Michael Wooldridge. An Introduction to MultiAgent Systems. Wiley, 2009. [https://www.wiley.com/en-be/An+Introduction+to+MultiAgent+Systems%2C+2nd+Edition-p-9780470519462](https://www.wiley.com/en-be/An+Introduction+to+MultiAgent+Systems%2C+2nd+Edition-p-9780470519462).
-   \[WZ24\]↑ Dandan Wang and Shiqing Zhang. Large language models in medical and healthcare fields: applications, advances, and challenges. Artificial Intelligence Review, 2024.
-   \[X<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>25\]↑ Yunfei Xiang et al. Integrating knowledge graph and large language model for safety management regulatory texts. In Lecture Notes in Computer Science, volume 14250, pages 976–988. 2025.
-   \[Y<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24\]↑ An Yang et al. Qwen2.5 technical report. arXiv preprint, 2024.
-   \[Y<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>25\]↑ Rui Yang et al. Retrieval-augmented generation for generative artificial intelligence in health care. npj Digital Medicine, 2025.
-   \[Z<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>13\]↑ Anna Zygmunt et al. Agent-based environment for knowledge integration. arXiv preprint, 2013.
-   \[Z<sup class="ltx_sup"><span class="ltx_text ltx_font_italic">+</span></sup>24\]↑ Tianyang Zhong et al. Evaluation of openai o1: Opportunities and challenges of agi. arXiv preprint, 2024.