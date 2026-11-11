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

Every decision keeps its reasons: `classify_traced` returns, for each clause and type, the rules that fired, a
one-sentence message and the exact text (character offsets into the clause's raw_text) that made each rule fire,
including every alternative that would have fired on its own. `classify` returns the same types without the
reasons; both run the same code. src/extraction/faithfulness.py checks the reasons with deletion tests.

Nothing here refers to a document, a paragraph number or a jurisdiction.
"""
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from src.contracts.models import EvidenceSpan, RuleReason

TYPES = ("prohibit_anonymous", "cdd_triggers", "verify_customer", "identify_ubo",
         "pep_edd", "pep_prohibition", "pep_approval", "cdd_incomplete")
IDENTIFICATION = {"verify_customer", "identify_ubo"}

# --- text helpers ------------------------------------------------------------------------------------------

# what body_text removes from the start of a clause, in this order
BODY_PREFIXES = (
    re.compile(r"^#+\s*"),                                                    # Markdown heading marker
    re.compile(r"^\d+[a-zA-Z]?(?:\.\d+[a-zA-Z]?)*(?:\(\d+[a-zA-Z]?\))*\s+"),  # paragraph number
    re.compile(r"^\((?:[a-z]{1,2}|[ivx]+|\d+|[a-z]\.[a-z]+)\)\s*"),          # list label
)
WHITESPACE = re.compile(r"\s+")
ABBREVIATION = re.compile(r"\b(e\.g|i\.e|etc)\.")
SENTENCE_BREAK = re.compile(r"(?<=[.;])\s+")
TITLE = re.compile(r"^#{1,2}\s")  # document and section titles


def _strip_prefixes(raw: str) -> Tuple[int, str]:
    """(index in raw where the remaining text starts, remaining text) after the heading, number and list label."""
    text = raw.strip()
    offset = len(raw) - len(raw.lstrip())
    for prefix in BODY_PREFIXES:
        match = prefix.match(text)
        if match:
            text = text[match.end():]
            offset += match.end()
    return offset, text


def body_text(raw: str) -> str:
    """Lower-cased clause text without the Markdown heading marker, paragraph number or list label."""
    _, text = _strip_prefixes(raw)
    return WHITESPACE.sub(" ", text).strip().lower()


def body_offsets(raw: str) -> List[int]:
    """For every character of body_text(raw), the index in raw it comes from (a collapsed space maps to the
    first whitespace character of its run)."""
    offset, text = _strip_prefixes(raw)
    chars: List[str] = []
    positions: List[int] = []
    i = 0
    for run in WHITESPACE.finditer(text):
        chars.extend(text[i:run.start()])
        positions.extend(range(offset + i, offset + run.start()))
        chars.append(" ")
        positions.append(offset + run.start())
        i = run.end()
    chars.extend(text[i:])
    positions.extend(range(offset + i, offset + len(text)))
    while chars and chars[0].isspace():
        chars.pop(0)
        positions.pop(0)
    while chars and chars[-1].isspace():
        chars.pop()
        positions.pop()
    lowered = "".join(chars).lower()
    if len(lowered) != len(chars):  # a character whose lower case is longer, e.g. "İ"
        # Only the lengths come from lowering one character at a time: str.lower() on the whole string depends on
        # context (a word-final "Σ" becomes "ς", on its own "σ"), but never changes how many characters one gives.
        positions = [pos for ch, pos in zip(chars, positions) for _ in range(len(ch.lower()))]
    if lowered != body_text(raw) or len(positions) != len(lowered):
        raise ValueError("body offset map does not rebuild body_text")
    return positions


def body_start(raw: str) -> int:
    """Index in raw where body_text's text starts; len(raw) when the body is empty."""
    positions = body_offsets(raw)
    return positions[0] if positions else len(raw)


def is_list_item(raw: str) -> bool:
    """Whether the clause has a list label such as "(a)" after its heading marker and paragraph number."""
    text = raw.strip()
    for prefix in BODY_PREFIXES[:-1]:
        match = prefix.match(text)
        if match:
            text = text[match.end():]
    return bool(BODY_PREFIXES[-1].match(text))


def sentence_spans(text: str) -> List[Tuple[int, str]]:
    """(start offset in text, sentence) for every sentence; sentences() is this without the offsets."""
    protected = ABBREVIATION.sub(lambda m: m.group(0).replace(".", "§"), text)
    parts: List[Tuple[int, str]] = []
    start = 0
    for brk in SENTENCE_BREAK.finditer(protected):
        parts.append((start, protected[start:brk.start()]))
        start = brk.end()
    parts.append((start, protected[start:]))
    return [(start + len(p) - len(p.lstrip()), p.replace("§", ".").strip()) for start, p in parts if p.strip()]


def sentences(text: str) -> List[str]:
    return [s for _, s in sentence_spans(text)]


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


@dataclass
class Governed:
    """A match that a modal governs or that starts the item, with every modal that governs it."""
    hit: re.Match
    modals: List[re.Match] = field(default_factory=list)
    starts_item: bool = False


def governing(sentence: str, pattern: re.Pattern, window: int = 70) -> List[Governed]:
    """Matches of `pattern` that a modal governs (the first match within `window` characters after the modal)
    or that start the item, each once."""
    by_span: Dict[Tuple[int, int], Governed] = {}
    for modal in MODAL.finditer(sentence):
        span_end = min(len(sentence), modal.end() + window)
        hit = pattern.search(sentence, modal.end(), len(sentence))
        if hit and hit.start() <= span_end:
            by_span.setdefault(hit.span(), Governed(hit)).modals.append(modal)
    start = pattern.match(sentence)
    if start:
        by_span.setdefault(start.span(), Governed(start)).starts_item = True
    return list(by_span.values())


def governed(sentence: str, pattern: re.Pattern, window: int = 70) -> List[re.Match]:
    """Matches of `pattern` that a modal governs (within `window` characters after it) or that start the item."""
    return [g.hit for g in governing(sentence, pattern, window)]


# --- reasons -----------------------------------------------------------------------------------------------

# (where, start, end): inside own_reasons `where` is "own" (offsets into ClauseView.body) or "parent" (offsets into
# ClauseView.parent_body); classify turns both into (clause_id, offsets into that clause's body_text).
Span = Tuple[str, int, int]


@dataclass
class Reason:
    rule: str
    type: str
    message: str
    spans: List[Span] = field(default_factory=list)
    refs: List[str] = field(default_factory=list)        # paragraphs whose lead-in label this reason relies on
    depends_on: List[str] = field(default_factory=list)  # "<clause_id>#<type>"


def _q(match_or_text) -> str:
    text = match_or_text.group(0) if isinstance(match_or_text, re.Match) else match_or_text
    return f'"{text.strip()}"'


def _governor(g: Governed, item_start: bool = False) -> str:
    """`item_start`: the sentence is the first one of a list item, so the match that opens it opens the item."""
    if g.modals:
        return f"{_q(g.modals[0])} governs {_q(g.hit)}"
    return f"the {'item' if item_start else 'sentence'} starts with {_q(g.hit)}"


def _say(text: str) -> str:
    return text[0].upper() + text[1:]


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
OBJECT_END = re.compile(r"[;:]|\.(?=\s|$)")  # a full stop ends the object, the dot in "6.14" does not
SUBJECT_PREFIXES = (
    re.compile(r"^(?:and|or)\s+(?:take reasonable (?:measures|steps) to\s+)?(?:verify|identify)\s+"),
    re.compile(r"^(?:the\s+)?identit(?:y|ies)\s+of\s+"),
)
SUCH_OBJECT = re.compile(r"^\s*such\b")
SUCH_VERIFICATION = re.compile(r"\bsuch (?:verification|identification)\b")
COMPLETE = re.compile(r"\bcomplete\b")

Lookup = Callable[[str], Set[str]]
SUBJECT_WORDS = {"verify_customer": "the customer", "identify_ubo": "a beneficial owner"}


def _object_after(sentence: str, end: int) -> str:
    rest = sentence[end:]
    stop = OBJECT_END.search(rest)
    return rest[: stop.start()] if stop else rest


def _subjects(obj: str, lookup: Lookup) -> List[Tuple[str, str, Tuple[int, int], Optional[re.Match]]]:
    """(type, rule, span in obj, cross-reference match or None) for every subject found in `obj`."""
    offset = len(obj) - len(obj.lstrip(" ,"))
    o = obj.strip(" ,")
    for prefix in SUBJECT_PREFIXES:
        match = prefix.match(o)
        if match:
            o = o[match.end():]
            offset += match.end()
    found: List[Tuple[str, str, Tuple[int, int], Optional[re.Match]]] = []
    head = CUSTOMER_HEAD.match(o)
    if head:
        found.append(("verify_customer", "identify.subject", (offset + head.start(), offset + head.end()), None))
    for owner in BO_ANY.finditer(o):
        found.append(("identify_ubo", "identify.subject", (offset + owner.start(), offset + owner.end()), None))
    xrefs = list(XREF_PERSON.finditer(o))
    if xrefs:
        resolved = lookup(xrefs[0].group(1)) & IDENTIFICATION  # the first reference decides
        for xref in xrefs:  # later references to a paragraph with the same type would take over if it were deleted
            for t in sorted(lookup(xref.group(1)) & resolved):
                found.append((t, "identify.cross_reference", (offset + xref.start(), offset + xref.end()), xref))
    return found


def subject_types(obj: str, lookup: Lookup) -> Set[str]:
    """Identification types for the object of an identify/verify verb."""
    return {t for t, _, _, _ in _subjects(obj, lookup)}


def _mentions(text: str, lookup: Lookup) -> Dict[str, Tuple[List[Tuple[int, int]], List[str]]]:
    """type -> (spans in text, referenced paragraphs) of every mention of identifying someone of that type."""
    found: Dict[str, Tuple[List[Tuple[int, int]], List[str]]] = {}
    for start, sentence in sentence_spans(text):
        for hit in IDENT_CUE.finditer(sentence):
            for t, _, (s, e), xref in _subjects(_object_after(sentence, hit.end()), lookup):
                spans, refs = found.setdefault(t, ([], []))
                spans += [(start + hit.start(), start + hit.end()), (start + hit.end() + s, start + hit.end() + e)]
                if xref:
                    refs.append(xref.group(1))
    return found


def mentioned_identification(text: str, lookup: Lookup) -> Set[str]:
    """Who the text talks about identifying or verifying, whether or not it is a duty (used for "such verification")."""
    return set(_mentions(text, lookup))


# --- the eight types for one sentence ----------------------------------------------------------------------

CDD_OBJECT = re.compile(r"^\s*(?:the |all |such |appropriate )?(?:(?:customer due diligence|cdd)(?: \(cdd\))? measures|"
                        r"measures (?:as )?required by paragraphs?\b)")
TRIGGER_VERB = re.compile(r"\b(?:perform|apply|undertake|carry out|conduct)(?:s|ing|ed)?\b")
# A trigger needs a condition: a conjunction ("when", "where", "if", "before"), a relative clause on the actor
# ("a bank that undertakes any transaction ... shall"), or a monetary threshold on a transaction.
CONDITION = re.compile(r"(?<!as )\b(?:when|whenever|where|if|before|prior to|upon|at the time of)\b|"
                       r"\b(?:that|which|who)\s+(?:undertakes|effects|receives|establishes|carries out|enters into)\b")
TRANSACTION = re.compile("transaction")
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


def _scope_spans(start: int, end: int, parent_len: int, sentence_start: int) -> List[Span]:
    """Spans for a match in f"{parent_text} {sentence}", split at the joining space if it crosses it."""
    spans: List[Span] = []
    if start < parent_len:
        spans.append(("parent", start, min(end, parent_len)))
    if end > parent_len + 1:
        own_start = max(start, parent_len + 1) - parent_len - 1
        spans.append(("own", sentence_start + own_start, sentence_start + end - parent_len - 1))
    return spans


def _trigger_reasons(sentence: str, parent_text: str, sentence_start: int, item_start: bool = False) -> List[Reason]:
    """One reason for every governed trigger verb whose object is CDD measures and that has a condition in scope."""
    reasons: List[Reason] = []
    at = lambda s, e: ("own", sentence_start + s, sentence_start + e)
    where = lambda m: "the enclosing text" if m.start() < len(parent_text) else "the same sentence"
    for g in governing(sentence, TRIGGER_VERB):
        verb = g.hit
        before = sentence[max(0, verb.start() - 25): verb.start()]
        if "in addition to" in before or "third party to" in before:
            continue
        cdd_object = CDD_OBJECT.match(sentence[verb.end():])
        if not cdd_object:
            continue
        scope = f"{parent_text} {sentence}"
        conditions = list(CONDITION.finditer(scope))
        amounts, transactions = list(AMOUNT.finditer(scope)), list(TRANSACTION.finditer(scope))
        amount_on_transaction = bool(amounts and transactions)
        if not (conditions or amount_on_transaction):
            continue
        spans = [at(*m.span()) for m in g.modals] + [at(*verb.span()),
                                                     at(verb.end() + cdd_object.start(), verb.end() + cdd_object.end())]
        evidence = conditions + (amounts + transactions if amount_on_transaction else [])
        for m in evidence:
            spans += _scope_spans(m.start(), m.end(), len(parent_text), sentence_start)
        if conditions:
            condition = f"the condition {_q(conditions[0])} occurs in {where(conditions[0])}"
        else:
            places = {where(amounts[0]), where(transactions[0])}
            condition = (f"the amount {_q(amounts[0])} and \"transaction\" occur in "
                         f"{places.pop() if len(places) == 1 else 'the sentence and the enclosing text'}")
        reasons.append(Reason("trigger.cdd_on_condition", "cdd_triggers",
                              _say(f"{_governor(g, item_start)} with the object {_q(cdd_object)}, and {condition}."),
                              spans))
    return reasons


def _trigger(sentence: str, parent_text: str) -> bool:
    return bool(_trigger_reasons(sentence, parent_text, 0))


@dataclass
class ClauseView:
    """What the frames need to know about one clause."""
    body: str                 # own text (see body_text)
    parent_body: str          # text of the enclosing clauses, nearest last
    parent_types: Set[str]    # final types of the direct parent
    parent_kind: str          # list kind of the direct parent (see list_kind)
    is_item: bool = False     # the clause has a list label (only the reason messages use it)


def own_reasons(view: ClauseView, lookup: Lookup) -> Dict[str, List[Reason]]:
    """The clause's own types, each with the reasons (and all the evidence) that gave it."""
    found: Dict[str, List[Reason]] = {}

    def add(t: str, rule: str, message: str, spans: Iterable[Span], refs: Iterable[str] = ()) -> None:
        found.setdefault(t, []).append(Reason(rule, t, _say(message), list(spans), list(refs)))

    def from_parent(t: str, mentions) -> Tuple[List[Span], List[str]]:
        spans, refs = mentions[t]
        return [("parent", s, e) for s, e in spans], refs

    for so, sentence in sentence_spans(view.body):
        at = lambda m, shift=0: ("own", so + shift + m.start(), so + shift + m.end())
        governor_spans = lambda g: [at(m) for m in g.modals] + [at(g.hit)]
        item_start = view.is_item and so == 0
        governor = lambda g: _governor(g, item_start)
        if is_permission(sentence):
            continue
        anonymous = list(ANONYMOUS.finditer(sentence))
        prohibitions = list(PROHIBITION.finditer(sentence)) if anonymous else []
        if anonymous and prohibitions:
            add("prohibit_anonymous", "anonymous.prohibition",
                f"{_q(anonymous[0])} and the prohibition {_q(prohibitions[0])} occur in one sentence.",
                [at(m) for m in anonymous + prohibitions])
        unable = list(UNABLE.finditer(sentence))
        stop = list(STOP.finditer(sentence)) if unable else []
        if unable and stop:
            add("cdd_incomplete", "incomplete.unable_and_stop",
                f"{_q(unable[0])} and {_q(stop[0])} occur in one sentence.",
                [at(m) for m in unable + stop])
        for reason in _trigger_reasons(sentence, view.parent_body, so, item_start):
            found.setdefault("cdd_triggers", []).append(reason)
        peps = list(PEP.finditer(sentence))
        if peps:
            modals = list(MODAL.finditer(sentence))
            refusals, relationships = list(REFUSE.finditer(sentence)), list(RELATIONSHIP.finditer(sentence))
            if refusals and relationships:  # "prohibits" is itself deontic, no modal needed
                add("pep_prohibition", "pep.prohibition",
                    f"{_q(refusals[0])} and {_q(relationships[0])} occur in a sentence that mentions a politically "
                    f"exposed person ({_q(peps[0])}).",
                    [at(m) for m in peps + refusals + relationships])
            enhanced = list(ENHANCED.finditer(sentence))
            if modals and enhanced:
                add("pep_edd", "pep.enhanced",
                    f"{_q(modals[0])} and {_q(enhanced[0])} occur in a sentence that mentions a politically "
                    f"exposed person ({_q(peps[0])}).",
                    [at(m) for m in peps + modals + enhanced])
            in_edd_list = view.parent_kind == "measures" and "pep_edd" in view.parent_types
            approvals = list(APPROVAL.finditer(sentence))
            if modals and approvals and not in_edd_list:
                add("pep_approval", "pep.approval",
                    f"{_q(modals[0])} and {_q(approvals[0])} occur in a sentence that mentions a politically "
                    f"exposed person ({_q(peps[0])}).",
                    [at(m) for m in peps + modals + approvals])
        # identification of the customer or of beneficial owners
        for g in governing(sentence, IDENT_CUE):
            hit = g.hit
            obj = _object_after(sentence, hit.end())
            anaphora = ANAPHORA.match(sentence[hit.start():])
            such = SUCH_OBJECT.match(obj)
            if anaphora or such:
                cue = at(anaphora, hit.start()) if anaphora else at(such, hit.end())
                mentions = _mentions(view.parent_body, lookup)
                for t in mentions:
                    parent_spans, refs = from_parent(t, mentions)
                    add(t, "identify.anaphora",
                        f"{governor(g)}, whose object {_q(sentence[cue[1] - so:cue[2] - so])} points back to the "
                        f"enclosing text, which mentions identifying {SUBJECT_WORDS[t]}.",
                        governor_spans(g) + [cue] + parent_spans, refs)
            by_rule: Dict[Tuple[str, str], Tuple[List[Span], List[str]]] = {}
            for t, rule, (s, e), xref in _subjects(obj, lookup):
                spans, refs = by_rule.setdefault((t, rule), ([], []))
                spans.append(("own", so + hit.end() + s, so + hit.end() + e))
                if xref:
                    refs.append(xref.group(1))
            for (t, rule), (spans, refs) in by_rule.items():
                if rule == "identify.cross_reference":
                    message = (f"{governor(g)}, whose object is the person identified under paragraph {refs[0]}, "
                               f"which carries {t}.")
                else:
                    message = f"{governor(g)}, whose object is {SUBJECT_WORDS[t]}."
                add(t, rule, message, governor_spans(g) + spans, refs)
        such_verification = list(SUCH_VERIFICATION.finditer(sentence))
        completes = governing(sentence, COMPLETE)
        if such_verification and completes:
            mentions = _mentions(view.parent_body, lookup)
            for t in mentions:
                parent_spans, refs = from_parent(t, mentions)
                add(t, "identify.complete_such",
                    f"{governor(completes[0])}, whose object {_q(such_verification[0])} points back to the enclosing "
                    f"text, which mentions identifying {SUBJECT_WORDS[t]}.",
                    [s for g in completes for s in governor_spans(g)] + [at(m) for m in such_verification]
                    + parent_spans, refs)
        passive = list(PASSIVE_CUSTOMER.finditer(sentence))
        if passive:
            add("verify_customer", "identify.passive_customer",
                f"{_q(passive[0])} is a passive duty to identify the customer.", [at(m) for m in passive])
        for g in governing(sentence, OWNERSHIP_STRUCTURE, window=120):
            add("identify_ubo", "ubo.ownership_structure",
                f"{governor(g)}, a duty to understand an ownership and control structure.", governor_spans(g))
        for g in governing(sentence, OBTAIN):
            rest = sentence[g.hit.end():]
            info = INFO_OBJECT.match(rest.strip())
            if not info:
                continue
            purpose = FOR_PURPOSES.search(view.body)
            if not purpose:
                continue
            info_span = at(info, g.hit.end() + len(rest) - len(rest.lstrip()))
            for t in sorted(lookup(purpose.group(1)) & IDENTIFICATION):
                add(t, "identify.information_for_purposes",
                    f"{governor(g)} with the object {_q(info)}, the clause says {_q(purpose)}, and paragraph "
                    f"{purpose.group(1)} carries {t}.",
                    governor_spans(g) + [info_span, ("own", purpose.start(), purpose.end())], [purpose.group(1)])
    # an ownership threshold for beneficial owners is part of the identification duty, even in a footnote
    # ("a controlling ownership interest ... may be based on a threshold (e.g. 25%)")
    thresholds, percents = list(OWNERSHIP_THRESHOLD.finditer(view.body)), list(PERCENT.finditer(view.body))
    if thresholds and percents:
        add("identify_ubo", "ubo.ownership_threshold",
            f"{_q(thresholds[0])} and the percentage {_q(percents[0])} occur in one clause, read as an ownership "
            f"threshold for beneficial owners.", [("own", m.start(), m.end()) for m in thresholds + percents])
    return found


def own_types(view: ClauseView, lookup: Lookup) -> Set[str]:
    return set(own_reasons(view, lookup))


# --- lists -------------------------------------------------------------------------------------------------

INTRODUCER = r"[–—\-:⎯]"
EXCEPTION_LEAD = re.compile(rf"\b(?:except|unless|other than|save)\b[^.;]*{INTRODUCER}\s*$")
INFO_LEAD = re.compile(r"following (?:information|types of|details|particulars)")
MEASURES_LEAD = re.compile(r"following (?:enhanced |additional )?(?:cdd |customer due diligence )?measures|\bas follows\b")
CONDITION_LEAD = re.compile(rf"\b(?:when|whenever|if|where|before|in the following (?:circumstances|cases))\s*{INTRODUCER}?\s*$")
OTHER_LEAD = re.compile(r"\bfollowing\b")
DUTY_LEAD = re.compile(rf"{INTRODUCER}\s*$")
KIND_WORDS = {"info": "the information to obtain", "measures": "a list of measures",
              "condition": "the conditions of a duty", "duty": "a list of duties", "none": "its items"}


def list_kind_cues(body: str) -> Tuple[str, List[Tuple[int, int]]]:
    """How a lead-in relates to the items under it, and the text in the lead-in that says so."""
    tail_start = max(0, len(body) - 200)
    exception = EXCEPTION_LEAD.search(body[tail_start:])
    if exception:
        return "exception", [(tail_start + exception.start(), tail_start + exception.end())]
    for kind, pattern in (("info", INFO_LEAD), ("measures", MEASURES_LEAD)):
        cues = [m.span() for m in pattern.finditer(body)]
        if cues:
            return kind, cues
    for kind, pattern in (("condition", CONDITION_LEAD), ("other", OTHER_LEAD), ("duty", DUTY_LEAD)):
        cue = pattern.search(body)
        if cue:
            return kind, [cue.span()]
    return "none", []


def list_kind(body: str) -> str:
    """How a lead-in relates to the items under it."""
    return list_kind_cues(body)[0]


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


# --- one document --------------------------------------------------------------------------------------------

# (clause_id, start, end) in body_text coordinates of that clause
BodySpan = Tuple[str, int, int]
Trace = Dict[str, Dict[str, List[Reason]]]


def _ordered(reasons: Dict[str, List[Reason]]) -> Dict[str, List[Reason]]:
    return {t: reasons[t] for t in TYPES if t in reasons}


def _trace(clauses: List, paragraph_of: Callable[[object], str]) -> Trace:
    """
    Types for every clause of one document, each with its reasons, in two passes: the first gives each paragraph's
    own types so that cross-references ("person identified under paragraph 6.14") can be resolved in the second.
    Reason spans are (clause_id, start, end) in body_text coordinates.
    """
    by_id = {c.clause_id: c for c in clauses}
    bodies = {c.clause_id: body_text(c.raw_text) for c in clauses}

    def parent_chain(clause) -> Tuple[str, List[Tuple[str, int, int]]]:
        """Text of the enclosing clauses (titles skipped), and where each ancestor's body sits in it."""
        ids, parent_id = [], clause.parent_clause_id
        while parent_id and parent_id in by_id:
            parent = by_id[parent_id]
            if not TITLE.match(parent.raw_text):
                ids.append(parent_id)
            parent_id = parent.parent_clause_id
        segments, position = [], 0
        for ancestor in reversed(ids):
            segments.append((ancestor, position, position + len(bodies[ancestor])))
            position += len(bodies[ancestor]) + 1
        return " ".join(bodies[a] for a, _, _ in segments), segments

    chains = {c.clause_id: parent_chain(c) for c in clauses}

    # pass 1: own types without cross-references, kept for the lead-in of every paragraph
    paragraph_types: Dict[str, Set[str]] = {}
    paragraph_lead: Dict[str, str] = {}
    no_lookup: Lookup = lambda ref: set()
    for c in clauses:
        view = ClauseView(bodies[c.clause_id], chains[c.clause_id][0], set(), "none")
        paragraph = paragraph_of(c).lower()
        if paragraph and paragraph not in paragraph_types:
            paragraph_types[paragraph] = own_types(view, no_lookup)
            paragraph_lead[paragraph] = c.clause_id
    lookup: Lookup = lambda ref: paragraph_types.get(ref.lower(), set())

    def resolve(reason: Reason, clause_id: str) -> Reason:
        """Turn "own"/"parent" spans into clause spans and referenced paragraphs into labels."""
        spans: List[BodySpan] = []
        for where, start, end in reason.spans:
            if where == "own":
                spans.append((clause_id, start, end))
                continue
            for ancestor, seg_start, seg_end in chains[clause_id][1]:
                if start < seg_end and end > seg_start:
                    spans.append((ancestor, max(start, seg_start) - seg_start, min(end, seg_end) - seg_start))
        depends = [f"{paragraph_lead[ref.lower()]}#{reason.type}" for ref in reason.refs]
        return Reason(reason.rule, reason.type, reason.message, spans, reason.refs,
                      list(dict.fromkeys(reason.depends_on + depends)))

    # pass 2: own types with cross-references, then inheritance from the lead-in (parents come first)
    trace: Trace = {}
    for c in clauses:
        parent = by_id.get(c.parent_clause_id) if c.parent_clause_id else None
        parent_is_title = parent is not None and TITLE.match(parent.raw_text)
        has_lead = parent is not None and not parent_is_title
        kind, cues = list_kind_cues(bodies[parent.clause_id]) if has_lead else ("none", [])
        view = ClauseView(
            body=bodies[c.clause_id],
            parent_body=chains[c.clause_id][0],
            parent_types=set(trace.get(parent.clause_id, {})) if has_lead else set(),
            parent_kind=kind,
            is_item=is_list_item(c.raw_text),
        )
        own = own_reasons(view, lookup)
        reasons = {t: [resolve(r, c.clause_id) for r in rs] for t, rs in own.items()}
        for t in inherited_types(view, set(own)):
            cue_text = ", ".join(_q(bodies[parent.clause_id][s:e]) for s, e in cues)
            message = (f"The item continues a lead-in that introduces {KIND_WORDS[kind]}"
                       f"{f' ({cue_text})' if cue_text else ''}, so it takes the lead-in's type {t}.")
            reasons[t] = [Reason("list.inherit", t, message, [(parent.clause_id, s, e) for s, e in cues],
                                 depends_on=[f"{parent.clause_id}#{t}"])]
        trace[c.clause_id] = _ordered(reasons)

    # pass 3: lead-ins that only introduce duties take the type their items share
    children: Dict[str, List[str]] = {}
    for c in clauses:
        if c.parent_clause_id:
            children.setdefault(c.parent_clause_id, []).append(c.clause_id)
    for c in reversed(clauses):
        kids = children.get(c.clause_id)
        if not kids or TITLE.match(c.raw_text):
            continue
        kind, cues = list_kind_cues(bodies[c.clause_id])
        lead = set(trace[c.clause_id])
        new = propagate_up(lead, kind, (set(trace[k]) for k in kids))
        if new == lead:
            continue
        typed = [k for k in kids if trace[k]]
        cue_text = ", ".join(_q(bodies[c.clause_id][s:e]) for s, e in cues)
        trace[c.clause_id] = _ordered({t: [Reason(
            "list.propagate", t,
            f"The lead-in introduces a list of duties ({cue_text}) and every item with a type under it is {t}.",
            [(c.clause_id, s, e) for s, e in cues], depends_on=[f"{k}#{t}" for k in typed])] for t in new})
    return trace


def classify(clauses: List, paragraph_of: Callable[[object], str]) -> Dict[str, Set[str]]:
    """
    Types for every clause of one document, in two passes: the first gives each paragraph's own types so that
    cross-references ("person identified under paragraph 6.14") can be resolved in the second.
    `clauses` are objects with clause_id, parent_clause_id and raw_text, in document order.
    """
    return {clause_id: set(types) for clause_id, types in _trace(clauses, paragraph_of).items()}


def classify_traced(clauses: List, paragraph_of: Callable[[object], str]) -> Dict[str, Dict[str, List[RuleReason]]]:
    """
    classify with reasons: clause_id -> type -> reasons. A type is present iff it has at least one reason.
    Evidence spans are character offsets into the cited clause's raw_text, in document order.
    """
    raw = {c.clause_id: c.raw_text for c in clauses}
    order = {c.clause_id: i for i, c in enumerate(clauses)}
    offsets: Dict[str, List[int]] = {}

    def evidence(clause_id: str, start: int, end: int) -> Optional[EvidenceSpan]:
        body = body_text(raw[clause_id])
        while start < end and body[start].isspace():
            start += 1
        while end > start and body[end - 1].isspace():
            end -= 1
        if start >= end:
            return None
        if clause_id not in offsets:
            offsets[clause_id] = body_offsets(raw[clause_id])
        raw_start, raw_end = offsets[clause_id][start], offsets[clause_id][end - 1] + 1
        return EvidenceSpan(clause_id=clause_id, start=raw_start, end=raw_end, text=raw[clause_id][raw_start:raw_end])

    traced: Dict[str, Dict[str, List[RuleReason]]] = {}
    for clause_id, types in _trace(clauses, paragraph_of).items():
        traced[clause_id] = {}
        for t, reasons in types.items():
            converted = []
            for r in reasons:
                spans = {(s.clause_id, s.start, s.end): s for s in (evidence(*span) for span in r.spans) if s}
                ordered = [spans[k] for k in sorted(spans, key=lambda k: (order[k[0]], k[1], k[2]))]
                converted.append(RuleReason(rule=r.rule, obligation_type=t, message=r.message, spans=ordered,
                                            depends_on=r.depends_on))
            traced[clause_id][t] = converted
    return traced
