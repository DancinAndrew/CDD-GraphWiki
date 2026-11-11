import React, { useId, useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { ConflictRef, ContextEvidence, DocumentItemExplanation, SourceClauseEvidence } from './explanationTypes';
import { HighlightedText, markStyle } from './HighlightedText';

// 檢核表的文件清單：每列可展開，看依據的義務、可信度、出處條文（含規則理由與高亮片段）與相關衝突

const formatPercent = (value: number) => `${Math.round(value * 1000) / 10}%`;

// 可信度：依後端的 confidence_kind 決定怎麼稱呼這個數字，不解析說明文字；
// 實測精確率（保留文本）與模型自評（未校準）分開標示，其餘一律「未量測」；有說明時一律顯示
const TrustLine: React.FC<{ item: DocumentItemExplanation }> = ({ item }) => {
  const {
    obligation_confidence: confidence,
    obligation_confidence_basis: basis,
    obligation_confidence_kind: kind,
  } = item;
  let label = '未量測';
  if (confidence !== null && confidence !== undefined) {
    if (kind === 'measured_on_heldout') label = `實測精確率 ${formatPercent(confidence)}`;
    else if (kind === 'self_reported') label = `模型自評 ${formatPercent(confidence)}（未校準）`;
  }
  return (
    <div style={styles.trust}>
      <span style={styles.fieldLabel}>可信度</span>
      <span style={styles.trustValue}>{label}</span>
      {basis && <span style={styles.muted}>{basis}</span>}
    </div>
  );
};

const ADJUDICATION_LABELS: Record<string, string> = {
  resolved: '已裁決',
  pending_human_review: '待人工裁決',
};

const ConflictLine: React.FC<{ conflict: ConflictRef }> = ({ conflict }) => {
  const resolved = conflict.adjudication_status === 'resolved';
  return (
    <div style={styles.conflict}>
      <div style={styles.conflictHeader}>
        <code style={styles.code}>{conflict.conflict_id}</code>
        <span style={styles.muted}>{conflict.conflict_type}</span>
        <span style={{ ...styles.status, color: resolved ? 'var(--success)' : 'var(--warning)' }}>
          {ADJUDICATION_LABELS[conflict.adjudication_status] ?? conflict.adjudication_status}
          {resolved && conflict.resolved_by ? `（${conflict.resolved_by}）` : ''}
        </span>
      </div>
      <div style={styles.text}>{conflict.description}</div>
      {conflict.reconciliation_rule && <div style={styles.muted}>調和規則：{conflict.reconciliation_rule}</div>}
    </div>
  );
};

// 片段所在條文的稱呼；經引用而來的條文要講出是誰引用的：本條文，或上層（或其他）條文
const contextLabel = (span: ContextEvidence) => {
  const ref = span.section_ref ?? span.clause_id;
  if (span.relation === 'ancestor') return `依據上層條文 ${ref}`;
  if (span.relation === 'descendant') return `依據下層項目 ${ref}`;
  const citer = span.cited_by;
  if (!citer || citer.relation === 'self') return `依據本條引用的條文 ${ref}`;
  const citerRef = citer.section_ref ?? citer.clause_id;
  const citerKind = citer.relation === 'ancestor' ? '上層條文' : citer.relation === 'descendant' ? '下層項目' : '條文';
  return `依據${citerKind} ${citerRef} 引用的條文 ${ref}`;
};

// 理由片段中落在其他條文的部分，依條文（與引用者）分組：「依據上層條文 1.2(b)：」後列出被引用的字詞
const ContextEvidenceLines: React.FC<{ evidence: ContextEvidence[] }> = ({ evidence }) => {
  const groups: { key: string; label: string; spans: ContextEvidence[] }[] = [];
  for (const span of evidence) {
    const label = contextLabel(span);
    const key = `${span.clause_id}|${label}`;
    let group = groups.find((g) => g.key === key);
    if (!group) {
      group = { key, label, spans: [] };
      groups.push(group);
    }
    group.spans.push(span);
  }
  return (
    <>
      {groups.map((group) => (
        <div key={group.key} style={styles.context}>
          <span style={styles.muted}>{group.label}：</span>
          {group.spans.map((span) => (
            <mark key={`${span.start}:${span.end}`} title={span.rules.join(', ')} style={markStyle}>
              「{span.text}」
            </mark>
          ))}
        </div>
      ))}
    </>
  );
};

const SourceClause: React.FC<{ clause: SourceClauseEvidence }> = ({ clause }) => (
  <div style={styles.clause}>
    <div style={styles.clauseHeader}>
      <span style={styles.clauseRef}>{clause.section_ref ?? clause.clause_id}</span>
      <span style={styles.muted}>{clause.document_title ?? '來源文件不明'}</span>
    </div>
    {clause.raw_text ? (
      <div style={styles.rawText}>
        <HighlightedText text={clause.raw_text} highlights={clause.highlights} />
      </div>
    ) : (
      <div style={styles.muted}>知識庫中找不到這條條文的原文（{clause.clause_id}）</div>
    )}
    {clause.raw_text && clause.highlights.length === 0 && (
      <div style={styles.muted}>本條文內沒有標記片段，判斷依據見下方理由。</div>
    )}
    {clause.context_evidence.length > 0 && <ContextEvidenceLines evidence={clause.context_evidence} />}
    {clause.reasons.length > 0 ? (
      <ul style={styles.reasons}>
        {clause.reasons.map((reason, i) => (
          <li key={`${reason.rule}:${i}`} style={styles.reason}>
            <code style={styles.code}>{reason.rule}</code>
            <span>{reason.message}</span>
            {reason.depends_on && reason.depends_on.length > 0 && (
              <span style={styles.muted}>depends on: {reason.depends_on.join(', ')}</span>
            )}
          </li>
        ))}
      </ul>
    ) : (
      <div style={styles.muted}>這條出處沒有記錄規則理由。</div>
    )}
  </div>
);

const ItemDetails: React.FC<{ item: DocumentItemExplanation }> = ({ item }) => (
  <div style={styles.details}>
    <div style={styles.field}>
      <span style={styles.fieldLabel}>依據義務</span>
      <code style={styles.code}>{item.obligation_id}</code>
      {!item.obligation_found && <span style={{ ...styles.status, color: 'var(--danger)' }}>知識庫中找不到這個義務</span>}
    </div>
    {item.obligation_found && <TrustLine item={item} />}
    {item.source_clauses.length > 0 && (
      <div style={styles.group}>
        <span style={styles.fieldLabel}>出處條文（{item.source_clauses.length}）</span>
        {item.source_clauses.map((clause) => <SourceClause key={clause.clause_id} clause={clause} />)}
      </div>
    )}
    {item.conflicts.length > 0 && (
      <div style={styles.group}>
        <span style={styles.fieldLabel}>相關衝突</span>
        {item.conflicts.map((c) => <ConflictLine key={c.conflict_id} conflict={c} />)}
      </div>
    )}
  </div>
);

// 依文件名稱把檢核表的每一列對上解釋中的項目（同名文件依序配對）
const matchItems = (documents: string[], items: DocumentItemExplanation[]) => {
  const used = new Set<number>();
  return documents.map((doc) => {
    const index = items.findIndex((item, i) => !used.has(i) && item.document === doc);
    if (index < 0) return null;
    used.add(index);
    return items[index];
  });
};

interface ChecklistItemListProps {
  documents: string[];
  items: DocumentItemExplanation[] | null; // null：解釋請求失敗或尚未載入
  obligationsWithoutDocuments: string[];
  obligationConflicts: Record<string, ConflictRef[]>; // 每個適用義務的相關衝突
  checked: boolean;
}

const visuallyHidden: React.CSSProperties = {
  position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px',
  overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', whiteSpace: 'nowrap', border: 0,
};

export const ChecklistItemList: React.FC<ChecklistItemListProps> = ({
  documents,
  items,
  obligationsWithoutDocuments,
  obligationConflicts,
  checked,
}) => {
  const idPrefix = useId();
  const [open, setOpen] = useState<Set<number>>(new Set());
  const matched = items ? matchItems(documents, items) : documents.map(() => null);

  const toggle = (idx: number) => {
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div style={styles.container}>
      {documents.map((doc, idx) => {
        const item = matched[idx];
        const isOpen = open.has(idx);
        const detailsId = `${idPrefix}-details-${idx}`;
        // 勾選框只是狀態的視覺提示（不可操作、不可聚焦），狀態以文字放進列的名稱裡
        const status = checked ? '沒有待處理的人工審查' : '待人工審查';
        const label = (
          <>
            <span style={styles.document}>{doc}</span>
            <span style={visuallyHidden}>（{status}）</span>
            {item && <code style={styles.code}>{item.obligation_id}</code>}
          </>
        );
        return (
          <div key={`${doc}:${idx}`} style={styles.row}>
            <div style={styles.rowHeader}>
              <input
                type="checkbox"
                readOnly
                checked={checked}
                tabIndex={-1}
                aria-hidden="true"
                style={styles.checkbox}
              />
              {item ? (
                <button
                  type="button"
                  style={styles.toggle}
                  aria-expanded={isOpen}
                  aria-controls={detailsId}
                  onClick={() => toggle(idx)}
                >
                  {label}
                  {isOpen
                    ? <ChevronDown size={16} color="var(--text-muted)" aria-hidden="true" />
                    : <ChevronRight size={16} color="var(--text-muted)" aria-hidden="true" />}
                </button>
              ) : (
                <div style={styles.toggleStatic}>
                  {label}
                  {items && <span style={styles.muted}>解釋中沒有這份文件</span>}
                </div>
              )}
            </div>
            {item && isOpen && (
              <div id={detailsId} role="region" aria-label={`${doc} 的依據`}>
                <ItemDetails item={item} />
              </div>
            )}
          </div>
        );
      })}
      {items && obligationsWithoutDocuments.length > 0 && (
        <div style={styles.noDocs}>
          <span style={styles.fieldLabel}>適用但不需另收文件的義務</span>
          <div style={styles.chips}>
            {obligationsWithoutDocuments.map((ob) => <code key={ob} style={styles.code}>{ob}</code>)}
          </div>
          {obligationsWithoutDocuments.map((ob) => {
            const conflicts = obligationConflicts[ob] ?? [];
            if (conflicts.length === 0) return null;
            return (
              <div key={ob} style={styles.group}>
                <span style={styles.fieldLabel}><code style={styles.code}>{ob}</code> 的相關衝突</span>
                {conflicts.map((c) => <ConflictLine key={c.conflict_id} conflict={c} />)}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const mono = 'ui-monospace, SFMono-Regular, Menlo, monospace';

const styles: Record<string, React.CSSProperties> = {
  container: { display: 'flex', flexDirection: 'column', gap: '8px' },
  row: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    borderRadius: '8px',
  },
  rowHeader: { display: 'flex', alignItems: 'center', gap: '10px', padding: '12px' },
  checkbox: { accentColor: 'var(--primary)', cursor: 'default', pointerEvents: 'none' },
  toggle: {
    flex: 1, display: 'flex', alignItems: 'center', gap: '10px', padding: 0, margin: 0,
    background: 'none', border: 'none', color: 'inherit', font: 'inherit', textAlign: 'left', cursor: 'pointer',
  },
  toggleStatic: { flex: 1, display: 'flex', alignItems: 'center', gap: '10px' },
  document: { flex: 1, fontSize: '0.85rem', lineHeight: '1.4', color: '#e2e8f0' },
  details: {
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    padding: '12px 14px 14px 38px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  field: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  fieldLabel: { fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', minWidth: '64px' },
  trust: { display: 'flex', alignItems: 'baseline', gap: '8px', flexWrap: 'wrap' },
  trustValue: { fontSize: '0.82rem', fontWeight: 600, color: 'var(--secondary)' },
  group: { display: 'flex', flexDirection: 'column', gap: '8px' },
  clause: {
    background: 'rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    padding: '10px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  clauseHeader: { display: 'flex', alignItems: 'baseline', gap: '10px', flexWrap: 'wrap' },
  clauseRef: { fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.82rem', color: 'var(--primary)' },
  rawText: {
    fontSize: '0.8rem',
    lineHeight: '1.55',
    color: '#cbd5e1',
    whiteSpace: 'pre-wrap',
    maxHeight: '180px',
    overflowY: 'auto',
  },
  context: { display: 'flex', alignItems: 'baseline', gap: '6px', flexWrap: 'wrap', fontSize: '0.78rem' },
  reasons: { listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '4px' },
  reason: { display: 'flex', gap: '8px', alignItems: 'baseline', flexWrap: 'wrap', fontSize: '0.78rem', color: '#e2e8f0' },
  conflict: {
    border: '1px dashed rgba(255, 179, 0, 0.25)',
    borderRadius: '8px',
    padding: '8px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  conflictHeader: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  status: { fontSize: '0.75rem', fontWeight: 600 },
  text: { fontSize: '0.8rem', color: '#e2e8f0', lineHeight: '1.45' },
  code: {
    fontFamily: mono, fontSize: '0.72rem', color: 'var(--text-muted)',
    background: 'rgba(255, 255, 255, 0.04)', padding: '1px 6px', borderRadius: '4px',
  },
  muted: { fontSize: '0.75rem', color: 'var(--text-muted)' },
  noDocs: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px', padding: '6px 2px' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
};
