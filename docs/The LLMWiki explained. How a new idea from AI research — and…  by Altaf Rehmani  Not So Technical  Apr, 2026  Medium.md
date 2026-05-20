Featured

# The LLMWiki explained

[

![Altaf Rehmani](https://miro.medium.com/v2/resize:fill:64:64/0*US28PP8Ab8pHhDpu.jpg)



](https://medium.com/@altafr?source=post_page---byline--e3b5eb806f36---------------------------------------)

11 min read

Apr 9, 2026

## How a new idea from AI research — and its answer to the scaling problem — can transform how enterprises manage procedures, compliance rules, and regulatory obligations forever.

Somewhere in your organisation right now, a compliance analyst is trying to determine the exact documentary requirements for onboarding a mid-market corporate client domiciled in a FATF-listed jurisdiction. She has four PDF tabs open. Two SharePoint folders. A Teams message to someone who “dealt with this last year.” And a printed copy of the Customer Due Diligence (CDD) procedure document from 2024 — which may or may not have been superseded.

This is not a technology failure. It is a knowledge architecture failure. And it is costing more than anyone wants to admit — in regulatory risk, operational latency, and the quiet exodus of experienced staff who get tired of being the human search engine for institutional memory.

Your CDD policy document is approximately 147 pages long. It has been amended 19 times since it was drafted. This is not a judgment. It is a sector-wide condition. The Basel Committee calls it “operational complexity.” The rest of us call it document soup.

## A new idea from an unexpected source

Last week, Andrej Karpathy — the former head of AI at Tesla and one of the most respected researchers in artificial intelligence — published a short document titled “LLM Wiki.” It attracted over 5,000 stars in days and sparked implementations across dozens of industries. The idea is simple, counterintuitive, and enormously relevant to how large institutions manage knowledge.

The core insight is this: most AI systems rediscover knowledge from scratch on every query. RAG — the dominant approach today — retrieves fragments of documents, stitches together an answer, and then forgets everything. Ask the same question twice and it does the same work twice. Nothing accumulates.

Karpathy proposes something different. Instead of making the AI search documents every time, what if the AI **built its own Wikipedia** from your documents?

Not just a summary. An actual interlinked wiki — with pages for every concept, person, rule, and idea. Pages that link to each other. Pages that get updated automatically when new information arrives. A wiki that gets smarter over time, not dumber.

> ## A new idea from an unexpected source
> 
> “The tedious part of maintaining a knowledge base is not the reading or the thinking — it’s the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims. Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don’t get bored, don’t forget to update a cross-reference, and can touch 15 files in one pass.” _— Andrej Karpathy_

The analogy he reaches for is telling. Traditional RAG is a library where the librarian dies after every visit. The LLM Wiki is a library where the librarian reads every book, builds an interconnected index, and updates it every time a new edition arrives.

## Three approaches, one problem

Press enter or click to view image in full size

![](https://miro.medium.com/v2/resize:fit:1400/1*iZ-vY2PSIKOaYDa1ZveHHw.png)

## Three approaches, one problem

Before getting specific about CDD, it helps to understand where the LLM Wiki sits relative to the two dominant approaches most large organisations have already evaluated or deployed.

**RAG (Retrieval-Augmented Generation)** is essentially a Google search inside your documents. You ask a question, the AI finds the most relevant paragraphs, reads them, and answers. Fast to set up, widely deployed, and genuinely useful for simple queries. But it has zero memory. Every answer is assembled fresh. It struggles to connect dots across five different documents without getting confused, and it cannot flag when something it said last week contradicts what it’s saying today.

**Knowledge graphs** are the expensive alternative. Build a massive mind map of everything in your documents — every person, place, rule, and how they connect. Powerful for structured questions like “who owns what?” — but the build cost is high, maintenance is brittle, and the graph only knows what the architects decided to encode. Changing one regulation can require a schema rebuild.

**The LLM Wiki** sits between them — and in many ways beyond both. The AI builds and maintains a living Wikipedia from your source documents. Every page is human-readable and interlinked. New document arrives? The AI integrates it, updates the affected pages, and flags anything that contradicts existing knowledge. The wiki compounds in value over time rather than staying static.

Here is the honest comparison across dimensions that matter in a regulated institution:

Press enter or click to view image in full size

![](https://miro.medium.com/v2/resize:fit:1400/1*PJ6igq09GlUB9xuzRWIrJA.png)

## Applying this to CDD: a worked example

In banking, Customer Due Diligence (or CDD) is the ideal test case. It sits at the intersection of everything that makes policy management hard: multiple regulatory frameworks (FATF, MAS Notice 626, FCA SYSC 6.3, HKMA AML/CFT), frequent amendments, significant downstream risk if misapplied, and enough variation by customer segment and jurisdiction to defeat any simple retrieval system.

Karpathy describes three layers that make the architecture work. In a banking context, they map like this:

**Layer 1 — Raw sources (immutable).** The original documents. FATF Recommendations, MAS Notice 626, FCA SYSC 6.3, HKMA AMLO Guideline, internal CDD Policy, product risk appetite statements, sanctions screening procedures, SAR filing thresholds, country risk register. The AI reads them but never modifies them. This is your source of truth.

**Layer 2 — The wiki (LLM-maintained, human-readable).** Hundreds of interlinked markdown pages. Entity pages for Corporate client, PEP, Beneficial owner, HNWI, SME. Concept pages for Risk-based approach, EDD trigger conditions, Source of wealth, Ongoing monitoring frequency. Rule pages for Documentary requirements by jurisdiction, Threshold matrix, Escalation criteria. And critically: a Contradiction log — a live record of places where frameworks disagree, like “MAS 626 §4.2 conflicts with internal policy on PEP refresh cycles.”

**Layer 3 — The schema (governs LLM behaviour).** A document — Karpathy calls it CLAUDE.md or AGENTS.md — that tells the AI exactly how to write wiki pages, what counts as a contradiction, how to maintain citation standards, and how often to run a health check. This is what keeps the system disciplined rather than just chatting.

## What this looks like in practice

A MAS circular amending EDD requirements for digital asset businesses arrives. The AI reads it, identifies which existing wiki pages are affected — EDD triggers, customer segment: digital asset VASP, documentary requirements: Singapore — updates those pages, logs the change, and flags a contradiction with a legacy internal threshold that has not been updated.

A relationship manager asks: “What documents do I need to onboard a Hong Kong-registered holding company whose beneficial owner is a foreign national classified as a politically exposed person, with a declared source of wealth in real estate?” The wiki synthesises the answer from four linked pages. The answer is already compiled. It cites the exact clauses.

Quarterly, the AI health-checks the wiki. It finds orphan pages (concepts mentioned but not linked), a stale claim (a country risk rating updated externally but not propagated internally), and pages where cross-framework synthesis is missing. It proposes corrections. A compliance officer reviews and approves.

When the regulator requests evidence of your CDD framework’s fitness, you produce not a PDF but a structured wiki with version history, source provenance, contradiction log, and amendment trail. Every claim traces back to its source document with a hash. The regulator can see exactly what you knew, when you knew it, and how it informed your procedures.

## But does it scale?

This is the right question to ask, and Karpathy is honest about it in the paper itself. The `index.md` approach — where the AI reads a master index file to navigate the wiki — works well at "moderate scale (~100 sources, ~hundreds of pages)." Beyond that, you need a search upgrade.

For a CDD wiki covering multiple jurisdictions and customer segments, you will comfortably exceed a few hundred pages at steady state. So what does the scaling path actually look like?

The answer comes from the GitHub comments on Karpathy’s paper, which are unusually high-quality — several people had already built implementations independently and reported back with real numbers.

**Paul-Kyle** reported running 227 files with 2,230 indexed chunks using a git-versioned approach with hybrid search via SQLite, and confirmed: “the compounding effect is real — agents that remember prior sessions make fewer mistakes and ask better questions.”

**bradwmorris** ran the filesystem approach for six to twelve months before switching to local SQLite as the storage layer, finding it a significantly better abstraction once the wiki grows and multiple contributors start feeding into it.

**xoai**, building an implementation called sage-wiki, identified that the compiler works best as a pipeline of focused passes — diff, summarise, extract concepts, write articles — where a new document touches ten to fifteen wiki pages but skips everything else, exactly like how `make` only rebuilds what changed. A single-prompt approach falls apart at scale; a staged pipeline holds together.

The scaling map, practically speaking:

Scale What works Up to ~100 pages `index.md` is sufficient — no extra tooling needed 100–500 pages Hybrid search: BM25 keyword + vector similarity (tools like `qmd` or SQLite-vec) 500+ pages SQLite as the storage layer, pipeline-style compilation, proposition-level provenance 1,000+ pages Multi-agent setup, typed entity system, decay model for stale knowledge

## The hardest scaling problem: concept deduplication

Storage and search are solvable engineering problems. The genuinely hard problem at scale is concept deduplication — and xoai’s paper flagged this specifically.

Is “attention mechanism” the same wiki node as “self-attention”? In a CDD context: is “beneficial owner verification” the same concept as “UBO identification”? Is “source of wealth” the same as “source of funds”? Free-form linking — where the AI just uses whatever term it encountered first — produces wikis that fragment the same concept across multiple orphaned pages that never cross-reference each other.

The solution is a typed entity system with explicit relation types: is-a, part-of, contradicts, supersedes. You define the canonical term once in the schema, and the AI maps everything else to it. This keeps the wiki scannable even as it grows — a compliance officer searching for “UBO” finds the same page whether the source document used “beneficial owner,” “ultimate beneficial owner,” or “controlling party.”

## Provenance: the audit feature that scales with you

One commenter, Jwcjwc12, added a feature that is particularly relevant for regulated institutions: structural provenance. Every claim in the wiki records which source files produced it and their content hashes at compilation time. When a source document changes, any claim derived from it is automatically flagged as potentially stale. Match = valid. Mismatch = stale.

This is more rigorous than any audit trail currently maintained in most banks’ policy management systems. It means you can answer “when did your EDD threshold for digital asset businesses last change, and what regulatory source triggered it?” with a single query rather than an email chain.

## The governance model: human review stays

A reasonable concern: if an AI is writing and maintaining our policy wiki, who is accountable for what it says?

The answer is the same people who are accountable today — with far better tooling.

The wiki operates on a propose-review-commit model. The AI proposes changes. No update to a Tier 1 page — regulatory obligation, risk threshold, escalation criterion — is committed without human sign-off. Every committed change carries the reviewer’s name and timestamp. This is more rigorous than the current model, where policy documents are amended by whoever has SharePoint edit access and the changelog is a comment in a footnote.

Material changes — anything touching regulatory thresholds, escalation procedures, or cross-border obligations — trigger a mandatory review gate. The AI drafts. The compliance officer decides. The audit log records both.

## The strategic case, plainly stated

The regulatory environment is not getting simpler. FATF updates, MAS circulars, FCA thematic reviews, HKMA guidance — the volume and velocity of change is accelerating. Organisations that manage this through periodic PDF updates and SharePoint folders are operating a system designed for a slower world.

The LLM Wiki offers four things that the current approach cannot:

**Consistency.** Every question gets the same answer regardless of who asks or when. Institutional knowledge does not retire when people do.

**Compounding value.** Every new source, every regulatory update, every good question asked of the wiki makes it richer. The system improves over time rather than degrading.

**Audit readiness.** Full provenance trail. Contradiction log. Amendment history. Not a document — a living record of how the organisation understands and applies its obligations.

**Speed.** When the documentary requirements for any customer scenario can be synthesised instantly and accurately, the bottleneck shifts from knowledge retrieval to relationship effort — where it belongs.

## What Karpathy got right about maintenance

The most important line in the paper is this:

> ## What Karpathy got right about maintenance
> 
> “Humans abandon wikis because the maintenance burden grows faster than the value.”

Every large organisation has attempted an internal knowledge base. Most have a SharePoint site that was last meaningfully curated in 2019 and is now a monument to good intentions. The reason is not lack of effort. It is that maintenance at scale is humanly expensive and professionally unrewarding. Nobody gets promoted for updating the cross-reference links in the CDD procedure manual.

The LLM Wiki removes the maintenance burden from humans. The human’s job becomes what it should have always been: curating sources, making judgement calls on material changes, and asking good questions. The AI does everything else.

Karpathy reaches back to Vannevar Bush’s 1945 concept of the Memex — a personal knowledge store with associative trails between documents. “The part he couldn’t solve,” Karpathy writes, “was who does the maintenance.” In a bank, that question has always been answered by committee. Now it can be answered by a well-instructed language model operating under human governance. The committee can focus on the decisions that actually require judgment.

## Proposed first step

A pilot can be scoped, built, and evaluated in less than 30 days ( you must code with AI and go governance in parallel.)

Pick one customer segment — mid-market corporate works well — in one jurisdiction. Define the source corpus: the four or five regulatory documents and internal policies that govern CDD for that segment. Build the schema collaboratively with Compliance and Legal. Run the first ingest and review what the initial wiki surfaces — this process alone typically reveals contradictions and stale claims that nobody knew were there. Then present thirty real CDD queries to both the wiki and the current process and measure the difference in response time, accuracy, and source traceability.

The technology exists today. It does not require new infrastructure, new vendors, or a programme board. It requires a decision about how the organisation wants to manage institutional knowledge — and whether it wants a knowledge base that reads every circular, integrates every change, flags every contradiction, and answers every question with full provenance.

PS : That system is buildable now. [I built one in few hours. try it here.](https://llmwikidemo.lovable.app/) Dont have the time to try it out? watch how it works in the website above.

_Altaf Rehmani is a Digital Solutions Architect at HSBC, founder of the School of Applied AI, and author of Generative AI for Everyone. When not working, he loves to share, teach and play with everything Generative AI._

_The LLM Wiki paper by Andrej Karpathy is available at:_ [_https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f_](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)