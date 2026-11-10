import os
import re
import yaml
from typing import List, Dict, Any, Optional, Tuple
from src.contracts.models import Obligation, Conflict, Clause, SourceDocument

OWNERSHIP_CONDITION = re.compile(r"controlling_ownership_interest_above_(\d+)_percent")
OCCASIONAL_CONDITION = re.compile(r"occasional_transaction_above_(\d+)_([a-z_]+)")
CURRENCY_LABELS = {"usd_eur": "USD/EUR ", "sgd": "S$"}


class ConflictDetector:
    """
    合規衝突偵測引擎。

    偵測只看抽取出的義務：同一類義務在不同來源文件的數值或立場不同，就標記衝突，
    並引用實際寫出該數值或立場的解析條文。目前涵蓋三類衝突：
    1. 實質受益人持股門檻不同（conf_ubo_threshold）
    2. 觸發 CDD 的偶發交易金額門檻不同（conf_occasional_threshold）
    3. 一方允許 PEP（加強審查後）、另一方禁止（conf_pep_jurisdiction）

    如何調和衝突是人的決定：裁決紀錄（data/reviews/conflict_adjudications.yaml）記下當時裁決的
    conflict_id 與條文集合，只有重新偵測出的衝突引用完全相同的條文時才套用。沒有裁決紀錄、
    或來源變了（例如新增一份政策）而與裁決時不同的衝突，維持 pending_human_review。
    """

    def __init__(self, adjudications: Optional[List[Dict[str, Any]]] = None):
        self.adjudications = {a["conflict_id"]: a for a in (adjudications or [])}

    @staticmethod
    def load_adjudications(path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []

    # -- 工具 -----------------------------------------------------------------

    def _index(self, clauses: Optional[List[Clause]], documents: Optional[List[SourceDocument]]):
        self._clauses = {c.clause_id: c for c in (clauses or [])}
        self._order = {c.clause_id: i for i, c in enumerate(clauses or [])}
        self._documents = {d.source_document_id: d for d in (documents or [])}

    def _document_id(self, ob: Obligation) -> str:
        for clause_id in ob.source_clause_ids:
            if clause_id in self._clauses:
                return self._clauses[clause_id].source_document_id
        return ob.jurisdiction

    def _document_name(self, ob: Obligation) -> str:
        doc_id = self._document_id(ob)
        doc = self._documents.get(doc_id)
        return doc.title.split(":")[0].strip() if doc else doc_id

    def _source_label(self, ob: Obligation, clause_ids: List[str]) -> str:
        """文件名稱加上實際引用條文的段落路徑，例如「FATF Recommendation 10 (Interpretive Note ..., Footnote 40)」。"""
        refs = [self._clauses[cid].section_ref.replace(" > ", ", ") for cid in clause_ids if cid in self._clauses]
        return f"{self._document_name(ob)} ({'; '.join(refs)})" if refs else self._document_name(ob)

    def _clauses_stating(self, ob: Obligation, needles: List[str]) -> List[str]:
        """回傳義務出處中，文字實際含有 needles 任一字串的條文；都找不到時退回錨點條文。"""
        hits = [cid for cid in ob.source_clause_ids
                if cid in self._clauses and any(n in self._clauses[cid].raw_text for n in needles)]
        return hits or ob.source_clause_ids[:1]

    def _sorted(self, clause_ids: List[str]) -> List[str]:
        unique = list(dict.fromkeys(clause_ids))
        return sorted(unique, key=lambda cid: (self._order.get(cid, len(self._order)), cid))

    def _finalize(self, conflict_id: str, conflict_type: str, clause_ids: List[str], description: str) -> Conflict:
        clause_ids = self._sorted(clause_ids)
        adjudication = self.adjudications.get(conflict_id)
        # 裁決只對它當時看過的那組條文有效；條文集合不同就視為需要重新裁決
        applies = adjudication is not None and set(adjudication.get("source_clause_ids") or []) == set(clause_ids)
        if adjudication is not None and not applies:
            description += (" A recorded adjudication exists for this conflict but covers different clauses, "
                            "so it needs a new human decision.")
        return Conflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            source_clause_ids=clause_ids,
            verifiability="retrieval-verifiable",
            description=description,
            reconciliation_rule=adjudication.get("reconciliation_rule") if applies else None,
            adjudication_status=adjudication.get("adjudication_status", "resolved") if applies else "pending_human_review",
            resolved_by=adjudication.get("resolved_by") if applies else None,
        )

    # -- 三類衝突 -------------------------------------------------------------

    def _ownership_threshold_conflict(self, obligations: List[Obligation]) -> Optional[Conflict]:
        entries: List[Tuple[int, Obligation]] = []
        for ob in obligations:
            if ob.object != "beneficial_owner":
                continue
            for cond in ob.conditions:
                m = OWNERSHIP_CONDITION.fullmatch(cond)
                if m:
                    entries.append((int(m.group(1)), ob))
        if len({pct for pct, _ in entries}) < 2 or len({self._document_id(ob) for _, ob in entries}) < 2:
            return None

        clause_ids: List[str] = []
        parts = []
        for pct, ob in sorted(entries, key=lambda e: -e[0]):
            stating = self._clauses_stating(ob, [f"{pct}%", f"{pct} %"])
            clause_ids += stating
            # FATF 只以「e.g. 25%」舉例，描述時照實寫成範例門檻
            is_example = any("e.g." in self._clauses[cid].raw_text for cid in stating if cid in self._clauses)
            label = self._source_label(ob, stating)
            parts.append(f"{label} gives {pct}% as an example threshold" if is_example else f"{label} uses {pct}%")
        stricter = min(pct for pct, _ in entries)
        description = (f"Ownership thresholds for identifying beneficial owners differ between sources: "
                       f"{'; '.join(parts)}. The {stricter}% threshold is the stricter rule.")
        return self._finalize("conf_ubo_threshold", "Numerical", clause_ids, description)

    def _occasional_threshold_conflict(self, obligations: List[Obligation]) -> Optional[Conflict]:
        entries: List[Tuple[int, str, Obligation]] = []
        for ob in obligations:
            if ob.action != "perform_cdd":
                continue
            for cond in ob.conditions:
                m = OCCASIONAL_CONDITION.fullmatch(cond)
                if m:
                    entries.append((int(m.group(1)), m.group(2), ob))
        if len({(v, c) for v, c, _ in entries}) < 2 or len({self._document_id(ob) for _, _, ob in entries}) < 2:
            return None

        clause_ids: List[str] = []
        parts = []
        for value, currency, ob in entries:
            stating = self._clauses_stating(ob, [f"{value:,}"])
            clause_ids += stating
            parts.append(f"{self._source_label(ob, stating)} uses {CURRENCY_LABELS.get(currency, currency + ' ')}{value:,}")
        description = ("Occasional transaction thresholds that trigger CDD differ between sources: "
                       f"{'; '.join(parts)}.")
        return self._finalize("conf_occasional_threshold", "Numerical", clause_ids, description)

    def _pep_policy_conflict(self, obligations: List[Obligation]) -> Optional[Conflict]:
        permits = [ob for ob in obligations if ob.object == "pep" and ob.action == "perform_edd"]
        prohibits = [ob for ob in obligations if ob.object == "pep" and ob.action == "restrict_relationship"]
        if not permits or not prohibits:
            return None
        if {self._document_id(ob) for ob in permits} == {self._document_id(ob) for ob in prohibits}:
            return None

        clause_ids: List[str] = []
        permit_labels, prohibit_labels = [], []
        for ob in permits:
            clause_ids += ob.source_clause_ids[:1]
            permit_labels.append(self._source_label(ob, ob.source_clause_ids[:1]))
        for ob in prohibits:
            stating = self._clauses_stating(ob, ["prohibit"])
            clause_ids += stating
            prohibit_labels.append(self._source_label(ob, stating))
        description = (f"{', '.join(permit_labels)} allows business relations with PEPs subject to enhanced CDD, "
                       f"whereas {', '.join(prohibit_labels)} prohibits PEPs from high-risk jurisdictions.")
        return self._finalize("conf_pep_jurisdiction", "PolicyReversal", clause_ids, description)

    def detect_conflicts(
        self,
        obligations: List[Obligation],
        clauses: Optional[List[Clause]] = None,
        documents: Optional[List[SourceDocument]] = None,
    ) -> List[Conflict]:
        """
        分析 Obligation 列表並回傳偵測到的 Conflict。傳入 clauses 時，衝突會引用實際含有門檻數字或
        禁止字樣的條文；傳入 documents 時，描述會使用文件名稱。
        """
        self._index(clauses, documents)
        detected = [
            self._ownership_threshold_conflict(obligations),
            self._pep_policy_conflict(obligations),
            self._occasional_threshold_conflict(obligations),
        ]
        return [c for c in detected if c is not None]

    @staticmethod
    def save_conflicts_to_yaml(conflicts: List[Conflict], output_path: str):
        """
        將 Conflict 實體列表序列化為 YAML 並保存至檔案。
        """
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump([conf.model_dump() for conf in conflicts], f, allow_unicode=True, sort_keys=False)
