"""
Deletion tests for the LLM's quoted evidence: quote location, the two perturbations, and scoring from cached
answers. Fast and offline: no test here calls a model.
"""
import json
from pathlib import Path

import pytest

from src.heldout import evaluate, llm_compare, llm_faithfulness as lf

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(REPO_ROOT / "data")
UK_RUN = REPO_ROOT / "data" / "heldout" / "llm_runs" / "uk_mlr_2017" / "qwen3_5_9b.jsonl"

PARAGRAPH = [
    ("p", "A bank must apply customer due diligence measures if the bank—"),
    ("p_a", "(a) establishes a business relationship;"),
    ("p_b", "(b) suspects money laundering, and must apply them again."),
]


@pytest.fixture(scope="module")
def uk_corpus():
    return evaluate.load_corpus(DATA_DIR, "uk_mlr_2017")


# --- quote location -------------------------------------------------------------------------------------------

def test_quotes_are_found_despite_case_whitespace_and_typographic_variants():
    text = "The bank’s  customer — MUST\nverify “identity”"
    (start, end), = lf.find_all("the bank's customer - must verify \"identity\"", text)
    assert text[start:end] == text  # the span maps back onto the original characters


def test_a_quote_that_is_not_in_the_text_is_not_located():
    assert lf.find_all("occasional transaction", PARAGRAPH[0][1]) == []
    assert lf.locate("occasional transaction", PARAGRAPH, "p_a") is None
    assert lf.locate("   ", PARAGRAPH, "p_a") is None


def test_a_quote_matches_whole_words_only():
    text = "A person must act on it; personal data, on."
    assert [text[s:e] for s, e in lf.find_all("on", text)] == ["on", "on"]  # not inside "person" or "personal"
    assert lf.find_all("customer", "customers must") == []
    assert lf.find_all("customers", "the customers must") == [(4, 13)]
    # an end that is not a letter or digit needs no boundary there
    assert lf.find_all("-it;", "do-it;x") == [(2, 6)]


def test_the_labelled_clause_is_searched_first_then_the_others_in_order():
    assert lf.locate("must apply", PARAGRAPH, "p_b") == ("p_b", (35, 45))
    assert lf.locate("must apply", PARAGRAPH, "p_a") == ("p", (7, 17))


def test_units_keep_the_clause_texts_exactly_as_sent(uk_corpus):
    for unit in llm_compare.paragraph_units(uk_corpus):
        assert llm_compare.clause_lines(unit["clauses"]) == unit["text"]
        assert [cid for cid, _ in unit["clauses"]] == unit["clause_ids"]


# --- the two perturbations ------------------------------------------------------------------------------------

def test_deletion_removes_every_occurrence_of_every_quote_in_every_clause():
    text = lf.deletion_text(PARAGRAPH, ["Must apply", "business relationship"])
    assert text == ("[p] A bank   customer due diligence measures if the bank—\n"
                    "[p_a] (a) establishes a  ;\n"
                    "[p_b] (b) suspects money laundering, and   them again.")


def test_deletion_of_a_short_quote_leaves_other_words_intact():
    paragraph = [("p", "A relevant person must apply measures on request if the person—"),
                 ("p_a", "(a) establishes a business relationship;")]
    assert lf.deletion_text(paragraph, ["on"]) == ("[p] A relevant person must apply measures   request if the person—\n"
                                                  "[p_a] (a) establishes a business relationship;")
    assert "s" in lf.deletion_text([("c", "customers")], ["customer"])  # "customers" is not cut to "s"


def test_rationale_only_keeps_the_first_located_occurrence_of_each_quote_in_its_clause():
    text = lf.rationale_only_text(PARAGRAPH, ["must apply", "business  relationship", "customer due diligence"], "p_a")
    assert text == ("[p] must apply customer due diligence\n"
                    "[p_a] business relationship\n"
                    "[p_b] ")


def test_overlapping_quotes_are_kept_once():
    text = lf.rationale_only_text(PARAGRAPH, ["must apply customer", "apply customer due"], "p")
    assert text.splitlines()[0] == "[p] must apply customer due"


def test_coverage_counts_quoted_characters_over_the_clauses_touched_plus_the_labelled_one():
    # "business relationship" (21 chars) in p_a, labelled clause p_a: 21 / len(p_a)
    assert lf.coverage(PARAGRAPH, ["business relationship"], "p_a") == pytest.approx(21 / len(PARAGRAPH[1][1]))
    # quote in the lead-in for a label on p_a: denominator is p plus p_a
    assert lf.coverage(PARAGRAPH, ["customer due diligence"], "p_a") == \
        pytest.approx(22 / (len(PARAGRAPH[0][1]) + len(PARAGRAPH[1][1])))


def test_coverage_counts_every_occurrence_the_deletion_removes():
    # "must apply" occurs in p and in p_b: both are deleted, so both count, over p, p_a (labelled) and p_b
    assert lf.coverage(PARAGRAPH, ["must apply"], "p_a") == pytest.approx(20 / sum(len(t) for _, t in PARAGRAPH))
    assert lf.repeated_quotes(PARAGRAPH, ["must apply", "business relationship"]) == ["must apply"]


# --- answers in both formats ----------------------------------------------------------------------------------

def _record(paragraph, answer, **extra):
    return json.dumps({"paragraph": paragraph, "model": "fake", "prompt_version": "test",
                       "response": json.dumps(answer), **extra}) + "\n"


def test_load_answers_reads_both_answer_formats(uk_corpus, tmp_path):
    first, second = llm_compare.paragraph_units(uk_corpus)[:2]
    run = tmp_path / "run.jsonl"
    run.write_text(
        _record(first["paragraph"], {"labels": [{"clause_id": first["clause_ids"][0],
                                                 "types": ["cdd_triggers", "verify_customer"]}]})
        + _record(second["paragraph"], {"labels": [
            {"clause_id": second["clause_ids"][0], "type": "cdd_triggers", "evidence": ["must also apply"]},
            {"clause_id": second["clause_ids"][0], "type": "made_up", "evidence": []}]}))
    loaded = llm_compare.load_answers(str(run), uk_corpus)
    assert loaded["predictions"][first["clause_ids"][0]] == {"cdd_triggers", "verify_customer"}
    assert loaded["predictions"][second["clause_ids"][0]] == {"cdd_triggers"}
    assert loaded["evidence"][(second["clause_ids"][0], "cdd_triggers")] == ["must also apply"]
    assert loaded["evidence"][(first["clause_ids"][0], "cdd_triggers")] == []
    assert loaded["stats"]["invalid_type_names"] == [f"{second['paragraph']}: made_up"]


def test_the_v1_prompt_is_unchanged_so_the_cached_run_still_matches(uk_corpus):
    unit = llm_compare.paragraph_units(uk_corpus)[0]
    cached = json.loads(UK_RUN.read_text(encoding="utf-8").splitlines()[0])
    assert cached["paragraph"] == unit["paragraph"]
    system = llm_compare.system_prompt(DATA_DIR, uk_corpus)
    assert llm_compare.prompt_sha256(system, llm_compare.user_prompt(uk_corpus, unit["paragraph"], unit["text"])) \
        == cached["prompt_sha256"]
    # the evidence prompt keeps the same task text and changes only the answer format
    evidence = llm_compare.system_prompt(DATA_DIR, uk_corpus, evidence=True)
    assert evidence.split("Answer with JSON only")[0] == system.split("Answer with JSON only")[0]


# --- scoring from tiny caches ---------------------------------------------------------------------------------

def test_scoring_counts_passes_failures_and_failed_requests_separately(uk_corpus, tmp_path):
    unit = llm_compare.paragraph_units(uk_corpus)[0]  # 27(1): lead-in plus items (a)-(d)
    lead, item_a, item_b = unit["clause_ids"][:3]
    run = tmp_path / "fake_evidence.jsonl"
    run.write_text(_record(unit["paragraph"], {"labels": [
        {"clause_id": lead, "type": "cdd_triggers", "evidence": ["must apply customer due diligence measures"]},
        {"clause_id": item_a, "type": "cdd_triggers", "evidence": ["establishes a business relationship"]},
        {"clause_id": item_b, "type": "cdd_triggers", "evidence": ["occasional transaction", "not in the text"]},
        {"clause_id": item_b, "type": "verify_customer", "evidence": []},
    ]}))
    items = {(i["clause_id"], i["type"]): i for i in lf.label_items(uk_corpus, str(run))}
    assert items[(item_b, "cdd_triggers")]["category"] == "some_located"
    assert items[(item_b, "verify_customer")]["category"] == "no_evidence"

    system = llm_compare.system_prompt(DATA_DIR, uk_corpus, evidence=True)

    def cached(clause_id, test, answer=None, error=None):
        item = items[(clause_id, "cdd_triggers")]
        record = {"paragraph": unit["paragraph"], "clause_id": clause_id, "type": "cdd_triggers", "test": test,
                  "perturbed_sha256": lf.perturbed_prompt(system, uk_corpus, item, test)[1], "model": "fake"}
        record.update({"error": error} if error else {"response": json.dumps({"labels": answer})})
        return json.dumps(record) + "\n"

    keep = [{"clause_id": lead, "type": "cdd_triggers", "evidence": []}]
    cache = tmp_path / "cache.jsonl"
    cache.write_text(
        cached(lead, "deletion", answer=[]) + cached(lead, "rationale_only", answer=keep)          # passes both
        + cached(item_a, "deletion", answer=[{"clause_id": item_a, "type": "cdd_triggers"}])      # fails deletion
        + cached(item_a, "rationale_only", answer=[{"clause_id": item_a, "type": "cdd_triggers"}])
        + cached(item_b, "deletion", error="ReadTimeout: timed out")                             # request failed
        + cached(item_b, "rationale_only", answer=[]))                                           # fails rationale-only
    summary = lf.score(DATA_DIR, uk_corpus, str(run), str(cache))

    assert summary["labels"] == 4 and summary["labels_tested"] == 3
    assert summary["evidence"] == {"quotes_given": 4, "quotes_located": 3, "labels_by_category": {
        "all_located": 2, "some_located": 1, "none_located": 0, "no_evidence": 1}, "labels_with_repeated_quotes": 0}
    assert summary["deletion"] == {"passed": 1, "tested": 2, "rate": 0.5,
                                   "failed_requests": 1, "unparseable": 0, "not_run": 0}
    assert summary["rationale_only"]["passed"] == 2 and summary["rationale_only"]["tested"] == 3
    assert summary["both"] == {"passed": 1, "tested": 2, "rate": 0.5}
    assert [(f["clause_id"], f["test"]) for f in summary["failures"]] == [(item_a, "deletion"), (item_b, "rationale_only")]
    assert summary["failures"][0]["answer_types"] == ["cdd_triggers"]
    assert summary["request_failures"] == [{"clause_id": item_b, "type": "cdd_triggers", "test": "deletion",
                                            "error": "ReadTimeout: timed out"}]
    assert 0 < summary["coverage"]["mean"] < 1
    # the five answers used (the not-run test excluded): one failed request, none with the output cap
    assert summary["generation"]["records"] == 6 and summary["generation"]["answers"] == 5
    assert summary["generation"]["hit_cap"] == 0 and summary["generation"]["invalid_json"] == 0


def test_an_answer_for_a_different_perturbed_prompt_counts_as_not_run(uk_corpus, tmp_path):
    unit = llm_compare.paragraph_units(uk_corpus)[0]
    run = tmp_path / "fake_evidence.jsonl"
    run.write_text(_record(unit["paragraph"], {"labels": [
        {"clause_id": unit["clause_ids"][0], "type": "cdd_triggers", "evidence": ["must apply"]}]}))
    cache = tmp_path / "cache.jsonl"
    cache.write_text(json.dumps({"paragraph": unit["paragraph"], "clause_id": unit["clause_ids"][0],
                                 "type": "cdd_triggers", "test": "deletion", "perturbed_sha256": "stale",
                                 "response": "{\"labels\": []}"}) + "\n")
    summary = lf.score(DATA_DIR, uk_corpus, str(run), str(cache))
    assert summary["deletion"]["not_run"] == 1 and summary["deletion"]["tested"] == 0
    assert summary["rationale_only"]["not_run"] == 1


def test_an_answer_in_the_wrong_shape_is_unparseable_not_a_deletion_pass():
    # {"result": []} is valid JSON but does not say the label is gone; counting it as a pass would flatter the model
    ids = {"c1", "c2"}
    assert lf.answer_types('{"result": []}', "c1", ids) is None
    assert lf.answer_types('{"labels": "none"}', "c1", ids) is None
    assert lf.answer_types("not json", "c1", ids) is None
    assert lf.answer_types('{"labels": []}', "c1", ids) == []
    assert lf.answer_types('{"labels": [{"clause_id": "c1", "type": "cdd_triggers", "evidence": []}]}', "c1", ids) \
        == ["cdd_triggers"]
    assert lf.answer_types('{"labels": [{"clause_id": "c2", "types": ["cdd_triggers"]}]}', "c1", ids) == []


@pytest.mark.parametrize("answer", [
    {"labels": [{"id": "c1", "type": "cdd_triggers"}]},                         # no clause_id
    {"labels": [{"clause_id": "c1", "label": "cdd_triggers"}]},                 # no type or types
    {"labels": [{"clause_id": "[c1]", "type": "cdd_triggers"}]},                # a clause ID that was not sent
    {"labels": ["cdd_triggers"]},                                               # an entry that is not an object
    {"labels": [{"clause_id": "c1", "obligation_types": ["cdd_triggers"]}]},    # no type or types
    {"labels": [{"clause_id": "c2", "type": "verify_customer"},                 # one good entry does not save
                {"clause_id": "uk_c1", "type": "cdd_triggers"}]},               # a mangled ID in another
])
def test_an_answer_in_a_drifted_entry_shape_is_off_format_not_a_pass_or_failure(answer):
    assert lf.answer_types(json.dumps(answer), "c1", {"c1", "c2"}) is None
    assert lf.answer_problem(json.dumps(answer), {"c1", "c2"})


def test_drifted_answers_are_counted_on_their_own_in_both_tests(uk_corpus, tmp_path):
    unit = llm_compare.paragraph_units(uk_corpus)[0]
    lead = unit["clause_ids"][0]
    run = tmp_path / "fake_evidence.jsonl"
    run.write_text(_record(unit["paragraph"], {"labels": [
        {"clause_id": lead, "type": "cdd_triggers", "evidence": ["must apply"]}]}))
    item = next(i for i in lf.label_items(uk_corpus, str(run)) if i["located"])
    system = llm_compare.system_prompt(DATA_DIR, uk_corpus, evidence=True)
    mangled = lead.replace("uk_mlr_2017_", "uk_mlr_")  # the drift seen in the real cache
    cache = tmp_path / "cache.jsonl"
    cache.write_text("".join(json.dumps({
        "paragraph": unit["paragraph"], "clause_id": lead, "type": "cdd_triggers", "test": test, "model": "fake",
        "perturbed_sha256": lf.perturbed_prompt(system, uk_corpus, item, test)[1],
        "response": json.dumps(answer)}) + "\n" for test, answer in (
            ("deletion", {"labels": [{"id": lead, "type": "cdd_triggers"}]}),                    # would be a false pass
            ("rationale_only", {"labels": [{"clause_id": mangled, "type": "cdd_triggers"}]}))))  # a false failure
    summary = lf.score(DATA_DIR, uk_corpus, str(run), str(cache))
    for test in lf.TESTS:
        assert summary[test]["unparseable"] == 1 and summary[test]["tested"] == 0 and summary[test]["passed"] == 0
    assert summary["failures"] == []
    assert [f["error"].split(":")[0] for f in summary["request_failures"]] == [
        "an entry has no clause_id", "cites a clause ID that was not sent"]


def test_an_empty_or_partly_written_runs_file_is_skipped_with_a_message(uk_corpus, tmp_path, capsys):
    empty = tmp_path / "empty_evidence.jsonl"
    empty.write_text("")
    assert lf.score(DATA_DIR, uk_corpus, str(empty), str(tmp_path / "missing.jsonl")) is None
    assert "skipping" in capsys.readouterr().err
    unit = llm_compare.paragraph_units(uk_corpus)[0]
    partial = tmp_path / "partial_evidence.jsonl"
    partial.write_text(_record(unit["paragraph"], {"labels": []}) + '{"paragraph": "27(2)", "resp')
    assert lf.score_files(DATA_DIR, "uk_mlr_2017", str(partial), str(tmp_path / "missing.jsonl"),
                          str(tmp_path / "out")) is None
    assert "not valid JSON" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_a_cache_line_cut_off_while_being_written_counts_as_not_run(tmp_path, capsys):
    cache = tmp_path / "cache.jsonl"
    good = {"paragraph": "27(1)", "clause_id": "c", "type": "cdd_triggers", "test": "deletion", "response": "{}"}
    cache.write_text(json.dumps(good) + "\n" + '{"paragraph": "27(1)", "clause_id": "c", "ty')
    assert list(lf.read_cache(str(cache)).values()) == [good]
    assert "skipping line 2" in capsys.readouterr().err


def test_resume_keeps_answers_for_the_same_prompt_and_asks_only_the_rest(uk_corpus, tmp_path, monkeypatch):
    data_dir = str(Path(__file__).resolve().parents[2] / "data")
    units = llm_compare.paragraph_units(uk_corpus)[:3]
    system = llm_compare.system_prompt(data_dir, uk_corpus, evidence=True)
    out = tmp_path / "run.jsonl"
    first = units[0]
    kept = {"paragraph": first["paragraph"], "model": "m", "response": '{"labels": []}',
            "prompt_sha256": llm_compare.prompt_sha256(system, llm_compare.user_prompt(uk_corpus, first["paragraph"], first["text"]))}
    stale = {"paragraph": units[1]["paragraph"], "model": "m", "response": '{"labels": []}', "prompt_sha256": "old"}
    out.write_text(json.dumps(kept) + "\n" + json.dumps(stale) + "\n", encoding="utf-8")
    asked = []
    monkeypatch.setattr(llm_compare, "endpoint", lambda base_url, data_dir: {"local": True, "api_key": "ollama"})
    monkeypatch.setattr(llm_compare, "chat", lambda client, model, base_url, conn, system, user: asked.append(user) or {"response": '{"labels": []}'})
    llm_compare.run_model(data_dir, "uk_mlr_2017", "m", "http://localhost:11434/v1", str(out), limit=3, evidence=True, resume=True)
    records = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [r["paragraph"] for r in records] == [u["paragraph"] for u in units]
    assert records[0] == kept                      # same prompt: kept as it was
    assert len(asked) == 2                         # the stale prompt and the missing paragraph are asked again
    assert records[1]["num_predict"] == llm_compare.MAX_NEW_TOKENS
    assert not (tmp_path / "run.jsonl.partial").exists()


def test_unknown_or_missing_type_names_make_an_answer_unscorable():
    ids, types = {"c1", "c2"}, {"cdd_triggers", "verify_customer"}
    for answer in ('{"labels": [{"clause_id": "c1", "type": "CDD triggers"}]}',
                   '{"labels": [{"clause_id": "c1", "type": null}]}',
                   '{"labels": [{"clause_id": "c1", "types": []}]}'):
        assert lf.answer_types(answer, "c1", ids, types) is None, answer
    assert lf.answer_types('{"labels": [{"clause_id": "c2", "type": "verify_customer"}]}', "c1", ids, types) == []


def test_resume_skips_a_line_cut_off_by_an_interrupted_run(tmp_path):
    out = tmp_path / "run.jsonl"
    (tmp_path / "run.jsonl.partial").write_text('{"paragraph": "27(1)", "model": "m", "response": "{}"}\n{"paragraph": "27(2)", "mod', encoding="utf-8")
    cached = llm_compare._cached(str(out), "m")
    assert list(cached) == ["27(1)"]
