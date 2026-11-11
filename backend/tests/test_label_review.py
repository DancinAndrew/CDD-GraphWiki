"""
英國保留文本金標的獨立審核：預先登錄的金標不可改、修訂版只能由審核結果產生，評分同時報告兩版。
"""
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from src.heldout import evaluate, label_review

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = str(REPO_ROOT / "data")
HELDOUT = REPO_ROOT / "data" / "heldout"
REVIEW = HELDOUT / "reviews" / "uk_mlr_2017"

# 預先登錄（commit 5a89252）時的內容；審核不得改動金標原檔，也不得改標註指南（它同時是 LLM 提示的一部分）
PRE_REGISTERED_SHA256 = {
    "gold_labels_uk_mlr_2017.yaml": "b7d73c32c6c467d8b2a71a6d9548ee5ecc8aa695d9539609de18799daf5be65e",
    "ANNOTATION_GUIDELINE.md": "5d413864bc588dcc94329caf446968a0729c202ef59afad305081c8972ba2486",
}


@pytest.fixture(scope="module")
def corpus():
    return evaluate.load_corpus(DATA_DIR, "uk_mlr_2017", labels="pre_registered")


@pytest.fixture(scope="module")
def candidates(corpus):
    return label_review.build_candidates(DATA_DIR, corpus)


@pytest.fixture(scope="module")
def rows(corpus, candidates):
    return label_review.decisions(DATA_DIR, corpus, candidates)


@pytest.mark.parametrize("name", sorted(PRE_REGISTERED_SHA256))
def test_pre_registered_files_are_untouched(name):
    assert hashlib.sha256((HELDOUT / name).read_bytes()).hexdigest() == PRE_REGISTERED_SHA256[name]


def test_the_adjudicators_sheet_is_rebuilt_from_the_stage1_answers(corpus, candidates):
    """裁決者拿到的那份清單可由三位初審者的答案重建，一字不差。"""
    assert label_review.candidates_sheet(corpus, candidates) == (REVIEW / "stage2" / "candidates.md").read_text(encoding="utf-8")
    # 只要有一位初審者和預先登錄的類型不同，就是候選；完全一致的條文不送裁決
    assert len(candidates) == 42
    assert all(alt["types"] != k["pre_registered"] for k in candidates for alt in k["alternatives"])


def test_committed_review_outputs_match_a_rebuild(corpus, rows):
    assert label_review._decisions_yaml(corpus, rows) == (REVIEW / "decisions.yaml").read_text(encoding="utf-8")
    revised_path = HELDOUT / evaluate.label_file(corpus.spec, "revised")
    assert label_review.revised_label_doc(DATA_DIR, corpus, rows) == revised_path.read_text(encoding="utf-8")
    assert json.loads((REVIEW / "agreement.json").read_text()) == label_review.agreement(DATA_DIR, corpus)
    assert json.loads((REVIEW / "scores_before_after.json").read_text()) == json.loads(
        json.dumps(label_review.scores_before_after(DATA_DIR, corpus, rows)))


def test_revised_labels_differ_only_where_a_change_was_accepted(corpus, rows):
    revised = evaluate.load_corpus(DATA_DIR, "uk_mlr_2017", labels="revised").gold
    changed = {row["clause_id"]: set(row["types"]) for row in rows if row["outcome"] == "changed"}
    assert {cid for cid in corpus.gold if corpus.gold[cid] != revised[cid]} == set(changed)
    assert all(revised[cid] == types for cid, types in changed.items())
    # 這次審核唯一接受的修改：28(3)(b)(ii) 董事與高階人員姓名屬於關聯方，指南把關聯方排除在 verify_customer 之外
    assert changed == {"uk_mlr_2017_28_cdd_measures_28_3_b_ii": set()}


def test_outcomes_follow_the_protocol(rows):
    assert {o: sum(1 for r in rows if r["outcome"] == o) for o in ("changed", "kept", "guideline_gap")} == {
        "changed": 1, "kept": 12, "guideline_gap": 29}
    for row in rows:
        assert row["outcome"] == label_review.decide(
            {"pre_registered": row["pre_registered"]},
            {v["adjudicator"]: v for v in row["votes"]})["outcome"]


def _vote(types, decided=True, breaks=False, quote="guideline words"):
    return {"types": types, "decided_by_guideline": decided, "pre_registered_breaks_guideline": breaks,
            "guideline_quote": quote}


VC = ["verify_customer"]
CT = ["cdd_triggers"]


@pytest.mark.parametrize("original,votes,outcome,types,preferred", [
    # 兩票選同一組、都說原標註違反指南並引用原文：改
    (VC, [_vote([], breaks=True), _vote([], breaks=True), _vote(VC)], "changed", [], []),
    # 兩票偏好另一組，但都認為原標註說得通：保留，只記下多數偏好的讀法
    (CT, [_vote(CT + ["prohibit_anonymous"]), _vote(CT + ["prohibit_anonymous"]), _vote(CT)],
     "kept", CT, CT + ["prohibit_anonymous"]),
    # 說違反指南卻沒有引用原文，不算數
    (VC, [_vote([], breaks=True, quote=""), _vote([], breaks=True), _vote(VC)], "kept", VC, []),
    # 兩票說指南沒有決定這個情況：記為指南缺口，標註不變
    (VC, [_vote([], decided=False), _vote([], decided=False), _vote([], breaks=True)], "guideline_gap", VC, []),
    # 兩票都要改，但改成不同的組合：不改
    (VC, [_vote([], breaks=True), _vote(["identify_ubo"], breaks=True), _vote(VC)], "kept", VC, None),
])
def test_decision_rule(original, votes, outcome, types, preferred):
    d = label_review.decide({"pre_registered": original}, dict(enumerate(votes, 1)))
    assert (d["outcome"], d["types"], d["preferred_reading"]) == (outcome, types, preferred)


def test_only_sets_with_a_reviewed_label_file_can_load_revised_labels():
    with pytest.raises(ValueError):
        evaluate.load_corpus(DATA_DIR, "mas_notice_626", labels="revised")
    revised = evaluate.load_corpus(DATA_DIR, "uk_mlr_2017", labels="revised")
    assert sum(1 for types in revised.gold.values() if types) == 74


def test_results_folder_still_scores_against_the_pre_registered_labels(corpus):
    """data/heldout/results/ 的分數維持預先登錄的金標；審核後的分數另外寫在 reviews/。"""
    committed = json.loads((HELDOUT / "results" / "uk_mlr_2017" / "rules_summary.json").read_text())
    scores = json.loads((REVIEW / "scores_before_after.json").read_text())
    for version in ("rules_v1", "rules_v2"):
        assert scores["systems"][version]["pre_registered"] == {k: committed[version][k] for k in ("clause", "paragraph")}


def test_reviewers_used_only_known_clauses_and_types(corpus):
    ids, types = set(corpus.gold), set(corpus.types)
    for name in ("annotator_a", "annotator_b"):
        doc = yaml.safe_load((REVIEW / "stage1" / f"{name}.yaml").read_text(encoding="utf-8"))
        assert all(e["clause_id"] in ids and set(e["types"]) <= types for e in doc["labels"])
    for n in label_review.ADJUDICATORS:
        doc = yaml.safe_load((REVIEW / "stage2" / f"adjudicator_{n}.yaml").read_text(encoding="utf-8"))
        assert sorted(d["candidate"] for d in doc["decisions"]) == [f"K{i:03d}" for i in range(1, 43)]
