"""
Convert the official MAS Notice 626 PDF into Markdown that src.ingestion.parser can read.

    PYTHONPATH=backend python -m src.heldout.convert

The output uses the same layout as data/sources/mas_notice_626.md:
"## <section>" for the 15 numbered sections, "### <paragraph number>" for each paragraph,
"(a)" lines for sub-paragraphs and "  (i)" lines for the next level. Paragraph text is copied
from the PDF word for word (only line breaks and runs of spaces are normalised). Left out:
page numbers, footnotes, "[MAS Notice 626 (Amendment) 2025]" tags, the unnumbered sub-headings
between paragraphs, the endnotes and the two appendices. A test checks every converted line
against the PDF text.
"""
import os
import re
import argparse
from typing import List, Optional, Tuple

from pypdf import PdfReader

from src.paths import find_data_dir

# Section titles as printed in the Notice (title case). Sections 6 and 8 reuse the headings of the
# development excerpt so that the same paragraph gets the same clause ID in both corpora.
SECTION_TITLES = {
    "1": "Introduction",
    "2": "Definitions",
    "3": "Underlying Principles",
    "4": "Assessing Risks and Applying a Risk-Based Approach",
    "5": "New Products, Practices and Technologies",
    "6": "Customer Due Diligence",
    "7": "Simplified Customer Due Diligence",
    "8": "Enhanced Customer Due Diligence",
    "9": "Reliance on Third Parties",
    "10": "Correspondent Banking",
    "11": "Wire Transfers",
    "11A": "Value Transfers",
    "12": "Record Keeping",
    "13": "Personal Data",
    "14": "Suspicious Transactions Reporting",
    "15": "Internal Policies, Compliance, Audit and Training",
}
SECTION_ORDER = list(SECTION_TITLES)

SECTION_RE = re.compile(r"^(\d{1,2}A?)\s{2,}([A-Z][A-Z ,/&()“”\"'\-]+)$")
PARAGRAPH_RE = re.compile(r"^(\d{1,2}A?\.\d{1,3}[A-Z]?)\s+(.*)$")
FOOTNOTE_RE = re.compile(r"^(\d{1,2}) \S")
AMENDMENT_TAG_RE = re.compile(r"\[MAS Notice 626 \(Amendment\) \d{4}\]")
PAGE_NUMBER_RE = re.compile(r"^\s*\d{1,2}\s*$")
# Definition paragraphs (2.1, 9.1, 10.1, 11.1, 11A.2) restart their lists at (a) for every term, so their
# items stay inline in one paragraph instead of becoming list clauses with clashing IDs.
DEFINITIONS_RE = re.compile(r"^For the purposes of (this Notice|paragraph \d{1,2}A?)\s*[–-]")
ITEM_RE = re.compile(r"^\(([a-z]{1,2}|[ivx]+|[A-Z])\)\s+(.*)$")
END_MARKER = "Endnotes on History of Amendments"

HEADER = (
    "# MAS Notice 626: Prevention of Money Laundering and Countering the Financing of Terrorism – Banks\n\n"
    "> Full text of MAS Notice 626 (dated 28 March 2024, last revised on 30 June 2025), converted from the "
    "official PDF at data/sources/official/mas_notice_626.pdf by src/heldout/convert.py. Paragraph text is "
    "verbatim; page numbers, footnotes, amendment tags, unnumbered sub-headings, endnotes and appendices are "
    "left out.\n"
)


def _page_lines(text: str, next_footnote: int) -> Tuple[List[str], int]:
    """
    Drop the page number, amendment tags and the footnote block at the bottom of a page.
    Footnotes are numbered 1, 2, 3 ... through the Notice, so a line counts as a footnote only when it
    starts with the next expected number (this keeps lines such as "28 March 2024" on the cover).
    """
    lines = [AMENDMENT_TAG_RE.sub("", line).rstrip() for line in text.splitlines()]
    out: List[str] = []
    in_footnotes = False
    for line in lines:
        match = FOOTNOTE_RE.match(line)
        if match and int(match.group(1)) == next_footnote:
            in_footnotes = True
            next_footnote += 1
        if not in_footnotes:
            out.append(line)
    while out and (not out[-1].strip() or PAGE_NUMBER_RE.match(out[-1])):
        out.pop()
    return out, next_footnote


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _join(parts: List[str]) -> str:
    text = ""
    for part in parts:
        part = re.sub(r"\s+", " ", part.strip())
        if not part:
            continue
        if text.endswith("-") and len(text) > 1 and text[-2].isalpha():
            text += part  # word broken across lines, e.g. "cross-" + "border"
        else:
            text = f"{text} {part}" if text else part
    return text


def convert(pdf_path: str) -> str:
    pages = [page.extract_text(extraction_mode="layout") or "" for page in PdfReader(pdf_path).pages]
    lines: List[str] = []
    next_footnote = 1
    for page in pages:
        page_lines, next_footnote = _page_lines(page, next_footnote)
        lines.extend(page_lines)

    blocks: List[str] = []          # finished Markdown lines
    current: Optional[List[str]] = None  # [prefix, text parts...] of the block being collected
    section = ""
    started = False
    inline_items = False
    in_subheading = False  # a sub-heading can wrap onto an indented second line

    def flush() -> None:
        nonlocal current
        if current:
            prefix, parts = current[0], current[1:]
            body = _join(parts)
            if body:
                blocks.append(f"{prefix}{body}")
        current = None

    for line in lines:
        if END_MARKER in line:
            break
        stripped = line.strip()
        if not stripped:
            in_subheading = False
            continue
        section_match = SECTION_RE.match(stripped) if _indent(line) == 0 else None
        position = SECTION_ORDER.index(section) + 1 if section else 0
        expected = SECTION_ORDER[position] if position < len(SECTION_ORDER) else None
        if section_match and section_match.group(1) == expected:
            flush()
            section = expected
            started = True
            blocks.append(f"\n## {section} {SECTION_TITLES[section]}")
            continue
        if not started:
            continue
        paragraph_match = PARAGRAPH_RE.match(stripped) if _indent(line) == 0 else None
        if paragraph_match and paragraph_match.group(1).split(".")[0] == section:
            in_subheading = False
            flush()
            blocks.append(f"\n### {paragraph_match.group(1)}")
            current = ["", paragraph_match.group(2)]
            inline_items = bool(DEFINITIONS_RE.match(paragraph_match.group(2)))
            continue
        item_match = ITEM_RE.match(stripped) if _indent(line) > 0 and not inline_items else None
        if item_match:
            flush()
            prefix = "  " if _indent(line) >= 15 else ""
            current = [f"{prefix}({item_match.group(1)}) ", item_match.group(2)]
            continue
        if _indent(line) == 0 and section != "2":
            # An unnumbered sub-heading between paragraphs: left out. (In section 2 the definitions
            # themselves start at the margin, so there every line is paragraph text.)
            flush()
            in_subheading = True
            continue
        if in_subheading:
            continue
        if current is None:
            # text after a list that belongs to the enclosing paragraph, e.g. the closing words of 2.1 "business relations"
            current = ["", stripped]
        else:
            current.append(stripped)
    flush()
    return HEADER + "\n".join(blocks).replace("\n\n\n", "\n\n") + "\n"


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="Convert the official MAS Notice 626 PDF to Markdown")
    parser.add_argument("--pdf", default=os.path.join(data_dir, "sources", "official", "mas_notice_626.pdf"))
    parser.add_argument("--out", default=os.path.join(data_dir, "heldout", "sources", "mas_notice_626.md"))
    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(convert(args.pdf))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
