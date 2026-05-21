# Legal Requirements Translation from Law

\\UseRawInputEncoding

Anmol Singhal, Travis Breaux

###### Abstract

Report issue for preceding element

Software systems must comply with legal regulations, which is a resource-intensive task, particularly for small organizations and startups lacking dedicated legal expertise. Extracting metadata from regulations to elicit legal requirements for software is a critical step to ensure compliance. However, it is a cumbersome task due to the length and complex nature of legal text. Although prior work has pursued automated methods for extracting structural and semantic metadata from legal text, key limitations remain: they do not consider the interplay and interrelationships among attributes associated with these metadata types, and they rely on manual labeling or heuristic-driven machine learning, which does not generalize well to new documents.

Report issue for preceding element

In this paper, we introduce an approach based on textual entailment and in-context learning for automatically generating a canonical representation of legal text—encodable and executable as Python code. Our representation is instantiated from a manually designed Python class structure that serves as a domain-specific metamodel, capturing both structural and semantic legal metadata and their interrelationships. This design choice reduces the need for large, manually labeled datasets and enhances applicability to unseen legislation. We evaluate our approach on 13 U.S. state data breach notification laws, demonstrating that our generated representations pass approximately 89.4% of test cases and achieve a precision and recall of 82.2 and 88.7 respectively.

Report issue for preceding element

###### Index Terms:

Report issue for preceding element legal requirement translation, textual entailment, in-context learning, metadata extraction, code generation

## I Introduction

Technology companies develop products and services for users across multiple jurisdictions, each governed by distinct legal and regulatory frameworks. Ensuring compliance with diverse legal requirements is critical to avoiding sanctions and other penalties and ensuring uninterrupted operations. However, compliance verification is a resource-intensive process, particularly for small enterprises and startups lacking dedicated, in-house legal expertise. At the foundation of this challenge lies the need to accurately interpret and analyze legal text. Within requirements engineering (RE), structural and semantic metadata extraction from legal text plays an important role in systematically identifying a company’s obligations, supporting traceability, and enabling the transition from regulatory documents to formal models, specifications, and eventually source code and other software artifacts. Structural metadata captures the hierarchical organization of legal provisions, which are often laden with nested statements, intricately inferred dependencies, and cross-references \[[16](https://arxiv.org/html/2507.02846v1#bib.bib16)\]. On the other hand, semantic metadata encapsulates fine-grained attributes such as the entities regulated, deontic modalities assigned to actions, and pre- and post-conditions on actions \[[24](https://arxiv.org/html/2507.02846v1#bib.bib24)\].

While prior work has explored taxonomies of individual metadata types and approaches to extract structural and semantic metadata attributes in isolation \[[24](https://arxiv.org/html/2507.02846v1#bib.bib24)\], a major limitation has been the failure to maintain the contextual relationships between extracted elements, potentially leading to misinterpretation of regulatory obligations. For example, the data breach notification statute in the US State of Maryland (14–3504) consists of multiple layers of sub-rules and interdependencies (see Figure [1](https://arxiv.org/html/2507.02846v1#S1.F1 "Figure 1 ‣ I Introduction ‣ Legal Requirements Translation from Law")) that are necessary for a comprehensive understanding of legal text. Critically, legal meaning often emerges not from individual metadata elements alone, but from the relationships between them—such as how obligations, conditions, and exceptions interact across clauses and sub-sections \[[40](https://arxiv.org/html/2507.02846v1#bib.bib40), [43](https://arxiv.org/html/2507.02846v1#bib.bib43)\]. Furthermore, existing approaches have largely relied on manual annotation or heuristic-driven machine learning (ML), both of which show weak generalization to unseen regulations. These challenges highlight the need for a structured and scalable approach to metadata extraction that not only captures the fine-grained semantics of legal text but also preserves its inherent structure and interdependencies for accurate and context-aware interpretation.

Recent advances in Large Language Models (LLMs) have demonstrated remarkable capabilities across various domains \[[2](https://arxiv.org/html/2507.02846v1#bib.bib2)\]. These models can perform significantly well on complex tasks at inference time using in-context learning, eliminating the need for large labeled datasets for training \[[2](https://arxiv.org/html/2507.02846v1#bib.bib2)\]. Despite emergent properties like Chain-of-Thought \[[7](https://arxiv.org/html/2507.02846v1#bib.bib7)\], LLMs struggle with long-range dependencies \[[8](https://arxiv.org/html/2507.02846v1#bib.bib8), [12](https://arxiv.org/html/2507.02846v1#bib.bib12)\] and logical consistency \[[5](https://arxiv.org/html/2507.02846v1#bib.bib5)\], including those affecting implications \[[6](https://arxiv.org/html/2507.02846v1#bib.bib6)\], negation \[[4](https://arxiv.org/html/2507.02846v1#bib.bib4)\] and transitivity \[[11](https://arxiv.org/html/2507.02846v1#bib.bib11)\], making them unreliable for tasks requiring structured and factual outputs, such as legal compliance. To mitigate these issues, researchers have explored structured prompting techniques that encourage LLMs to generate outputs in predefined formats, such as JavaScript Serializable Object Notation (JSON), Python, or C++, instead of natural language. Prior work suggests that prompting LLMs to generate structured representations can help reduce hallucinations and generate reliable confidence estimates \[[3](https://arxiv.org/html/2507.02846v1#bib.bib3)\]. Moreover, these representations can enforce a defined schema, which eases parsing the output and limits the model’s ability to generate irrelevant information.

In this work, we propose an approach based on LLM code generation to generate a canonical representation of legal text automatically, which can be encoded and executed as a Python program. Our representation is designed to be minimal in complexity yet expressive enough to simultaneously capture the structural and semantic metadata of legal text. The approach consists of three key steps: (1) an iterative method to design a Python class structure for legal metadata representation, (2) a demonstration selection strategy based on textual entailment and cosine similarity to retrieve relevant exemplars for in-context learning, and (3) a code generation prompting technique to generate the encoded representation from a given legal provision. To the best of our knowledge, using a code-based representation to extract metadata elements and represent legal text has not been previously explored.

We evaluate our approach on data breach notification laws from 13 US states. We extracted legal provisions from each law and manually annotated them with our representation to create a benchmark dataset, against which we assess the correctness of our approach. We propose an evaluation method incorporating unit testing and define 21 distinct test cases per sampled provision, each corresponding to a metadata attribute in our representation. We conduct experiments in two settings: (1) k-fold cross-validation on a development set of six state regulations and (2) testing on seven unseen state regulations. The results show that our approach passes 89.4% of the total tests and significantly outperforms baselines.

The main contributions of the paper are as follows:

-   •
    
    We propose a structured, executable representation to capture structural and semantic metadata, and preserve their interrelationships.
    
    Report issue for preceding element
    
-   •
    
    We propose a method based on textual entailment and in-context learning to automatically generate the representation of legal text.
    
    Report issue for preceding element
    
-   •
    
    We propose an evaluation method based on unit testing to assess the correctness of the generated representation.
    
    Report issue for preceding element
    
-   •
    
    We analyze the trade-offs between structured code-based representations and natural language representations for legal metadata extraction.
    
    Report issue for preceding element
    

The remainder of the paper is organized as follows: we present background and related work in Section [II](https://arxiv.org/html/2507.02846v1#S2 "II Background and Related Work ‣ Legal Requirements Translation from Law"); we present our method and approach in Section [III](https://arxiv.org/html/2507.02846v1#S3 "III Method and Approach ‣ Legal Requirements Translation from Law") and our experimental setup in Section [IV](https://arxiv.org/html/2507.02846v1#S4 "IV Experimental Evaluation ‣ Legal Requirements Translation from Law"); we present results in Section [V](https://arxiv.org/html/2507.02846v1#S5 "V Results ‣ Legal Requirements Translation from Law") with discussion in Section [VI](https://arxiv.org/html/2507.02846v1#S6 "VI Discussion ‣ Legal Requirements Translation from Law"), followed by threats to validity in Section [VII](https://arxiv.org/html/2507.02846v1#S7 "VII Threats to Validity ‣ Legal Requirements Translation from Law") and conclusion in Section [VIII](https://arxiv.org/html/2507.02846v1#S8 "VIII Conclusion and Future Work ‣ Legal Requirements Translation from Law").

{mdframed}

\[linewidth=1pt\] 14–3504.  
(d)(1) The notification required under subsections (b) and (c) of this section may be delayed:

-   (i)
    
    If a law enforcement agency determines that the notification will impede a criminal investigation or jeopardize homeland or national security;
    
    Report issue for preceding element
    
-   (ii)
    
    To determine the scope of the breach of the security of a system, identify the individuals affected, or restore the integrity of the system.
    
    Report issue for preceding element
    

(2) If notification is delayed under paragraph (1)(i) of this subsection, notification shall be given as soon as reasonably practicable after the law enforcement agency determines that it will not impede a criminal investigation and will not jeopardize homeland or national security.

Figure 1: Maryland Personal Information Protection Act (§14–3504)

Section   \+ sectionNumber: str \+ sectionTitle: str \+ subSections: Section\[\*\] \+ expressions: Expression\[\*\] \+ statements: Statement\[\*\]   \+ add\_subsection(): void \+ add\_expression(): void \+ add\_statement(): void Expression   \+ text: str \+ includes: Expression\[\*\] Reference   \+ target: Expression or Statement \+ relationship: str Statement   \+ relationships: dict   \+ add\_refines(): void \+ add\_exception(): void \+ add\_follows(): void \+ add\_is\_refined\_by(): void \+ add\_is\_exception\_to(): void \+ add\_is\_followed\_by(): void Rule   \+ rule\_type: int \+ entity: Expression \+ description: Expression \+ conditions: Expression\[\*\] Definition   \+ defined\_term: Expression \+ meaning: Expression\[\*\] \+ exclusions: Expression\[\*\] Information   \+ description: Expression\[\*\] Exemption   \+ description: Expression\[\*\] 0..\*0..\*

Figure 2: UML Class Diagram for Python Code Structure

1s \= Section(sectionNumber\="14-3504.")

2sd \= Section(sectionNumber\="(d)")

3s.add\_subsection(sd)

4sd1 \= Section(sectionNumber\="(1)")

5sd.add\_subsection(sd1)

6r1 \= Rule(sd1, Expression(sd1,

7 "The notification required under subsections (b) and (c) of this section"))

8r1.rule\_type \= Rule.PERMISSION

9r1.description \= Expression(sd1, "may be delayed")

10ref1 \= Reference(sd1, "subsection (b) and (c) of this section", target\=r1)

11r1.add\_is\_exception\_to(ref1)

12

13sd1i \= Section("(i)")

14sd1.add\_subsection(sd1i)

15r1.conditions.append(Expression(sd1i,

16 "a law enforcement agency determines that the notification will impede "

17 "a criminal investigation or jeopardize homeland or national security"))

18

19sd1ii \= Section("(ii)")

20sd1.add\_subsection(sd1ii)

21r1.conditions.append(Expression(sd1ii,

22 "To determine the scope of the breach of the security of a system, "

23 "identify the individuals affected, or restore the integrity of the system"))

24

25sd2 \= Section(sectionNumber\="(2)")

26sd.add\_subsection(sd2)

27r2 \= Rule(sd2, Expression(sd2, "notification"))

28r2.conditions.append(Expression(sd2,

29 "notification is delayed under paragraph (1)(i) of this subsection"))

30r2.rule\_type \= Rule.OBLIGATION

31r2.description \= Expression(sd2,

32 "shall be given as soon as reasonably practicable after the "

33 "law enforcement agency determines that it will not impede a criminal "

34 "investigation and will not jeopardize homeland or national security")

35ref2 \= Reference(sd2, "paragraph (1)(i) of this subsection", target\=r2)

36r2.add\_follows(ref2)

Figure 3: Structured Representation of Section 14–3504 in Code Form

## II Background and Related Work

### II-A Legal Metadata

Regulations and legal provisions dictate obligations, permissions, prohibitions, and constraints that must be adhered to, but their complexity makes manual compliance verification costly and error-prone. Automating compliance verification requires a structured understanding of legal provisions, which is where legal metadata extraction plays a crucial role.

Legal metadata refers to structured information that aids in the interpretation of legal provisions \[[41](https://arxiv.org/html/2507.02846v1#bib.bib41)\]. Within RE, structural and semantic metadata are essential for systematically identifying obligations, supporting traceability, and enabling the transition from regulatory documents to formal specifications.

-   •
    
    Structural metadata captures the hierarchical organization of legal provisions, including sections, sub-sections, cross-references, and dependencies between rules.
    
    Report issue for preceding element
    
-   •
    
    Semantic metadata encapsulates key legal elements such as deontic modalities (obligations, permissions, prohibitions), involved entities, conditions, and references to external provisions.
    
    Report issue for preceding element
    

### II-B Automating Legal Metadata Extraction

#### II-B1 Structural metadata

Report issue for preceding element

Structural metadata is used mainly for establishing traceability to legal provisions  \[[16](https://arxiv.org/html/2507.02846v1#bib.bib16)\], and for performing tasks such as requirements change impact analysis \[[13](https://arxiv.org/html/2507.02846v1#bib.bib13)\] and prioritization \[[18](https://arxiv.org/html/2507.02846v1#bib.bib18), [19](https://arxiv.org/html/2507.02846v1#bib.bib19)\]. Early methods for structural metadata extraction predominantly relied on rule-based systems that encode patterns to identify structural elements in legal texts. Akoma Ntoso \[[20](https://arxiv.org/html/2507.02846v1#bib.bib20)\] is a framework for representing structural metadata in legal texts that defines XML-based tags and mark structural elements such as $<$section$>$, $<$article$>$, $<$clause$>$, and $<$heading$>$. GaiusT \[[22](https://arxiv.org/html/2507.02846v1#bib.bib22)\] employed pattern-based heuristics to identify section markers, references, and clause boundaries in regulatory texts. Recently, ML-based approaches have been proposed for structural metadata analysis. Chalkidis et al. \[[23](https://arxiv.org/html/2507.02846v1#bib.bib23)\] introduced the EURLEX57K dataset to facilitate hierarchical structure identification in European Union legislation.

Report issue for preceding element

#### II-B2 Semantic metadata

Report issue for preceding element

Foundational work in requirements engineering relies on manual or semi-automatic methods for semantic metadata extraction. Breaux et al. \[[1](https://arxiv.org/html/2507.02846v1#bib.bib1)\] tackle the elicitation of rights and permissions following the principles of deontic logic. Massey et al. \[[19](https://arxiv.org/html/2507.02846v1#bib.bib19), [18](https://arxiv.org/html/2507.02846v1#bib.bib18)\] developed an approach to map the terminology of a legal text onto that of a requirements specification. With the rise of ML and NLP in the last decade, research in legal text processing has increasingly applied ML and NLP pipelines to regulations. Bhatia et al.\[[26](https://arxiv.org/html/2507.02846v1#bib.bib26)\] apply constituency and dependency parsing for analyzing privacy policies. Humphreys et al. \[[25](https://arxiv.org/html/2507.02846v1#bib.bib25)\] describe using Semantic Role Labeling to extract who-does-what information from legal texts and fill a legal ontology. Sleimi et al. \[[24](https://arxiv.org/html/2507.02846v1#bib.bib24)\] proposed a harmonized view of semantic metadata in RE and used a hybrid approach involving NLP and heuristic-based ML to automatically extract semantic metadata from legal text. Amaral et al.\[[28](https://arxiv.org/html/2507.02846v1#bib.bib28)\] developed an NLP-based approach that uses semantic frames to check a Data Processing Agreement (DPA) against GDPR obligations.

Report issue for preceding element

#### II-B3 Limitations of Existing Work

While the proposed methods in prior work have contributed significantly to the field, they suffer from key limitations:

-   •
    
    Losing Relationship between Structural and Semantic Metadata: Most existing techniques extract metadata elements as independent fragments, often failing to maintain the hierarchical and logical relationships within legal provisions. For example, in Maryland’s Data Breach Notification Law (14–3504), different rules are interdependent. Extracting a single rule present in section (d)(2) in Figure [1](https://arxiv.org/html/2507.02846v1#S1.F1 "Figure 1 ‣ I Introduction ‣ Legal Requirements Translation from Law") without preserving its link to the preceding statement in section (d)(1) can lead to misinterpretations.
    
    Report issue for preceding element
    
-   •
    
    Scalability Challenges: Heuristic-based methods require extensive manual effort in designing extraction patterns and do not generalize well to new or unseen regulations. ML-based approaches often require large annotated datasets, which are expensive to create and maintain.
    
    Report issue for preceding element
    
-   •
    
    Inability to Generate Actionable Representations: Extracting metadata alone is not enough for compliance automation. There is a need for representations that encapsulate metadata in a structured format, allowing it to be used in downstream compliance verification tasks.
    
    Report issue for preceding element
    

### II-C Code-based Representation

Given the challenges of legal text complexity, scalability, and reliability, our approach is based on textual entailment to generate a canonical, executable representation of legal provisions as Python code. Specifically, the generated code instantiates a manually constructed Python class hierarchy—i.e., a domain metamodel—that encodes structural and semantic metadata attributes relevant to legal requirements. We leverage in-context learning, a technique that uses examples within a prompt to train LLMs how to perform tasks at inference time.

In recent years, several prompting techniques have been explored to use general LLMs for producing high-quality code, including zero-shot, few-shot, Chain-of-Thought (CoT), and self reflection \[[29](https://arxiv.org/html/2507.02846v1#bib.bib29)\]. LLMs pre-trained on code (Code-LLMs), such as OpenAI’s CodeX \[[32](https://arxiv.org/html/2507.02846v1#bib.bib32)\] and DeepMind’s AlphaCode \[[31](https://arxiv.org/html/2507.02846v1#bib.bib31)\], enable software engineers to automatically generate functions and sub-routines. A key benefit of using code LLMs is their ability to express natural language constraints for the desired functionalities that engineers want in their generated code \[[33](https://arxiv.org/html/2507.02846v1#bib.bib33), [34](https://arxiv.org/html/2507.02846v1#bib.bib34)\]. In addition to these natural language prompts, existing work has looked at directly providing code snippets as input to the model with an accompanying declarative instruction \[[35](https://arxiv.org/html/2507.02846v1#bib.bib35)\]. A recent prompting trend for code generation is to explicitly separate the problem-solving plan from the coding. Li et al. \[[30](https://arxiv.org/html/2507.02846v1#bib.bib30)\] proposed a method named structured CoT, based on using structured reasoning steps before outputting the final code. Another approach, called PAL \[[36](https://arxiv.org/html/2507.02846v1#bib.bib36)\] (Program-Aided Language models), has the model output a piece of code (e.g. in Python) that, when executed, produces the answer to a problem. The success of PAL shows that asking the model to generate code as an intermediate step to solve a task can be useful for tasks that require deterministic model outputs.

Our approach extends this idea of structured code representations to legal text, which, while more formalized than natural language, presents unique challenges such as nested dependencies, deontic modalities, and inter-paragraph references. In this work, we study the effectiveness of code generation to represent the relationships between structural and semantic metadata in legal text. Our approach offers several advantages:

-   •
    
    Preserves Structural and Semantic Metadata: By encoding legal text as Python code, we retain the hierarchical organization and dependencies between legal rules.
    
    Report issue for preceding element
    
-   •
    
    Enhances Generalization Across Regulations: Unlike heuristic-based methods, prompting LLMs to generate code dynamically adapts to different legal texts, improving generalizability to new jurisdictions and unseen laws.
    
    Report issue for preceding element
    
-   •
    
    Actionable Representation of Legal Requirements: Our representation can be executed by a Python interpreter, making it flexible to build custom visualizations of a legal provision for analysis, including representing relevant information as a knowledge graph.
    
    Report issue for preceding element
    

Importantly, we do not treat code translation as a method for semantic paraphrasing of the entire legal document. Instead, we define a canonical intermediate representation—formally specified via Python classes—that captures specific, pre-defined legal constructs (e.g., rules, references, conditions). This design parallels how code generation tasks restrict output to a constrained syntax to improve reliability \[[36](https://arxiv.org/html/2507.02846v1#bib.bib36)\].

## III Method and Approach

Our research method consists of three key steps: (1) discovering a Python class structure that encodes legal metadata; (2) developing a demonstration selection strategy using textual entailment and cosine similarity to retrieve relevant exemplars for in-context learning; and (3) designing a code generation prompt to generate structured legal encodings. The following sections detail the dataset creation and each step in the method.

### III-A Legal Rule Code Corpus

We selected 13 data breach notification laws from various U.S. states that govern the protection of residents’ personal information. Our selection process followed the methodology described in \[[16](https://arxiv.org/html/2507.02846v1#bib.bib16)\], with the exception that we replaced the Alaska (AK) and Massachusetts (MA-S) laws included in their set with the California (CA) and Virginia (VA) laws. This change reflects the significant privacy law amendments enacted in California and Virginia over the past decade.

This dataset provides breadth in how laws are written while controlling for key criteria: every law is in English, follows the same legal system (Common Law), and addresses the same societal problem — under what conditions companies must notify data subjects about a breach of their personal information. While these regulations address the same theme, they vary in length, organization, and how they define legal entities and conditions for permitted, required, and prohibited actions. In distributed systems spanning these jurisdictions, such variations require businesses to decide how to comply. The selected laws are:

-   •
    
    Arkansas (AR): Personal Information Protection Act, Arkansas Code §§ 4-110-101 et seq., enacted 2005.
    
    Report issue for preceding element
    
-   •
    
    Connecticut (CT): CT: Breach of Security Regarding Computerized Data Containing Personal Information, Connecticut General Statute 36a-701b, enacted 2006.
    
    Report issue for preceding element
    
-   •
    
    Massachusetts (MA): Security Breach Law, Massachusetts General Laws Chapter 93H, enacted 2007.
    
    Report issue for preceding element
    
-   •
    
    Maryland (MD): Maryland Personal Information Protection Act, §§ 14-3501 et seq., enacted 2008.
    
    Report issue for preceding element
    
-   •
    
    Mississippi (MS): Mississippi Consumer Data Privacy Act, Mississippi Code Annotated, §§ 75-24-29, enacted 2011.
    
    Report issue for preceding element
    
-   •
    
    Nevada (NV): Security of Personal Information Law, Nevada Revised Statutes Chapter 603A, enacted 2006.
    
    Report issue for preceding element
    
-   •
    
    New York (NY): Information Security Breach and Notification Act, New York General Business Law § 899-aa, enacted 2005.
    
    Report issue for preceding element
    
-   •
    
    Oregon (OR): Oregon Consumer Identity Theft Protection Act, Oregon Revised Statutes §§ 646A.600–628, enacted 2007.
    
    Report issue for preceding element
    
-   •
    
    Utah (UT): Protection of Personal Information Act, Utah Code §§ 13-44-101 et seq., enacted 2006.
    
    Report issue for preceding element
    
-   •
    
    Wisconsin (WI): Notice of Unauthorized Acquisition of Personal Information, Wisconsin Statutes § 134.98, enacted 2006.
    
    Report issue for preceding element
    
-   •
    
    California (CA): California Data Breach Notification Law, California Civil Code § 1798.82, enacted 2002.
    
    Report issue for preceding element
    
-   •
    
    Virginia (VA): Breach of Personal Information Notification Act, Virginia Code § 18.2-186.6, enacted 2008.
    
    Report issue for preceding element
    
-   •
    
    Vermont (VT): Security Breach Notice Act, Vermont Statutes Annotated, Title 9, § 2435, enacted 2006.
    
    Report issue for preceding element
    

To construct our dataset, we used regular expressions to extract paragraphs from each legal document. Each paragraph can entail one or more legal statements that are related to one another and represent a legal requirement. We manually corrected any inconsistencies resulting from special characters, inconsistent punctuation, and other lexical errors. After the cleaning process, we obtained a total of 332 legal paragraphs.

### III-B Creating the Python Class Structure

Report issue for preceding element

We conceptualize the legal translation task as generating an instance of a formal metamodel tailored for regulatory texts. This metamodel is realized as a Python class structure designed to encode essential metadata types (e.g., rules, definitions, conditions) and their interrelationships (e.g., exceptions, refinements, follow-ups). Each generated legal translation is thus an instantiation of this metamodel, where class objects and their attributes capture the content of legal paragraphs.

Report issue for preceding element

The first author applied open coding \[[14](https://arxiv.org/html/2507.02846v1#bib.bib14)\] to the corpus of legal paragraphs described in Section [III-A](https://arxiv.org/html/2507.02846v1#S3.SS1 "III-A Legal Rule Code Corpus ‣ III Method and Approach ‣ Legal Requirements Translation from Law") to identify metadata attributes, yielding a coding frame consisting of 17 labels and corresponding definitions shown in Table [I](https://arxiv.org/html/2507.02846v1#S3.T1 "TABLE I ‣ III-B Creating the Python Class Structure ‣ III Method and Approach ‣ Legal Requirements Translation from Law"). This analysis began by assigning labels from existing taxonomies \[[13](https://arxiv.org/html/2507.02846v1#bib.bib13), [16](https://arxiv.org/html/2507.02846v1#bib.bib16)\] to phrases in the legal text. While these taxonomies define several fine-grained semantic metadata attributes, we focused on those that occurred most frequently in our dataset. For example, in the excerpt depicted in Figure [1](https://arxiv.org/html/2507.02846v1#S1.F1 "Figure 1 ‣ I Introduction ‣ Legal Requirements Translation from Law"), the author identified the following labels: section, subsection, obligation, continuation, condition, reference, entity, and description. The coding frame was updated whenever the author encountered a new phrase without a proper label or if an existing definition required modification to cover the new phrase. The coding process continued until saturation was reached, which occurred when the author coded 150 paragraphs corresponding to seven laws without identifying new labels in the remaining 182 paragraphs.

Report issue for preceding element

TABLE I: Coding Frame with Labels and Definitions

|   Tag Name    |                                                                Description                                                                |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------|
|  #definition  |                                            A legal statement defining the meaning of concepts                                             |
|  #exclusion   |                                   A phrase highlighting what is excluded from the definition of a term                                    |
|  #exemption   |                                       A legal statement that exempts someone/something from a rule                                        |
|  #obligation  |                                     A statement imposing mandatory action to be performed by an agent                                     |
|  #permission  |                    A statement indicating the possibility to perform an action without an obligation or a prohibition                     |
| #prohibition  |                                         A statement forbidding an action to happen or take place                                          |
|   #penalty    |                                      A statement indicating the punishment for not following a rule                                       |
| #information  |                                   A legal statement about something that is known or proved to be true                                    |
| #continuation |              Denoting nested legal statements; assigned whenever a phrase contains a colon and is followed by a bullet list               |
|  #condition   |                               A phrase in a statement highlighting a constraint under which a rule applies                                |
|   #follows    |        Relation that connects a statement to references or other statements that precede (act as pre-conditions to) the statement         |
|   #refines    | Relation that connects a statement that provides more information about a reference or base statement to the reference or base statement  |
| #followed_by  |                      Relation that connects a statement to references or other statements that follow the statement                       |
|  #refined_by  | Relation that connects a base statement to a cross-reference or another statement that provides more information about the base statement |
|  #exception   |                 Relation that connects a statement to references or other statements that are exceptions to the statement                 |
| #exception_to |    Relation that connects a statement that acts as an exception to a reference or base statement with the reference or base statement     |
|  #reference   |                         When the text contains pointers, numbers, or names to other sections, paragraphs, or laws                         |

Report issue for preceding element

After coding the dataset, the authors analyzed each label and the relationships among labels to identify classes and attributes. For example, obligations, permissions, prohibitions, and penalties were deemed as different kinds of rules. In addition, it was observed that these varieties have relationships to similar components represented in the text, such as entities who are the subject of the required or permitted action and conditions that must be true before the entity is required, permitted, or prohibited to perform the action. These observations led to the introduction of a Rule class with class attributes to include the rule\_type, entity and a Python list of conditions. Additionally, during the open coding exercise, the authors observed that exemption statements may not directly refer to or address specific entities, unlike rules. Consequently, exemption statements were mapped to a class separate from the Rule class.

Report issue for preceding element

The paragraph structure of legal text often includes sentences that begin in one section and finish in another, complicating the translation of legal rules into data structures while preserving fine-traceability of which phrases come from which sections. To address this, a distinction was introduced with the Expressions and Statement classes. The Expression class encodes text within a legal paragraph, the smallest textual unit. Conversely, the Statement class can span multiple legal paragraphs if those paragraphs are nested under a larger one (i.e., the term continuation has been previously used for this arrangement). Finally, paragraphs and the outer sections that contain them are organized hierarchically using the Section class.

Report issue for preceding element

The final Python class structure is depicted in Figure [2](https://arxiv.org/html/2507.02846v1#S1.F2 "Figure 2 ‣ I Introduction ‣ Legal Requirements Translation from Law"). Docstrings were included to explain each class attribute, method, and data type. Based on the class diagram, the encoded representation for the Maryland statute is illustrated in Figure [3](https://arxiv.org/html/2507.02846v1#S1.F3 "Figure 3 ‣ I Introduction ‣ Legal Requirements Translation from Law"). It demonstrates how the labels and legal text are aligned to yield the Python code as a translation of the law.

Report issue for preceding element

### III-C Demonstration Selection

Report issue for preceding element

In-context learning with LLMs improves with demonstrations or examples that are added to the input prompt \[[9](https://arxiv.org/html/2507.02846v1#bib.bib9), [17](https://arxiv.org/html/2507.02846v1#bib.bib17)\]. To create a dataset of demonstrations, the first author manually translated the dataset of legal provisions into the corresponding Python class structure. The author executed each code translation using a Python interpreter to ensure the syntactic correctness of the ground truth code. Due to the manual translation effort, the author required two weeks to complete the process and yield 332 legal text translations. On average, this involved approximately five minutes per paragraph to write and verify the code.

Report issue for preceding element

We partitioned the labeled dataset into a development set comprising of 150 paragraphs that were translated before reaching saturation and a test set consisting of the remaining 182 paragraphs, corresponding to six laws. We utilized the development set to sample demonstrations for in-context learning. The test set was used to evaluate our method. We have made the development and test sets publicly available.

Report issue for preceding element

LLMs can exhibit strong performance improvements with just one demonstration on specific applications. In our experience, dependencies in translating legal text through legal metadata into Python are highly contextual, i.e., the presence or absence of one metadatum could change whether a later metadatum is expected (e.g., when a conditional phrase signals a subsequent rule but not a definition). In contrast, a multinomial labeling exercise that outputs one of a few labels is easier to demonstrate by sampling demonstrations across the labeling space. To address this challenge, we first use a zero-shot prompt to assign labels to a legal text paragraph drawn from the test set that needs to be translated. In Figure [4](https://arxiv.org/html/2507.02846v1#S3.F4 "Figure 4 ‣ III-C Demonstration Selection ‣ III Method and Approach ‣ Legal Requirements Translation from Law"), we show the prompt, which includes a task explanation, a dictionary of possible labels with definitions, the required output format, and an instruction to avoid generating explanations.

Report issue for preceding element

| Read the text and assign tags based on the definitions provided. Do not create your own tags. |
|-----------------------------------------------------------------------------------------------|
|                      Only output the tags in the form of a python list.                       |
|                Do not include the assigned parts of the text in your response.                |
|           Tag Definitions: Python Dictionary containing tags and their definitions            |
|                                          Text: input                                          |

Figure 4: Prompt to Label Legal Text

Report issue for preceding element

After generating labels for the input text paragraph, we retrieve demonstrations from the development set with the highest score, assigning one point for each matching label. From this list, we select three demonstrations with the highest cosine similarity score to the input text paragraph using the OpenAI text-embedding-3-large model. This demonstration selection method is motivated by the observation that high similarity scores are often correlated with legal text paragraphs sharing common labels. For example, two paragraphs defining “personal information” using the keyword “means” will typically yield a high similarity score, and both will be labeled as #definition. We repeat this process for each legal text paragraph in the test set.

Report issue for preceding element

### III-D Legal Text Translation Task

Report issue for preceding element

We used GPT-4o, a closed-source LLM by OpenAI, to translate the input legal text paragraph into Python code. The translation prompt (see Figure [5](https://arxiv.org/html/2507.02846v1#S3.F5 "Figure 5 ‣ III-D Legal Text Translation Task ‣ III Method and Approach ‣ Legal Requirements Translation from Law")) includes a minimal instruction, the Python class definitions described in Section [III-B](https://arxiv.org/html/2507.02846v1#S3.SS2 "III-B Creating the Python Class Structure ‣ III Method and Approach ‣ Legal Requirements Translation from Law"), and the demonstrations describing example translations from legal text into Python that were selected using the strategy described in Section [III-C](https://arxiv.org/html/2507.02846v1#S3.SS3 "III-C Demonstration Selection ‣ III Method and Approach ‣ Legal Requirements Translation from Law"). The instruction explicitly discourages classes or class attributes not shown in the structure. Owing to the deterministic nature of the translation task, we set a temperature parameter 0.5 for our experiments.

Report issue for preceding element

| Read the text and convert it to Python code. Use the class structure detailed below to write code. Do not create your own names. Examples have been provided. |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                                             Class Structure: Python class structure enclosed in triple back-ticks                                             |
|                                                          Examples: the three sampled demonstrations                                                           |
|                                                                          Text: input                                                                          |

Figure 5: Prompt to Translate Legal Text into Python

Report issue for preceding element

## IV Experimental Evaluation

We evaluate the approach by answering the following research questions (RQs):

-   •
    
    RQ1: How accurate is the generated Python code?
    
    Report issue for preceding element
    
-   •
    
    RQ2: How does the method compare to traditional LLM text extraction using JSON?
    
    Report issue for preceding element
    
-   •
    
    RQ3: To what extent do the method steps contribute to overall performance improvement?
    
    Report issue for preceding element
    
-   •
    
    RQ4: To what extent does the method generalize to unseen legal texts?
    
    Report issue for preceding element
    
-   •
    
    RQ5: What are the sources of error in the steps within the method?
    
    Report issue for preceding element
    

We now describe the development of our evaluation strategy by first introducing our use of unit tests to score the generated Python code, followed by the metrics used to compute scores, before describing the two methods for evaluation.

### IV-A Unit Testing-based Evaluation

Translating legal text into code provides the benefit that the generated representation can be analyzed programmatically using traditional test harnesses. In our case, we adopt a unit testing framework to perform _model conformance checks_, i.e., verifying whether the generated code correctly instantiates the expected legal metadata structure and semantics.

Although unit tests are typically associated with verifying execution behavior, we use them to validate that each generated code instance conforms to the manually defined Python class structure (described in Section [III-B](https://arxiv.org/html/2507.02846v1#S3.SS2 "III-B Creating the Python Class Structure ‣ III Method and Approach ‣ Legal Requirements Translation from Law")) and matches ground truth attribute values.

Our evaluation proceeds in three steps. First, we manually author test cases for each attribute defined in the class structure. Then, we generate the Python code for a legal paragraph (see Figure [5](https://arxiv.org/html/2507.02846v1#S3.F5 "Figure 5 ‣ III-D Legal Text Translation Task ‣ III Method and Approach ‣ Legal Requirements Translation from Law")), execute it using the Python interpreter, and serialize the resulting instantiated objects. Finally, we run the test cases on the serialized objects to compare each generated attribute value with the corresponding value in the ground truth. Thus, each test validates a specific structural or semantic property of the instance.

We designed three categories of tests:

-   •
    
    Compilation Test: This test verifies whether the generated code is syntactically correct with respect to the predefined class structure. The code passes this test if it executes without errors in the Python interpreter. Failures typically arise from hallucinations, for example, references to undefined classes, methods, or attribute names.
    
    Report issue for preceding element
    
-   •
    
    Structural Tests: These tests check if each generated class has the expected minimal attributes (e.g., a Definition must contain a term, regardless of the value assigned). The list of attributes is shown in Table [I](https://arxiv.org/html/2507.02846v1#S3.T1 "TABLE I ‣ III-B Creating the Python Class Structure ‣ III Method and Approach ‣ Legal Requirements Translation from Law"). Structural tests are paragraph-independent and include five tests.
    
    Report issue for preceding element
    
-   •
    
    Semantic Tests: These tests verify whether the attribute values generated for each paragraph semantically match those of the ground truth. We used an exact match comparison after normalizing the strings (lowercase, stop-word removal, and punctuation stripping). For example, words such as “means” or “if” are removed before comparison. Semantic tests include 16 paragraph-independent checks. An example of a semantic unit test to identify the correct references in the legal excerpt in [1](https://arxiv.org/html/2507.02846v1#S1.F1 "Figure 1 ‣ I Introduction ‣ Legal Requirements Translation from Law") will check if the objects of class Reference are initialized with the same values in the generated and ground truth code (subsections (b) and (c), paragraph (1)(i) in this case).
    
    Report issue for preceding element
    

Each generated paragraph is evaluated using this suite of 22 tests: one compilation test, five structural tests, and sixteen semantic tests. A paragraph-level output is considered fully correct only if all 22 tests pass. Although implemented using a unit testing framework, the purpose of these tests is to validate the conformance of the generated code to a well-defined and interpretable metamodel, rather than to test the functional execution or control flow behavior.

### IV-B Evaluation Metrics

We computed the following metrics for each paragraph in our development and test sets:

-   •
    
    Overall accuracy: The number of tests passed divided by the total number of tests executed.
    
    Report issue for preceding element
    
-   •
    
    Attribute Precision: The number of semantic tests passed where the attribute in the generated code was present in the ground truth code divided by the total number of semantic tests where the attribute was present in the generated code.
    
    Report issue for preceding element
    
-   •
    
    Attribute Recall: The number of semantic tests passed where the attribute in the generated code was present in the ground truth code divided by the total number of semantic tests where the attribute was present in the ground truth code.
    
    Report issue for preceding element
    

We report average scores at the paragraph level and attribute level in the results in Section [V](https://arxiv.org/html/2507.02846v1#S5 "V Results ‣ Legal Requirements Translation from Law").

In addition to the above tests, we compute pass@k \[[15](https://arxiv.org/html/2507.02846v1#bib.bib15)\], a standard metric used in the evaluation of generative code tasks. This metric is particularly relevant for LLM-based code generation, where sampling is non-deterministic, meaning that the same prompt can yield different outputs across multiple runs. Pass@k asks whether any of the $k$ sampled generations yields a completely correct code translation, i.e., one that passes all unit tests for that paragraph.

Pass@k is important to account for stochasticity in LLM outputs and better reflects real-world use cases where multiple samples can be taken to increase reliability. For example, even if a single generation is imperfect, users might run the model multiple times to obtain a valid solution.

Precision and recall are computed for attributes that are present in both the generated and ground truth code. These metrics provide insight into the partial correctness of the outputs, which is useful for debugging specific failures and identifying attribute types that are more difficult to generate. However, they do not reflect whether an entire output is usable or not. Accuracy measures the proportion of tests passed across all test cases and paragraphs but similarly does not capture whether a complete, semantically accurate representation has been generated for each paragraph. Therefore, we report both standard metrics (precision, recall, accuracy) and pass@k score to give a more holistic picture of the correctness and practical usability of the method.

To measure pass@k, we test whether the generated code passes all the 21 syntactic and semantic test cases, i.e., that the model output correctly generates all the attributes present in a paragraph within $k$ prompt executions. The pass@k score is computed by generating $n$ code solutions per paragraph, where $n$ must be greater than or equal to $k$. Let $c$ be the number of solutions that pass all unit tests, where $c$ is less than or equal to $n$. The pass@k score is calculated using the following equation:

-   •
    
    $n$ is the number of coding solutions;
    
    Report issue for preceding element
    
-   •
    
    $c$ is the number of solutions that passed all unit tests out of $n$;
    
    Report issue for preceding element
    
-   •
    
    $k$ is the number of $k$ combinations selected from $n$;
    
    Report issue for preceding element
    
-   •
    
    $comb(n-c,k)$ is the number of $k$ combinations that fail to pass the unit test, chosen from $n$;
    
    Report issue for preceding element
    
-   •
    
    The fraction $comb(n-c,k)/comb(n,k)$ represents the probability that all $k$ generated solutions fail the unit test.
    
    Report issue for preceding element
    

|  | pass@k=E(1−(comb(n−c,k)/comb(n,k))pass@k=E(1-(comb(n-c,k)/comb(n,k))\\ italic_p italic_a italic_s italic_s @ italic_k = italic_E ( 1 - ( italic_c italic_o italic_m italic_b ( italic_n - italic_c , italic_k ) / italic_c italic_o italic_m italic_b ( italic_n , italic_k ) ) |  | (1) |
|-----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|-----|

We compute pass@k by varying the value of $k$ from one to five. We assumed that the values of $k$ and $n$ are equal, meaning that we sample $k$ model outputs per paragraph in the dataset. We report the paragraph-level metrics for the samples that passed the maximum number of test cases.

### IV-C Evaluation Strategy

The evaluation strategy consists of two evaluation methods:

-   •
    
    Five-Fold Cross Validation on Development Set: Because the translation of legal text to code can yield inconsistencies in the expected output that are sensitive to the prompt design and the class structure, we chose to fully employ the development set to refine the prompts and class structure. We divided the development set into five folds through random sampling, and for five iterations, four folds (amounting to 120 paragraphs in our dataset) served as the demonstration sampling dataset, while one held-out fold (consisting of 30 paragraphs) served as the test set to obtain model output. We report the average scores obtained across all five folds to answer RQ1.
    
    Report issue for preceding element
    
-   •
    
    Document-Level Evaluation on Test Set: We evaluate the documents in the test set individually and compute scores for each document separately to address RQ2. We report both the cumulative average scores obtained across documents in the test set.
    
    Report issue for preceding element
    

We answer RQ1 by computing the metrics in Section [IV-B](https://arxiv.org/html/2507.02846v1#S4.SS2 "IV-B Evaluation Metrics ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law") for the development and test set. We report the results for RQ2, RQ3, and RQ4 on the test set. To the best of our knowledge, no prior work has evaluated code-generation models on the task of translating legal text into structured representations. As such, we cannot directly compare our results for RQ2 to those of existing techniques on this task. Therefore, to answer RQ2, we run a baseline prompt (see Figure [6](https://arxiv.org/html/2507.02846v1#S4.F6 "Figure 6 ‣ IV-C Evaluation Strategy ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law")) in which we instruct the model to assign values to each attribute using a JSON schema. We provide the model with the definitions of each attribute and specify the input and output format. The model output is serialized into a dictionary and compared with the serialized ground truth code.

| Read the provided text and identify the portion of text that corresponds to each attribute explained below. If the text does not contain a specific attribute, ignore it and move to the next one. Include all the parameters for each attribute in your response. The output should be in the form of a JSON list. An example has been provided. |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                                                                                                                                                              Attribute Definitions:                                                                                                                                                               |
|                                                                                                                                                               Attribute Parameters:                                                                                                                                                               |
|                                                                                                                                                                     Example:                                                                                                                                                                      |
|                                                                                                                                                                    Text: input                                                                                                                                                                    |

Figure 6: Baseline Prompt for Direct Attribute Extraction

TABLE II: Evaluation Results for Different Approaches

| Dataset |         Approach         | Compilation Test | Structural Test | Semantic Test | Semantic Test | Semantic Test | Pass@3 |
|---------|--------------------------|------------------|-----------------|---------------|---------------|---------------|--------|
|         |                          |                  |    Accuracy     |   Precision   |    Recall     |               |        |
|  Test   | Text-gen (JSON baseline) |        NA        |      54.2%      |     72.1%     |     68.5%     |     61.0%     | 31.2%  |
|  Test   |     Code-gen + class     |      98.5%       |      75.0%      |     83.7%     |     80.4%     |     67.4%     | 38.0%  |
|  Test   |     Code-gen + demo      |      85.7%       |      82.8%      |     82.0%     |     73.8%     |     72.8%     | 42.1%  |
|   Dev   | Code-gen + class + demo  |      98.4%       |      83.4%      |     86.9%     |     79.1%     |     85.3%     | 56.7%  |
|  Test   | Code-gen + class + demo  |      99.2%       |      82.0%      |     89.4%     |     82.2%     |     88.7%     | 62.1%  |

We answer RQ3 by conducting two ablation studies:

-   •
    
    Class Structure: We compare our approach with a baseline in which we remove the class structure as context from the prompt and instructed the model to convert the text to code only on the basis of the demonstrations.
    
    Report issue for preceding element
    
-   •
    
    Demonstration Selection: We compare our approach to a baseline in which we replace the demonstration selection strategy with a keyword-based approach to select examples to prompt the LLM. The keywords represent frequently occurring phrases in the text that could trigger the assignment of a label. For example, ‘if’ and ‘whether’ are keywords for assigning the #condition label.
    
    Report issue for preceding element
    

## V Results

Report issue for preceding element

Table [II](https://arxiv.org/html/2507.02846v1#S4.T2 "TABLE II ‣ IV-C Evaluation Strategy ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law") presents the overall accuracy, precision, recall and pass@$k=3$ results: the Approach column includes the Code-gen + class + demo study, which is the end-to-end study providing the class structure and demonstration strategy to select demonstrations; the Text-gen study evaluates the traditional LLM-based text extraction of the attributes using a JSON schema; the Code-gen + demo study is the first ablation study in which the the class structure is removed, and the Code-gen + class study is the second ablation study in which the class structure is presented, but the demonstrations are randomly sampled, ignoring the selection strategy.

Report issue for preceding element

The RQ1 asks “how accurate is the generated Python code structure?”. In Table [II](https://arxiv.org/html/2507.02846v1#S4.T2 "TABLE II ‣ IV-C Evaluation Strategy ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law"), we see that the attribute-level accuracy, precision, and recall are all highest for the complete method, and outperform the Text-gen approach by a margin of 30% on the pass@k score. This result also answers RQ2, which asks “How does the method compare to traditional LLM text extraction using JSON?”. The ablation results in Table [II](https://arxiv.org/html/2507.02846v1#S4.T2 "TABLE II ‣ IV-C Evaluation Strategy ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law") show that the end-to-end method benefits from all of its features, including the class structure and demonstration strategy, in response to RQ3 that asks “To what extent do the method steps contribute to overall performance improvement?”.

Report issue for preceding element

The pass@k score trend, which denotes the number of paragraphs in the data set that passed all test cases in $k$ attempts is reported in Figure [7](https://arxiv.org/html/2507.02846v1#S5.F7 "Figure 7 ‣ V Results ‣ Legal Requirements Translation from Law"). For only one generation per paragraph, GPT-4o yields a pass@1 score of 40%. The score improves significantly as we increase the value of $k$ to $k=3$, and only marginally improves for $k>3$.

Report issue for preceding element

For $k=3$, our approach demonstrates a high accuracy across compilation, structural, and semantic tests on both the development and test sets (Table [II](https://arxiv.org/html/2507.02846v1#S4.T2 "TABLE II ‣ IV-C Evaluation Strategy ‣ IV Experimental Evaluation ‣ Legal Requirements Translation from Law")). The compilation test reported a near-perfect score, which shows that GPT-4o reliably generates executable Python code based on the class structure. The structural test and semantic test accuracy of approximately 90% on the total tests conducted shows that our approach generates a representation that closely resembles the ground truth representation. The recall is slightly lower than the precision. The error analysis is reported in Section [VI](https://arxiv.org/html/2507.02846v1#S6 "VI Discussion ‣ Legal Requirements Translation from Law").

Report issue for preceding element

![Refer to caption](https://arxiv.org/html/2507.02846v1/x1.png)

Figure 7: Pass@k score trend on the test set

Report issue for preceding element

The pass@3 score was approximately 56.7% and 62.1% on the development and test sets, respectively. These scores indicate that while the generated code matched the ground truth for most attributes, a few attributes demonstrated a higher failure rate, lowering the overall correctness of the model output. We discuss the implications of these findings in Section [VI](https://arxiv.org/html/2507.02846v1#S6 "VI Discussion ‣ Legal Requirements Translation from Law").

Report issue for preceding element

TABLE III: Results For Each Attribute

|       Attribute       | Accuracy | Precision | Recall |
|-----------------------|----------|-----------|--------|
|      Information      |  96.9%   |   50.0%   | 25.0%  |
|    Definition term    |  97.6%   |   100%    | 93.4%  |
|  Definition meaning   |  95.2%   |   100%    | 92.8%  |
| Definition exclusions |  97.6%   |   50.0%   | 50.0%  |
|       Exemption       |  85.9%   |   37.5%   | 37.5%  |
|      Rule Entity      |  86.6%   |   85.3%   | 94.4%  |
|   Rule Description    |  78.7%   |   78.8%   | 93.7%  |
|    Rule Condition     |  78.7%   |   87.5%   | 83.3%  |
|       Rule Type       |  89.0%   |   86.1%   | 94.4%  |
|      References       |  74.8%   |   58.3%   |  100%  |
|   Relationship type   |  85.0%   |   33.1%   | 45.8%  |
|    No. of sections    |  93.0%   |   91.5%   | 92.5%  |
|  No. of subsections   |  87.0%   |   85.0%   | 86.0%  |
|   No. of statements   |  89.0%   |   87.5%   | 88.0%  |
|  No. of expressions   |  84.5%   |   81.0%   | 82.5%  |
|    Section naming     |  91.0%   |   88.0%   | 89.5%  |

Report issue for preceding element

RQ4 asks “To what extent does the method generalize to unseen legal texts?” Across six legal texts held out in the test set, we observe that the method performed better than the development set by +6% on the pass@3 metric. The increase could be attributed to our design choice, where a higher number of legal paragraphs were used to sample demonstrations on the test set (150 paragraphs) than the validation set (120 paragraphs). We further discuss this finding in Section [VI](https://arxiv.org/html/2507.02846v1#S6 "VI Discussion ‣ Legal Requirements Translation from Law").

Report issue for preceding element

We also compare the test set results for each attribute in the dataset in [III](https://arxiv.org/html/2507.02846v1#S5.T3 "TABLE III ‣ V Results ‣ Legal Requirements Translation from Law"). We report the aggregate score for relationship type by averaging the individual scores for each of the six types of relationship we observed in the dataset. The method performed best across definitions and the number of section-related tests. The results were primarily poor across exemptions, references, rule conditions, and relationship types, which we explain in the discussion section.

Report issue for preceding element

## VI Discussion

Our findings demonstrate that a code-based representation of legal text can substantially improve both the structural and semantic accuracy of extracting legal metadata. Below, we discuss the implications of these results and highlight the potential benefits of this representation.

### VI-A Error Analysis

We conducted a detailed error analysis of the errors obtained on the test set. We identified 20 unique errors that are broadly categorized into four types:

-   •
    
    Reference-related errors: Errors that include missing reference objects, incorrect relationship assignment, and exhibit detailed expressions as references.
    
    Report issue for preceding element
    
-   •
    
    Sentence decomposition inconsistency: Failure to identify dependent clauses for entities and actions, such as conditions and exceptions, causing a high mismatch error rate across these attributes.
    
    Report issue for preceding element
    
-   •
    
    Inference-related errors: Incorrect statement type, incorrect rule type, incorrect relationship between statements
    
    Report issue for preceding element
    
-   •
    
    Sectioning-related errors: Flattening hierarchical structure and missing clauses
    
    Report issue for preceding element
    

A root cause analysis shows that a possible cause of these errors is the imperfect retrieval of high-quality examples. While the demonstration selection strategy boosts the performance of GPT-4o on the code generation task, the earlier tagging task is less reliable and can produce incorrect labels, leading to the selection of the wrong demonstrations. To make the step more deterministic, prompting techniques, such as Chain-of-Thought \[[7](https://arxiv.org/html/2507.02846v1#bib.bib7)\], or fine-tuning a separate classifier to predict labels may be useful.

### VI-B Takeaways from Results

Report issue for preceding element

Our conformance-based unit testing approach ensures that the generated representation is well-formed, complete, and semantically aligned with the source text, even though it does not simulate rule execution. This is analogous to unit tests in code synthesis pipelines where the goal is to verify correct API usage, structural properties, or data flow conformance before execution-level behaviors are modeled.

Report issue for preceding element

The high accuracy in structural and semantic tests shows that prompting GPT-4o to generate class-based code structures yields outputs closely mirroring the ground truth annotations. By encoding legal statements as Python objects, our approach enforces rigorous formatting and data-typing constraints in the narrower vocabulary of code. The near-perfect compilation rate suggests that the structured prompt and class definitions improve task selection at inference time, reducing free-form text errors like hallucinations or incomplete clauses that may occur in text-to-text generation.

Report issue for preceding element

While paragraph-level accuracy, precision, and recall metrics show our approach closely resembles the ground truth, the pass@k scores plateau near 62% on the test set. This result may be due to the strict evaluation, which measures total correctness using an exact match on ground truth attribute values, meaning that all attributes must be identified exactly as represented in the ground truth code.

Report issue for preceding element

Although the approach achieved strong scores for most attributes, references and conditional clauses showed comparatively higher error rates. This highlights the complexity of legal language and cross-referencing. Unfortunately, these mechanisms communicate critical exceptions that trigger only under specific conditions. Developing targeted strategies for reference extraction may be needed to manage deeply nested and multi-layered cross-references. Combining textual entailment with self-reflection \[[38](https://arxiv.org/html/2507.02846v1#bib.bib38), [39](https://arxiv.org/html/2507.02846v1#bib.bib39)\] could potentially address some of these errors.

Report issue for preceding element

Our method shows a significant improvement over the JSON baseline. This finding is consistent with prior work, which shows that flattening structured representations into text tends to reduce task accuracy \[[42](https://arxiv.org/html/2507.02846v1#bib.bib42)\]. This decline occurs because: (1) serialized structures are underrepresented in pre-training data compared to free-form text, and (2) flattening a structured graph often separates semantically related nodes, found close together in the graph, across distant positions in a flat string.

Report issue for preceding element

### VI-C Potential Benefits of a Code-Based Representation

Report issue for preceding element

By translating legal provisions into Python code, our framework produces an “executable” representation of regulatory text. Because each generated output is an instantiation of a formally defined metamodel, our method offers a new avenue for compliance automation: legal requirements captured in code could be integrated with testing frameworks and model-driven engineering tools. Moreover, once encoded as Python objects, provisions are amenable to further transformations, such as generating visual dependency graphs, programmatically verifying contradictions, or enforcing traceability by tagging software artifacts.

Report issue for preceding element

In-context learning leverages a small set of carefully selected demonstrations, thus diminishing the need for large, manually labeled datasets. In settings where domain experts (e.g., legal counsel) are scarce, this approach lowers the overhead of preparing corpora by requiring attorneys to annotate texts. Rather, the generated code could be visually represented and inspected by attorneys to save time and focus their feedback on structural representations more amenable to software developers. It also allows for agile updates: when new regulations arise, only a few additional exemplars are needed for the model to adapt, rather than retraining an entire pipeline.

Report issue for preceding element

Legal text differs from general natural language in its use of formal constructs and well-defined logical dependencies among obligations, exceptions, and definitions. Our empirical results show that these properties make legal text particularly suitable for deterministic translation into structured representations. Representing these constructs through a unified class hierarchy (e.g., separate classes for rules, exemptions, references) ensures that the nested relationships remain explicit. Generating Python code that instantiates well-defined classes provides a traceable “paper trail” from the legal provision to its structured form. Stakeholders, such as compliance officers, can inspect the resulting code, run unit tests to confirm fidelity, and revise specific attributes if needed. This fosters greater trust in the process, as the representation is both human-auditable and machine-readable, encouraging stronger collaboration between legal and engineering experts.

Report issue for preceding element

Overall, the results highlight the practical feasibility of code-based representations to capture the complex structures of legal requirements. We acknowledge that our representation is not a full semantic equivalent of the legal text but a structured abstraction of it. By limiting the scope of representation to a closed class structure, we minimize ambiguity and ensure that downstream tasks (e.g., compliance checks or traceability) are grounded in testable, interpretable representations.

Report issue for preceding element

### VI-D Generalizability of the Python Class Structure

The current Python class structure was derived through open coding of 13 U.S. state data breach notification laws. It primarily reflects the structural and semantic patterns found in the laws that govern personal information protection and breach notification obligations. Therefore, some degree of adaptation may be necessary when applying this structure to laws from different legal domains or jurisdictions with distinct drafting conventions. However, the following features of the class structure support its generalizability:

-   •
    
    Domain-agnostic core classes: Classes such as Section, Statement, and Expression represent hierarchical and atomic units of legal text that are fundamental across most legal documents. These form the structural backbone of the representation and are unlikely to change drastically.
    
    Report issue for preceding element
    
-   •
    
    Flexible semantic encoding: The Rule, Definition, Exemption, and Information classes were designed to capture commonly occurring modalities and constraints. While their current form covers obligations, permissions, prohibitions, and exceptions found in data breach laws, more specialized domains may require the addition of new classes or enrichment of existing ones (e.g., more detailed condition types).
    
    Report issue for preceding element
    
-   •
    
    Extensible attributes and optional defaults: All class attributes are optional with default values, which ensures that code generated from laws lacking certain elements (e.g., no explicit conditions or exemptions) will still compile and remain structurally valid. This design supports partial representations and minimizes breakage when new attributes are introduced.
    
    Report issue for preceding element
    
-   •
    
    Additive evolution: The design can be updated by introducing new classes or attributes to accommodate unseen elements without invalidating existing representations.
    
    Report issue for preceding element
    

## VII Threats to Validity

Report issue for preceding element

Construct Validity refers to whether we are truly measuring what we believe we are measuring \[[37](https://arxiv.org/html/2507.02846v1#bib.bib37)\]. We use a comprehensive test suite to verify the syntactic and semantic attributes of the code representation. While these tests capture many possible errors, passing all tests may not guarantee complete semantic equivalence with the original legal text. Deeply nested or context-dependent provisions could still go undetected if not encoded in our test cases. Furthermore, the ground truth relies on human annotations when translating legal provisions into Python class objects. Although these annotations were verified through iterative checks and unit test execution, there is a risk that errors may occur. We mitigated this by testing the comparability of the manually written code. The first author also revisited the annotations to identify and correct any inconsistencies.

Report issue for preceding element

Internal validity refers to validity of analyses and conclusions drawn from the data \[[37](https://arxiv.org/html/2507.02846v1#bib.bib37)\]. In addition, the final class structure was derived through open coding and iterative refinement. Although the schema was designed to capture core legal metadata (e.g., definitions, obligations, prohibitions, exemptions), other researchers might define or group attributes differently based on alternative theoretical frameworks or application requirements.

Report issue for preceding element

External validity refers to the generalizability of results \[[37](https://arxiv.org/html/2507.02846v1#bib.bib37)\]. We employed GPT-4o and model-specific behavior, such as tokenization, learned embeddings, and instruction tuning, affect how the model reponds to a prompt and how it handles long-range dependencies. A different model family or a later model release from the same family should be expected to yield different results, limiting exact reproducibility and requiring adjustments to the prompts.

Report issue for preceding element

The experimental dataset includes 13 U.S. state data breach notification statutes, all written in English. Although these laws vary in length and drafting style, they represent only a subset of the broader legal landscape. Generalizing our results to other jurisdictions (e.g., non-English texts, international regulations) or domains (e.g., tax law, environmental regulations) may require additional tuning or domain-specific exemplars. Although we selected diverse state statutes, focusing on data breach notification requirements may limit our findings’ applicability to statutes with significantly different thematic content or structural complexity (e.g., intellectual property law).

Report issue for preceding element

## VIII Conclusion and Future Work

Report issue for preceding element

In this paper, we presented a novel method to automatically generate a structured, executable representation of legal text using GPT-4o. By combining textual entailment and in-context learning, our approach preserves both the structural hierarchy and rich semantic information within legal provisions. We integrated this information into a Python class structure that can be parsed, analyzed, and tested programmatically.

Report issue for preceding element

Evaluations on 13 US State data breach notification laws show that our approach achieves high correctness scores, with near-perfect compilation rates and strong precision and recall across most metadata attributes. The experiments further suggest that code-based representations outperform conventional text-based outputs (e.g., JSON), especially for tasks that demand explicit preservation of the original legal text, hierarchical nesting, and cross-references. Additionally, we demonstrated the approach’s ability to generalize to new, unseen statutes with minimal performance degradation.

Report issue for preceding element

Future work will expand this framework to other regulatory domains, and explore more sophisticated retrieval and prompting algorithms for demonstration selection. We envision using this “executable” legal translation for downstream analysis of compliance verification, including requirement tracing, conflict detection, and creating knowledge graphs to show how engineers interpret law in designing accountable software systems.

Report issue for preceding element

## Data Availability Statement

Report issue for preceding element

The code and data used in this study are publicly available at Zenodo<sup class="ltx_note_mark">1</sup><sup class="ltx_note_mark">1</sup>1https://doi.org/10.5281/zenodo.15794182\[[44](https://arxiv.org/html/2507.02846v1#bib.bib44)\]. The repository includes source code, legal text datasets, model outputs, evaluation scripts, and instructions for reproduction.

Report issue for preceding element

## Acknowledgment

Report issue for preceding element

This research was sponsored in part by NSF Award #2217572.

Report issue for preceding element

## References

Report issue for preceding element

-   \[1\]↑ T.D. Breaux, M.W. Vail, A.I. Anton. (2006). “Towards regulatory compliance: Extracting rights and obligations to align requirements with regulations.” $14^{th}$ IEEE International Requirements Engineering Conference, pp. 49-58.
-   \[2\]↑ Brown et al., “Language Models are Few-Shot Learners,” Advances in Neural Information Processing Systems (NeurIPS), 33, 2020.
-   \[3\]↑ A, Kabra, S. Rangreji, Y. Mathur, A. Madaan, E. Liu, and G. Neubig. 2024. “Program-Aided Reasoners (Better) Know What They Know”. Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), pages 2262–2278.
-   \[4\]↑ B. Ghosh, S. Hasan, N.A. Arafat, A. Khan. (2025). “Logical consistency of large language models in fact-checking.” International Conference on Learning Representations.
-   \[5\]↑ M. Jang, T. Lukasiewicz. (2023). “Consistency analysis of ChatGPT.” Empirical Methods in Natural Language Processing, pp. 15970–15985.
-   \[6\]↑ J. Jung, L. Qin, S. Welleck, F. Brahman, C. Bhagavatula, R. Le Bras, Y. Choi. (2022). “Maieutic prompting: Logically consistent reasoning with recursive explanations.” Empirical Methods in Natural Language Processing, pp. 1266–1279.
-   \[7\]↑ T. Kojima, S. Gu, M. Reid, Y. Matsuo, Y. Iwasawa. “Large Language Models are Zero-shot Reasoners.” Advances in Neural Information Processing Systems (NeurIPS) 35, pp. 22199-22213, 2022.
-   \[8\]↑ N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, P. Liang. “Lost in the Middle: How Language Models Use Long Contexts,” Transactions of the Association for Computational Linguistics, vol. 12, pp. 157–173, 2024.
-   \[9\]↑ Y. Lu, M. Bartolo, A. Moore, S. Riedel, P. Stenetorp, “Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity,” $60^{th}$ Annual Meeting of the Association for Computational Linguistics, pp. 8086–8098, 2022.
-   \[10\]↑ J.C. Maxwell, A.I. Antón, P. Swire, P. (2011). “A legal cross-references taxonomy for identifying conflicting software requirements.” $19^{th}$ IEEE International Requirements Engineering Conference, pp. 197-206.
-   \[11\]↑ E. Mitchell, J. Noh, S. Li, W. Armstrong, A. Agarwal, P. Liu, C. Finn, C. Manning. (2022). “Enhancing self-consistency and performance of pre-trained language models through natural language inference.” Empirical Methods in Natural Language Processing, pp. 1754–1768.
-   \[12\]↑ M. Ravaut, A. Sun, N. Chen, and S. Joty. “On Context Utilization in Summarization with Large Language Models,” 62<sup class="ltx_sup" id="bib.bib12.2.1"><span class="ltx_text ltx_font_italic" id="bib.bib12.2.1.1">nd</span></sup> Annual Meeting of the Association for Computational Linguistics vol. 1, pp. 2764–2781, 2024.
-   \[13\]↑ N. Sannier, M. Adedjouma, M., Sabetzadeh, L. Briand (2017). “An automated framework for detection and resolution of cross references in legal texts.” Requirements Engineering, 22: 215-237.
-   \[14\]↑ J. Saldanã. The Coding Manual for Qualitative Researchers, SAGE Publications, 2012.
-   \[15\]↑ Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H.P.D.O., Kaplan, J., Edwards, H., Burda, Y., Joseph, N., Brockman, G. and Ray, A. “Evaluating large language models trained on code.” arXiv preprint arXiv:2107.03374, 2021.
-   \[16\]↑ T.D. Breaux, D.G. Gordon. “Regulatory Requirements Traceability and Analysis Using Semi-formal Specifications”. Requirements Engineering: Foundation for Software Quality. REFSQ 2013. Lecture Notes in Computer Science, vol 7830. Springer, Berlin, Heidelberg, 2013.
-   \[17\]↑ T.Z. Zhao, E. Wallace, S. Feng, D. Klein, S. Singh, “Calibrate Before Use: Improving Few-Shot Performance of Language Models”. $38^{t}h$ International Conference on Machine Learning (PMLR) 139, 2021.
-   \[18\]↑ A Massey. “Legal requirements metrics for compliance analysis”. PhD thesis, North Carolina State University (2012).
-   \[19\]↑ AK Massey, PN Otto, LJ Hayward, AI Anton. “Evaluating existing security and privacy requirements for legal compliance”. Requirements Engineering 15(1):119–137 (2010).
-   \[20\]↑ M. Palmirani, F. Vitali. “Akoma-Ntoso for Legal Documents”. Legislative XML for the Semantic Web. Law, Governance and Technology Series, vol 4. Springer, Dordrecht (2011).
-   \[21\]↑ S. Santos, T.D. Breaux, T. Norton, S. Haghighi, S. Ghanavati (2024). “Requirements Satisfiability with In-Context Learning,” International Requirements Engineering Conference.
-   \[22\]↑ Zeni, N., Kiyavitskaya, N., Mich, L. et al. “GaiusT: supporting the extraction of rights and obligations for regulatory compliance”. Requirements Engineering 20, 1–22 (2015).
-   \[23\]↑ Chalkidis, I., Fergadiotis, M., Malakasiotis, P., Androutsopoulos, I. (2019). “Large-scale multi-label text classification on EU legislation”. arXiv preprint arXiv:1906.02192.
-   \[24\]↑ Sleimi, A., Sannier, N., Sabetzadeh, M. et al. “An automated framework for the extraction of semantic legal metadata from legal texts”. Empir Software Eng 26, 43 (2021).
-   \[25\]↑ Humphreys, L. and Boella, G. and van der Torre, L. and Robaldo, L. and Di Caro, L. and Ghanavati, S. and Muthuri, R. “Populating legal ontologies using semantic role labeling”, Artificial Intelligence and Law (2020).
-   \[26\]↑ Bhatia J, Evans MC, Wadkar S, Breaux TD (2016b) “Automated extraction of regulated information types using hyponymy relations”. Proceedings of the 3rd International Workshop on Artificial Intelligence for Requirements Engineering, pp 19–25.
-   \[27\]↑ Maxwell JC, Anton AI (2010). “The production rule framework: developing a canonical set of software requirements for compliance with law”. Proceedings of the ACM International Health Informatics Symposium, pp 629–636.
-   \[28\]↑ Cejas, O.A., Azeem, M.I., Abualhaija, S., Briand, L.C. (2022). “NLP-Based Automated Compliance Checking of Data Processing Agreements Against GDPR”. IEEE Transactions on Software Engineering, 49, 4282-4303.
-   \[29\]↑ Jiang, J., Wang, F., Shen, J., Kim, S., Kim, S. (2024). “A survey on large language models for code generation”. arXiv preprint arXiv:2406.00515.
-   \[30\]↑ Li, J., Li, G., Li, Y., Jin, Z. (2025). “Structured chain-of-thought prompting for code generation”. ACM Transactions on Software Engineering and Methodology, 34(2), 1-23.
-   \[31\]↑ Li, Y., Choi, D., Chung, J., Kushman, N., Schrittwieser, J., Leblond, R., …, Vinyals, O. (2022). Competition-level code generation with alphacode. Science, 378(6624), 1092-1097.
-   \[32\]↑ Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. D. O., Kaplan, J., …, Zaremba, W. (2021). “Evaluating large language models trained on code”. arXiv preprint arXiv:2107.03374.
-   \[33\]↑ Austin, J., Odena, A., Nye, M., Bosma, M., Michalewski, H., Dohan, D., …, Sutton, C. (2021). Program synthesis with large language models. arXiv preprint arXiv:2108.07732.
-   \[34\]↑ E. Jiang, E. Toh, A. Molina, K. Olson, C. Kayacik, A. Donsbach, C. J Cai, and M. Terry. 2022. “Discovering the Syntax and Strategies of Natural Language Programming with Generative Language Models”. In Proceedings of the 2022 CHI Conference on Human Factors in Computing Systems.
-   \[35\]↑ Johnson, D. D., Tarlow, D., and Walder, C. (2023). “Ru-sure? uncertainty-aware code suggestions by maximizing utility across random user intents”. arXiv preprint arXiv:2303.00732.
-   \[36\]↑ Gao, L., Madaan, A., Zhou, S., Alon, U., Liu, P., Yang, Y., … and Neubig, G. (2023, July). Pal: Program-aided language models. In International Conference on Machine Learning (pp. 10764-10799). PMLR.
-   \[37\]↑ R. K. Yin, "Case study research: Design and methods", vol. 5. Sage, 2009.
-   \[38\]↑ Z. Ji, T. Yu, Y. Xu, N. Lee, E. Ishii, and P. Fung. 2023. “Towards Mitigating LLM Hallucination via Self Reflection”. In Findings of the Association for Computational Linguistics: EMNLP 2023, pages 1827–1843, Singapore. Association for Computational Linguistics.
-   \[39\]↑ Renze, M., and Guven, E. (2024). “Self-reflection in llm agents: Effects on problem-solving performance.” arXiv preprint arXiv:2405.06682.
-   \[40\]↑ P. N. Otto and A. I. Anton, “Addressing Legal Requirements in Requirements Engineering.” 15th IEEE International Requirements Engineering Conference (RE 2007), Delhi, India, 2007, pp. 5-14.
-   \[41\]↑ S. Kerrigan, K.H. Law. “Logic-Based Regulation Compliance-Assistance.” Proc. of the 9th Int’l Conf. on AI and Law, pp. 126-135, June 2003.
-   \[42\]↑ A. Madaan, S. Zhou, U. Alon, Y. Yang, G. Neubig. “Language Models of Code are Few-Shot Commonsense Learners.” Proc. of the 2022 Conference on Empirical Methods in Natural Language Processing (EMNLP 2022), pp. 1384–1403.
-   \[43\]↑ D. G. Gordon, T. D. Breaux (2013, July). “Assessing regulatory change through legal requirements coverage modeling”. In 2013 21st IEEE International Requirements Engineering Conference (RE) (pp. 145-154). IEEE.
-   \[44\]↑ A. Singhal, T. Breaux (2025). “Legal Requirements Translation from Law”. IEEE International Requirements Engineering Conference 2025 (RE), Valencia, Spain. Zenodo. https://doi.org/10.5281/zenodo.15794182