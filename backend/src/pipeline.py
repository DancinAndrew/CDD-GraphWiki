"""
CDD-GraphWiki 一鍵重建管線。

    PYTHONPATH=backend python -m src.pipeline

依序執行：解析來源 → 抽取義務並與金標比對 → 偵測衝突並套用人工裁決 → 為合成客戶產生檢查清單，
把結果寫進 data/processed，並印出 README 與 CV 引用的所有數字。輸出是確定性的：
同樣的輸入重跑兩次，檔案內容完全相同。data/processed/audit_log.json 是只能追加的稽核日誌，管線不會動它。
"""
import os
import json
import argparse
from collections import Counter
from typing import Any, Dict, List

import yaml

from src.contracts.models import Clause, SourceDocument, Obligation, Conflict, CustomerContext, CDDChecklist
from src.ingestion.parser import run_pipeline as parse_sources
from src.extraction.extractor import (
    ObligationExtractionPipeline,
    extract_obligations,
)
from src.association.conflict_detector import ConflictDetector
from src.decision.engine import CDDChecklistEngine, ChecklistEvaluator
from src.paths import find_data_dir

DATA_DIR = find_data_dir()


def _read_yaml(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _write_yaml(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)


def evaluate_conflicts(detected: List[Conflict], gold: List[Conflict]) -> Dict[str, Any]:
    """衝突偵測對金標：conflict_id 相同且引用的條文集合完全相同才算命中。"""
    gold_map = {c.conflict_id: set(c.source_clause_ids) for c in gold}
    matched = sum(1 for c in detected if gold_map.get(c.conflict_id) == set(c.source_clause_ids))
    precision = matched / len(detected) if detected else 0.0
    recall = matched / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"detected": len(detected), "gold": len(gold), "matched": matched,
            "precision": round(precision, 4), "recall": round(recall, 4), "f1_score": round(f1, 4)}


def check_provenance(clauses: List[Clause], obligations: List[Obligation],
                     conflicts: List[Conflict], checklists: List[CDDChecklist]) -> Dict[str, Any]:
    """所有出處都必須解析到條文；每組衝突至少引用兩份不同的來源文件。"""
    by_id = {c.clause_id: c for c in clauses}
    refs = ([cid for ob in obligations for cid in ob.source_clause_ids]
            + [cid for cf in conflicts for cid in cf.source_clause_ids]
            + [cid for chk in checklists for cid in chk.citations])
    unresolved = sorted({cid for cid in refs if cid not in by_id})
    single_source = [cf.conflict_id for cf in conflicts
                     if len({by_id[cid].source_document_id for cid in cf.source_clause_ids if cid in by_id}) < 2]
    return {"references_checked": len(refs), "unresolved_references": unresolved,
            "conflicts_citing_one_source": single_source}


def run(sources_dir: str, gold_dir: str, out_dir: str, adjudications_path: str) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)

    # 1. 解析來源文件 → source_documents.yaml、clauses.yaml
    parse_sources(sources_dir, out_dir)
    documents = [SourceDocument.model_validate(d) for d in _read_yaml(os.path.join(out_dir, "source_documents.yaml"))]
    clauses = [Clause.model_validate(c) for c in _read_yaml(os.path.join(out_dir, "clauses.yaml"))]

    # 2. 規則式義務抽取 → obligations.yaml、low_confidence_review_queue.yaml、evaluation_report.txt
    jurisdictions = {d.source_document_id: d.jurisdiction for d in documents}
    extraction = ObligationExtractionPipeline(jurisdictions=jurisdictions)
    obligations, review_queue = extract_obligations(clauses, extraction.extractor)
    _write_yaml(os.path.join(out_dir, "obligations.yaml"), [o.model_dump() for o in obligations])
    _write_yaml(os.path.join(out_dir, "low_confidence_review_queue.yaml"), review_queue)
    extraction_metrics = extraction.evaluate_against_gold(
        obligations, os.path.join(gold_dir, "obligations.yaml"), os.path.join(out_dir, "evaluation_report.txt"))

    # 3. 衝突偵測（套用人工裁決紀錄）→ conflicts.yaml
    detector = ConflictDetector(ConflictDetector.load_adjudications(adjudications_path))
    conflicts = detector.detect_conflicts(obligations, clauses=clauses, documents=documents)
    ConflictDetector.save_conflicts_to_yaml(conflicts, os.path.join(out_dir, "conflicts.yaml"))
    gold_conflicts = [Conflict.model_validate(c) for c in _read_yaml(os.path.join(gold_dir, "conflicts.yaml"))]
    conflict_metrics = evaluate_conflicts(conflicts, gold_conflicts)

    # 4. 為合成客戶產生 CDD 檢查清單 → checklists.yaml
    customers = [CustomerContext.model_validate(c) for c in _read_yaml(os.path.join(gold_dir, "customer_contexts.yaml"))]
    engine = CDDChecklistEngine()
    checklists = [engine.generate_checklist(cust, obligations, conflicts) for cust in customers]
    _write_yaml(os.path.join(out_dir, "checklists.yaml"), [c.model_dump() for c in checklists])
    checklist_metrics = ChecklistEvaluator().evaluate_alignment(
        checklists, _read_yaml(os.path.join(gold_dir, "checklists.yaml")))

    heading_only = [c.clause_id for c in clauses
                    if c.raw_text.lstrip("#").strip() == c.section_ref.split(" > ")[-1].strip()]
    summary = {
        "clauses": len(clauses),
        "clauses_with_text": len(clauses) - len(heading_only),
        "heading_only_clause_records": heading_only,
        "clauses_by_source": dict(sorted(Counter(c.source_document_id for c in clauses).items())),
        "obligations": len(obligations),
        "clauses_sent_to_review_queue": len(review_queue),
        "conflicts": len(conflicts),
        "conflict_ids": [c.conflict_id for c in conflicts],
        "customer_profiles": len(customers),
        "checklists": len(checklists),
        "checklists_routed_to_human_review": sum(1 for c in checklists if c.human_review_required),
        "extraction_vs_gold": extraction_metrics,
        "conflict_detection_vs_gold": conflict_metrics,
        "checklist_alignment_vs_gold": checklist_metrics,
        "provenance_check": check_provenance(clauses, obligations, conflicts, checklists),
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return summary


def print_summary(s: Dict[str, Any]) -> None:
    ex, cf, ck, pv = (s["extraction_vs_gold"], s["conflict_detection_vs_gold"],
                      s["checklist_alignment_vs_gold"], s["provenance_check"])
    by_source = ", ".join(f"{k}: {v}" for k, v in s["clauses_by_source"].items())
    print("\n================== CDD-GraphWiki pipeline summary ==================")
    print(f"Clauses parsed .............. {s['clauses']} records ({by_source}); "
          f"{s['clauses_with_text']} carry text, {len(s['heading_only_clause_records'])} are section headings")
    print(f"Obligations extracted ....... {s['obligations']} "
          f"(gold matched {ex['matched']}/{ex['gold']}, P/R/F1 {ex['precision']:.2f}/{ex['recall']:.2f}/{ex['f1_score']:.2f})")
    print(f"Obligation provenance ....... anchor clause + jurisdiction {ex['provenance_matches']}/{ex['gold']}, "
          f"exact source clause sets {ex['exact_source_matches']}/{ex['gold']}")
    print(f"Conflicts detected .......... {s['conflicts']} ({', '.join(s['conflict_ids'])}); "
          f"matched gold incl. cited clauses {cf['matched']}/{cf['gold']}")
    print(f"Checklists .................. {s['checklists']} for {s['customer_profiles']} synthetic profiles, "
          f"{s['checklists_routed_to_human_review']} routed to human review; "
          f"fields aligned with gold {int(ck['aligned_fields'])}/{int(ck['total_evaluated_fields'])}")
    print(f"Provenance references ....... {pv['references_checked']} checked, "
          f"{len(pv['unresolved_references'])} unresolved, "
          f"{len(pv['conflicts_citing_one_source'])} conflicts citing a single source")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild data/processed and print the project's numbers")
    parser.add_argument("--sources", default=os.path.join(DATA_DIR, "sources"))
    parser.add_argument("--gold", default=os.path.join(DATA_DIR, "gold"))
    parser.add_argument("--adjudications", default=os.path.join(DATA_DIR, "reviews", "conflict_adjudications.yaml"))
    parser.add_argument("--out", default=os.path.join(DATA_DIR, "processed"))
    args = parser.parse_args()
    print_summary(run(args.sources, args.gold, args.out, args.adjudications))


if __name__ == "__main__":
    main()
