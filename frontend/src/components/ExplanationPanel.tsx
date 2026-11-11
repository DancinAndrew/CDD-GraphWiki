import React from 'react';
import {
  ChecklistExplanation,
  Counterfactual,
  DecisionStep,
  NonDecisiveAttribute,
  RiskTriggerExplanation,
  attributeLabel,
  decisionLabel,
  formatValue,
  yesNo,
} from './explanationTypes';

// 決策路徑、反事實、風險標記與未讀屬性；資料全部來自 explanation API，不在前端另做推理

const Outcome: React.FC<{ ok: boolean }> = ({ ok }) => (
  <span style={{ ...styles.outcome, color: ok ? 'var(--success)' : 'var(--danger)' }}>{ok ? '✓' : '✗'}</span>
);

const PathStepRow: React.FC<{ step: DecisionStep; index: number }> = ({ step, index }) => (
  <li style={styles.row}>
    <div style={styles.stepHeader}>
      <span style={styles.stepIndex}>{index + 1}</span>
      <span style={styles.stepQuestion}>{step.question}</span>
      <Outcome ok={step.outcome} />
      <span style={styles.muted}>{yesNo(step.outcome)}</span>
    </div>
    <div style={styles.stepValues}>
      讀到：
      {step.attributes.map((a) => `${attributeLabel(a)} = ${formatValue(step.observed[a], a)}`).join('、')}
    </div>
    {step.parts.length > 0 && (
      <ul style={styles.parts}>
        <li style={styles.muted}>任一條件成立即為「是」：</li>
        {step.parts.map((part) => (
          <li key={`${part.attribute}:${part.condition}`} style={styles.part}>
            <Outcome ok={part.holds} />
            <span>{attributeLabel(part.attribute)} = {formatValue(part.observed, part.attribute)}</span>
            <code style={styles.code}>{part.condition}</code>
          </li>
        ))}
      </ul>
    )}
  </li>
);

const ChangeList: React.FC<{ label: string; added: string[]; removed: string[] }> = ({ label, added, removed }) => {
  if (added.length === 0 && removed.length === 0) return null;
  return (
    <div style={styles.change}>
      <span style={styles.changeLabel}>{label}</span>
      {added.map((x) => <span key={`+${x}`} style={{ ...styles.chip, ...styles.chipAdded }}>＋ {x}</span>)}
      {removed.map((x) => <span key={`-${x}`} style={{ ...styles.chip, ...styles.chipRemoved }}>－ {x}</span>)}
    </div>
  );
};

const CounterfactualRow: React.FC<{ cf: Counterfactual }> = ({ cf }) => (
  <li style={styles.row}>
    <div style={styles.cfHeader}>
      若 {attributeLabel(cf.attribute)} 由 <strong>{formatValue(cf.current_value, cf.attribute)}</strong> 改為{' '}
      <strong>{formatValue(cf.counterfactual_value, cf.attribute)}</strong>：
    </div>
    {cf.value_note && <div style={styles.muted}>{formatValue(cf.counterfactual_value, cf.attribute)}：{cf.value_note}</div>}
    {!cf.computed && (
      <div style={styles.change}>
        <span style={styles.changeLabel}>結果</span>
        <span style={{ color: 'var(--warning)' }}>引擎無法重算，不知道輸出會不會改變</span>
      </div>
    )}
    {cf.decision && (
      <div style={styles.change}>
        <span style={styles.changeLabel}>決策</span>
        {decisionLabel(cf.decision[0])} → {decisionLabel(cf.decision[1])}
      </div>
    )}
    {cf.branch && (
      <div style={styles.change}>
        <span style={styles.changeLabel}>分支</span>
        <span title={cf.branch[0].id}>{cf.branch[0].label}</span> → <span title={cf.branch[1].id}>{cf.branch[1].label}</span>
        <code style={styles.code}>{cf.branch[0].id} → {cf.branch[1].id}</code>
      </div>
    )}
    <ChangeList label="文件" added={cf.documents_added} removed={cf.documents_removed} />
    <ChangeList label="義務" added={cf.obligations_added} removed={cf.obligations_removed} />
    <ChangeList label="風險標記" added={cf.triggers_added} removed={cf.triggers_removed} />
    <ChangeList label="未裁決衝突" added={cf.conflicts_added} removed={cf.conflicts_removed} />
    <ChangeList label="引用條文" added={cf.citations_added} removed={cf.citations_removed} />
    {cf.human_review && (
      <div style={styles.change}>
        <span style={styles.changeLabel}>人工審查</span>
        {cf.human_review[0] ? '需要' : '不需要'} → {cf.human_review[1] ? '需要' : '不需要'}
      </div>
    )}
  </li>
);

const NonDecisiveRow: React.FC<{ item: NonDecisiveAttribute }> = ({ item }) => (
  <li style={styles.row}>
    <div style={styles.cfHeader}>
      {attributeLabel(item.attribute)} = <strong>{formatValue(item.observed, item.attribute)}</strong>
    </div>
    <div style={styles.muted}>{item.reason}</div>
  </li>
);

const Badge: React.FC<{ tone: 'ok' | 'warn' | 'bad' | 'neutral'; children: React.ReactNode }> = ({ tone, children }) => (
  <span style={{ ...styles.badge, ...badgeTones[tone] }}>{children}</span>
);

const CHECKED_BY: Record<RiskTriggerExplanation['checked_by'], string> = {
  decision_path: '由決策路徑檢查',
  own_condition: '由標記自己的條件檢查',
  branch_outcome: '描述分支結果',
};

const observedText = (trigger: RiskTriggerExplanation) =>
  trigger.attributes.map((a) => `${attributeLabel(a)} = ${formatValue(trigger.observed[a], a)}`).join('、');

const TriggerRow: React.FC<{ trigger: RiskTriggerExplanation }> = ({ trigger }) => (
  <li style={styles.row}>
    <div style={styles.triggerHeader}>
      <code style={styles.triggerName}>{trigger.trigger}</code>
      <Badge tone={trigger.checked_by === 'branch_outcome' ? 'neutral' : 'ok'}>{CHECKED_BY[trigger.checked_by]}</Badge>
      {trigger.holds === false && <Badge tone="neutral">條件不成立，未列出</Badge>}
      <Badge tone="neutral">{trigger.obligation_id}</Badge>
    </div>
    <div style={styles.muted}>寫出這個條件的條文：<code style={styles.code}>{trigger.clause_id}</code></div>
    <div style={styles.muted}>
      {trigger.condition
        ? <>條件 <code style={styles.code}>{trigger.condition}</code>；客戶資料：{observedText(trigger)}</>
        : '這個標記只陳述分支的結果，不對客戶資料下斷言'}
    </div>
  </li>
);

interface ExplanationPanelProps {
  explanation: ChecklistExplanation;
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => (
  <>
    <section style={styles.section}>
      <h4 style={styles.title}>決策路徑</h4>
      <ol style={styles.list}>
        {explanation.path.map((step, i) => <PathStepRow key={step.test_id} step={step} index={i} />)}
        <li style={{ ...styles.row, ...styles.leaf }}>結果：{explanation.branch.label}</li>
      </ol>
    </section>

    <section style={styles.section}>
      <h4 style={styles.title}>如果…會怎樣</h4>
      <p style={styles.muted}>只改一個客戶屬性、重跑引擎後輸出確實改變的情況；引擎無法重算的改值也會列出並說明原因。</p>
      {explanation.counterfactuals.length > 0 ? (
        <ul style={styles.list}>
          {explanation.counterfactuals.map((cf) => (
            <CounterfactualRow key={`${cf.attribute}:${JSON.stringify(cf.counterfactual_value)}`} cf={cf} />
          ))}
        </ul>
      ) : (
        <p style={styles.muted}>沒有任何單一屬性的改變會影響這份檢核表。</p>
      )}
      {explanation.attributes_read_but_not_decisive.length > 0 && (
        <>
          <h5 style={styles.subtitle}>單獨改變也不會改變結果</h5>
          <p style={styles.muted}>決策路徑讀到這些資料，但只改其中一項、重跑引擎後檢核表完全相同。</p>
          <ul style={styles.list}>
            {explanation.attributes_read_but_not_decisive.map((item) => (
              <NonDecisiveRow key={item.attribute} item={item} />
            ))}
          </ul>
        </>
      )}
    </section>

    <section style={styles.section}>
      <h4 style={styles.title}>風險標記</h4>
      {explanation.risk_triggers.length > 0 ? (
        <ul style={styles.list}>
          {explanation.risk_triggers.map((t) => <TriggerRow key={t.trigger} trigger={t} />)}
        </ul>
      ) : (
        <p style={styles.muted}>這位客戶沒有成立的風險標記。</p>
      )}
      {explanation.triggers_not_raised.length > 0 && (
        <>
          <h5 style={styles.subtitle}>檢查過但不成立</h5>
          <p style={styles.muted}>這個分支會檢查這些標記的條件，但對這位客戶不成立，所以沒有列在檢核表上。</p>
          <ul style={styles.list}>
            {explanation.triggers_not_raised.map((t) => <TriggerRow key={t.trigger} trigger={t} />)}
          </ul>
        </>
      )}
    </section>

    <section style={styles.section}>
      <h4 style={styles.title}>決策樹從不讀取的客戶資料</h4>
      {explanation.attributes_not_read.length > 0 ? (
        <div style={styles.chips}>
          {explanation.attributes_not_read.map((a) => <code key={a} style={styles.chip}>{a}</code>)}
        </div>
      ) : (
        <p style={styles.muted}>這位客戶的每一項資料都會被決策樹的某個測試讀取。</p>
      )}
    </section>
  </>
);

const badgeTones: Record<'ok' | 'warn' | 'bad' | 'neutral', React.CSSProperties> = {
  ok: { background: 'rgba(0, 230, 118, 0.1)', color: 'var(--success)', borderColor: 'rgba(0, 230, 118, 0.3)' },
  warn: { background: 'rgba(255, 179, 0, 0.1)', color: 'var(--warning)', borderColor: 'rgba(255, 179, 0, 0.3)' },
  bad: { background: 'rgba(255, 23, 68, 0.1)', color: 'var(--danger)', borderColor: 'rgba(255, 23, 68, 0.3)' },
  neutral: { background: 'rgba(79, 172, 254, 0.1)', color: 'var(--secondary)', borderColor: 'rgba(79, 172, 254, 0.3)' },
};

const styles: Record<string, React.CSSProperties> = {
  section: { display: 'flex', flexDirection: 'column', gap: '10px' },
  title: { fontFamily: 'var(--font-display)', fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc' },
  subtitle: { fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', marginTop: '4px' },
  list: { listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px' },
  row: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    padding: '10px 14px',
    fontSize: '0.85rem',
    color: '#e2e8f0',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  leaf: { borderColor: 'rgba(0, 242, 254, 0.3)', color: 'var(--primary)', fontWeight: 600 },
  stepHeader: { display: 'flex', alignItems: 'center', gap: '8px' },
  stepIndex: {
    width: '20px', height: '20px', borderRadius: '50%', background: 'rgba(0, 242, 254, 0.1)',
    color: 'var(--primary)', fontSize: '0.7rem', fontWeight: 700,
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  stepQuestion: { flex: 1, fontWeight: 500 },
  stepValues: { fontSize: '0.8rem', color: 'var(--text-muted)', paddingLeft: '28px' },
  parts: { listStyle: 'none', paddingLeft: '28px', display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem' },
  part: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  outcome: { fontWeight: 700, fontSize: '0.9rem' },
  code: {
    fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.72rem',
    color: 'var(--text-muted)', background: 'rgba(255, 255, 255, 0.04)', padding: '1px 6px', borderRadius: '4px',
  },
  cfHeader: { fontWeight: 500 },
  change: { display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', fontSize: '0.8rem' },
  changeLabel: { color: 'var(--text-muted)', minWidth: '64px' },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
  chip: {
    fontSize: '0.75rem', padding: '2px 8px', borderRadius: '6px',
    background: 'rgba(255, 255, 255, 0.04)', border: '1px solid rgba(255, 255, 255, 0.08)', color: '#cbd5e1',
  },
  chipAdded: { color: 'var(--success)', borderColor: 'rgba(0, 230, 118, 0.3)' },
  chipRemoved: { color: 'var(--danger)', borderColor: 'rgba(255, 23, 68, 0.3)' },
  triggerHeader: { display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' },
  triggerName: { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: '0.8rem', color: '#f8fafc' },
  badge: { fontSize: '0.7rem', fontWeight: 600, padding: '2px 8px', borderRadius: '10px', border: '1px solid' },
  muted: { fontSize: '0.78rem', color: 'var(--text-muted)' },
};
