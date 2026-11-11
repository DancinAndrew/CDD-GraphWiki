# Candidates for adjudication

Each candidate is one clause where at least one reviewer's set of types differs from the pre-registered label.
Reviewers are anonymised. 'Pre-registered' is the label under review, not a reference answer.

## Paragraph 27(7B)

Whole paragraph (context):

- `uk_mlr_2017_27_cdd_27_7b`: 27(7B) The letting agent must apply customer due diligence measures under paragraph (7A) in relation to both the person by whom the land is being let, and the person who is renting the land.

### K001  `uk_mlr_2017_27_cdd_27_7b`

Text: 27(7B) The letting agent must apply customer due diligence measures under paragraph (7A) in relation to both the person by whom the land is being let, and the person who is renting the land.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['verify_customer']:
  - Reviewer 1: 27(7B) requires the letting agent to apply CDD (under 28(2), identifying and verifying) to both the landlord and the tenant, i.e. it says whom the agent must identify as its customer. The guideline excludes 'on whom' only from cdd_triggers, so this is correctly not a trigger, but it is a requirement about identifying customers. Weak because generic 'apply customer due diligence measures' is labelled verify_customer nowhere else (27(1), 27(2) etc.). | guideline: verify_customer | identify the customer or verify the customer's identity | confidence: low

## Paragraph 27(8)

Whole paragraph (context):

- `uk_mlr_2017_27_cdd_27_8`: 27(8) A relevant person must also apply customer due diligence measures—
(za) when the relevant person has any legal duty in the course of the calendar year to contact an existing customer for the purpose of reviewing any information which—
- `uk_mlr_2017_27_cdd_27_8_i`: (i) is relevant to the relevant person’s risk assessment for that customer, and
- `uk_mlr_2017_27_cdd_27_8_ii`: (ii) relates to the beneficial ownership of the customer, including information which enables the relevant person to understand the ownership or control structure of a legal person, trust, foundation or similar arrangement who is the beneficial owner of the customer; (zb) when the relevant person has to contact an existing customer in order to fulfil any duty under the International Tax Compliance Regulations 2015 ;
- `uk_mlr_2017_27_cdd_27_8_a`: (a) at other appropriate times to existing customers on a risk based approach;
- `uk_mlr_2017_27_cdd_27_8_b`: (b) when the relevant person becomes aware that the circumstances of an existing customer relevant to its risk assessment for that customer have changed.

### K002  `uk_mlr_2017_27_cdd_27_8_a`

Text: (a) at other appropriate times to existing customers on a risk based approach;

Pre-registered types: ['cdd_triggers']
Pre-registered note: CDD on existing customers when reviewing beneficial ownership, at appropriate times and when circumstances change; (i) and (ii) describe the review in (za).

Alternative [] (no type):
  - Reviewer 1: 'at other appropriate times to existing customers on a risk based approach' names no event or circumstance. It is a risk-based periodic refresh of CDD on the existing book, closer to the excluded ongoing monitoring (28(11)(b): reviews of existing records and keeping CDD information up to date) than to an event trigger. The 27(8) lead-in keeps cdd_triggers through (za)/(zb) and (b). | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs / Requirements of other kinds that the system does not model: ... ongoing monitoring | confidence: low

## Paragraph 27(9)

Whole paragraph (context):

- `uk_mlr_2017_27_cdd_27_9`: 27(9) For the purposes of paragraph (8), in determining when it is appropriate to take customer due diligence measures in relation to existing customers, a relevant person must take into account, among other things—
- `uk_mlr_2017_27_cdd_27_9_a`: (a) any indication that the identity of the customer, or of the customer's beneficial owner, has changed;
- `uk_mlr_2017_27_cdd_27_9_b`: (b) any transactions which are not reasonably consistent with the relevant person's knowledge of the customer;
- `uk_mlr_2017_27_cdd_27_9_c`: (c) any change in the purpose or intended nature of the relevant person's relationship with the customer;
- `uk_mlr_2017_27_cdd_27_9_d`: (d) any other matter which might affect the relevant person's assessment of the money laundering or terrorist financing risk in relation to the customer.

### K003  `uk_mlr_2017_27_cdd_27_9`

Text: 27(9) For the purposes of paragraph (8), in determining when it is appropriate to take customer due diligence measures in relation to existing customers, a relevant person must take into account, among other things—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 2: Requires the firm, in deciding when CDD is due for existing customers, to take into account listed events, so it elaborates the 27(8) triggers. | hard case: 'For the purposes of paragraph (8) ... must take into account' could be read as only saying how 27(8)(a) is read, or as a risk-assessment input; I read its items (change in customer or BO identity, inconsistent transactions, change of purpose) as events that make CDD on existing customers due, and labelled the lead-in and (a) to (d) cdd_triggers.
  - Reviewer 3: Requires the firm to take listed matters into account when deciding when CDD on existing customers is due, i.e. it states the circumstances that trigger CDD (cdd_triggers). | hard case: Factors the firm 'must take into account' in deciding when CDD on existing customers is appropriate; each factor (identity or beneficial owner changed, inconsistent transactions, change of purpose, other risk matters) is a circumstance that makes CDD due. Labelled cdd_triggers on the lead-in and (a)-(d). Alternative: no type, read as guidance on how 27(8)(a) is applied, or as risk assessment.
  - Reviewer 1: 27(9) says when CDD on existing customers under 27(8) is 'appropriate' and lists the circumstances the firm must take into account. If 27(8)(a) ('at other appropriate times') is a trigger, the circumstances that make a time appropriate are the stated events: a change in the customer's or BO's identity, inconsistent transactions, a change in the purpose of the relationship. They are more concrete than 27(8)(a). Either 27(8)(a) loses cdd_triggers or 27(9) and its items (a)-(c) gain it. Item (d), 'any other matter which might affect the ... risk assessment', is risk assessment. | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs (... doubts about earlier information ...) | confidence: low

### K004  `uk_mlr_2017_27_cdd_27_9_a`

Text: (a) any indication that the identity of the customer, or of the customer's beneficial owner, has changed;

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 2: An indication that the identity of the customer or its beneficial owner has changed is an event that prompts CDD on an existing customer.
  - Reviewer 3: An indication that the identity of the customer or its beneficial owner has changed is a circumstance making CDD due under 27(8)-(9) (cdd_triggers).
  - Reviewer 1: 'any indication that the identity of the customer, or of the customer's beneficial owner, has changed' is a stated circumstance that should prompt CDD on an existing customer, comparable to 27(8)(b) (circumstances of an existing customer have changed), which is labelled cdd_triggers. | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs | confidence: low

### K005  `uk_mlr_2017_27_cdd_27_9_b`

Text: (b) any transactions which are not reasonably consistent with the relevant person's knowledge of the customer;

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 2: Transactions inconsistent with the firm's knowledge of the customer are an event that prompts CDD on an existing customer.
  - Reviewer 3: Transactions inconsistent with the firm's knowledge of the customer are a circumstance making CDD due under 27(8)-(9) (cdd_triggers).
  - Reviewer 1: 'any transactions which are not reasonably consistent with the relevant person's knowledge of the customer' is a stated circumstance for refreshing CDD under 27(8). It has the same character as 29(11)(b) (updated CDD where use is not consistent with knowledge of the customer), which is labelled cdd_triggers. Counter-argument: it is also an ongoing-monitoring signal. | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs | confidence: low

### K006  `uk_mlr_2017_27_cdd_27_9_c`

Text: (c) any change in the purpose or intended nature of the relevant person's relationship with the customer;

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 2: A change in the purpose or intended nature of the relationship is an event that prompts CDD on an existing customer.
  - Reviewer 3: A change in the purpose or nature of the relationship is a circumstance making CDD due under 27(8)-(9) (cdd_triggers).
  - Reviewer 1: 'any change in the purpose or intended nature of the relevant person's relationship with the customer' is a stated event for CDD on an existing customer, of the same kind as 27(8)(b). | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs | confidence: low

### K007  `uk_mlr_2017_27_cdd_27_9_d`

Text: (d) any other matter which might affect the relevant person's assessment of the money laundering or terrorist financing risk in relation to the customer.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 2: Any other matter affecting the customer's risk assessment is a circumstance to weigh in deciding when CDD is due, part of the same trigger list.
  - Reviewer 3: Any other matter affecting the risk assessment of the customer is a circumstance making CDD due under 27(8)-(9) (cdd_triggers).

## Paragraph 28(3)

Whole paragraph (context):

- `uk_mlr_2017_28_cdd_measures_28_3`: 28(3) Where the customer is a body corporate—
- `uk_mlr_2017_28_cdd_measures_28_3_a`: (a) the relevant person must obtain and verify—
- `uk_mlr_2017_28_cdd_measures_28_3_a_i`: (i) the name of the body corporate;
- `uk_mlr_2017_28_cdd_measures_28_3_a_ii`: (ii) its company number or other registration number;
- `uk_mlr_2017_28_cdd_measures_28_3_a_iii`: (iii) the address of its registered office, and if different, its principal place of business;
- `uk_mlr_2017_28_cdd_measures_28_3_b`: (b) subject to paragraph (5), the relevant person must take reasonable measures to determine and verify—
- `uk_mlr_2017_28_cdd_measures_28_3_b_i`: (i) the law to which the body corporate is subject, and its constitution (whether set out in its articles of association or other governing documents);
- `uk_mlr_2017_28_cdd_measures_28_3_b_ii`: (ii) the full names of the board of directors (or if there is no board, the members of the equivalent management body) and the senior persons responsible for the operations of the body corporate.

### K008  `uk_mlr_2017_28_cdd_measures_28_3_b_ii`

Text: (ii) the full names of the board of directors (or if there is no board, the members of the equivalent management body) and the senior persons responsible for the operations of the body corporate.

Pre-registered types: ['verify_customer']
Pre-registered note: Identification information about a customer that is a body corporate.

Alternative [] (no type):
  - Reviewer 2: (gave this clause no type) | hard case: Full names of the board of directors and senior persons are information about the body corporate customer (a reading that would give verify_customer), but directors and persons with executive authority are the customer's connected parties, which the guideline expressly excludes from verify_customer; I followed the exclusion. The 28(3)(b) lead-in keeps verify_customer through item (i).
  - Reviewer 3: (gave this clause no type) | hard case: The full names of the board of directors and senior persons of a body-corporate customer are customer-identification information in UK practice, but they are exactly MAS 'connected parties', which the guideline excludes from verify_customer. Not labelled. Alternative: verify_customer like its sibling 28(3)(b)(i).
  - Reviewer 1: 28(3)(b)(ii) requires the firm to determine and verify the full names of the board of directors and of the senior persons responsible for the operations of a body-corporate customer. These are the customer's directors and senior managers, i.e. its connected parties in the guideline's (MAS) sense, not the customer. The siblings 28(3)(a)(i)-(iii) (name, registration number, address) and 28(3)(b)(i) (governing law, constitution) are attributes of the customer itself and rightly verify_customer; (b)(ii) is about other natural persons and falls in the verify_customer carve-out. Same logic that correctly leaves 28(10) (persons acting for the customer) unlabelled. The 28(3)(b) lead-in keeps verify_customer through (b)(i). | guideline: It does not cover persons acting on the customer's behalf, connected parties or life-policy beneficiaries. | confidence: medium

## Paragraph 28(8)

Whole paragraph (context):

- `uk_mlr_2017_28_cdd_measures_28_8`: 28(8) If paragraph (7) applies, the relevant person must—
- `uk_mlr_2017_28_cdd_measures_28_8_a`: (a) keep records in writing of all the actions it has taken to identify the beneficial owner of the body corporate;
- `uk_mlr_2017_28_cdd_measures_28_8_b`: (b) take reasonable measures to verify the identity of the senior person in the body corporate responsible for managing it, and keep records in writing of—
- `uk_mlr_2017_28_cdd_measures_28_8_b_i`: (i) all the actions the relevant person has taken in doing so, and
- `uk_mlr_2017_28_cdd_measures_28_8_b_ii`: (ii) any difficulties the relevant person has encountered in doing so.

### K009  `uk_mlr_2017_28_cdd_measures_28_8`

Text: 28(8) If paragraph (7) applies, the relevant person must—

Pre-registered types: ['identify_ubo']
Pre-registered note: Where no beneficial owner can be identified, verify the senior managing person treated as beneficial owner; (a) and (b)(i)-(ii) are record keeping.

Alternative [] (no type):
  - Reviewer 1: The lead-in's own text ('If paragraph (7) applies, the relevant person must-') states no type. Its items are (a) record keeping and (b) verifying the senior managing person plus record keeping. If (b) is not identify_ubo (see the 28(8)(b) entry), the lead-in has no typed items. | guideline: A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items have type T. | confidence: low

### K010  `uk_mlr_2017_28_cdd_measures_28_8_b`

Text: (b) take reasonable measures to verify the identity of the senior person in the body corporate responsible for managing it, and keep records in writing of—

Pre-registered types: ['identify_ubo']
Pre-registered note: Where no beneficial owner can be identified, verify the senior managing person treated as beneficial owner; (a) and (b)(i)-(ii) are record keeping.

Alternative [] (no type):
  - Reviewer 1: 28(8)(b) applies only when the firm has exhausted all means of identifying the beneficial owner and failed (28(7)). The person to be verified is the senior person managing the body corporate, who is not a beneficial owner: 28(6) only permits the firm to 'treat' that person as one, a deeming permission that the guideline reads as interpretation. A senior manager is a connected party, excluded from verify_customer. The rest of (b) and all of (a) is record keeping. Counter-argument: in the usual beneficial-ownership cascade the senior managing official is the BO of last resort. | guideline: deeming provisions (...) are read as interpretation and not labelled / It does not cover persons acting on the customer's behalf, connected parties | confidence: low

## Paragraph 28(9)

Whole paragraph (context):

- `uk_mlr_2017_28_cdd_measures_28_9`: 28(9) Relevant persons do not satisfy their requirements under paragraph (4) by relying solely on information delivered to the registrar under any enactment that requires information to be delivered to the registrar about registrable persons, registrable relevant legal entities or registrable beneficial owners.

### K011  `uk_mlr_2017_28_cdd_measures_28_9`

Text: 28(9) Relevant persons do not satisfy their requirements under paragraph (4) by relying solely on information delivered to the registrar under any enactment that requires information to be delivered to the registrar about registrable persons, registrable relevant legal entities or registrable beneficial owners.

Pre-registered types: ['identify_ubo']
Pre-registered note: Beneficial owner identification may not rely solely on the company registers (a requirement on how the duty is met, like MAS 6.9 for customers).

Alternative [] (no type):
  - Reviewer 1: 28(9) imposes no act of its own; it says that the requirements under paragraph (4) are not satisfied by relying solely on information delivered to the companies registrar. That is a rule about how paragraph (4) is read (a negative deeming provision). The guideline treats the positive mirror image ('is to be treated as identifying', 30ZA(4)) as interpretation and the labels leave it unlabelled; the labels also leave 28(18)(a) and 28(19) (what counts as a reliable, independent source for verification) unlabelled. Labelling 28(9) but not those is inconsistent. The identify_ubo definition covers 'the information to obtain about them' and the ownership/control structure; 'the sources to use' appears only in the verify_customer definition. The label note's analogy to MAS 6.9 does not change the form of this paragraph. | guideline: Definitions, scope statements and paragraphs that only say how other paragraphs are read. / deeming provisions ("is to be treated as identifying") are read as interpretation and not labelled | confidence: medium

## Paragraph 29(7)

Whole paragraph (context):

- `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_7`: 29(7) The relevant person must apply customer due diligence measures to all anonymous accounts and passbooks in existence on the date on which these Regulations come into force, and in any event before such accounts or passbooks are used in any way.

### K012  `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_7`

Text: 29(7) The relevant person must apply customer due diligence measures to all anonymous accounts and passbooks in existence on the date on which these Regulations come into force, and in any event before such accounts or passbooks are used in any way.

Pre-registered types: ['cdd_triggers']
Pre-registered note: CDD on existing anonymous accounts and passbooks before they are used.

Alternative ['cdd_triggers', 'prohibit_anonymous']:
  - Reviewer 2: Requires CDD on all pre-existing anonymous accounts and passbooks before any use, which bars keeping anonymous accounts and makes their existence a CDD trigger. | hard case: Applying CDD to pre-existing anonymous accounts before use is the 'keep' half of the anonymous-account prohibition, and also CDD on a stated circumstance (accounts existing when the Regulations commence, like the guideline's 'revision of the Notice' trigger); I gave both. The same applies to 29(7A). Either type alone is a plausible reading.
  - Reviewer 3: Requires CDD on all anonymous accounts and passbooks existing at commencement and before any use, so existing anonymous accounts may not be kept (prohibit_anonymous) and the commencement of the Regulations triggers CDD (cdd_triggers). | hard case: Requires CDD on anonymous accounts already existing when the Regulations commenced, before they are used. It fits prohibit_anonymous ('not ... keep anonymous accounts') and cdd_triggers (the commencement of the law resembles the guideline's 'revision of the Notice' trigger). Alternative: only one of the two. 29(7A) (safe-deposit boxes, not strictly 'accounts') was treated the same way.
  - Reviewer 1: 29(6) bars setting up anonymous accounts (labelled prohibit_anonymous). 29(7) deals with anonymous accounts and passbooks that already exist: CDD must be applied to all of them, and in any event before they are used in any way. In effect the firm may not keep operating an anonymous account, which is the 'keep' half of the prohibit_anonymous definition. Labelling only the transitional trigger drops the prohibition, and the paragraph-level view of reg 29 then credits prohibit_anonymous only for new accounts. | guideline: prohibit_anonymous | not open or keep anonymous accounts or accounts in fictitious names. | confidence: medium

## Paragraph 29(7A)

Whole paragraph (context):

- `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_7a`: 29(7A) The relevant person must apply customer due diligence measures to all anonymous safe-deposit boxes in existence on 10th January 2019, and in any event before such safe-deposit boxes are used in any way.

### K013  `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_7a`

Text: 29(7A) The relevant person must apply customer due diligence measures to all anonymous safe-deposit boxes in existence on 10th January 2019, and in any event before such safe-deposit boxes are used in any way.

Pre-registered types: ['cdd_triggers']
Pre-registered note: CDD on existing anonymous safe-deposit boxes before they are used.

Alternative ['cdd_triggers', 'prohibit_anonymous']:
  - Reviewer 2: Requires CDD on all anonymous safe-deposit boxes existing on 10 January 2019 before any use, which bars keeping them anonymous and makes their existence a CDD trigger. | hard case: Same reasoning as 29(7), for anonymous safe-deposit boxes existing on 10 January 2019.
  - Reviewer 3: Requires CDD on all anonymous safe-deposit boxes existing on 10 January 2019 and before any use, so they may not be kept anonymous (prohibit_anonymous) and that date triggers CDD (cdd_triggers).
  - Reviewer 1: Same as 29(7), for anonymous safe-deposit boxes existing on 10 January 2019: CDD must be applied before they are used in any way, so they cannot be kept anonymous. 29(6), which covers safe-deposit boxes, is already labelled prohibit_anonymous, so the labels already treat safe-deposit boxes as within the type. | guideline: prohibit_anonymous | not open or keep anonymous accounts or accounts in fictitious names. | confidence: medium

## Paragraph 29(8)

Whole paragraph (context):

- `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_8`: 29(8) A relevant person which—
- `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_8_a`: (a) is an open-ended investment company within the meaning of regulation 2(1) of the Open-Ended Investment Companies Regulations 2001 ; and
- `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_8_b`: (b) is authorised on or after the date on which these Regulations come into force, may not issue shares evidenced by a share certificate (or any other documentary evidence) indicating that the holder of the certificate or document is entitled to the shares specified in it.

### K014  `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_8`

Text: 29(8) A relevant person which—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['prohibit_anonymous']:
  - Reviewer 1: Lead-in of the bearer-share prohibition; it is only meaningful with (b), which carries the 'may not issue'. It gets the type only if 29(8)(b) does. | guideline: A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items have type T. | confidence: low

### K015  `uk_mlr_2017_29_additional_cdd_measures_credit_institutions_and_financial_institutions_29_8_b`

Text: (b) is authorised on or after the date on which these Regulations come into force, may not issue shares evidenced by a share certificate (or any other documentary evidence) indicating that the holder of the certificate or document is entitled to the shares specified in it.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['prohibit_anonymous']:
  - Reviewer 1: Read with 29(8) and (a): a newly authorised open-ended investment company 'may not issue' bearer share certificates, i.e. instruments whose holder is anonymous. 'May not' is a prohibition, not a permission, and it sits next to the anonymous-account ban in 29(6). Weak because it concerns the firm's own shares, not customer accounts, and the type text names accounts. | guideline: prohibit_anonymous | not open or keep anonymous accounts or accounts in fictitious names. | confidence: low

## Paragraph 30ZA(2)

Whole paragraph (context):

- `uk_mlr_2017_30za_insolvent_bank_customers_30za_2`: 30ZA(2) Before permitting an insolvent bank customer to open an account and transact from it under paragraph (1), the credit institution must—
- `uk_mlr_2017_30za_insolvent_bank_customers_30za_2_a`: (a) identify the customer in accordance with regulation 28(2)(a); and
- `uk_mlr_2017_30za_insolvent_bank_customers_30za_2_b`: (b) where applicable, identify a person purporting to act on the customer’s behalf and verify that such person is authorised so to act in accordance with regulation 28(10)(a) and (b).

### K016  `uk_mlr_2017_30za_insolvent_bank_customers_30za_2`

Text: 30ZA(2) Before permitting an insolvent bank customer to open an account and transact from it under paragraph (1), the credit institution must—

Pre-registered types: ['verify_customer']
Pre-registered note: Identify an insolvent bank customer before letting it transact; (b) concerns a person acting on the customer's behalf.

Alternative [] (no type):
  - Reviewer 1: Like 30ZA(3), 30ZA(2) is a condition the 30ZA(1) permission is expressly 'subject to'. Comparable conditions on relaxations are unlabelled: 30(3) (verify during establishment provided completed as soon as practicable), 30(4) (safeguards proviso) and 31(5)(a) (the insolvency practitioner 'has taken all reasonable steps to satisfy the requirements set out in regulation 28(2) and (10)'). Only the 'must' wording separates 30ZA(2) from them. | guideline: Permissions and exemptions (...), including the exception conditions attached to a requirement. They relax an obligation rather than impose one. | confidence: low

### K017  `uk_mlr_2017_30za_insolvent_bank_customers_30za_2_a`

Text: (a) identify the customer in accordance with regulation 28(2)(a); and

Pre-registered types: ['verify_customer']
Pre-registered note: Identify an insolvent bank customer before letting it transact; (b) concerns a person acting on the customer's behalf.

Alternative [] (no type):
  - Reviewer 1: Item of 30ZA(2), 'identify the customer in accordance with regulation 28(2)(a)', as the minimum condition for using the 30ZA(1) permission. Same argument as 30ZA(2): it is a condition attached to a permission, compared with the unlabelled 31(5)(a) condition that also refers to satisfying regulation 28(2). | guideline: Permissions and exemptions (...), including the exception conditions attached to a requirement. | confidence: low

## Paragraph 30ZA(3)

Whole paragraph (context):

- `uk_mlr_2017_30za_insolvent_bank_customers_30za_3`: 30ZA(3) After permitting an insolvent bank customer to open an account and transact from it under paragraph (1), the credit institution must—
- `uk_mlr_2017_30za_insolvent_bank_customers_30za_3_a`: (a) apply the other customer due diligence measures required by regulation 28 as soon as practicable; and
- `uk_mlr_2017_30za_insolvent_bank_customers_30za_3_b`: (b) if it becomes apparent that any of the situations or cases set out in regulation 33(1) apply, carry out no further transactions from the insolvent bank customer’s account until it has completed the customer due diligence measures required by regulation 28, with the exception of regulation 28(11).

### K018  `uk_mlr_2017_30za_insolvent_bank_customers_30za_3`

Text: 30ZA(3) After permitting an insolvent bank customer to open an account and transact from it under paragraph (1), the credit institution must—

Pre-registered types: ['cdd_incomplete', 'cdd_triggers']
Pre-registered note: Apply the remaining CDD as soon as practicable; carry out no further transactions until CDD is complete when regulation 33(1) cases apply.

Alternative ['cdd_incomplete', 'identify_ubo', 'verify_customer']:
  - Reviewer 2: Lead-in introduces (a), completing the remaining regulation 28 measures as soon as practicable, and (b), stopping transactions until CDD is complete, so it carries the types of both items.
  - Reviewer 3: Lead-in introduces item (a), completing the remaining regulation 28 measures as soon as practicable (verify_customer, identify_ubo), and item (b), stopping transactions until CDD is completed (cdd_incomplete).
  - Reviewer 1: The lead-in's types follow its items. If (3)(a) is completion timing rather than a trigger, the lead-in should not carry cdd_triggers. 'After permitting an insolvent bank customer to open an account' restates the 30ZA(1) deferral, not a new CDD-triggering event. (If 30ZA(2)-(3) are instead read as conditions of the 30ZA(1) permission, see the 30ZA(3)(b) entry: then it gets no type.) | guideline: A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items have type T. | confidence: low

### K019  `uk_mlr_2017_30za_insolvent_bank_customers_30za_3_a`

Text: (a) apply the other customer due diligence measures required by regulation 28 as soon as practicable; and

Pre-registered types: ['cdd_triggers']
Pre-registered note: Apply the remaining CDD as soon as practicable; carry out no further transactions until CDD is complete when regulation 33(1) cases apply.

Alternative ['identify_ubo', 'verify_customer']:
  - Reviewer 2: Requires the remaining regulation 28 measures (customer verification and beneficial-owner identification and verification) to be applied as soon as practicable, a completion-timing requirement. | hard case: 'Apply the other customer due diligence measures required by regulation 28 as soon as practicable' names no specific measure; I read it as a completion deadline for the outstanding customer verification and beneficial-owner work, covered by 'when verification must be completed'. Alternatives: no type (generic CDD) or cdd_triggers (opening the account under 30ZA(1) as the event).
  - Reviewer 3: Requires the remaining regulation 28 measures (customer verification and beneficial-owner identification) to be completed as soon as practicable, i.e. when verification must be completed (verify_customer, identify_ubo). | hard case: 'Apply the other customer due diligence measures required by regulation 28 as soon as practicable' is generic CDD wording; I read it as setting when the remaining verification of the customer and identification of beneficial owners must be completed (the guideline puts timing of verification under verify_customer). Alternative: no type, because generic 'apply CDD' names neither identification nor beneficial owners.
  - Reviewer 1: The CDD duty for an insolvent bank customer is already triggered by establishing the relationship (27(1)(a)); 30ZA(1) only lets the bank defer completing it. 30ZA(3)(a) sets the deadline for completing the deferred reg 28 measures ('as soon as practicable'), i.e. when verification of the customer (28(2)(b)) and the BO (28(4)) must be completed. The guideline puts timing under verify_customer and says how CDD is done is not a trigger. It also clashes with 30(3), where the same 'completed as soon as practicable' wording is unlabelled. Counter-argument: the trigger list includes 'acquiring another institution's customers', which taking on a failed bank's customers resembles. | guideline: verify_customer | ... including the information to obtain, the sources to use and when verification must be completed. / Saying *how* CDD is done, or *on whom*, is not a trigger. | confidence: low

### K020  `uk_mlr_2017_30za_insolvent_bank_customers_30za_3_b`

Text: (b) if it becomes apparent that any of the situations or cases set out in regulation 33(1) apply, carry out no further transactions from the insolvent bank customer’s account until it has completed the customer due diligence measures required by regulation 28, with the exception of regulation 28(11).

Pre-registered types: ['cdd_incomplete']
Pre-registered note: Apply the remaining CDD as soon as practicable; carry out no further transactions until CDD is complete when regulation 33(1) cases apply.

Alternative [] (no type):
  - Reviewer 1: 30ZA(1): 'Subject to paragraphs (2) and (3), a credit institution may permit an insolvent bank customer to open an account and transact ... before completing CDD'. Paragraphs (2) and (3) are therefore the conditions the permission is subject to. The same rule elsewhere, no transactions until verification is complete, appears in 30(4) as the condition of a deferral permission ('provided that there are adequate safeguards in place to ensure that no transactions are carried out ... before verification has been completed') and is unlabelled. Labelling 30ZA(3)(b) cdd_incomplete but not 30(4) is inconsistent; on the guideline's text (exception conditions are not labelled) neither should be labelled. The alternative fix is to label 30(4) cdd_incomplete. | guideline: Permissions and exemptions ("may", "shall not be required to", "in lieu of"), including the exception conditions attached to a requirement. | confidence: low

## Paragraph 30A(1A)

Whole paragraph (context):

- `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a`: 30A(1A) The information specified in this paragraph is as follows—
- `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a_a`: (a) in relation to a firm of a type described in paragraphs (1)(a) to (e), information relating to beneficial owners of the customer; and
- `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a_b`: (b) in relation to an overseas entity of a type described in paragraph (1)(f), required information relating to registrable beneficial owners specified under Schedule 1 to the Economic Crime (Transparency and Enforcement) Act 2022.

### K021  `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a`

Text: 30A(1A) The information specified in this paragraph is as follows—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['identify_ubo']:
  - Reviewer 2: Specifies the beneficial ownership information the firm must collect under 30A(1), i.e. the list of information to obtain about beneficial owners. | hard case: Phrased like a definition ('The information specified in this paragraph is as follows'), but it is the list of beneficial-ownership information the firm must collect under 30A(1), which matches the guideline's example of an item in the information to obtain about a beneficial owner; labelled with (a) and (b).
  - Reviewer 3: Specifies the information the 30A(1) excerpt must contain, i.e. the beneficial-ownership information to obtain (identify_ubo). | hard case: A separate paragraph listing the beneficial-ownership information the 30A(1) register excerpt must contain; it could be read as a definition (excluded), but it functions as the list of information to obtain about beneficial owners. Labelled identify_ubo with its items. The 30A(1)(a)-(e) customer-type items are labelled because they sit inside the same requirement sentence; the discrepancy-reporting provisions are left unlabelled.
  - Reviewer 1: 30A(1A) lists the BO information the firm must collect from the register under 30A(1) and 30A(2A), both labelled identify_ubo. The guideline's own example of a typed sub-paragraph is 'an item in the list of information the bank shall obtain about a beneficial owner', and the parallel lists of customer information (28(3)(a)(i)-(iii)) are labelled. Weak because it is phrased as a definition ('The information specified in this paragraph is as follows') and definitions are not labelled. | guideline: e.g. an item in the list of information the bank shall obtain about a beneficial owner / identify_ubo | ... including the information to obtain about them | confidence: low

### K022  `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a_a`

Text: (a) in relation to a firm of a type described in paragraphs (1)(a) to (e), information relating to beneficial owners of the customer; and

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['identify_ubo']:
  - Reviewer 2: Item: information relating to the customer's beneficial owners is the information to be collected (identify_ubo).
  - Reviewer 3: The information to collect is information on the customer's beneficial owners (identify_ubo).
  - Reviewer 1: 'information relating to beneficial owners of the customer', the BO information to be collected from the register for companies, LLPs, Scottish partnerships and trusts under 30A(1)/(2A). Same argument and same counter-argument as 30A(1A). | guideline: identify_ubo | ... including the information to obtain about them | confidence: low

### K023  `uk_mlr_2017_30a_requirement_to_report_discrepancies_in_registers_30a_1a_b`

Text: (b) in relation to an overseas entity of a type described in paragraph (1)(f), required information relating to registrable beneficial owners specified under Schedule 1 to the Economic Crime (Transparency and Enforcement) Act 2022.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['identify_ubo']:
  - Reviewer 2: Item: required information on registrable beneficial owners of an overseas entity is the information to be collected (identify_ubo).
  - Reviewer 3: The information to collect for overseas entities is information on registrable beneficial owners (identify_ubo).
  - Reviewer 1: 'required information relating to registrable beneficial owners', the BO information to be collected from the register for overseas entities under 30A(1)(f)/(2A). Same argument and same counter-argument as 30A(1A). | guideline: identify_ubo | ... including the information to obtain about them | confidence: low

## Paragraph 35(1)

Whole paragraph (context):

- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1`: 35(1) A relevant person must have in place appropriate risk-management systems and procedures to determine whether a customer or the beneficial owner of a customer is—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1_a`: (a) a politically exposed person (a “PEP”); or
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1_b`: (b) a family member or a known close associate of a PEP, and to manage the enhanced risks arising from the relevant person's business relationship or transactions with such a customer.

### K024  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1`

Text: 35(1) A relevant person must have in place appropriate risk-management systems and procedures to determine whether a customer or the beneficial owner of a customer is—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 2: Requires systems to determine whether a customer or beneficial owner is a PEP and to manage the enhanced risks of such relationships, the gateway to PEP enhanced measures. | hard case: 'Have in place risk-management systems and procedures to determine whether ... a PEP' reads like screening and internal policies, both excluded; but (b) adds the duty to manage the enhanced risks of PEP relationships, and the paragraph is the gateway to PEP EDD, so I labelled the lead-in, (a) and (b) pep_edd. The alternative is no type for the whole paragraph.
  - Reviewer 3: Requires systems to determine whether a customer or beneficial owner is a PEP and to manage the enhanced risks of the relationship with such a customer; the risk-management duty is an enhanced measure because of PEP status (pep_edd). | hard case: 35(1) mixes PEP determination (screening) and 'have in place risk-management systems and procedures' (internal policies), both excluded, with a duty 'to manage the enhanced risks' of relationships with PEPs, which is an enhanced measure because of PEP status. I labelled the lead-in and both items pep_edd on the strength of the risk-management duty. Alternative reading: no type, as a screening/internal-systems provision whose actual measures sit in 35(3)-(5).
  - Reviewer 1: Lead-in carrying the 'must' for 35(1)(a)-(b): systems to determine whether a customer or its BO is a PEP and to manage the enhanced risks of relationships with such customers. If 35(1)(b) is pep_edd, the lead-in introduces a list whose items have that type. Weakened by the exclusions for screening and internal policies: determining PEP status is arguably screening. | guideline: A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items have type T. | confidence: low

### K025  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1_a`

Text: (a) a politically exposed person (a “PEP”); or

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 2: Item of the 35(1) requirement: determining whether the customer or beneficial owner is a PEP.
  - Reviewer 3: Names PEPs as the customers whose enhanced risks must be managed under 35(1) (pep_edd).
  - Reviewer 1: Item of the 35(1) list (customer or BO is a PEP); the 'manage the enhanced risks ... with such a customer' limb in (b) applies to both (a) and (b). If the list is pep_edd, (a) is part of that requirement. Same counter-argument (screening / internal policies) as 35(1). | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

### K026  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_1_b`

Text: (b) a family member or a known close associate of a PEP, and to manage the enhanced risks arising from the relevant person's business relationship or transactions with such a customer.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 2: Covers family members and close associates of PEPs and carries the duty to manage the enhanced risks of relationships with them (pep_edd).
  - Reviewer 3: Extends 35(1) to family members and close associates of PEPs and carries the duty to manage the enhanced risks of relationships with them (pep_edd).
  - Reviewer 1: Read with its lead-in, 35(1)(b) requires the firm to have systems and procedures to determine whether a customer or its beneficial owner is a family member or known close associate of a PEP 'and to manage the enhanced risks arising from the relevant person's business relationship or transactions with such a customer'. The second limb (in this record's text) is a duty to manage enhanced risk because the customer or a BO is a PEP or connected to one. The labels give pep_edd to 35(3)/(3)(b), which only requires assessing the extent of EDD; 35(1)(b) is at least as much an enhanced measure. Counter-argument: 'risk-management systems and procedures' could be read as internal policies, which are excluded. | guideline: pep_edd | apply enhanced measures because the customer or a beneficial owner is a PEP, or a family member or close associate of one. | confidence: medium

## Paragraph 35(3)

Whole paragraph (context):

- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3`: 35(3) If a relevant person has determined that a customer or a potential customer is a PEP, or a family member or known close associate of a PEP, the relevant person must assess—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3_a`: (a) the level of risk associated with that customer, and
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3_b`: (b) the extent of the enhanced customer due diligence measures to be applied in relation to that customer.

### K027  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3`

Text: 35(3) If a relevant person has determined that a customer or a potential customer is a PEP, or a family member or known close associate of a PEP, the relevant person must assess—

Pre-registered types: ['pep_edd']
Pre-registered note: Assess the extent of enhanced CDD for a PEP customer; (a) is a risk-level assessment.

Alternative [] (no type):
  - Reviewer 1: 35(3) requires only an assessment: of (a) the level of risk associated with the PEP customer and (b) the extent of enhanced CDD to apply. The measures themselves are imposed by 33(1)(d) and 35(5). The labels already drop (a) as a risk assessment; with (b) also an assessment step, the lead-in's own text ('must assess') states no pep_edd requirement. | guideline: Requirements of other kinds that the system does not model: risk assessment, ... | confidence: low

### K028  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3_a`

Text: (a) the level of risk associated with that customer, and

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 2: Item of the PEP-triggered assessment: the level of risk of the PEP customer, which calibrates the enhanced measures.
  - Reviewer 3: Assessing the risk of the PEP customer is part of the PEP-specific enhanced requirement in 35(3) (pep_edd).

### K029  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_3_b`

Text: (b) the extent of the enhanced customer due diligence measures to be applied in relation to that customer.

Pre-registered types: ['pep_edd']
Pre-registered note: Assess the extent of enhanced CDD for a PEP customer; (a) is a risk-level assessment.

Alternative [] (no type):
  - Reviewer 1: (a) 'assess the level of risk associated with that customer' and (b) 'assess the extent of the enhanced CDD measures to be applied' are two parts of one assessment duty under the same lead-in. The labels call (a) risk assessment and (b) pep_edd. Deciding how much EDD to apply is calibration of the risk-based approach, as in 28(12) (extent of measures must reflect the risk assessment), which is unlabelled. Either both are pep_edd or neither is. | guideline: Requirements of other kinds that the system does not model: risk assessment, ... | confidence: low

## Paragraph 35(4)

Whole paragraph (context):

- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4`: 35(4) In assessing the extent of the enhanced customer due diligence measures to be taken in relation to any particular person (which may differ from case to case), a relevant person—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4_a`: (a) must take account of any relevant information made available to the relevant person under regulations 17(9) and 47; and
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4_b`: (b) may take into account any guidance which has been—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4_b_i`: (i) issued by the FCA; or
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4_b_ii`: (ii) issued by any other supervisory authority or appropriate body and approved by the Treasury.

### K030  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4`

Text: 35(4) In assessing the extent of the enhanced customer due diligence measures to be taken in relation to any particular person (which may differ from case to case), a relevant person—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 1: If 35(3)(b) (assess the extent of PEP EDD) is pep_edd, then 35(4), which governs that same assessment ('In assessing the extent of the enhanced customer due diligence measures to be taken ...'), introduces a list whose mandatory item (a) is part of the same requirement. Labelling 35(3)(b) but not 35(4)/(4)(a) is inconsistent; the alternative fix is to drop 35(3)(b). | guideline: A lead-in gets type T when its own text states a requirement of type T, or introduces a list whose items have type T. | confidence: low

### K031  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_4_a`

Text: (a) must take account of any relevant information made available to the relevant person under regulations 17(9) and 47; and

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 1: 'must take account of any relevant information made available ... under regulations 17(9) and 47' when assessing the extent of PEP EDD. This is the same duty as 35(3)(b), which is labelled pep_edd. 35(4)(b) is a 'may' and stays unlabelled. | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

## Paragraph 35(5)

Whole paragraph (context):

- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_5`: 35(5) A relevant person who proposes to have, or to continue, a business relationship with a PEP, or a family member or a known close associate of a PEP, must, in addition to the measures required by regulation 33—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_5_a`: (a) have approval from senior management for establishing or continuing the business relationship with that person;
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_5_b`: (b) take adequate measures to establish the source of wealth and source of funds which are involved in the proposed business relationship or transactions with that person; and
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_5_c`: (c) where the business relationship is entered into, conduct enhanced ongoing monitoring of the business relationship with that person.

### K032  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_5_c`

Text: (c) where the business relationship is entered into, conduct enhanced ongoing monitoring of the business relationship with that person.

Pre-registered types: ['pep_edd']
Pre-registered note: PEP relationships: senior management approval, source of wealth and funds, enhanced ongoing monitoring (one list of enhanced measures, so (a) is pep_edd, not pep_approval).

Alternative [] (no type):
  - Reviewer 1: 'conduct enhanced ongoing monitoring of the business relationship' is ongoing monitoring, a category the guideline says the system does not model. The other items of 35(5), senior management approval and source of wealth/funds, carry pep_edd for the lead-in. Counter-argument: pep_edd is the specific type for enhanced PEP measures and this is one item of that list. | guideline: Requirements of other kinds that the system does not model: ... ongoing monitoring ... | confidence: low

## Paragraph 35(8)

Whole paragraph (context):

- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8`: 35(8) A relevant person must, in addition to the measures required by regulation 33, ensure that—
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8_a`: (a) its senior management is informed before it pays out any sums under an insurance policy the beneficiary of which is a PEP or a person who comes within paragraph (6)(b) in relation to a PEP, and
- `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8_b`: (b) its entire business relationship with the holder of the insurance policy (“the policy holder”) is scrutinised on an ongoing basis in accordance with enhanced procedures, whether or not the policy holder is a PEP or a family member or known close associate of a PEP.

### K033  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8`

Text: 35(8) A relevant person must, in addition to the measures required by regulation 33, ensure that—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 1: 35(8) has exactly the structure of 35(5), which is labelled pep_edd: 'A relevant person must, in addition to the measures required by regulation 33, ensure that ...'. It imposes enhanced measures (senior management informed before pay-out; the entire relationship with the policy holder scrutinised under enhanced procedures) because a PEP is involved. 35(9), labelled pep_edd, requires the firm to keep applying 'the requirements in paragraphs (5) and (8)' after a person stops being a PEP, so the labels treat (8)'s content as PEP measures in (9) but not at source. Against: the PEP here is the policy beneficiary, and the UK note says life-policy beneficiaries are not beneficial owners, while pep_edd needs the customer or a BO to be the PEP. | guideline: pep_edd | apply enhanced measures because the customer or a beneficial owner is a PEP | confidence: low

### K034  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8_a`

Text: (a) its senior management is informed before it pays out any sums under an insurance policy the beneficiary of which is a PEP or a person who comes within paragraph (6)(b) in relation to a PEP, and

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 1: Item of 35(8): senior management must be informed before any pay-out where the beneficiary is a PEP or a family member/close associate. If 35(8) is pep_edd this item is part of it. It is not pep_approval: 'informed' is not a sign-off, and it is one item of a list. Same beneficiary-is-not-BO counter-argument as 35(8). | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

### K035  `uk_mlr_2017_35_enhanced_cdd_politically_exposed_persons_35_8_b`

Text: (b) its entire business relationship with the holder of the insurance policy (“the policy holder”) is scrutinised on an ongoing basis in accordance with enhanced procedures, whether or not the policy holder is a PEP or a family member or known close associate of a PEP.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['pep_edd']:
  - Reviewer 1: Item of 35(8): the whole relationship with the policy holder (the customer) must be scrutinised under enhanced procedures when the beneficiary is a PEP. If 35(8) is pep_edd this item is part of it. Against: it is enhanced ongoing scrutiny (ongoing monitoring is excluded) and the trigger is the beneficiary's PEP status, not the customer's. | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

## Paragraph 37(8)

Whole paragraph (context):

- `uk_mlr_2017_37_application_of_simplified_cdd_37_8`: 37(8) A relevant person must not continue to apply simplified customer due diligence measures under paragraph (1)—
- `uk_mlr_2017_37_application_of_simplified_cdd_37_8_a`: (a) if it doubts the veracity or accuracy of any documents or information previously obtained for the purposes of identification or verification;
- `uk_mlr_2017_37_application_of_simplified_cdd_37_8_b`: (b) if its risk assessment changes and it no longer considers that there is a low degree of risk of money laundering and terrorist financing;
- `uk_mlr_2017_37_application_of_simplified_cdd_37_8_c`: (c) if it suspects money laundering or terrorist financing; or
- `uk_mlr_2017_37_application_of_simplified_cdd_37_8_d`: (d) if any of the conditions set out in regulation 33(1) apply.

### K036  `uk_mlr_2017_37_application_of_simplified_cdd_37_8`

Text: 37(8) A relevant person must not continue to apply simplified customer due diligence measures under paragraph (1)—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: 'must not continue to apply simplified customer due diligence measures' in the listed circumstances. In effect the firm must move to full CDD when those events occur. Two of the events, (a) doubts about earlier identification information and (c) suspicion, are named word for word in the cdd_triggers definition and labelled in 27(1)(c)-(d). Weak because the guideline excludes 'simplified CDD' as a whole. | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs (... a suspicion, doubts about earlier information ...) | confidence: low

### K037  `uk_mlr_2017_37_application_of_simplified_cdd_37_8_a`

Text: (a) if it doubts the veracity or accuracy of any documents or information previously obtained for the purposes of identification or verification;

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: 'if it doubts the veracity or accuracy of any documents or information previously obtained for the purposes of identification or verification', nearly identical to 27(1)(d) (labelled cdd_triggers). Same simplified-CDD counter-argument as 37(8). | guideline: cdd_triggers | ... (... doubts about earlier information ...) | confidence: low

### K038  `uk_mlr_2017_37_application_of_simplified_cdd_37_8_c`

Text: (c) if it suspects money laundering or terrorist financing; or

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: 'if it suspects money laundering or terrorist financing', identical to 27(1)(c) (labelled cdd_triggers). Same simplified-CDD counter-argument as 37(8). | guideline: cdd_triggers | ... (... a suspicion ...) | confidence: low

## Paragraph 38(2)

Whole paragraph (context):

- `uk_mlr_2017_38_electronic_money_38_2`: 38(2) Paragraph (1) does not apply to any transaction which consists of the redemption in cash, or a cash withdrawal, of the monetary value of the electronic money, where—
- `uk_mlr_2017_38_electronic_money_38_2_a`: (a) the amount redeemed exceeds £50; or
- `uk_mlr_2017_38_electronic_money_38_2_b`: (b) in the case of remote payment transactions, the amount redeemed exceeds £50 per transaction.

### K039  `uk_mlr_2017_38_electronic_money_38_2`

Text: 38(2) Paragraph (1) does not apply to any transaction which consists of the redemption in cash, or a cash withdrawal, of the monetary value of the electronic money, where—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: 38(2) withdraws the e-money exemption in 38(1) for cash redemptions and withdrawals above £50, so CDD applies to those transactions: a monetary-threshold event of the same kind as 27(2), 27(3) and 27(5), which are labelled cdd_triggers. Weak because it is worded as a scope statement on paragraph (1) ('Paragraph (1) does not apply to ...'). | guideline: cdd_triggers | perform CDD measures when a stated event or circumstance occurs (... a transaction above a threshold ...) | confidence: low

### K040  `uk_mlr_2017_38_electronic_money_38_2_a`

Text: (a) the amount redeemed exceeds £50; or

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: The threshold condition (amount redeemed exceeds £50) of the 38(2) carve-back; part of the trigger if 38(2) is one, as with 27(7C)(a)-(b). | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

### K041  `uk_mlr_2017_38_electronic_money_38_2_b`

Text: (b) in the case of remote payment transactions, the amount redeemed exceeds £50 per transaction.

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['cdd_triggers']:
  - Reviewer 1: The per-transaction £50 threshold for remote payment transactions in the 38(2) carve-back; part of the trigger if 38(2) is one. | guideline: A sub-paragraph is read together with the lead-in of its paragraph. It gets type T when it is part of a requirement of type T | confidence: low

## Paragraph 38(4A)

Whole paragraph (context):

- `uk_mlr_2017_38_electronic_money_38_4a`: 38(4A) Credit institutions and financial institutions, acting as acquirers for payment using an anonymous prepaid card issued in a third country, shall only accept payment where—
- `uk_mlr_2017_38_electronic_money_38_4a_a`: (a) the anonymous prepaid card is subject to requirements in national legislation having an equivalent effect to those laid down in this regulation; and
- `uk_mlr_2017_38_electronic_money_38_4a_b`: (b) the anonymous prepaid card satisfies those requirements.

### K042  `uk_mlr_2017_38_electronic_money_38_4a`

Text: 38(4A) Credit institutions and financial institutions, acting as acquirers for payment using an anonymous prepaid card issued in a third country, shall only accept payment where—

Pre-registered types: [] (no type)
Pre-registered note: (none)

Alternative ['prohibit_anonymous']:
  - Reviewer 1: Credit and financial institutions acting as acquirers 'shall only accept payment' made with an anonymous prepaid card issued in a third country if the card is subject to equivalent requirements. This is a 'shall' restriction on anonymous payment instruments. Weak: the firm is not opening or keeping an account, which is what the type text names. | guideline: prohibit_anonymous | not open or keep anonymous accounts or accounts in fictitious names. | confidence: low

