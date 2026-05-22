import yaml
from typing import List, Dict, Any, Optional, Set, Literal
from src.contracts.models import (
    CustomerContext,
    CDDChecklist,
    Obligation,
    Conflict,
    EvaluationMetrics,
    DiagnosticReport,
    ComparisonReport,
    RegulatoryGraph,
    Clause
)


class EvaluationHarness:
    """
    評估框架核心引擎 (EvaluationHarness)。
    負責載入金標黃金標準數據並針對檢索、義務提取、衝突檢測、檢核表正確性及引用忠實度（防止幻覺）進行全自動量化評估，
    支持解耦式錯誤歸因診斷與基準對比分析。
    """

    def evaluate_retrieval(
        self,
        predicted_citations: List[str],
        gold_citations: List[str]
    ) -> EvaluationMetrics:
        """
        評估條文檢索的 Precision, Recall, F1 與 Accuracy。
        """
        pred_set = set(predicted_citations)
        gold_set = set(gold_citations)

        if not gold_set:
            # 如果金標沒有任何引用，而預測也沒有，則是完美的 precision/recall
            p = 1.0 if not pred_set else 0.0
            r = 1.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            return EvaluationMetrics(precision=p, recall=r, f1_score=f1, accuracy=p)

        true_positives = pred_set.intersection(gold_set)
        
        precision = len(true_positives) / len(pred_set) if pred_set else 0.0
        recall = len(true_positives) / len(gold_set)
        
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
            
        # 簡單將 accuracy 定義為 Jaccard 相似度或精確匹配比率
        union_size = len(pred_set.union(gold_set))
        accuracy = len(true_positives) / union_size if union_size > 0 else 0.0

        return EvaluationMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4)
        )

    def evaluate_extraction(
        self,
        extracted_obligations: List[Obligation],
        gold_obligations: List[Obligation]
    ) -> EvaluationMetrics:
        """
        比對提取出的 obligations 與金標 obligations 在 actor、action、object 與 required_evidence 上的屬性精確度。
        """
        ext_map = {ob.obligation_id: ob for ob in extracted_obligations}
        gold_map = {ob.obligation_id: ob for ob in gold_obligations}

        total_fields = 0
        correct_fields = 0

        fields_to_compare = ["actor", "action", "object", "required_evidence"]

        for ob_id, gold_ob in gold_map.items():
            if ob_id not in ext_map:
                # 缺失預測，全部扣分
                total_fields += len(fields_to_compare)
                continue

            ext_ob = ext_map[ob_id]
            for field in fields_to_compare:
                total_fields += 1
                ext_val = getattr(ext_ob, field)
                gold_val = getattr(gold_ob, field)

                if isinstance(gold_val, list):
                    if sorted(list(ext_val)) == sorted(list(gold_val)):
                        correct_fields += 1
                else:
                    if ext_val == gold_val:
                        correct_fields += 1

        # 也將預測中多餘的 obligations 列入考量 (作為 precision 的分母)
        extra_count = len(set(ext_map.keys()) - set(gold_map.keys()))
        total_fields += extra_count * len(fields_to_compare)

        if total_fields == 0:
            return EvaluationMetrics(precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0)

        precision = correct_fields / total_fields
        # recall 基準分母
        recall_denom = len(gold_map) * len(fields_to_compare)
        recall = correct_fields / recall_denom if recall_denom > 0 else 0.0

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
        
        accuracy = correct_fields / total_fields

        return EvaluationMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4)
        )

    def evaluate_conflict_detection(
        self,
        detected_conflicts: List[Conflict],
        gold_conflicts: List[Conflict]
    ) -> EvaluationMetrics:
        """
        驗證衝突檢測引擎的 Precision 與 Recall。
        """
        det_ids = {c.conflict_id for c in detected_conflicts}
        gold_ids = {c.conflict_id for c in gold_conflicts}

        if not gold_ids:
            p = 1.0 if not det_ids else 0.0
            r = 1.0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
            return EvaluationMetrics(precision=p, recall=r, f1_score=f1, accuracy=p)

        true_positives = det_ids.intersection(gold_ids)
        precision = len(true_positives) / len(det_ids) if det_ids else 0.0
        recall = len(true_positives) / len(gold_ids)

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        union_size = len(det_ids.union(gold_ids))
        accuracy = len(true_positives) / union_size if union_size > 0 else 0.0

        return EvaluationMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4)
        )

    def evaluate_checklist_correctness(
        self,
        predicted_checklists: List[CDDChecklist],
        gold_checklists: List[CDDChecklist]
    ) -> EvaluationMetrics:
        """
        驗證 Checklist 決策等級（decision）、required_documents 與 risk_triggers 是否完全正確。
        """
        pred_map = {item.customer_id: item for item in predicted_checklists}
        gold_map = {item.customer_id: item for item in gold_checklists}

        total_fields = 0
        correct_fields = 0

        fields_to_compare = ["decision", "required_documents", "risk_triggers", "human_review_required"]

        for cust_id, gold_chk in gold_map.items():
            if cust_id not in pred_map:
                total_fields += len(fields_to_compare)
                continue

            pred_chk = pred_map[cust_id]
            for field in fields_to_compare:
                total_fields += 1
                pred_val = getattr(pred_chk, field)
                gold_val = getattr(gold_chk, field)

                if isinstance(gold_val, list):
                    if sorted(list(pred_val)) == sorted(list(gold_val)):
                        correct_fields += 1
                else:
                    if pred_val == gold_val:
                        correct_fields += 1

        if total_fields == 0:
            return EvaluationMetrics(precision=1.0, recall=1.0, f1_score=1.0, accuracy=1.0)

        precision = correct_fields / total_fields
        recall = correct_fields / total_fields  # 因為是一對一匹配
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = correct_fields / total_fields

        return EvaluationMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            accuracy=round(accuracy, 4)
        )

    def check_citation_faithfulness(
        self,
        valid_citations: Set[str],
        checklists: List[CDDChecklist]
    ) -> float:
        """
        引用忠實度與幻覺檢查。
        遍歷檢核表中的 citations，驗證所引用的條款是否在 valid_citations（由圖譜或條款庫定義）中真實存在。
        比對前，將標點符號（如逗號、句點）與多餘空白去除，並轉換成小寫，以避免格式微小差異導致誤判。
        返回比例 (0.0 到 1.0)。若有任何 citation 不存在，將觸發幻覺警告。
        """
        def _normalize(s: str) -> str:
            import re
            return re.sub(r'\s+', ' ', s.replace(",", "").replace(".", "").strip()).lower()

        normalized_valid = {_normalize(vc) for vc in valid_citations}
        total_citations = 0
        faithful_citations = 0

        for chk in checklists:
            for citation in chk.citations:
                total_citations += 1
                if _normalize(citation) in normalized_valid:
                    faithful_citations += 1

        if total_citations == 0:
            return 1.0

        return round(faithful_citations / total_citations, 4)


    def run_diagnostic_tree(
        self,
        predicted: CDDChecklist,
        gold: CDDChecklist,
        valid_citations: Set[str],
        extracted_obligations: List[Obligation],
        detected_conflicts: List[Conflict]
    ) -> DiagnosticReport:
        """
        執行解耦式錯誤歸因診斷樹。當推理結果與金標不一致時，精確指出根源。
        """
        # 1. 檢查是否有錯誤
        has_decision_error = predicted.decision != gold.decision
        has_docs_error = sorted(predicted.required_documents) != sorted(gold.required_documents)
        has_triggers_error = sorted(predicted.risk_triggers) != sorted(gold.risk_triggers)
        
        has_error = has_decision_error or has_docs_error or has_triggers_error

        if not has_error:
            return DiagnosticReport(
                checklist_id=predicted.checklist_id,
                has_error=False,
                error_source=None,
                diagnostic_details="預測檢核表與黃金標準完全一致，無合規錯誤。"
            )

        # 2. 開始診斷樹
        
        # 診斷點 A：檢查是否涉及政策衝突漏判
        # 如果金標中應有特定決策但與衝突有關，或者 predicted.unresolved_conflicts 與金標不符
        if len(predicted.unresolved_conflicts) != len(gold.unresolved_conflicts):
            return DiagnosticReport(
                checklist_id=predicted.checklist_id,
                has_error=True,
                error_source="conflict_handling",
                diagnostic_details=(
                    f"衝突檢測不匹配。系統檢測到的未解決衝突數量為 {len(predicted.unresolved_conflicts)}，"
                    f"而金標預期為 {len(gold.unresolved_conflicts)}。這導致了合規決策錯誤。"
                )
            )

        # 診斷點 B：檢查檢索條款是否缺失（Retrieval 錯誤）
        # 比較預測引用與金標引用的交集。如果預測引用缺失了金標中的關鍵條款
        gold_cits = set(gold.citations)
        pred_cits = set(predicted.citations)
        missing_cits = gold_cits - pred_cits

        if missing_cits:
            return DiagnosticReport(
                checklist_id=predicted.checklist_id,
                has_error=True,
                error_source="retrieval",
                diagnostic_details=(
                    f"檢索條文缺失。預測引用漏掉了金標必備條款：{missing_cits}。在法規 "
                    "Ingestion/Retrieval 階段未能成功檢索並關聯到該客戶情境，是導致決策錯誤的根源。"
                )
            )

        # 診斷點 C：檢查義務屬性提取是否缺失或錯誤（Extraction 錯誤）
        # 檢查對應義務 ID 的屬性是否完整
        # 遍歷金標對應的 applicable_obligations，看看系統是否有提取，且屬性是否齊全
        ext_ids = {ob.obligation_id for ob in extracted_obligations}
        gold_ob_ids = set(gold.applicable_obligations)
        missing_obs = gold_ob_ids - ext_ids

        if missing_obs:
            return DiagnosticReport(
                checklist_id=predicted.checklist_id,
                has_error=True,
                error_source="extraction",
                diagnostic_details=(
                    f"義務提取漏判。Obligation Extractor 未能從條文文本中成功提取出義務：{missing_obs}，"
                    "導致下游推理引擎缺乏必要的合規規則依據。"
                )
            )

        # 檢查已提取義務的 evidence 屬性是否與決策所需文件矛盾
        # 如果 required_documents 有缺漏，很可能是 Extraction 漏提取了 evidence 欄位
        for ob in extracted_obligations:
            if ob.obligation_id in gold_ob_ids:
                # 這裡比對 required_evidence
                # 簡化判斷：如果系統 checklist required_documents 缺漏，且對應的 ob.required_evidence 也缺漏
                if len(predicted.required_documents) < len(gold.required_documents):
                    # 判斷這是不是因為 extraction 漏了 evidence
                    # 比如 ob 提取出的 required_evidence 為空
                    if not ob.required_evidence:
                        return DiagnosticReport(
                            checklist_id=predicted.checklist_id,
                            has_error=True,
                            error_source="extraction",
                            diagnostic_details=(
                                f"義務屬性提取不全。義務 {ob.obligation_id} 的 'required_evidence' 欄位提取為空，"
                                f"導致決策引擎無法產出正確的 required_documents（漏判了文件要求）。"
                            )
                        )

        # 診斷點 D：檢查圖譜建模（Graph Modeling）錯誤
        # 如果條文、義務都存在，但圖譜關聯有問題（比如 edge 斷裂）
        if "internal_ubo_threshold_triggered_10_percent" in gold.risk_triggers and "internal_ubo_threshold_triggered_10_percent" not in predicted.risk_triggers:
            # 這通常是關係網絡沒建立好，或是邊的對應關係（stricter_than 或是 applies_to 邊）遺漏
            return DiagnosticReport(
                checklist_id=predicted.checklist_id,
                has_error=True,
                error_source="graph_modeling",
                diagnostic_details=(
                    "合規圖譜建模錯誤。圖譜中未正確關聯 Corporate 客戶的 custom_attributes 股權層級 "
                    "與 Global Bank 內部 10% 穿透規則邊，導致決策引擎無法透過圖遍歷匹配到該隱式義務。"
                )
            )

        # 診斷點 E：若以上皆非，則歸結為 Reasoning 推理邏輯錯誤
        return DiagnosticReport(
            checklist_id=predicted.checklist_id,
            has_error=True,
            error_source="reasoning",
            diagnostic_details=(
                f"推理決策邏輯錯誤。雖然條文與義務均齊全，但決策引擎推理出的 Decision 為 {predicted.decision}，"
                f"而金標預期為 {gold.decision}。應重新審查決策引擎的 Rule Matching Logic 分支。"
            )
        )

    def generate_comparison_report(
        self,
        cdd_wiki_checklists: List[CDDChecklist],
        baseline_checklists: List[CDDChecklist],
        gold_checklists: List[CDDChecklist],
        valid_citations: Set[str],
        extracted_obligations: List[Obligation],
        detected_conflicts: List[Conflict]
    ) -> ComparisonReport:
        """
        匯總 CDD-GraphWiki 與 Baseline 評估對比結果，並產生診斷報告。
        """
        # 1. 引用忠實性檢測 (Anti-hallucination)
        cdd_faith = self.check_citation_faithfulness(valid_citations, cdd_wiki_checklists)
        base_faith = self.check_citation_faithfulness(valid_citations, baseline_checklists)

        # 2. 計算 Checklist 正確性指標
        cdd_checklist_metrics = self.evaluate_checklist_correctness(cdd_wiki_checklists, gold_checklists)
        base_checklist_metrics = self.evaluate_checklist_correctness(baseline_checklists, gold_checklists)

        # 3. 計算 檢索指標 (以 citations 為目標)
        cdd_all_cits = []
        base_all_cits = []
        gold_all_cits = []
        for c in cdd_wiki_checklists:
            cdd_all_cits.extend(c.citations)
        for c in baseline_checklists:
            base_all_cits.extend(c.citations)
        for c in gold_checklists:
            gold_all_cits.extend(c.citations)

        cdd_retrieval_metrics = self.evaluate_retrieval(cdd_all_cits, gold_all_cits)
        base_retrieval_metrics = self.evaluate_retrieval(base_all_cits, gold_all_cits)

        # 4. 建立兩套系統的 metrics map
        cdd_metrics = {
            "retrieval": cdd_retrieval_metrics,
            "checklist": cdd_checklist_metrics,
            "citation_faithfulness": EvaluationMetrics(
                precision=cdd_faith, recall=1.0, f1_score=2*cdd_faith/(cdd_faith+1) if (cdd_faith+1)>0 else 0.0, accuracy=cdd_faith
            )
        }
        
        base_metrics = {
            "retrieval": base_retrieval_metrics,
            "checklist": base_checklist_metrics,
            "citation_faithfulness": EvaluationMetrics(
                precision=base_faith, recall=1.0, f1_score=2*base_faith/(base_faith+1) if (base_faith+1)>0 else 0.0, accuracy=base_faith
            )
        }

        # 5. 針對 predicted_checklists 的每一項進行診斷
        diagnostics = []
        gold_map = {item.customer_id: item for item in gold_checklists}
        for pred in cdd_wiki_checklists:
            if pred.customer_id in gold_map:
                diag = self.run_diagnostic_tree(
                    pred,
                    gold_map[pred.customer_id],
                    valid_citations,
                    extracted_obligations,
                    detected_conflicts
                )
                diagnostics.append(diag)

        # 也為 baseline 跑診斷
        for pred in baseline_checklists:
            if pred.customer_id in gold_map:
                diag = self.run_diagnostic_tree(
                    pred,
                    gold_map[pred.customer_id],
                    valid_citations,
                    extracted_obligations,
                    detected_conflicts
                )
                # 為了區分，修改一下 ID
                diag.checklist_id = f"baseline_{diag.checklist_id}"
                diagnostics.append(diag)

        return ComparisonReport(
            cdd_wiki_metrics=cdd_metrics,
            baseline_metrics=base_metrics,
            diagnostics=diagnostics
        )
