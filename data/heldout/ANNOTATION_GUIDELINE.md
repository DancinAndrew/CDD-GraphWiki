# Held-out annotation guideline

This guideline defines the labels in [`gold_labels.yaml`](gold_labels.yaml) (MAS Notice 626) and
[`gold_labels_uk_mlr_2017.yaml`](gold_labels_uk_mlr_2017.yaml) (UK Money Laundering Regulations 2017). Each set
of labels was written and committed **before** the rules it tests were run on its text; the git history shows
the order.

## Corpora and held-out sets

**MAS Notice 626** (labels committed in `aaa389c`, before rules v1 were run on it)

- Corpus: the full text of MAS Notice 626 in [`sources/mas_notice_626.md`](sources/mas_notice_626.md),
  converted from the official PDF by `backend/src/heldout/convert.py` (167 numbered paragraphs).
- Development paragraphs: 6.3, 6.5, 6.6, 6.9, 6.13, 6.14, 6.14B, 6.35, 8.2 and 8.3. These are the MAS
  paragraphs in the development excerpt (`data/sources/mas_notice_626.md`) that the rules were written
  against. Every clause of these paragraphs, including sub-paragraphs left out of the excerpt, is excluded.
- Held-out set: every other clause of the Notice that has text. Section-heading records carry no text and are
  not scored. Rules v2 were designed after studying the v1 errors here, so for v2 this set is no longer unseen.

**UK Money Laundering Regulations 2017, Part 3** (labels committed after rules v2 were frozen in `98332e9`)

- Corpus: regulations 27 to 38 (customer due diligence) in [`sources/uk_mlr_2017.md`](sources/uk_mlr_2017.md),
  converted from the legislation.gov.uk XML by `backend/src/heldout/convert_uk.py` (137 numbered paragraphs).
  Contains public sector information licensed under the Open Government Licence v3.0.
- No development paragraphs: the whole text is held out, for rules v1, rules v2 and the LLM alike.
- Notes on applying the types to this text: "relevant person" is the regulated firm; beneficiaries of a trust
  are its beneficial owners (regulation 6), beneficiaries of a life insurance policy are not; collecting the
  company register's beneficial ownership information (regulation 30A) is part of identifying beneficial
  owners; deeming provisions ("is to be treated as identifying") are read as interpretation and not labelled.

## Unit of annotation

A clause is one record produced by the parser: a numbered paragraph (its lead-in text), a sub-paragraph such as
(a), or a nested sub-paragraph such as (a)(i). Each held-out clause gets zero or more of the eight types below.
Clauses not listed in `gold_labels.yaml` have no type.

- A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a
  requirement of type T, e.g. an item in the list of information the bank shall obtain about a beneficial owner.
- A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items
  have type T. This follows the development annotation, where the lead-ins of 6.3, 6.6, 6.14 and 8.3 are part
  of their obligations.
- A clause can have more than one type, e.g. a requirement to verify both the customer and its beneficial owners.

## What is not labelled

- Permissions and exemptions ("may", "shall not be required to", "in lieu of"), including the exception
  conditions attached to a requirement. They relax an obligation rather than impose one.
- Definitions, scope statements and paragraphs that only say how other paragraphs are read.
- Documentation-only duties ("shall document ...").
- Requirements of other kinds that the system does not model: risk assessment, screening, ongoing monitoring,
  record keeping, reliance on third parties, correspondent banking, wire-transfer message content, suspicious
  transaction reporting, simplified CDD, internal policies, and enhanced measures for higher-risk customers who
  are not politically exposed persons (PEPs).

## The eight types

These are the obligation types the system models. The labels apply to MAS text whether or not the rules
have a Singapore profile for that type.

| Type | Label a clause when it requires the bank to ... |
| --- | --- |
| `prohibit_anonymous` | not open or keep anonymous accounts or accounts in fictitious names. |
| `cdd_triggers` | perform CDD measures when a stated event or circumstance occurs (establishing business relations, a transaction above a threshold, a suspicion, doubts about earlier information, acquiring another institution's customers, a revision of the Notice). Saying *how* CDD is done, or *on whom*, is not a trigger. |
| `verify_customer` | identify the customer or verify the customer's identity, including the information to obtain, the sources to use and when verification must be completed. "Customer" covers the originator or beneficiary of a wire or value transfer whose identity the bank must establish. It does not cover persons acting on the customer's behalf, connected parties or life-policy beneficiaries. |
| `identify_ubo` | inquire about, identify or verify the beneficial owners of a customer, including the information to obtain about them and understanding the customer's ownership and control structure. |
| `pep_edd` | apply enhanced measures because the customer or a beneficial owner is a PEP, or a family member or close associate of one. |
| `pep_prohibition` | refuse or end a relationship because the customer is a PEP. |
| `pep_approval` | obtain a named approver's sign-off for a PEP relationship, as a requirement of its own rather than one item of a list of enhanced measures. |
| `cdd_incomplete` | not start or continue a relationship, transaction or transfer because the required customer due diligence (identification and verification) could not be completed. |

## Paragraph-level view

Results are reported per clause and per paragraph. A paragraph has type T when any of its clauses has type T;
the extractor finds it when it assigns T to any clause of that paragraph.
