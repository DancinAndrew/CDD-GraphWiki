"""
規則義務的信心值是量出來的：規則 v2 在未見過的英國條例保留文本上、段落層級的各類型精確率。
"""
import json
import os
import re
import subprocess
import sys

import pytest
import yaml

from src.contracts.models import Obligation
from src.extraction import frames, reliability
from src.extraction.extractor import RuleBasedObligationExtractor, extract_obligations, profile_for

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(REPO_ROOT, "data")
UK_TITLE = "Part 3 of the UK Money Laundering Regulations 2017"
PROCESSED = os.environ["CDD_PROCESSED_DIR"]  # rebuilt by conftest.py


def rule_type_of(ob: Obligation) -> str:
    """從義務 ID 與管轄區反查規則類型（樣板對照表），不看 explanations。"""
    hits = [t for t in frames.TYPES
            if re.fullmatch(re.escape(profile_for(t, ob.jurisdiction).obligation_id).replace(r"\{pct\}", r"(?:_\d+)?"),
                            ob.obligation_id)]
    assert len(hits) == 1, (ob.obligation_id, hits)
    return hits[0]


@pytest.fixture(scope="module")
def measured():
    return reliability.measured_precision(DATA_DIR)


def test_numbers_equal_committed_held_out_scores(measured):
    """與 src.heldout.label_review 寫出的 scores_before_after.json（rules v2、審核後金標、段落層級）一致。"""
    assert reliability.RELIABILITY_LABELS == "revised"  # PROTOCOL.md 第 6 條事先定好：有修訂就用審核後的金標
    path = os.path.join(DATA_DIR, "heldout", "reviews", "uk_mlr_2017", "scores_before_after.json")
    with open(path, encoding="utf-8") as f:
        by_type = json.load(f)["systems"]["rules_v2"]["revised"]["paragraph"]["by_type"]
    assert set(measured) == set(frames.TYPES)
    for rule_type, entry in measured.items():
        scores = by_type.get(rule_type, {"tp": 0, "fp": 0, "fn": 0})
        assert entry["correct"] == scores["tp"]
        assert entry["flagged"] == scores["tp"] + scores["fp"]
        assert entry["gold"] == scores["tp"] + scores["fn"] and entry["missed"] == scores["fn"]
        if entry["flagged"]:
            assert entry["precision"] == scores["precision"]
    assert any(e["flagged"] for e in measured.values())


def test_basis_sentences(measured):
    for entry in measured.values():
        if entry["flagged"]:
            assert entry["basis"] == (
                f"Rules v2 on unseen text ({UK_TITLE}, labelled after the rules were frozen, then independently "
                f"reviewed): "
                f"{entry['correct']} of {entry['flagged']} paragraphs flagged with this type were correct.")
        elif entry["gold"]:
            assert entry["basis"] == (
                f"Not measured: rules v2 flagged no paragraph with this type in unseen text ({UK_TITLE}), although "
                f"the reviewed gold labels give it to {entry['gold']} paragraphs there; the rules found none of them.")
        else:
            assert entry["basis"] == (
                f"Not measured: rules v2 flagged no paragraph with this type in unseen text ({UK_TITLE}), "
                f"and the reviewed gold labels give it to no paragraph there either.")


def test_types_never_flagged_have_no_precision(measured):
    unmeasured = [t for t, e in measured.items() if not e["flagged"]]
    for rule_type in unmeasured:
        entry = measured[rule_type]
        assert entry == {"correct": 0, "flagged": 0, "precision": None, "gold": entry["missed"],
                         "missed": entry["missed"], "basis": entry["basis"]}
        fields = reliability.confidence_for(measured, rule_type)
        assert fields["confidence"] is None and fields["confidence_kind"] is None


def test_a_type_the_rules_missed_everywhere_is_not_reported_as_unlabelled(measured):
    """沒被標過的類型分兩種：金標有、規則全漏（召回率量到 0），和金標與規則都沒有（沒有證據）。"""
    # 審核後的英國金標（段落層級與預先登錄的相同）：PEP 加強審查 4 段、無法完成 CDD 2 段，規則 v2 一段都沒找到
    assert {t: (e["gold"], e["missed"]) for t, e in measured.items() if not e["flagged"] and e["gold"]} == {
        "pep_edd": (4, 4), "cdd_incomplete": (2, 2)}
    # 英國保留文本的金標沒有 PEP 禁令與 PEP 核准這兩類，規則也就不可能在那裡被量測
    assert {t for t, e in measured.items() if not e["flagged"] and not e["gold"]} == {"pep_prohibition", "pep_approval"}
    assert "4 paragraphs" in measured["pep_edd"]["basis"] and "found none" in measured["pep_edd"]["basis"]
    assert "no paragraph there either" in measured["pep_approval"]["basis"]
    assert reliability.basis_sentence({"correct": 0, "flagged": 0, "gold": 1, "missed": 1}, "T") == (
        "Not measured: rules v2 flagged no paragraph with this type in unseen text (T), although the gold labels "
        "give it to 1 paragraph there; the rules found none of them.")


def test_confidence_rounds_precision_to_two_places(measured):
    for rule_type, entry in measured.items():
        fields = reliability.confidence_for(measured, rule_type)
        expected = round(entry["precision"], 2) if entry["precision"] is not None else None
        # 種類只在真的有量測值時標成 measured_on_heldout
        kind = "measured_on_heldout" if expected is not None else None
        assert fields == {"confidence": expected, "confidence_basis": entry["basis"], "confidence_kind": kind}


def test_extractor_without_reliability():
    fields = reliability.confidence_for(None, "cdd_triggers")
    assert fields == {"confidence": None, "confidence_basis": reliability.NO_RELIABILITY_BASIS,
                      "confidence_kind": None}
    assert RuleBasedObligationExtractor().reliability is None


def test_pipeline_writes_measured_confidence():
    """管線輸出的每個規則義務，信心值與出處說明都等於其類型的量測結果；summary.json 記錄量測本身。"""
    with open(os.path.join(PROCESSED, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)["rule_reliability"]
    assert summary["set"] == "uk_mlr_2017" and summary["level"] == "paragraph" and summary["labels"] == "revised"
    measured = reliability.measured_precision(DATA_DIR)
    assert summary["by_type"] == {t: {k: v for k, v in e.items() if k != "basis"} for t, e in measured.items()}

    with open(os.path.join(PROCESSED, "obligations.yaml"), encoding="utf-8") as f:
        obligations = [Obligation.model_validate(o) for o in yaml.safe_load(f)]
    assert obligations
    for ob in obligations:
        assert {"confidence": ob.confidence, "confidence_basis": ob.confidence_basis,
                "confidence_kind": ob.confidence_kind} == \
            reliability.confidence_for(measured, rule_type_of(ob)), ob.obligation_id


def test_profiles_carry_no_hand_set_confidence():
    assert not hasattr(profile_for("cdd_triggers", "Singapore"), "confidence")
    assert not hasattr(profile_for("cdd_triggers", "Testland"), "confidence")


def test_the_extractor_cli_writes_the_same_measured_confidence_as_the_pipeline(tmp_path):
    """python -m src.extraction.extractor 預設寫進 data/processed，信心值必須和 src.pipeline 一樣是量測值。"""
    out = tmp_path / "cli"
    subprocess.run(
        [sys.executable, "-m", "src.extraction.extractor", "--clauses", os.path.join(PROCESSED, "clauses.yaml"),
         "--gold", os.path.join(DATA_DIR, "gold", "obligations.yaml"),
         "--sources", os.path.join(PROCESSED, "source_documents.yaml"), "--out", str(out)],
        cwd=os.path.join(REPO_ROOT, "backend"), check=True, capture_output=True,
        env={**os.environ, "PYTHONPATH": os.path.join(REPO_ROOT, "backend")})
    with open(out / "obligations.yaml", encoding="utf-8") as f:
        from_cli = yaml.safe_load(f)
    with open(os.path.join(PROCESSED, "obligations.yaml"), encoding="utf-8") as f:
        from_pipeline = yaml.safe_load(f)
    assert from_cli == from_pipeline
    assert any(ob["confidence_kind"] == "measured_on_heldout" for ob in from_cli)
