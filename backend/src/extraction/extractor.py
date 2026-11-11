import os
import re
import yaml
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Iterable, Set
from src.contracts.models import Clause, Obligation, RuleReason, SourceDocument
from src.extraction import frames, reliability as reliability_data


# ---------------------------------------------------------------------------
# 文字特徵：門檻與觸發條件都從條文本身解析，不寫死在規則裡
# ---------------------------------------------------------------------------

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
    applies_to: Dict[str, Any] = field(default_factory=dict)
    base_conditions: Tuple[str, ...] = ()
    required_evidence: Tuple[str, ...] = ()
    review_flags: Tuple[str, ...] = ()


PROFILES: Dict[Tuple[str, str], ObligationProfile] = {
    ("prohibit_anonymous", "Global"): ObligationProfile(
        "ob_prohibit_anonymous", "financial_institution", "prohibit", "anonymous_accounts",
        review_flags=("anonymous_account_creation_attempt",)),
    ("cdd_triggers", "Global"): ObligationProfile(
        "ob_cdd_on_relationship", "financial_institution", "perform_cdd", "customer",
        required_evidence=("cdd_checklist_completed",)),
    ("cdd_triggers", "Singapore"): ObligationProfile(
        "ob_cdd_on_relationship_mas", "bank", "perform_cdd", "customer",
        required_evidence=("cdd_completed_signoff",)),
    ("verify_customer", "Global"): ObligationProfile(
        "ob_verify_customer_identity", "financial_institution", "identify_and_verify", "customer_identity",
        base_conditions=("cdd_triggered",),
        required_evidence=("reliable_independent_source_documents",),
        review_flags=("unverifiable_identity_documents",)),
    ("verify_customer", "Singapore"): ObligationProfile(
        "ob_verify_customer_mas", "bank", "identify_and_verify", "customer_identity",
        base_conditions=("cdd_triggered",),
        required_evidence=("full_name", "unique_id_number", "residential_address", "date_of_birth",
                           "nationality", "reliable_independent_source_documents"),
        review_flags=("missing_mandatory_identification_fields",)),
    # identify_ubo 的 ID 依解析到的持股門檻決定：{pct} 會變成 "_25"、"_10" 或空字串
    ("verify_customer", "Internal"): ObligationProfile(
        "ob_verify_customer_gb", "bank", "identify_and_verify", "customer_identity",
        base_conditions=("cdd_triggered",),
        required_evidence=("independent_passport_or_identity_card", "official_registry_extract"),
        review_flags=("customer_not_verified_before_onboarding",)),
    ("identify_ubo", "Global"): ObligationProfile(
        "ob_identify_ubo{pct}", "financial_institution", "identify_and_verify", "beneficial_owner",
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ownership_chart", "identity_documents_of_ubo"),
        review_flags=("unclear_ownership_structure", "complex_multi_layer_ownership")),
    ("identify_ubo", "Singapore"): ObligationProfile(
        "ob_identify_ubo{pct}_mas", "bank", "identify_and_verify", "beneficial_owner",
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ubo_declaration", "corporate_profile"),
        review_flags=("ubo_not_identified", "multi_jurisdictional_layers")),
    ("identify_ubo", "Internal"): ObligationProfile(
        "ob_identify_ubo{pct}_gb", "bank", "identify_and_verify", "beneficial_owner",
        applies_to={"customer_type": "legal_person"},
        required_evidence=("ubo_proof_of_identity", "shareholder_registry"),
        review_flags=("ownership_between_10_and_25_percent",)),
    ("pep_edd", "Singapore"): ObligationProfile(
        "ob_pep_edd_mas", "bank", "perform_edd", "pep",
        applies_to={"pep_exposure": True},
        base_conditions=("pep_detected",),
        required_evidence=("senior_management_approval", "source_of_wealth_verification",
                           "source_of_funds_verification"),
        review_flags=("pep_without_senior_mgmt_signoff", "insufficient_source_of_wealth_evidence")),
    ("pep_prohibition", "Internal"): ObligationProfile(
        "ob_pep_prohibitions_gb", "bank", "restrict_relationship", "pep",
        applies_to={"pep_exposure": True},
        base_conditions=("pep_from_high_risk_jurisdiction",),
        required_evidence=("rejected_onboarding_record",),
        review_flags=("pep_from_high_risk_country",)),
    ("pep_approval", "Internal"): ObligationProfile(
        "ob_pep_approval_gb", "bank", "obtain_approval", "pep",
        applies_to={"pep_exposure": True},
        base_conditions=("pep_not_from_high_risk_jurisdiction",),
        required_evidence=("head_of_compliance_approval", "two_levels_senior_mgmt_approval",
                           "source_of_funds_verification", "source_of_wealth_verification"),
        review_flags=("pep_without_head_compliance_signoff",)),
    ("cdd_incomplete", "Singapore"): ObligationProfile(
        "ob_cdd_incomplete_mas", "bank", "refuse_relationship", "customer",
        base_conditions=("cdd_measures_not_completed",),
        required_evidence=("account_opening_rejection_record", "str_consideration_record"),
        review_flags=("cdd_incomplete",)),
}


# 沒有專屬樣板的管轄區（例如測試用的英國法規）用通用樣板：規則照樣能判斷，義務 ID 帶上管轄區
RULE_DEFAULTS: Dict[str, Tuple[str, str, Dict[str, Any]]] = {
    "prohibit_anonymous": ("prohibit", "anonymous_accounts", {}),
    "cdd_triggers": ("perform_cdd", "customer", {}),
    "verify_customer": ("identify_and_verify", "customer_identity", {}),
    "identify_ubo": ("identify_and_verify", "beneficial_owner", {"customer_type": "legal_person"}),
    "pep_edd": ("perform_edd", "pep", {"pep_exposure": True}),
    "pep_prohibition": ("restrict_relationship", "pep", {"pep_exposure": True}),
    "pep_approval": ("obtain_approval", "pep", {"pep_exposure": True}),
    "cdd_incomplete": ("refuse_relationship", "customer", {}),
}
JURISDICTION_SUFFIX = {"Global": "", "Singapore": "mas", "Internal": "gb"}


def profile_for(rule: str, jurisdiction: str) -> ObligationProfile:
    if (rule, jurisdiction) in PROFILES:
        return PROFILES[(rule, jurisdiction)]
    suffix = JURISDICTION_SUFFIX.get(jurisdiction, re.sub(r"[^a-z0-9]+", "_", jurisdiction.lower()).strip("_"))
    action, obj, applies_to = RULE_DEFAULTS[rule]
    pct = "{pct}" if rule == "identify_ubo" else ""
    return ObligationProfile(f"ob_{rule}{pct}{'_' + suffix if suffix else ''}", "regulated_entity", action, obj,
                             applies_to=dict(applies_to))


@dataclass
class ClauseMatch:
    """單一條文命中某條規則的結果；同一規則與管轄區的多筆命中會合併成一個義務。"""
    rule: str
    jurisdiction: str
    clause_id: str
    conditions: List[str]
    reasons: List[RuleReason] = field(default_factory=list)  # 這條條文得到這個類型的規則理由（frames.classify_traced）


def _paragraph_of(clause: Clause) -> str:
    parts = clause.section_ref.split(" > ")
    return parts[1] if len(parts) > 1 else ""


class RuleBasedObligationExtractor:
    """
    規則式合規義務抽取器（第 2 版）。

    - 判斷依據是句子的結構（src/extraction/frames.py）：助動詞或條列開頭的動詞是否真的要求這個動作、
      主詞是客戶還是實質受益人、「may」與「shall not be required to」等放寬句，以及條列與上層段落的關係。
    - 一條條文可以同時屬於多種義務類型。
    - 管轄區只決定義務 ID 與樣板，不決定規則能不能命中；沒有專屬樣板的管轄區用通用樣板。
    - 持股與金額門檻從條文文字解析，不寫死。
    - 信心值不是手寫常數：`reliability` 是各類型在未見過的保留文本上量到的精確率
      （src/extraction/reliability.py）；沒有給就不填信心值，出處說明寫明沒有量測資料。
    """

    def __init__(self, jurisdictions: Optional[Dict[str, str]] = None,
                 reliability: Optional[Dict[str, Dict[str, Any]]] = None):
        self.jurisdictions = jurisdictions or {}
        self.reliability = reliability

    def jurisdiction_for(self, source_document_id: str) -> str:
        return self.jurisdictions.get(source_document_id) or infer_jurisdiction(source_document_id)

    def classify(self, clauses: List[Clause]) -> Dict[str, Set[str]]:
        """每條條文的義務類型。條文依文件分組後逐份判斷，交叉引用只在同一份文件內解析。"""
        by_document: Dict[str, List[Clause]] = {}
        for clause in clauses:
            by_document.setdefault(clause.source_document_id, []).append(clause)
        types: Dict[str, Set[str]] = {}
        for document_clauses in by_document.values():
            types.update(frames.classify(document_clauses, _paragraph_of))
        return types

    def classify_traced(self, clauses: List[Clause]) -> Dict[str, Dict[str, List[RuleReason]]]:
        """同 classify，但每個類型附上規則理由與原文證據位置：clause_id -> 類型 -> 理由。"""
        by_document: Dict[str, List[Clause]] = {}
        for clause in clauses:
            by_document.setdefault(clause.source_document_id, []).append(clause)
        traced: Dict[str, Dict[str, List[RuleReason]]] = {}
        for document_clauses in by_document.values():
            traced.update(frames.classify_traced(document_clauses, _paragraph_of))
        return traced

    def _rule_conditions(self, rule: str, own: str) -> List[str]:
        if rule == "cdd_triggers":
            return trigger_conditions(own)
        if rule == "identify_ubo":
            pct = parse_percent(own)
            return [f"controlling_ownership_interest_above_{pct}_percent"] if pct else []
        return []

    def matches_for(self, clause: Clause, rules: Iterable[str],
                    reasons: Optional[Dict[str, List[RuleReason]]] = None) -> Tuple[List[ClauseMatch], Optional[str]]:
        """把一條條文的義務類型轉成 ClauseMatch；沒有類型時回傳未命中的原因。`reasons` 是這條條文各類型的規則理由。"""
        jurisdiction = self.jurisdiction_for(clause.source_document_id)
        own = clause.normalized_text.lower()
        rules = [r for r in frames.TYPES if r in set(rules)]
        if not rules:
            if any(indicator in own for indicator in OBLIGATION_INDICATORS):
                return [], "MISSING_CORE_ELEMENTS"
            return [], "NON_OBLIGATION_TEXT"
        reasons = reasons or {}
        return [ClauseMatch(r, jurisdiction, clause.clause_id, self._rule_conditions(r, own), list(reasons.get(r, [])))
                for r in rules], None

    def match_clause(self, clause: Clause, context: str = "") -> Tuple[Optional[ClauseMatch], Optional[str]]:
        """
        單一條文的便利介面：`context` 是上層段落的文字（例如 6.3 的導言），當成這條條文的上層條文一起判斷。
        回傳第一個命中的類型。
        """
        matches, reason = self.match_clause_all(clause, context)
        return (matches[0], None) if matches else (None, reason)

    def match_clause_all(self, clause: Clause, context: str = "") -> Tuple[List[ClauseMatch], Optional[str]]:
        document: List[Clause] = []
        if context.strip():
            parent = Clause(clause_id="__context__", source_document_id=clause.source_document_id,
                            section_ref=clause.section_ref, parent_clause_id=None,
                            raw_text=context, normalized_text=context.lower(), citations=["__context__"])
            document.append(parent)
            clause = clause.model_copy(update={"parent_clause_id": "__context__"})
        document.append(clause)
        # 理由的證據若落在 `context`，會引用虛擬條文 "__context__"
        traced = frames.classify_traced(document, _paragraph_of)
        reasons = traced.get(clause.clause_id, {})
        return self.matches_for(clause, set(reasons), reasons)

    def build_obligation(self, matches: List[ClauseMatch]) -> Obligation:
        """把同一規則、同一管轄區的命中合併成一個強型別 Obligation。"""
        first = matches[0]
        profile = profile_for(first.rule, first.jurisdiction)

        source_clause_ids: List[str] = []
        conditions: List[str] = list(profile.base_conditions)
        explanations: Dict[str, List[RuleReason]] = {}
        for m in matches:
            if m.clause_id not in source_clause_ids:
                source_clause_ids.append(m.clause_id)
            explanations.setdefault(m.clause_id, []).extend(m.reasons)
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
            **reliability_data.confidence_for(self.reliability, first.rule),
            review_status="approved",
            explanations=explanations,
        )

    def extract_obligation(self, clause: Clause, context: str = "") -> Tuple[Optional[Obligation], Optional[str]]:
        """單一條文的便利介面：命中時回傳只含這一條出處的 Obligation（第一個類型）。"""
        match, reason = self.match_clause(clause, context)
        if not match:
            return None, reason
        return self.build_obligation([match]), None


def build_contexts(clauses: List[Clause]) -> Dict[str, str]:
    """
    為每條條文組出上層段落的文字：沿 parent_clause_id 往上收集，略過章節標題（'#'、'##' 開頭的條文）。
    給 match_clause 這類單條介面使用；整份文件請用 extract_obligations，它會一起判斷條列與交叉引用。
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
    整份文件一起判斷，依文件順序合併同一規則與管轄區的命中。
    回傳 (義務列表, 未命中而送入低信心審查佇列的條文)。
    """
    extractor = extractor or RuleBasedObligationExtractor()
    traced = extractor.classify_traced(clauses)

    grouped: Dict[Tuple[str, str], List[ClauseMatch]] = {}
    review_queue: List[Dict[str, Any]] = []
    for clause in clauses:
        reasons = traced.get(clause.clause_id, {})
        matches, reason = extractor.matches_for(clause, set(reasons), reasons)
        for match in matches:
            grouped.setdefault((match.rule, match.jurisdiction), []).append(match)
        if not matches:
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
    def __init__(self, jurisdictions: Optional[Dict[str, str]] = None,
                 reliability: Optional[Dict[str, Dict[str, Any]]] = None):
        self.extractor = RuleBasedObligationExtractor(jurisdictions, reliability)

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
    parser.add_argument("--data", type=str, default=None,
                        help="Data directory holding heldout/, used to measure rule reliability "
                             "(default: the parent of the gold file's directory)")
    args = parser.parse_args()

    # 信心值和 src.pipeline 一樣取自保留文本上量到的精確率；少了它，寫進 data/processed 的信心值會全部變成未量測
    data_dir = args.data or os.path.dirname(os.path.dirname(os.path.abspath(args.gold)))
    measured = reliability_data.measured_precision(data_dir)
    print(f"[Extraction] Rule reliability measured on {reliability_data.RELIABILITY_SET} "
          f"({reliability_data.RELIABILITY_LEVEL} level) from {data_dir}.")
    pipeline = ObligationExtractionPipeline(jurisdictions=load_jurisdictions(args.sources), reliability=measured)
    pipeline.run(args.clauses, args.gold, args.out)
