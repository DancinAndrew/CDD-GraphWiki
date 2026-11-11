"""
Held-out evaluation on the full MAS Notice 626: the corpus is a faithful conversion of the official PDF,
the gold labels only touch held-out clauses, and the committed scores can be recomputed exactly.
"""
import json
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from src.heldout import convert, evaluate, llm_compare
from src.ingestion.parser import SemanticHierarchicalSegmenter

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(REPO_ROOT / "data")
PDF = REPO_ROOT / "data" / "sources" / "official" / "mas_notice_626.pdf"
FULL_TEXT = REPO_ROOT / "data" / "heldout" / "sources" / "mas_notice_626.md"
RESULTS = REPO_ROOT / "data" / "heldout" / "results" / "mas_notice_626"
LLM_RUN = REPO_ROOT / "data" / "heldout" / "llm_runs" / "mas_notice_626" / f"{llm_compare.model_slug(llm_compare.DEFAULT_MODEL)}.jsonl"


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text).replace("–", "-")


def _found_across_page_breaks(line: str, official: str, max_gap: int = 2500) -> bool:
    """
    True when the line appears in the PDF text in order, allowing a gap where a paragraph runs over a page
    break (the plain PDF text puts the page number and footnotes there). Each piece must be at least 8 characters.
    """
    rest, start, window_end = line, 0, len(official)
    while rest:
        window = official[start:window_end]
        lo, hi = 0, len(rest)
        while lo < hi:  # longest prefix of `rest` that occurs in the window
            mid = (lo + hi + 1) // 2
            if rest[:mid] in window:
                lo = mid
            else:
                hi = mid - 1
        if lo < min(8, len(rest)):
            return False
        start = start + window.index(rest[:lo]) + lo
        rest = rest[lo:]
        window_end = start + max_gap
    return True


@pytest.fixture(scope="module")
def corpus():
    return evaluate.load_corpus(DATA_DIR)


def test_full_text_is_the_committed_conversion_of_the_official_pdf():
    assert convert.convert(str(PDF)) == FULL_TEXT.read_text(encoding="utf-8")


def test_full_text_lines_are_verbatim_from_the_official_pdf():
    from pypdf import PdfReader
    official = _squash(" ".join(page.extract_text() or "" for page in PdfReader(str(PDF)).pages))
    body = [ln.strip() for ln in FULL_TEXT.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith(("#", ">"))]
    body = [re.sub(r"^\(([a-z]{1,2}|[ivx]+|[A-Z])\)\s+", "", ln) for ln in body]
    assert len(body) > 300
    missing = [ln[:80] for ln in body if not _found_across_page_breaks(_squash(ln), official)]
    assert missing == [], f"Lines not found in the official PDF text: {missing}"


def test_full_text_has_every_numbered_paragraph_and_unique_clause_ids():
    markdown = FULL_TEXT.read_text(encoding="utf-8")
    assert len(re.findall(r"^### \d", markdown, flags=re.M)) == 167
    _, clauses = SemanticHierarchicalSegmenter("mas_notice_626").parse(markdown)
    duplicates = [cid for cid, n in Counter(c.clause_id for c in clauses).items() if n > 1]
    assert duplicates == []


def test_development_clauses_keep_their_ids_in_the_full_text(corpus):
    dev_ids = [c["clause_id"] for c in yaml.safe_load((REPO_ROOT / "data" / "gold" / "clauses.yaml").read_text())
               if c["source_document_id"] == "mas_notice_626"]
    full_ids = {c.clause_id for c in corpus.clauses}
    assert dev_ids and set(dev_ids) <= full_ids


def test_held_out_set_excludes_every_development_paragraph(corpus):
    held_paragraphs = {corpus.paragraph_of[c.clause_id] for c in corpus.held_out}
    assert held_paragraphs.isdisjoint(corpus.development_paragraphs)
    assert len(held_paragraphs) == 157


def test_gold_labels_cover_only_held_out_clauses(corpus):
    labelled = {cid: types for cid, types in corpus.gold.items() if types}
    assert len(labelled) == 42
    assert all(types <= set(corpus.types) for types in labelled.values())


def test_rule_scores_match_the_committed_report(corpus, tmp_path):
    summary = evaluate.run_set(DATA_DIR, "mas_notice_626", str(tmp_path))
    committed = json.loads((RESULTS / "rules_summary.json").read_text())
    assert summary == committed
    for version in ("rules_v1", "rules_v2"):
        assert (tmp_path / f"{version}_report.txt").read_text() == (RESULTS / f"{version}_report.txt").read_text()


def test_frozen_v1_rules_still_find_1_of_18_held_out_obligations(corpus):
    """The frozen copy of the original rules reproduces the score committed before v2 existed."""
    scores = evaluate.score(corpus, evaluate.rules_v1_predictions(corpus, "Singapore"))
    paragraph = scores["paragraph"]["overall"]
    assert (paragraph["tp"], paragraph["fp"], paragraph["fn"]) == (1, 6, 17)


def test_llm_scores_can_be_recomputed_offline_from_cached_answers(tmp_path):
    summary = llm_compare.score_cached(DATA_DIR, "mas_notice_626", str(LLM_RUN), str(tmp_path))
    slug = LLM_RUN.stem
    committed = json.loads((RESULTS / f"llm_{slug}_summary.json").read_text())
    assert summary == committed
    assert summary["requests"]["paragraphs_sent"] == 157


def test_answers_citing_clause_ids_that_were_not_sent_are_counted_not_scored(corpus, tmp_path):
    first = llm_compare.paragraph_units(corpus)[0]
    run = tmp_path / "fake.jsonl"
    answer = {"labels": [{"clause_id": first["clause_ids"][0], "types": ["cdd_triggers"]},
                         {"clause_id": "mas_notice_626_99_invented", "types": ["cdd_triggers"]}]}
    run.write_text(json.dumps({"paragraph": first["paragraph"], "model": "fake",
                               "response": "```json\n" + json.dumps(answer) + "\n```"}) + "\n")
    loaded = llm_compare.load_answers(str(run), corpus)
    assert loaded["stats"]["invalid_clause_ids"] == [f"{first['paragraph']}: mas_notice_626_99_invented"]
    assert loaded["predictions"][first["clause_ids"][0]] == {"cdd_triggers"}
    assert "mas_notice_626_99_invented" not in loaded["predictions"]


def test_parse_answer_ignores_reasoning_and_code_fences():
    content = "<think>maybe 6.1</think>Here you go:\n```json\n{\"labels\": []}\n```"
    assert llm_compare.parse_answer(content) == {"labels": []}


# --- UK Money Laundering Regulations 2017, Part 3: the second held-out set, unseen by both rule versions ------

UK_XML = REPO_ROOT / "data" / "heldout" / "sources" / "official" / "uk_mlr_2017_part_3.xml"
UK_TEXT = REPO_ROOT / "data" / "heldout" / "sources" / "uk_mlr_2017.md"
UK_RESULTS = REPO_ROOT / "data" / "heldout" / "results" / "uk_mlr_2017"


def _found_in_order(line: str, reference: str, max_gap: int = 8) -> bool:
    """The line's characters occur in the reference in order, with gaps of at most `max_gap` characters
    (where the reference has a sub-paragraph number that the converted text writes differently)."""
    rest, start, first = line, 0, True
    while rest:
        lo, hi, found_at = 0, len(rest), -1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            end = len(reference) if first else start + max_gap + mid
            at = reference.find(rest[:mid], start, end)
            if at != -1:
                lo, found_at = mid, at
            else:
                hi = mid - 1
        if lo < min(8, len(rest)):
            return False
        start, rest, first = found_at + lo, rest[lo:], False
    return True


@pytest.fixture(scope="module")
def uk_corpus():
    return evaluate.load_corpus(DATA_DIR, "uk_mlr_2017")


def test_uk_text_is_the_committed_conversion_of_the_official_xml():
    from src.heldout import convert_uk
    assert convert_uk.convert(str(UK_XML)) == UK_TEXT.read_text(encoding="utf-8")


def test_uk_text_lines_are_verbatim_from_the_official_xml():
    import xml.etree.ElementTree as ET
    ns = "{http://www.legislation.gov.uk/namespaces/legislation}"
    body = ET.parse(str(UK_XML)).getroot().find(f".//{ns}Body")

    def words(el):
        if el.tag in (f"{ns}CommentaryRef", f"{ns}Commentary"):
            return el.tail or ""
        return (el.text or "") + "".join(words(child) for child in el) + (el.tail or "")

    reference = _squash(words(body))
    lines = [ln.strip() for ln in UK_TEXT.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.lstrip().startswith(("#", ">"))]
    lines = [re.sub(r"^\(([a-z]{1,2}|[ivx]+)\)\s+", "", ln) for ln in lines]
    # deeper levels such as "(aa)" are kept inline by the converter; the XML numbers them "aa" without brackets
    lines = [re.sub(r"\((?:[a-z]{2}|[ivx]{2,4})\)\s", "", ln) for ln in lines]
    assert len(lines) > 300
    missing = [ln[:80] for ln in lines if not _found_in_order(_squash(ln), reference)]
    assert missing == [], f"Lines not found in the legislation.gov.uk XML: {missing}"


def test_uk_set_is_fully_held_out_and_labels_point_at_its_clauses(uk_corpus):
    assert uk_corpus.development_paragraphs == []
    assert len({uk_corpus.paragraph_of[c.clause_id] for c in uk_corpus.held_out}) == 137
    assert sum(1 for types in uk_corpus.gold.values() if types) == 75


def test_uk_rule_scores_match_the_committed_report(tmp_path):
    summary = evaluate.run_set(DATA_DIR, "uk_mlr_2017", str(tmp_path))
    assert summary == json.loads((UK_RESULTS / "rules_summary.json").read_text())
    for version in ("rules_v1", "rules_v2"):
        assert (tmp_path / f"{version}_report.txt").read_text() == (UK_RESULTS / f"{version}_report.txt").read_text()
    assert summary["rules_v1"]["paragraph"]["overall"]["tp"] == 0  # v1 has no profile for the United Kingdom


def test_uk_llm_scores_can_be_recomputed_offline_from_cached_answers(tmp_path):
    run = REPO_ROOT / "data" / "heldout" / "llm_runs" / "uk_mlr_2017" / f"{llm_compare.model_slug(llm_compare.DEFAULT_MODEL)}.jsonl"
    summary = llm_compare.score_cached(DATA_DIR, "uk_mlr_2017", str(run), str(tmp_path))
    assert summary == json.loads((UK_RESULTS / f"llm_{run.stem}_summary.json").read_text())
    assert summary["requests"]["paragraphs_sent"] == 137
    # the one clause ID the model made up, following the naming pattern for "(zb)" in regulation 27(8)
    assert summary["requests"]["invalid_clause_ids"] == ["27(8): uk_mlr_2017_27_cdd_27_8_zb"]


def test_trust_tiers_add_up_to_each_extractor_s_own_scores(uk_corpus):
    """both + llm only = the LLM's labels, both + rules only = the rules' labels; correct items = true positives."""
    run = REPO_ROOT / "data" / "heldout" / "llm_runs" / "uk_mlr_2017" / f"{llm_compare.model_slug(llm_compare.DEFAULT_MODEL)}.jsonl"
    llm = llm_compare.load_answers(str(run), uk_corpus)["predictions"]
    rules = evaluate.rules_v2_predictions(uk_corpus, uk_corpus.spec.jurisdiction)
    tiers = llm_compare.agreement_with_rules(uk_corpus, llm, rules)
    for level in ("paragraph", "clause"):
        t = tiers[level]
        for predictions, own in ((llm, "llm_only"), (rules, "rules_only")):
            o = evaluate.score(uk_corpus, predictions)[level]["overall"]
            assert t["both"]["items"] + t[own]["items"] == o["tp"] + o["fp"]
            assert t["both"]["correct"] + t[own]["correct"] == o["tp"]
    assert "note" not in tiers  # the UK set is unseen by rules v2


# --- llm_compare run bookkeeping (no model is called) ---------------------------------------------------------

def _stub_model(monkeypatch, asked, answer=None):
    answer = answer or {"response": '{"labels": []}', "done_reason": "stop", "eval_count": 5}
    monkeypatch.setattr(llm_compare, "endpoint", lambda base_url, data_dir: {"local": True, "api_key": "ollama"})
    monkeypatch.setattr(llm_compare, "chat",
                        lambda client, model, base_url, conn, system, user: asked.append(user) or dict(answer))


def test_resume_with_limit_keeps_every_cached_record_outside_the_selected_paragraphs(uk_corpus, tmp_path, monkeypatch):
    units = llm_compare.paragraph_units(uk_corpus)
    out = tmp_path / "run.jsonl"
    cached = [{"paragraph": u["paragraph"], "model": "m", "response": '{"labels": []}', "prompt_sha256": "old"}
              for u in units]
    cached[5] = {"paragraph": units[5]["paragraph"], "model": "m", "error": "ReadTimeout"}  # kept too, as it was
    out.write_text("".join(json.dumps(r) + "\n" for r in reversed(cached)), encoding="utf-8")
    asked = []
    _stub_model(monkeypatch, asked)
    llm_compare.run_model(DATA_DIR, "uk_mlr_2017", "m", "http://localhost:11434/v1", str(out), limit=2, resume=True)
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert len(asked) == 2                                                 # only the two selected (stale) ones
    assert [r["paragraph"] for r in records] == [u["paragraph"] for u in units]   # all of them, in paragraph order
    assert records[2:] == cached[2:]
    assert records[0]["done_reason"] == "stop" and records[0]["eval_count"] == 5


def test_an_answer_cut_by_the_output_cap_is_logged_as_truncated(uk_corpus, tmp_path, monkeypatch, capsys):
    asked = []
    _stub_model(monkeypatch, asked, {"response": '{"labels": [{"clause_id": "x", "ty', "done_reason": "length",
                                     "eval_count": llm_compare.MAX_NEW_TOKENS})
    out = tmp_path / "run.jsonl"
    llm_compare.run_model(DATA_DIR, "uk_mlr_2017", "m", "http://localhost:11434/v1", str(out), limit=1)
    assert ": truncated (" in capsys.readouterr().out
    assert llm_compare.request_status({"error": "x"}) == "error"
    assert llm_compare.request_status({"response": "{}"}) == "ok"  # records made before the stop reason was stored


def test_chat_keeps_ollama_s_stop_reason_and_token_count():
    class Reply:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "{}"}, "done_reason": "length", "eval_count": 2048}

    class Client:
        def post(self, url, json):
            assert json["options"]["num_predict"] == llm_compare.MAX_NEW_TOKENS
            return Reply()

    assert llm_compare.chat(Client(), "m", "http://localhost:11434/v1", {"local": True}, "s", "u") == \
        {"response": "{}", "done_reason": "length", "eval_count": 2048}


def test_the_scored_summary_shows_mixed_generation_settings_invalid_json_and_cap_hits(uk_corpus, tmp_path):
    units = llm_compare.paragraph_units(uk_corpus)[:4]
    records = [
        {"paragraph": units[0]["paragraph"], "model": "m", "response": '{"labels": []}'},                 # no cap
        {"paragraph": units[1]["paragraph"], "model": "m", "response": '{"labels": [', "num_predict": 2048},
        {"paragraph": units[2]["paragraph"], "model": "m", "response": '{"labels": [', "num_predict": 2048,
         "done_reason": "length"},
        {"paragraph": units[3]["paragraph"], "model": "m", "error": "ReadTimeout", "num_predict": 2048},
    ]
    run = tmp_path / "m.jsonl"
    run.write_text("".join(json.dumps(r) + "\n" for r in records))
    summary = llm_compare.score_cached(DATA_DIR, "uk_mlr_2017", str(run), str(tmp_path))
    assert summary["generation"] == {"records": 4, "answers": 3, "with_num_predict": 3, "without_num_predict": 1,
                                     "num_predict_values": [2048], "invalid_json": 2, "with_done_reason": 1,
                                     "hit_cap": 1}
    report = (tmp_path / "llm_m_report.txt").read_text()
    assert ("Generation: 4 records, 3 with an output cap (num_predict 2048), 1 without (mixed settings); answers "
            "not valid JSON: 2; answers that hit the cap: 1 of the 1 that store the stop reason (stop reason not "
            "stored for 2).") \
        in report


def test_an_empty_or_partly_written_run_file_is_skipped_not_a_crash(tmp_path, capsys):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("\n")
    assert llm_compare.score_cached(DATA_DIR, "uk_mlr_2017", str(empty), str(tmp_path / "out")) is None
    partial = tmp_path / "partial.jsonl"
    partial.write_text('{"paragraph": "27(1)", "model": "m", "response": "{}"}\n{"paragraph": "27(2)", "mod')
    assert llm_compare.score_cached(DATA_DIR, "uk_mlr_2017", str(partial), str(tmp_path / "out")) is None
    err = capsys.readouterr().err
    assert "skipping" in err and "no records" in err and "line 2 is not valid JSON" in err
    assert not (tmp_path / "out").exists()
