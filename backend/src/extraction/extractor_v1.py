"""
Frozen copy of the version-1 rule-based extractor (as of commit b7fe062).

This is the version that matched 12/12 development obligations and found 1 of 18 obligations in the held-out
MAS Notice 626 paragraphs. It is kept unchanged only so that src/heldout/evaluate.py can score the old and the
new rules side by side; the pipeline and the API use src/extraction/extractor.py.
"""
import os
import re
import yaml
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterable
from src.contracts.models import Clause, Obligation, SourceDocument


# ---------------------------------------------------------------------------
# 文字特徵：門檻與觸發條件都從條文本身解析，不寫死在規則裡
# ---------------------------------------------------------------------------

# CDD 觸發句型，例如 FATF「undertake customer due diligence (CDD) measures when」
# 或 MAS「perform the measures as required by paragraphs 6, 7 and 8 when」
TRIGGER_STATEMENT = re.compile(
    r"(customer due diligence|\bcdd\b)[^.:;]{0,40}\bmeasures\s+when"
    r"|measures as required by paragraphs [\d,\sand]+\bwhen"
)
AMOUNT_PATTERN = re.compile(r"(usd/eur|s\$|sgd)\s?(\d{1,3}(?:,\d{3})+|\d+)")
THRESHOLD_PERCENT_PATTERN = re.compile(r"threshold of (\d{1,3})\s?%")
PERCENT_PATTERN = re.compile(r"(\d{1,3})\s?%")
CURRENCY_CODES = {"usd/eur": "usd_eur", "s$": "sgd", "sgd": "sgd"}

DEFAULT_JURISDICTION_BY_PREFIX = (("mas", "Singapore"), ("fatf", "Global"))
OBLIGATION_INDICATORS = ("shall", "should", "prohibited", "required", "must", "undertake")


def infer_jurisdiction(source_document_id: str) -> str:
    """沒有來源文件 metadata 時，依文件 ID 前綴推定管轄區。"""
    for prefix, jurisdiction in DEFAULT_JURISDICTION_BY_PREFIX:
        if source_document_id.lower().startswith(prefix):
            return jurisdiction
    return "Internal"


def parse_amount(text: str) -> Optional[Tuple[int, str]]:
    """解析條文中的金額門檻，例如 'USD/EUR 15,000' -> (15000, 'usd_eur')、'S$20,000' -> (20000, 'sgd')。"""
    match = AMOUNT_PATTERN.search(text.lower())
    if not match:
        return None
    currency, amount = match.groups()
    return int(amount.replace(",", "")), CURRENCY_CODES[currency]


def parse_percent(text: str) -> Optional[int]:
    """解析持股門檻；優先取「threshold of X%」，否則取條文中第一個百分比。"""
    lowered = text.lower()
    match = THRESHOLD_PERCENT_PATTERN.search(lowered) or PERCENT_PATTERN.search(lowered)
    return int(match.group(1)) if match else None


def trigger_conditions(text: str) -> List[str]:
    """把 CDD 觸發子條款的文字轉成機器可讀的條件。"""
    lowered = text.lower()
    conditions = []
    if re.search(r"establish(es|ing)? business relation", lowered):
        conditions.append("establishing_business_relations")
    amount = parse_amount(lowered)
    if amount and "transaction" in lowered:
        value, currency = amount
        conditions.append(f"occasional_transaction_above_{value}_{currency}")
    if "suspicion of money laundering" in lowered:
        conditions.append("suspicion_of_money_laundering")
    if "doubts about the veracity" in lowered:
        conditions.append("doubts_about_veracity_of_data")
    return conditions


# ---------------------------------------------------------------------------
# 規則輸出設定：每條規則在每個管轄區對應一個義務樣板
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ObligationProfile:
    obligation_id: str
    actor: str
    action: str
    object: str
    confidence: float
    applies_to: Dict[str, Any] = field(default_factory=dict)
    base_conditions: Tuple[str, ...] = ()
    required_evidence: Tuple[str, ...] = ()
    review_flags: Tuple[str, ...] = ()


PROFILES: Dict[Tuple[str, str], ObligationProfile] = {
    ("prohibit_anonymous", "Global"): ObligationProfile(
        "ob_prohibit_anonymous", "financial_institution", "prohibit", "anonymous_accounts", 0.95,
        review_flags=("anonymous_account_creation_attempt",)),
    ("cdd_triggers", "Global"): ObligationProfile(
        "ob_cdd_on_relationship", "financial_institution", "perform_cdd", "customer", 0.92,
        required_evidence=("cdd_checklist_completed",)),
    ("cdd_triggers", "Singapore"): ObligationProfile(
        "ob_cdd_on_relationship_mas", "bank", "perform_cdd", "customer", 0.96,
        required_evidence=("cdd_completed_signoff",)),
    ("verify_customer", "Global"): ObligationProfile(
        "ob_verify_customer_identity", "financial_institution", "identify_and_verify", "customer_identity", 0.94,
        base_conditions=("cdd_triggered",),
        required_evidence=("reliable_independent_source_documents",),
        review_flags=("unverifiable_identity_documents",)),
    ("verify_customer", "Singapore"): ObligationProfile(
        "ob_verify_customer_mas", "bank", "identify_and_verify", "customer_identity", 0.95,
        base_conditions=("cdd_triggered",),
        required_evidence=("full_name", "unique_id_number", "residential_address", "date_of_birth",
                           "nationality", "reliable_independent_source_documents"),
        review_flags=("missing_mandatory_identification_fields",)),
    # identify_ubo 的 ID 依解析到的持股門檻決定：{pct} 會變成 "_25"、"_10" 或空字串
    ("identify_ubo", "Global"): ObligationProfile(
        "ob_identify_ubo{pct}", "financial_institution", "identify_and_verify", "beneficial_owner", 0.93,
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ownership_chart", "identity_documents_of_ubo"),
        review_flags=("unclear_ownership_structure", "complex_multi_layer_ownership")),
    ("identify_ubo", "Singapore"): ObligationProfile(
        "ob_identify_ubo{pct}_mas", "bank", "identify_and_verify", "beneficial_owner", 0.94,
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ubo_declaration", "corporate_profile"),
        review_flags=("ubo_not_identified", "multi_jurisdictional_layers")),
    ("identify_ubo", "Internal"): ObligationProfile(
        "ob_identify_ubo{pct}_gb", "bank", "identify_and_verify", "beneficial_owner", 0.98,
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ubo_proof_of_identity", "shareholder_registry"),
        review_flags=("ownership_between_10_and_25_percent",)),
    ("pep_edd", "Singapore"): ObligationProfile(
        "ob_pep_edd_mas", "bank", "perform_edd", "pep", 0.97,
        applies_to={"pep_exposure": True},
        base_conditions=("pep_detected",),
        required_evidence=("senior_management_approval", "source_of_wealth_verification",
                           "source_of_funds_verification"),
        review_flags=("pep_without_senior_mgmt_signoff", "insufficient_source_of_wealth_evidence")),
    ("pep_prohibition", "Internal"): ObligationProfile(
        "ob_pep_prohibitions_gb", "bank", "restrict_relationship", "pep", 0.99,
        applies_to={"pep_exposure": True},
        base_conditions=("pep_from_high_risk_jurisdiction",),
        required_evidence=("rejected_onboarding_record",),
        review_flags=("pep_from_high_risk_country",)),
    ("pep_approval", "Internal"): ObligationProfile(
        "ob_pep_approval_gb", "bank", "obtain_approval", "pep", 0.97,
        applies_to={"pep_exposure": True},
        base_conditions=("pep_not_from_high_risk_jurisdiction",),
        required_evidence=("head_of_compliance_approval", "two_levels_senior_mgmt_approval",
                           "source_of_funds_verification", "source_of_wealth_verification"),
        review_flags=("pep_without_head_compliance_signoff",)),
    ("cdd_incomplete", "Singapore"): ObligationProfile(
        "ob_cdd_incomplete_mas", "bank", "refuse_relationship", "customer", 0.95,
        base_conditions=("cdd_measures_not_completed",),
        required_evidence=("account_opening_rejection_record", "str_consideration_record"),
        review_flags=("cdd_incomplete",)),
}


@dataclass
class ClauseMatch:
    """單一條文命中某條規則的結果；同一規則與管轄區的多筆命中會合併成一個義務。"""
    rule: str
    jurisdiction: str
    clause_id: str
    conditions: List[str]


class RuleBasedObligationExtractor:
    """
    基於語法特徵與關鍵字匹配的合規義務抽取器。

    - 規則比對「條文本身＋段落層級的上層條文」，不比對章節標題。
    - 管轄區來自來源文件的 metadata（沒有時依文件 ID 前綴推定）。
    - 持股與金額門檻從條文文字解析，不寫死。
    """

    def __init__(self, confidence_threshold: float = 0.75, jurisdictions: Optional[Dict[str, str]] = None):
        self.confidence_threshold = confidence_threshold
        self.jurisdictions = jurisdictions or {}

    def jurisdiction_for(self, source_document_id: str) -> str:
        return self.jurisdictions.get(source_document_id) or infer_jurisdiction(source_document_id)

    # -- 規則 -----------------------------------------------------------------

    def _match_rule(self, own: str, ctx: str, jurisdiction: str) -> Optional[str]:
        """依序檢查規則，回傳第一條命中且該管轄區有樣板的規則名稱。"""
        is_pep = "politically exposed" in ctx or re.search(r"\bpeps?\b", ctx) is not None
        candidates = []
        if "anonymous" in own or "fictitious" in own:
            candidates.append("prohibit_anonymous")
        if "unable to complete" in ctx and "shall not commence" in ctx:
            candidates.append("cdd_incomplete")
        if is_pep and "approved by" in own:
            candidates.append("pep_approval")
        if is_pep and re.search(r"\bprohibit", ctx):
            candidates.append("pep_prohibition")
        if is_pep and ("enhanced cdd" in ctx or "enhanced due diligence" in ctx):
            candidates.append("pep_edd")
        if (("beneficial owner" in ctx or re.search(r"\bubos?\b", ctx) or "controlling ownership interest" in ctx)
                and re.search(r"\b(identify|identifying|identification|inquire|threshold)\b", ctx)):
            candidates.append("identify_ubo")
        # MAS 6.14B 以「identified under paragraph 6.14」指稱實質受益人，要求驗證其身分
        if re.search(r"identified under paragraph 6\.14\b", ctx):
            candidates.append("identify_ubo")
        if jurisdiction == "Global" and "identifying the customer and verifying" in ctx:
            candidates.append("verify_customer")
        if jurisdiction == "Singapore" and (
            "identify each customer" in ctx
            or "verify the identity of the customer" in ctx
            or "obtain at least the following information" in ctx
        ):
            candidates.append("verify_customer")
        if TRIGGER_STATEMENT.search(ctx):
            candidates.append("cdd_triggers")

        for rule in candidates:
            if (rule, jurisdiction) in PROFILES:
                return rule
        return None

    def _rule_conditions(self, rule: str, own: str) -> List[str]:
        if rule == "cdd_triggers":
            return trigger_conditions(own)
        if rule == "identify_ubo":
            pct = parse_percent(own)
            return [f"controlling_ownership_interest_above_{pct}_percent"] if pct else []
        return []

    def match_clause(self, clause: Clause, context: str = "") -> Tuple[Optional[ClauseMatch], Optional[str]]:
        """
        嘗試把單一條文對應到規則。
        成功回傳 (ClauseMatch, None)；失敗回傳 (None, failure_reason)。
        """
        own = clause.normalized_text.lower()
        ctx = f"{context.lower()} {own}".strip()
        jurisdiction = self.jurisdiction_for(clause.source_document_id)

        rule = self._match_rule(own, ctx, jurisdiction)
        if not rule:
            if any(indicator in ctx for indicator in OBLIGATION_INDICATORS):
                return None, "MISSING_CORE_ELEMENTS"
            return None, "NON_OBLIGATION_TEXT"

        if PROFILES[(rule, jurisdiction)].confidence < self.confidence_threshold:
            return None, "LOW_CONFIDENCE"

        return ClauseMatch(rule, jurisdiction, clause.clause_id, self._rule_conditions(rule, own)), None

    def build_obligation(self, matches: List[ClauseMatch]) -> Obligation:
        """把同一規則、同一管轄區的命中合併成一個強型別 Obligation。"""
        first = matches[0]
        profile = PROFILES[(first.rule, first.jurisdiction)]

        source_clause_ids: List[str] = []
        conditions: List[str] = list(profile.base_conditions)
        for m in matches:
            if m.clause_id not in source_clause_ids:
                source_clause_ids.append(m.clause_id)
            for cond in m.conditions:
                if cond not in conditions:
                    conditions.append(cond)

        obligation_id = profile.obligation_id
        if "{pct}" in obligation_id:
            pcts = sorted({int(c.split("_above_")[1].split("_")[0]) for c in conditions if c.endswith("_percent")})
            obligation_id = obligation_id.format(pct=f"_{pcts[0]}" if pcts else "")

        return Obligation(
            obligation_id=obligation_id,
            source_clause_ids=source_clause_ids,
            jurisdiction=first.jurisdiction,
            actor=profile.actor,
            action=profile.action,
            object=profile.object,
            applies_to=dict(profile.applies_to),
            conditions=conditions,
            exceptions=[],
            required_evidence=list(profile.required_evidence),
            review_flags=list(profile.review_flags),
            confidence=profile.confidence,
            review_status="approved",
        )

    def extract_obligation(self, clause: Clause, context: str = "") -> Tuple[Optional[Obligation], Optional[str]]:
        """單一條文的便利介面：命中時回傳只含這一條出處的 Obligation。"""
        match, reason = self.match_clause(clause, context)
        if not match:
            return None, reason
        return self.build_obligation([match]), None


def build_contexts(clauses: List[Clause]) -> Dict[str, str]:
    """
    為每條條文組出比對用的上下文：沿 parent_clause_id 往上收集段落層級的上層條文，
    略過章節標題（'#'、'##' 開頭的條文），避免「Enhanced Customer Due Diligence」這類章名污染判斷。
    """
    by_id = {c.clause_id: c for c in clauses}
    contexts: Dict[str, str] = {}
    for clause in clauses:
        parts: List[str] = []
        parent_id = clause.parent_clause_id
        while parent_id and parent_id in by_id:
            parent = by_id[parent_id]
            if not re.match(r"^#{1,2}\s", parent.raw_text):
                parts.append(parent.normalized_text)
            parent_id = parent.parent_clause_id
        contexts[clause.clause_id] = " ".join(reversed(parts))
    return contexts


def extract_obligations(
    clauses: List[Clause],
    extractor: Optional[RuleBasedObligationExtractor] = None,
) -> Tuple[List[Obligation], List[Dict[str, Any]]]:
    """
    依文件順序逐條比對，合併同一規則與管轄區的命中。
    回傳 (義務列表, 未命中而送入低信心審查佇列的條文)。
    """
    extractor = extractor or RuleBasedObligationExtractor()
    contexts = build_contexts(clauses)

    grouped: Dict[Tuple[str, str], List[ClauseMatch]] = {}
    review_queue: List[Dict[str, Any]] = []
    for clause in clauses:
        match, reason = extractor.match_clause(clause, contexts.get(clause.clause_id, ""))
        if match:
            grouped.setdefault((match.rule, match.jurisdiction), []).append(match)
        else:
            review_queue.append({
                "clause_id": clause.clause_id,
                "section_ref": clause.section_ref,
                "raw_text": clause.raw_text,
                "failure_reason": reason,
            })

    obligations = [extractor.build_obligation(matches) for matches in grouped.values()]
    return obligations, review_queue


def load_jurisdictions(source_documents_path: Optional[str]) -> Dict[str, str]:
    if not source_documents_path or not os.path.exists(source_documents_path):
        return {}
    with open(source_documents_path, "r", encoding="utf-8") as f:
        docs = [SourceDocument.model_validate(d) for d in (yaml.safe_load(f) or [])]
    return {d.source_document_id: d.jurisdiction for d in docs}


class ObligationExtractionPipeline:
    """
    合規義務抽取與黃金數據集比對管線。
    """
    def __init__(self, confidence_threshold: float = 0.75, jurisdictions: Optional[Dict[str, str]] = None):
        self.extractor = RuleBasedObligationExtractor(confidence_threshold, jurisdictions)

    def run(self, clauses_path: str, gold_path: str, out_dir: str) -> List[Obligation]:
        """
        執行抽取、分類與金標比對，輸出 obligations.yaml、low_confidence_review_queue.yaml 與 evaluation_report.txt。
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        with open(clauses_path, "r", encoding="utf-8") as f:
            clauses = [Clause.model_validate(c) for c in (yaml.safe_load(f) or [])]
        print(f"[Extraction] Loaded {len(clauses)} clauses from {clauses_path}.")

        extracted_obligations, review_queue = extract_obligations(clauses, self.extractor)

        with open(out_path / "obligations.yaml", "w", encoding="utf-8") as f:
            yaml.dump([o.model_dump() for o in extracted_obligations], f, allow_unicode=True, sort_keys=False)
        with open(out_path / "low_confidence_review_queue.yaml", "w", encoding="utf-8") as f:
            yaml.dump(review_queue, f, allow_unicode=True, sort_keys=False)

        print(f"[Extraction] Extracted {len(extracted_obligations)} distinct obligations.")
        print(f"[Extraction] Sent {len(review_queue)} clauses to low-confidence review queue.")

        if os.path.exists(gold_path):
            self.evaluate_against_gold(extracted_obligations, gold_path, out_path / "evaluation_report.txt")
        else:
            print(f"[Evaluation] Gold dataset not found at {gold_path}. Skipping evaluation.")
        return extracted_obligations

    def evaluate_against_gold(self, extracted: List[Obligation], gold_path: str, report_path: Path) -> Dict[str, Any]:
        """
        將抽取的義務與金標比對：
        - 義務層級的 Precision / Recall / F1（依 obligation_id）
        - 欄位層級對齊（actor、action、object）
        - 出處對齊：金標的錨點條文（source_clause_ids 第一條）出現在抽取結果中，且管轄區相同；
          另外統計出處條文集合完全相同的數量。
        """
        with open(gold_path, "r", encoding="utf-8") as f:
            gold_obs = [Obligation.model_validate(g) for g in (yaml.safe_load(f) or [])]
        gold_dict = {g.obligation_id: g for g in gold_obs}
        extracted_dict = {e.obligation_id: e for e in extracted}

        matched_count = 0
        field_match_score = 0.0
        provenance_matches = 0
        exact_source_matches = 0

        print("\n================== CDD-GraphWiki Evaluation ==================")
        details = [
            "CDD-GraphWiki Obligation Extraction Evaluation Report",
            "==================================================",
        ]

        for ob_id, gold_ob in gold_dict.items():
            if ob_id not in extracted_dict:
                line = f"Obligation ID: {ob_id} -> [MISSING] in extracted data."
                print(line)
                details.append(line)
                continue

            ext_ob = extracted_dict[ob_id]
            matched_count += 1
            field_match_ratio = sum([
                ext_ob.actor == gold_ob.actor,
                ext_ob.action == gold_ob.action,
                ext_ob.object == gold_ob.object,
            ]) / 3.0
            field_match_score += field_match_ratio

            anchor_ok = bool(gold_ob.source_clause_ids) and gold_ob.source_clause_ids[0] in ext_ob.source_clause_ids
            provenance_ok = anchor_ok and ext_ob.jurisdiction == gold_ob.jurisdiction
            provenance_matches += int(provenance_ok)
            exact_source_matches += int(set(ext_ob.source_clause_ids) == set(gold_ob.source_clause_ids))

            line = (f"Obligation ID: {ob_id} -> Match: [OK] Fields match ratio: {field_match_ratio:.2f} | "
                    f"Provenance: {'[OK]' if provenance_ok else '[MISMATCH]'} "
                    f"(anchor clause {gold_ob.source_clause_ids[0] if gold_ob.source_clause_ids else '-'})")
            print(line)
            details.append(line)

        for ob_id in extracted_dict:
            if ob_id not in gold_dict:
                line = f"Obligation ID: {ob_id} -> [EXTRA] not in gold set."
                print(line)
                details.append(line)

        precision = matched_count / len(extracted) if extracted else 0.0
        recall = matched_count / len(gold_obs) if gold_obs else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        field_accuracy = field_match_score / matched_count if matched_count > 0 else 0.0

        summary = [
            "\nEvaluation Metrics Summary:",
            f"- Extracted Obligations Count: {len(extracted)}",
            f"- Gold Obligations Count: {len(gold_obs)}",
            f"- Match Count: {matched_count}",
            f"- Precision (精準率): {precision:.2f}",
            f"- Recall (召回率): {recall:.2f}",
            f"- F1-Score: {f1_score:.2f}",
            f"- Field-level Alignment Accuracy: {field_accuracy:.2f}",
            f"- Provenance Match (anchor clause + jurisdiction): {provenance_matches}/{len(gold_obs)}",
            f"- Source Clause Set Exact Match: {exact_source_matches}/{len(gold_obs)}",
        ]
        for line in summary:
            print(line)
            details.append(line)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(details) + "\n")
        print(f"\n[Evaluation] Report saved to {report_path}")

        return {
            "extracted": len(extracted),
            "gold": len(gold_obs),
            "matched": matched_count,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "field_accuracy": round(field_accuracy, 4),
            "provenance_matches": provenance_matches,
            "exact_source_matches": exact_source_matches,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CDD-GraphWiki Obligation Extraction and Evaluation Prototype")
    parser.add_argument("--clauses", type=str, default="data/processed/clauses.yaml", help="Path to processed clauses yaml")
    parser.add_argument("--gold", type=str, default="data/gold/obligations.yaml", help="Path to gold obligations yaml")
    parser.add_argument("--sources", type=str, default="data/processed/source_documents.yaml", help="Path to source documents yaml")
    parser.add_argument("--out", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()

    pipeline = ObligationExtractionPipeline(jurisdictions=load_jurisdictions(args.sources))
    pipeline.run(args.clauses, args.gold, args.out)
