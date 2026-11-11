"""
Convert Part 3 (Customer Due Diligence) of the UK Money Laundering Regulations 2017 from legislation.gov.uk
XML into Markdown that src.ingestion.parser can read.

    PYTHONPATH=backend python -m src.heldout.convert_uk

Source: https://www.legislation.gov.uk/uksi/2017/692/part/3/data.xml, the revised version valid from 2026-06-30,
saved in data/heldout/sources/official/uk_mlr_2017_part_3.xml. Contains public sector information licensed
under the Open Government Licence v3.0.

Layout: "## <regulation> <title>", "### <regulation>(<paragraph>)" for each paragraph, "(a)" lines for
sub-paragraphs and "  (i)" lines for the next level; deeper levels and definition lists stay in the text of
their parent line. The words are taken from the XML unchanged; amendment markers and footnote references
are dropped.
"""
import os
import re
import argparse
import xml.etree.ElementTree as ET
from typing import List

from src.paths import find_data_dir

NS = "{http://www.legislation.gov.uk/namespaces/legislation}"
STRUCTURAL = {f"{NS}{t}" for t in ("P2", "P3", "P4", "P5", "P1group", "P1", "Chapter", "Part")}
SKIPPED = {f"{NS}CommentaryRef", f"{NS}Pnumber", f"{NS}Title"}

HEADER = (
    "# The Money Laundering, Terrorist Financing and Transfer of Funds (Information on the Payer) Regulations 2017 – "
    "Part 3: Customer Due Diligence\n\n"
    "> Regulations 27 to 38 of S.I. 2017/692 (revised version valid from 30 June 2026), converted from the "
    "legislation.gov.uk XML in data/heldout/sources/official/uk_mlr_2017_part_3.xml by src/heldout/convert_uk.py. "
    "The words are unchanged; amendment markers and footnote references are left out. Contains public sector "
    "information licensed under the Open Government Licence v3.0.\n"
)


def _raw_text(el: ET.Element) -> str:
    parts: List[str] = [el.text or ""]
    for child in el:
        if child.tag not in STRUCTURAL and child.tag not in SKIPPED:
            parts.append(_raw_text(child))  # amendment markers keep their own spaces ("providing  ", "  transaction")
        parts.append(child.tail or "")
    return "".join(parts)


def inline_text(el: ET.Element) -> str:
    """Text of an element without nested provisions, footnote references, numbers or titles."""
    return re.sub(r"\s+", " ", _raw_text(el)).strip()


def number(el: ET.Element) -> str:
    pnumber = el.find(f"{NS}Pnumber")
    return inline_text(pnumber) if pnumber is not None else ""


def render_level(el: ET.Element, depth: int, lines: List[str]) -> None:
    """A sub-paragraph (P3 at depth 0, P4 at depth 1, deeper levels inline in their parent)."""
    para = el.find(f"{NS}{el.tag.replace(NS, '')}para")
    label = f"({number(el)})"
    if depth >= 2:
        # (aa) and deeper: keep the words on the parent's line
        lines[-1] += " " + label + " " + (inline_text(para) if para is not None else "")
        for child in (para if para is not None else []):
            if child.tag in {f"{NS}P5", f"{NS}P6"}:
                render_level(child, depth + 1, lines)
        return
    lines.append(("  " if depth == 1 else "") + label + " " + (inline_text(para) if para is not None else ""))
    if para is None:
        return
    for child in para:
        if child.tag in {f"{NS}P4", f"{NS}P5", f"{NS}P6"}:
            render_level(child, depth + 1, lines)


def render_paragraph(reg: str, p2: ET.Element, lines: List[str]) -> None:
    lines.append(f"\n### {reg}({number(p2)})")
    para = p2.find(f"{NS}P2para")
    if para is None:
        return
    lead: List[str] = []
    started_items = False
    for child in para:
        if child.tag == f"{NS}P3":
            if not started_items and lead:
                lines.append(" ".join(lead))
            started_items = True
            render_level(child, 0, lines)
        else:
            text = inline_text(child)
            if not text:
                continue
            if started_items:
                lines.append(text)  # closing words after a list; the parser attaches them to the last item
            else:
                lead.append(text)
    if not started_items and lead:
        lines.append(" ".join(lead))


def convert(xml_path: str) -> str:
    root = ET.parse(xml_path).getroot()
    body = root.find(f".//{NS}Body")
    lines: List[str] = []
    for group in body.iter(f"{NS}P1group"):
        p1 = group.find(f"{NS}P1")
        reg = number(p1)
        title = inline_text(group.find(f"{NS}Title"))
        lines.append(f"\n## {reg} {title}")
        p1para = p1.find(f"{NS}P1para")
        p2s = p1para.findall(f"{NS}P2") if p1para is not None else []
        if p2s:
            for p2 in p2s:
                render_paragraph(reg, p2, lines)
        elif p1para is not None:
            lines.append(f"\n### {reg}")
            lines.append(inline_text(p1para))
    return HEADER + "\n".join(lines).replace("\n\n\n", "\n\n") + "\n"


def main() -> None:
    data_dir = find_data_dir()
    parser = argparse.ArgumentParser(description="Convert UK MLR 2017 Part 3 XML to Markdown")
    parser.add_argument("--xml", default=os.path.join(data_dir, "heldout", "sources", "official", "uk_mlr_2017_part_3.xml"))
    parser.add_argument("--out", default=os.path.join(data_dir, "heldout", "sources", "uk_mlr_2017.md"))
    args = parser.parse_args()
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(convert(args.xml))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
