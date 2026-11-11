// GET /api/v1/customers/{id}/explanation 的回應型別，對應 backend/src/decision/explain.py 的 ChecklistExplanation

export interface ConditionResult {
  attribute: string;
  condition: string;
  observed: unknown;
  holds: boolean;
}

export interface DecisionStep {
  test_id: string;
  question: string;
  attributes: string[];
  observed: Record<string, unknown>;
  outcome: boolean;
  parts: ConditionResult[]; // 只有 OR 測試才有
}

export interface EvidenceSpan {
  clause_id: string;
  start: number;
  end: number;
  text: string;
}

export interface RuleReason {
  rule: string;
  obligation_type: string;
  message: string;
  spans?: EvidenceSpan[];
  depends_on?: string[];
}

// start / end 是後端（Python）的字元位移，以 Unicode code point 計，不是 JavaScript 的 UTF-16 索引
export interface Highlight {
  start: number;
  end: number;
  text: string;
  rules: string[];
}

export type ClauseRelation = 'ancestor' | 'descendant' | 'referenced';

// 理由用到這個片段的條文；relation 是它和本條文的關係，self 代表本條文自己
export interface CitedBy {
  clause_id: string;
  section_ref: string | null;
  relation: ClauseRelation | 'self';
}

// 理由片段中落在其他條文（例如條列項目繼承的上層引言）的部分
export interface ContextEvidence extends Highlight {
  clause_id: string;
  section_ref: string | null;
  // 片段所在條文和本條文的關係：上層條文、下層項目，或經引用而來的其他條文
  relation: ClauseRelation;
  cited_by: CitedBy;
}

export interface SourceClauseEvidence {
  clause_id: string;
  section_ref: string | null;
  document_title: string | null;
  raw_text: string | null;
  reasons: RuleReason[];
  highlights: Highlight[];
  context_evidence: ContextEvidence[];
}

export interface ConflictRef {
  conflict_id: string;
  conflict_type: string;
  description: string;
  adjudication_status: string;
  reconciliation_rule: string | null;
  resolved_by: string | null;
}

export type ConfidenceKind = 'measured_on_heldout' | 'self_reported';

export interface DocumentItemExplanation {
  document: string;
  obligation_id: string;
  obligation_found: boolean;
  obligation_confidence: number | null;
  obligation_confidence_basis: string | null;
  // measured_on_heldout：保留文本實測精確率；self_reported：模型自評、未校準；null：未量測
  obligation_confidence_kind: ConfidenceKind | null;
  source_clauses: SourceClauseEvidence[];
  conflicts: ConflictRef[];
}

export interface RiskTriggerExplanation {
  trigger: string;
  // 葉節點宣告的義務；知識庫沒有任何義務對這位客戶要求這個條件時為 null，此時 note 說明原因
  obligation_id: string | null;
  // 該義務出處條文中寫出這個條件的那一條
  clause_id: string | null;
  note: string | null;
  attributes: string[];
  tested_by_decision: boolean;
  holds: boolean | null;
}

export interface BranchRef {
  id: string;
  label: string;
}

export interface Counterfactual {
  attribute: string;
  current_value: unknown;
  counterfactual_value: unknown;
  value_note: string | null;
  branch: [BranchRef, BranchRef] | null; // [原分支, 新分支]
  decision: [string, string] | null;
  documents_added: string[];
  documents_removed: string[];
  obligations_added: string[];
  obligations_removed: string[];
  triggers_added: string[];
  triggers_removed: string[];
  conflicts_added: string[]; // 改值後新出現的未裁決衝突
  conflicts_removed: string[];
  citations_added: string[];
  citations_removed: string[];
  human_review: [boolean, boolean] | null;
  computed: boolean; // false：引擎無法用改值後的資料重算，value_note 說明原因
}

// 路徑上讀到、但單獨改成任何候選值都不會改變輸出的屬性
export interface NonDecisiveAttribute {
  attribute: string;
  observed: unknown;
  reason: string;
}

export interface ChecklistExplanation {
  customer_id: string;
  checklist_id: string;
  decision: string;
  human_review_required: boolean;
  // 葉節點本身是否要求人工審查；false 而 human_review_required 為 true 時，審查來自未裁決衝突
  branch_human_review_required: boolean;
  unresolved_conflicts: string[];
  branch: BranchRef;
  path: DecisionStep[];
  items: DocumentItemExplanation[];
  obligations_without_documents: string[];
  // 每個適用義務（含不需另收文件的義務）的相關衝突
  obligation_conflicts: Record<string, ConflictRef[]>;
  risk_triggers: RiskTriggerExplanation[];
  counterfactuals: Counterfactual[];
  attributes_read_but_not_decisive: NonDecisiveAttribute[];
  attributes_not_read: string[];
}

const ATTRIBUTE_LABELS: Record<string, string> = {
  customer_type: '客戶類型',
  pep_exposure: 'PEP 身分',
  ubo_country_risk: '實質受益人國家風險',
  ubo_status: '實質受益人狀態',
  registration_jurisdiction: '註冊地',
  'custom_attributes.major_shareholder_pct': '大股東持股比例',
};

export const attributeLabel = (attribute: string) => ATTRIBUTE_LABELS[attribute] ?? attribute;

const DECISION_LABELS: Record<string, string> = {
  simplified_cdd: '簡化 CDD',
  standard_cdd: '標準 CDD',
  enhanced_due_diligence: '加強盡職調查（EDD）',
};

export const decisionLabel = (decision: string) => DECISION_LABELS[decision] ?? decision;

export const yesNo = (value: boolean) => (value ? '是' : '否');

// 屬性值的顯示：布林轉是/否、缺值顯示「未提供」、持股比例加 %
export const formatValue = (value: unknown, attribute?: string): string => {
  if (value === null || value === undefined) return '未提供';
  if (typeof value === 'boolean') return yesNo(value);
  if (typeof value === 'number' && attribute === 'custom_attributes.major_shareholder_pct') return `${value}%`;
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

const formatObserved = (step: DecisionStep) =>
  step.attributes.map((a) => `${attributeLabel(a)} = ${formatValue(step.observed[a], a)}`).join('、');

// 人工審查的來源：分支本身、未裁決衝突，或兩者
const reviewSentence = (exp: ChecklistExplanation) => {
  const conflicts = exp.unresolved_conflicts.length > 0
    ? `有未裁決衝突（${exp.unresolved_conflicts.join('、')}）`
    : '';
  if (exp.branch_human_review_required) {
    return conflicts ? `這個分支需要人工審查，另外${conflicts}。` : '這個分支需要人工審查。';
  }
  return conflicts ? `分支本身不需要人工審查，但${conflicts}，所以需要人工審查。` : '這個分支不需要人工審查。';
};

// 摘要：引擎初審的決策、分支，以及把路徑寫成「問題 是/否（讀到的值）→ …」的一條鏈。
// 解釋由引擎重新推理，不含人工審查後的更新，所以一律稱為「引擎初審」
export const buildSummary = (exp: ChecklistExplanation) => {
  const chain = exp.path
    .map((step) => `${step.question} ${yesNo(step.outcome)}（${formatObserved(step)}）`)
    .join(' → ');
  return {
    headline: `引擎初審：決策為${decisionLabel(exp.decision)}，落在分支「${exp.branch.label}」。${reviewSentence(exp)}`,
    chain: `${chain} → ${exp.branch.label}`,
  };
};
