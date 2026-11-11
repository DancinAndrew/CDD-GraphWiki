# Independent review of the UK MLR 2017 Part 3 held-out labels: protocol

Written on 2026-11-11, before any reviewer was run. The pre-registered labels
([`../../gold_labels_uk_mlr_2017.yaml`](../../gold_labels_uk_mlr_2017.yaml), commit `5a89252`) were written by the
project author alone. The author cannot judge the legal text, so this review uses independent model reviewers
(Claude sub-agents) and a fixed decision rule. Its result is reported as "the review found / did not find N
problems", never as "the labels are verified".

## What reviewers see

- The corpus as clause records with their IDs (generated from `data/heldout/sources/uk_mlr_2017.md` by the
  project parser), and [`../../ANNOTATION_GUIDELINE.md`](../../ANNOTATION_GUIDELINE.md) as committed with the labels.
- Never the rules, their predictions, the LLM runs or any score. Reviewers are told not to open the repository.

## Stage 1: find candidate problems (three reviewers, independent)

- **Blind annotator A** labels every clause from scratch, reading in document order.
- **Blind annotator B** labels every clause from scratch, sweeping the whole text once per type.
- **Critic C** sees the pre-registered labels and tries to show that each is wrong and that labels are missing.

A and B do not see the pre-registered labels. A clause is a **candidate** when any reviewer's set of types for it
differs from the pre-registered set (including clauses the labels leave empty).

## Stage 2: adjudicate each candidate (three adjudicators, independent)

Each adjudicator sees, for every candidate, the clause in context, the pre-registered types and note, and every
distinct alternative with the reasons given (reviewers anonymised). For each candidate it chooses the set of
types the guideline requires and quotes the guideline wording that decides it, or says the guideline does not
decide it.

## Decision rule

1. A label changes only when at least two of the three adjudicators choose the same set of types, that set
   differs from the pre-registered one, and each of them quotes guideline wording the pre-registered label breaks.
2. Otherwise the pre-registered label stays. Candidates where at least two adjudicators say the guideline does
   not decide the case are recorded as guideline gaps; their labels stay.
3. The guideline itself is not changed by this review. Proposals to change it are listed as open questions.
4. The pre-registered file is not edited. Accepted changes go to a separate revised file
   (`gold_labels_uk_mlr_2017_revised.yaml`) and to a decision log with the reason and votes for each change.
5. Scores are reported against both label sets, for rules v1, rules v2 and the LLM runs already recorded.
   Neither the rules nor the LLM prompt are changed in response; the UK set stays a test set.
6. If any change is accepted, the confidence the application shows (measured precision on the UK set) uses the
   revised labels, and the README shows the score against the pre-registered labels next to it. This choice is
   fixed here, before the result is known.

## Agreement

Before adjudication, agreement of A and B with the pre-registered labels (and with each other) is reported as
F1 over (unit, type) pairs at clause and paragraph level. It measures how reproducible the labels are under the
guideline, not whether they are right.

## Addendum (2026-11-11, after stage 1, before stage 2)

Blind annotators A and B ran on the same model and produced identical label sets (92 of 92 clause–type pairs),
although their reasons are worded differently and their file access logs show each read only the guideline and
the corpus. They are therefore one reading of the guideline repeated, not two independent ones. To reduce the
same correlation in stage 2, the three adjudicators run on three different Claude models. The decision rule is
unchanged. No score was computed at this point.
