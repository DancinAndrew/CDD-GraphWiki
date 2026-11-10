"""
Language frames for the version-2 rule-based extractor.

Version 1 matched phrases copied from the development paragraphs, so it found 1 of 18 obligations in unseen
MAS Notice 626 paragraphs. Version 2 looks at how a requirement is phrased instead:

- Deontic frame: an action counts only when a modal ("shall", "must", "should", "is required to") governs it,
  when a list item starts with it ("(b) Identify the beneficial owners ..."), or in a passive such as
  "every customer must be identified". "Failure to verify a UBO" is not a duty to verify.
- Permissions and exemptions ("the bank may obtain", "shall not be required to", "in lieu of") switch the
  sentence off.
- Subject: who must be identified decides the type. The customer, or the originator or beneficiary of a
  transfer, gives verify_customer; a beneficial owner gives identify_ubo; persons acting on the customer's
  behalf and connected parties give neither. "Person identified under paragraph 6.14" and "for the purposes
  of paragraph 6.5" are resolved by looking up the referenced paragraph.
- Lists: an item inherits its lead-in's types when the lead-in introduces conditions, enumerated measures or
  identification information; an imperative item ("(b) record adequate details") is a separate duty; items
  after "except where" are exceptions.
- A clause can carry several types.

Nothing here refers to a document, a paragraph number or a jurisdiction.
"""
import re
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Set

TYPES = ("prohibit_anonymous", "cdd_triggers", "verify_customer", "identify_ubo",
         "pep_edd", "pep_prohibition", "pep_approval", "cdd_incomplete")
IDENTIFICATION = {"verify_customer", "identify_ubo"}

# --- text helpers ------------------------------------------------------------------------------------------

def body_text(raw: str) -> str:
    """Lower-cased clause text without the Markdown heading marker, paragraph number or list label."""
    text = raw.strip()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\d+[a-zA-Z]?(?:\.\d+[a-zA-Z]?)*(?:\(\d+[a-zA-Z]?\))*\s+", "", text)
    text = re.sub(r"^\((?:[a-z]{1,2}|[ivx]+|\d+|[a-z]\.[a-z]+)\)\s*", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def sentences(text: str) -> List[str]:
    protected = re.sub(r"\b(e\.g|i\.e|etc)\.", lambda m: m.group(0).replace(".", "§"), text)
    return [p.replace("§", ".").strip() for p in re.split(r"(?<=[.;])\s+", protected) if p.strip()]


MODAL = re.compile(r"\b(?:shall|must|should|(?:is|are|be) required to|(?:is|are) to)\b")
PERMISSION = re.compile(
    r"\b(?:may|need not)\s+(?!not\b)(?:\w+\s+){0,2}?(?:perform|adopt|obtain|establish|rely|apply|take|use|defer|"
    r"accept|retain|collect|exclude|choose|decide|provide|include|determine|carry|undertake|treat|commence|"
    r"continue|stop|open)\b")
EXEMPTION = re.compile(r"\bnot be required to\b|\bnot required to\b|\bonly be required to\b|\bin lieu of\b|"
                       r"\bdoes not apply\b|\bshall not apply\b|\bneed not\b|\bexempt(?:ed)? from\b")
PEP = re.compile(r"politically exposed|\bpeps?\b")
PERCENT = re.compile(r"\d{1,3}\s?%")
AMOUNT = re.compile(r"(?:usd/eur|s\$|sgd|eur|€|£|\$)\s?\d")

# A list item that starts with a verb is a duty of its own ("(b) record adequate details ...").
IMPERATIVE_START = re.compile(
    r"^(?:not\s+)?(?:identify|identifying|verify|verifying|inquire|perform|performing|apply|applying|undertake|"
    r"undertaking|obtain|obtaining|establish|establishing|conduct|conducting|develop|implement|record|document|"
    r"keep|maintain|monitor|file|submit|report|assess|ensure|take|taking|provide|include|retain|screen|gather|"
    r"determine|complete|clearly|understand|understanding|consider|treat|refer|seek|carry out|carrying out|"
    r"substantiate|notify|apply)\b")


def is_permission(sentence: str) -> bool:
    return bool(PERMISSION.search(sentence) or EXEMPTION.search(sentence))


def governed(sentence: str, pattern: re.Pattern, window: int = 70) -> List[re.Match]:
    """Matches of `pattern` that a modal governs (within `window` characters after it) or that start the item."""
    hits: List[re.Match] = []
    for modal in MODAL.finditer(sentence):
        span_end = min(len(sentence), modal.end() + window)
        hit = pattern.search(sentence, modal.end(), len(sentence))
        if hit and hit.start() <= span_end:
            hits.append(hit)
    start = pattern.match(sentence)
    if start:
        hits.append(start)
    return hits


# --- who must be identified --------------------------------------------------------------------------------

IDENT_CUE = re.compile(r"\b(?:identify|identifying|verify|verifying|inquire(?: into| if| whether)?|"
                       r"(?:complete |completing )?(?:verification|identification) of)\b")
CUSTOMER_HEAD = re.compile(
    r"^(?:(?:the|a|an|each|every|that|such|any|all|its|their|existing)\s+)*"
    r"(?:customer|customers|client|clients|(?:(?:wire|value)\s+)?transfer\s+(?:originator|beneficiary)|originator)\b")
BO_ANY = re.compile(r"beneficial owner|\bubos?\b|ultimately (?:own|control)|ultimate (?:effective )?control|"
                    r"controlling ownership interest")
XREF_PERSON = re.compile(r"\bpersons?\s+identified\s+under\s+paragraph\s+(\d+[a-z]?(?:\.\d+[a-z]?)?)")
FOR_PURPOSES = re.compile(r"\bfor the purposes? of paragraph\s+(\d+[a-z]?(?:\.\d+[a-z]?)?)\b")
ANAPHORA = re.compile(r"^(?:such|that|the)\s+(?:verification|identification)\b")
PASSIVE_CUSTOMER = re.compile(r"\b(?:customer|customers|client|clients)\b[^.;:]{0,60}?\b(?:shall|must|should)\s+be\s+"
                              r"(?:identified|verified)\b")
OWNERSHIP_STRUCTURE = re.compile(r"\bunderstand(?:ing)?\b[^.;]{0,80}\bownership and control structure")
OWNERSHIP_THRESHOLD = re.compile(r"controlling ownership interest|ownership threshold|beneficial owner|\bubos?\b")
INFO_OBJECT = re.compile(r"^(?:and verify\s+)?(?:at least\s+)?(?:the following|such)\s+information\b")
OBTAIN = re.compile(r"\b(?:obtain|obtaining)\b")

Lookup = Callable[[str], Set[str]]


def _object_after(sentence: str, end: int) -> str:
    rest = sentence[end:]
    stop = re.search(r"[;:]|\.(?=\s|$)", rest)  # a full stop ends the object, the dot in "6.14" does not
    return rest[: stop.start()] if stop else rest


def subject_types(obj: str, lookup: Lookup) -> Set[str]:
    """Identification types for the object of an identify/verify verb."""
    o = obj.strip(" ,")
    o = re.sub(r"^(?:and|or)\s+(?:take reasonable (?:measures|steps) to\s+)?(?:verify|identify)\s+", "", o)
    o = re.sub(r"^(?:the\s+)?identit(?:y|ies)\s+of\s+", "", o)
    found: Set[str] = set()
    if CUSTOMER_HEAD.match(o):
        found.add("verify_customer")
    if BO_ANY.search(o):
        found.add("identify_ubo")
    xref = XREF_PERSON.search(o)
    if xref:
        found |= lookup(xref.group(1)) & IDENTIFICATION
    return found


def mentioned_identification(text: str, lookup: Lookup) -> Set[str]:
    """Who the text talks about identifying or verifying, whether or not it is a duty (used for "such verification")."""
    found: Set[str] = set()
    for sentence in sentences(text):
        for hit in IDENT_CUE.finditer(sentence):
            found |= subject_types(_object_after(sentence, hit.end()), lookup)
    return found


# --- the eight types for one sentence ----------------------------------------------------------------------

CDD_OBJECT = re.compile(r"^\s*(?:the |all |such |appropriate )?(?:(?:customer due diligence|cdd)(?: \(cdd\))? measures|"
                        r"measures (?:as )?required by paragraphs?\b)")
TRIGGER_VERB = re.compile(r"\b(?:perform|apply|undertake|carry out|conduct)(?:s|ing|ed)?\b")
# A trigger needs a condition: a conjunction ("when", "where", "if", "before"), a relative clause on the actor
# ("a bank that undertakes any transaction ... shall"), or a monetary threshold on a transaction.
CONDITION = re.compile(r"(?<!as )\b(?:when|whenever|where|if|before|prior to|upon|at the time of)\b|"
                       r"\b(?:that|which|who)\s+(?:undertakes|effects|receives|establishes|carries out|enters into)\b")
ANONYMOUS = re.compile(r"anonymous (?:account|accounts|passbook|safe)|fictitious name")
PROHIBITION = re.compile(r"\bprohibit|\bno\b[^.;]{0,40}\b(?:shall|may|must)\b|\b(?:shall|must|may|should) not\b")
UNABLE = re.compile(r"\b(?:unable|not able|fail(?:s|ed|ure)?) to (?:complete|apply|comply|carry out|perform)\b")
STOP = re.compile(r"\b(?:shall|must|should|may) not (?:commence|continue|establish|execute|carry out|undertake|open|"
                  r"enter|proceed)\b|\b(?:terminate|cease|discontinue)\b")
ENHANCED = re.compile(r"\benhanced (?:cdd|customer due diligence|due diligence|measures|monitoring|ongoing monitoring)\b")
REFUSE = re.compile(r"\bprohibit\w*|\b(?:shall|must|should|may) not (?:establish|enter|open|maintain|commence|continue)\b|"
                    r"\brefuse\b|\breject\w*")
RELATIONSHIP = re.compile(r"business relation|relationship|account|onboarding")
APPROVAL = re.compile(r"\bapproved by\b|\bapproval (?:of|from)\b|\bsign(?:ed)?[ -]off by\b")


def _trigger(sentence: str, parent_text: str) -> bool:
    for verb in governed(sentence, TRIGGER_VERB):
        before = sentence[max(0, verb.start() - 25): verb.start()]
        if "in addition to" in before or "third party to" in before:
            continue
        if not CDD_OBJECT.match(sentence[verb.end():]):
            continue
        scope = f"{parent_text} {sentence}"
        if CONDITION.search(scope) or (AMOUNT.search(scope) and "transaction" in scope):
            return True
    return False


@dataclass
class ClauseView:
    """What the frames need to know about one clause."""
    body: str                 # own text (see body_text)
    parent_body: str          # text of the enclosing clauses, nearest last
    parent_types: Set[str]    # final types of the direct parent
    parent_kind: str          # list kind of the direct parent (see list_kind)


def own_types(view: ClauseView, lookup: Lookup) -> Set[str]:
    found: Set[str] = set()
    for sentence in sentences(view.body):
        if is_permission(sentence):
            continue
        if ANONYMOUS.search(sentence) and PROHIBITION.search(sentence):
            found.add("prohibit_anonymous")
        if UNABLE.search(sentence) and STOP.search(sentence):
            found.add("cdd_incomplete")
        if _trigger(sentence, view.parent_body):
            found.add("cdd_triggers")
        has_modal = bool(MODAL.search(sentence))
        if PEP.search(sentence):
            if REFUSE.search(sentence) and RELATIONSHIP.search(sentence):
                found.add("pep_prohibition")  # "prohibits" is itself deontic, no modal needed
            if has_modal and ENHANCED.search(sentence):
                found.add("pep_edd")
            in_edd_list = view.parent_kind == "measures" and "pep_edd" in view.parent_types
            if has_modal and APPROVAL.search(sentence) and not in_edd_list:
                found.add("pep_approval")
        # identification of the customer or of beneficial owners
        for hit in governed(sentence, IDENT_CUE):
            obj = _object_after(sentence, hit.end())
            if ANAPHORA.match(sentence[hit.start():]) or re.match(r"^\s*such\b", obj):
                found |= mentioned_identification(view.parent_body, lookup)
            found |= subject_types(obj, lookup)
        if re.search(r"\bsuch (?:verification|identification)\b", sentence) and governed(sentence, re.compile(r"\bcomplete\b")):
            found |= mentioned_identification(view.parent_body, lookup)
        if PASSIVE_CUSTOMER.search(sentence):
            found.add("verify_customer")
        if governed(sentence, OWNERSHIP_STRUCTURE, window=120):
            found.add("identify_ubo")
        for hit in governed(sentence, OBTAIN):
            if INFO_OBJECT.match(sentence[hit.end():].strip()):
                purpose = FOR_PURPOSES.search(view.body)
                if purpose:
                    found |= lookup(purpose.group(1)) & IDENTIFICATION
    # an ownership threshold for beneficial owners is part of the identification duty, even in a footnote
    # ("a controlling ownership interest ... may be based on a threshold (e.g. 25%)")
    if OWNERSHIP_THRESHOLD.search(view.body) and PERCENT.search(view.body):
        found.add("identify_ubo")
    return found


# --- lists -------------------------------------------------------------------------------------------------

INTRODUCER = r"[–—\-:⎯]"


def list_kind(body: str) -> str:
    """How a lead-in relates to the items under it."""
    tail = body[-200:]
    if re.search(rf"\b(?:except|unless|other than|save)\b[^.;]*{INTRODUCER}\s*$", tail):
        return "exception"
    if re.search(r"following (?:information|types of|details|particulars)", body):
        return "info"
    if re.search(r"following (?:enhanced |additional )?(?:cdd |customer due diligence )?measures|\bas follows\b", body):
        return "measures"
    if re.search(rf"\b(?:when|whenever|if|where|before|in the following (?:circumstances|cases))\s*{INTRODUCER}?\s*$", body):
        return "condition"
    if re.search(r"\bfollowing\b", body):
        return "other"
    if re.search(rf"{INTRODUCER}\s*$", body):
        return "duty"
    return "none"


def inherited_types(view: ClauseView, own: Set[str]) -> Set[str]:
    """Types an item takes over from its lead-in."""
    if own or not view.parent_types:
        return set()
    if any(is_permission(s) for s in sentences(view.body)):
        return set()
    kind = view.parent_kind
    if kind in ("exception", "other"):
        return set()
    if kind == "info":
        return view.parent_types & IDENTIFICATION
    if kind in ("measures", "condition"):
        return set(view.parent_types)
    if IMPERATIVE_START.match(view.body):
        return set()  # a separate duty under "the bank shall –"
    return set(view.parent_types)


def propagate_up(lead_types: Set[str], lead_kind: str, child_types: Iterable[Set[str]]) -> Set[str]:
    """A lead-in such as "the bank shall –" with no type of its own takes the single type its items share."""
    if lead_types or lead_kind != "duty":
        return lead_types
    typed = [t for t in child_types if t]
    if typed and all(t == typed[0] for t in typed):
        return set(typed[0])
    return lead_types


def classify(clauses: List, paragraph_of: Callable[[object], str]) -> Dict[str, Set[str]]:
    """
    Types for every clause of one document, in two passes: the first gives each paragraph's own types so that
    cross-references ("person identified under paragraph 6.14") can be resolved in the second.
    `clauses` are objects with clause_id, parent_clause_id and raw_text, in document order.
    """
    by_id = {c.clause_id: c for c in clauses}
    bodies = {c.clause_id: body_text(c.raw_text) for c in clauses}

    def parent_chain_text(clause) -> str:
        parts, parent_id = [], clause.parent_clause_id
        while parent_id and parent_id in by_id:
            parent = by_id[parent_id]
            if not re.match(r"^#{1,2}\s", parent.raw_text):  # skip document and section titles
                parts.append(bodies[parent_id])
            parent_id = parent.parent_clause_id
        return " ".join(reversed(parts))

    # pass 1: own types without cross-references, kept for the lead-in of every paragraph
    paragraph_types: Dict[str, Set[str]] = {}
    no_lookup: Lookup = lambda ref: set()
    for c in clauses:
        view = ClauseView(bodies[c.clause_id], parent_chain_text(c), set(), "none")
        paragraph = paragraph_of(c).lower()
        if paragraph and paragraph not in paragraph_types:
            paragraph_types[paragraph] = own_types(view, no_lookup)
    lookup: Lookup = lambda ref: paragraph_types.get(ref.lower(), set())

    # pass 2: own types with cross-references, then inheritance from the lead-in (parents come first)
    types: Dict[str, Set[str]] = {}
    for c in clauses:
        parent = by_id.get(c.parent_clause_id) if c.parent_clause_id else None
        parent_is_title = parent is not None and re.match(r"^#{1,2}\s", parent.raw_text)
        view = ClauseView(
            body=bodies[c.clause_id],
            parent_body=parent_chain_text(c),
            parent_types=set(types.get(parent.clause_id, set())) if parent is not None and not parent_is_title else set(),
            parent_kind=list_kind(bodies[parent.clause_id]) if parent is not None and not parent_is_title else "none",
        )
        own = own_types(view, lookup)
        types[c.clause_id] = own | inherited_types(view, own)

    # pass 3: lead-ins that only introduce duties take the type their items share
    children: Dict[str, List[str]] = {}
    for c in clauses:
        if c.parent_clause_id:
            children.setdefault(c.parent_clause_id, []).append(c.clause_id)
    for c in reversed(clauses):
        kids = children.get(c.clause_id)
        if kids and not re.match(r"^#{1,2}\s", c.raw_text):
            types[c.clause_id] = propagate_up(types[c.clause_id], list_kind(bodies[c.clause_id]),
                                              (types[k] for k in kids))
    return types
