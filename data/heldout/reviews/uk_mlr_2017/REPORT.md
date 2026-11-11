# Independent review of the UK MLR 2017 Part 3 held-out labels: result

The review followed [`PROTOCOL.md`](PROTOCOL.md), written before any reviewer ran. Every file in this folder
except this report and the protocol is either a reviewer's answer as returned (`stage1/`, `stage2/adjudicator_*`)
or rebuilt from those answers by `PYTHONPATH=backend python -m src.heldout.label_review`. CI re-runs it and checks
that nothing changes.

**In short:** the review found one label that breaks the guideline's wording, and it was changed. It also found
29 cases that the guideline does not decide. Scores at paragraph level are the same before and after. All
reviewers are Claude models, not legal experts, so the result is "the review found 1 problem", not "the labels are
verified".

## Who reviewed

| Stage | Role | Model | Saw the pre-registered labels |
| --- | --- | --- | --- |
| 1 | Blind annotator A, reading in document order | claude-opus-5-5 | no |
| 1 | Blind annotator B, one sweep per type | claude-opus-5-5 | no |
| 1 | Critic C, told to attack the labels | claude-opus-5-5 | yes |
| 2 | Adjudicators 1, 2, 3, deciding every candidate | opus, fable, sonnet | yes, as the label under review |

No reviewer saw the rules, their predictions, the LLM runs or any score; each one's file access was checked after
it finished. Stage 2 adjudicators saw the stage 1 reviewers anonymised.

## Stage 1: candidates

| | Clause level F1 | Paragraph level F1 |
| --- | --- | --- |
| Annotator A vs pre-registered | 0.88 (74 shared, 18 only A, 3 only pre-registered) | 0.89 (31, 7, 1) |
| Annotator B vs pre-registered | 0.88 (identical to A) | 0.89 |
| A vs B | 1.00 | 1.00 |

A and B returned exactly the same labels, with differently worded reasons. They ran on the same model, so this is
one reading of the guideline repeated, not two independent readers agreeing ([`agreement.json`](agreement.json)).
Because of this, the three adjudicators were run on three different models (protocol addendum).

42 clauses became candidates ([`stage2/candidates.md`](stage2/candidates.md)): 17 raised by the blind annotators
(15 of them also by the critic) and 25 by the critic alone.

## Stage 2: outcomes ([`decisions.yaml`](decisions.yaml))

| Outcome | Candidates | What it means |
| --- | --- | --- |
| changed | 1 | All three adjudicators said the label breaks the guideline's wording and chose the same replacement. |
| kept | 12 | The guideline decides the case and the pre-registered label is right. All 12 were raised by the critic alone. |
| guideline gap | 29 | At least two adjudicators said the guideline's wording does not settle the case; the label stays. |

**The change.** `28(3)(b)(ii)`, the full names of a body corporate's directors and senior persons, had
`verify_customer`; it now has no type. The guideline says `verify_customer` "does not cover persons acting on the
customer's behalf, connected parties or life-policy beneficiaries", and directors are connected parties. The vote
was 3 of 3. One caveat: "connected parties" is a MAS Notice 626 term that the guideline does not define for UK
text, and all three adjudicators raised this as a guideline question even though they voted for the change. The
paragraph `28(3)` keeps `verify_customer` through its other items, so paragraph-level scores do not move.

**Readings most adjudicators preferred but did not find required (7, not adopted).** In these guideline gaps, two
or three adjudicators chose a different set of types, but none said the pre-registered label breaks the guideline:

- `29(7)`, `29(7A)`: add `prohibit_anonymous` to `cdd_triggers` (CDD before an existing anonymous account or box
  is used is the "keep" half of the prohibition).
- `30ZA(3)` lead-in and `(a)`: `verify_customer` and `identify_ubo` instead of `cdd_triggers` (a deadline for
  completing CDD rather than a new trigger).
- `30A(1A)` lead-in, `(a)`, `(b)`: `identify_ubo` (the list of beneficial-ownership information to collect).

## Scores ([`scores_before_after.txt`](scores_before_after.txt))

| Paragraph level F1 | Pre-registered | Revised | Sensitivity: revised + the 7 preferred readings |
| --- | --- | --- | --- |
| Rules v2 | 0.61 (15/32, precision 0.88) | 0.61 (15/32, 0.88) | 0.57 (15/36, 0.88) |
| LLM qwen3.5:9b | 0.57 | 0.57 | 0.56 |
| LLM qwen3.5:9b, evidence prompt | 0.51 | 0.51 | 0.51 |

At clause level the change removes one gold pair that every system missed, so recall rises by about 0.01 for
each. The sensitivity column is not a score of record. It shows that adopting the contested readings would lower
the rules' recall, not raise it: none of them were cases the rules got right.

The results in `data/heldout/results/` stay against the pre-registered labels. The measured confidence the
application shows uses the revised labels, as the protocol fixed in advance; its values are unchanged because the
paragraph-level counts are unchanged.

## Guideline gaps (open questions, guideline not changed)

The adjudicators' questions ([`stage2/`](stage2/)) group into these:

1. Factor lists: does "must take into account" (27(9), 35(4)) count as a trigger or a PEP measure, or only as how
   another paragraph is applied?
2. Scope of `prohibit_anonymous`: existing anonymous accounts (29(7), 29(7A)), and instruments that are not
   accounts (bearer shares in 29(8), anonymous prepaid cards in 38(4A)).
3. "Connected parties" has no UK definition (28(3)(b)(ii)).
4. "Must" duties that a permission is made subject to (30ZA(2), (3)) versus "may ... provided that" provisos
   (30(3), (4)).
5. Lists in a separate paragraph (30A(1A)) and rules on how a duty is met (28(9)): definitions, or part of
   `identify_ubo`?
6. Deadlines for completing CDD (30ZA(3)(a)): `verify_customer` / `identify_ubo`, or a trigger?
7. PEP systems and assessments (35(1), 35(3)): `pep_edd`, or excluded screening, risk assessment and internal
   policy?

Changing the guideline now would mean re-labelling the set after its scores are known, so these stay open. They
are what a second human annotator, or a future guideline version with a fresh held-out set, should settle first.

## Limits

- Every reviewer is a Claude model. The models are not legal experts, and models of one family can share the same
  misreadings. No human with legal training reviewed the labels.
- The two blind annotators are one model's reading, not two.
- The protocol, the candidate pipeline and this report were written by the same assistant that built the rules
  and had seen their errors. It did not add candidates or decide outcomes; candidates came only from the
  reviewers, and outcomes come from the rule in the protocol applied by code.
