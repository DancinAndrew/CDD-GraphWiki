import React, { useState, useEffect } from 'react';
import { ShieldAlert, CheckCircle2, XCircle, AlertCircle, Send, Check } from 'lucide-react';

interface ReviewCase {
  case_id: string;
  customer_id: string;
  checklist_id: string;
  approval_status: 'pending_review' | 'approved' | 'rejected' | 'needs_evidence';
  reviewer_decision: 'simplified_cdd' | 'standard_cdd' | 'enhanced_due_diligence' | null;
  review_reason: string[];
  reviewed_by: string | null;
  reviewed_at: string | null;
  notes: string | null;
  timestamp: string;
}

interface ReviewQueueProps {
  onReviewSubmitted: () => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ onReviewSubmitted }) => {
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null);
  
  // 表單狀態
  const [approvalStatus, setApprovalStatus] = useState<'approved' | 'rejected' | 'needs_evidence'>('approved');
  const [decision, setDecision] = useState<'simplified_cdd' | 'standard_cdd' | 'enhanced_due_diligence'>('enhanced_due_diligence');
  const [notes, setNotes] = useState('');
  const [officerId, setOfficerId] = useState('Compliance_Officer_Alice');
  
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchCases = () => {
    setLoading(true);
    fetch('http://localhost:8000/api/v1/cases')
      .then(res => res.json())
      .then(data => {
        setCases(data);
        if (data.length > 0) {
          // 預設選擇第一個 pending 的案件，若無，選擇第一個案件
          const pending = data.find((c: ReviewCase) => c.approval_status === 'pending_review');
          setSelectedCase(pending || data[0]);
        } else {
          setSelectedCase(null);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching cases:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchCases();
  }, []);

  useEffect(() => {
    if (selectedCase) {
      setErrorMsg(null);
      setSuccessMsg(null);
      // 自動帶入預設值或已審理的值
      if (selectedCase.approval_status !== 'pending_review') {
        setApprovalStatus(selectedCase.approval_status as any);
        setDecision((selectedCase.reviewer_decision || 'enhanced_due_diligence') as any);
        setNotes(selectedCase.notes || '');
        setOfficerId(selectedCase.reviewed_by || 'Compliance_Officer_Alice');
      } else {
        setApprovalStatus('approved');
        setDecision('enhanced_due_diligence');
        setNotes('');
        setOfficerId('Compliance_Officer_Alice');
      }
    }
  }, [selectedCase]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;

    if (notes.trim().length < 5) {
      setErrorMsg('審批意見筆記字數不可少於 5 個字元！');
      return;
    }
    if (!officerId.trim()) {
      setErrorMsg('合規官 ID 不能為空！');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const payload = {
      approval_status: approvalStatus,
      reviewer_decision: decision,
      notes: notes,
      reviewer_id: officerId
    };

    fetch(`http://localhost:8000/api/v1/cases/${selectedCase.case_id}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || '審核提交失敗');
        }
        return data;
      })
      .then((updatedCase) => {
        setSuccessMsg(`案件 ${selectedCase.case_id} 審查決策覆寫成功！`);
        setSubmitting(false);
        onReviewSubmitted(); // 通知 Sidebar 重新抓取 pending 數
        // 更新本地列表狀態
        setCases(prev => prev.map(c => c.case_id === updatedCase.case_id ? updatedCase : c));
        setSelectedCase(updatedCase);
      })
      .catch(err => {
        setErrorMsg(err.message || '連線錯誤，無法套用人工決策。');
        setSubmitting(false);
      });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending_review':
        return <ShieldAlert size={16} color="var(--warning)" />;
      case 'approved':
        return <CheckCircle2 size={16} color="var(--success)" />;
      case 'rejected':
        return <XCircle size={16} color="var(--danger)" />;
      case 'needs_evidence':
        return <AlertCircle size={16} color="var(--secondary)" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending_review':
        return <span style={{ color: 'var(--warning)', fontWeight: 600 }}>待審查 (Pending)</span>;
      case 'approved':
        return <span style={{ color: 'var(--success)', fontWeight: 600 }}>審查通過 (Approved)</span>;
      case 'rejected':
        return <span style={{ color: 'var(--danger)', fontWeight: 600 }}>審查拒絕 (Rejected)</span>;
      case 'needs_evidence':
        return <span style={{ color: 'var(--secondary)', fontWeight: 600 }}>需補件 (Needs Evidence)</span>;
      default:
        return status;
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 className="display-title" style={styles.title}>人工審查工作台 (HITL)</h1>
          <p style={styles.subtitle}>合規官覆寫決策與實時 SHA-256 前向防篡改日誌鏈聯動</p>
        </div>
      </header>

      {loading ? (
        <div style={styles.loadingWrapper}>載入審查案件中...</div>
      ) : (
        <div style={styles.mainGrid}>
          {/* 左側案件列表 */}
          <div className="glass-card" style={styles.listCard}>
            <h3 style={styles.sectionTitle}>案件隊列</h3>
            <p style={styles.sectionDesc}>人機協同自動分流路由進來的待決策件</p>

            {cases.length === 0 ? (
              <div style={styles.emptyWrapper}>🎉 目前無任何人工審查案件</div>
            ) : (
              <div style={styles.listWrapper}>
                {cases.map((c) => {
                  const isSelected = selectedCase?.case_id === c.case_id;
                  return (
                    <div
                      key={c.case_id}
                      onClick={() => setSelectedCase(c)}
                      style={{
                        ...styles.caseItem,
                        ...(isSelected ? styles.caseItemActive : {})
                      }}
                    >
                      <div style={styles.caseItemHeader}>
                        <span style={styles.caseId}>{c.case_id}</span>
                        <div style={styles.caseStatusWrap}>
                          {getStatusIcon(c.approval_status)}
                          <span style={styles.caseStatusText}>
                            {c.approval_status === 'pending_review' ? '待審查' : '已結案'}
                          </span>
                        </div>
                      </div>
                      <div style={styles.caseReasons}>
                        {c.review_reason.map((reason, idx) => (
                          <span key={idx} style={styles.reasonTag}>{reason}</span>
                        ))}
                      </div>
                      <div style={styles.caseFooter}>
                        <span>客戶: {c.customer_id}</span>
                        <span>{new Date(c.timestamp).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 右側審查操作面板 */}
          <div className="glass-card" style={styles.formCard}>
            {selectedCase ? (
              <>
                <div style={styles.formHeader}>
                  <div>
                    <h3 style={styles.sectionTitle}>
                      審查決策單：<span style={{ color: 'var(--primary)' }}>{selectedCase.case_id}</span>
                    </h3>
                    <p style={styles.sectionDesc}>關聯客戶：{selectedCase.customer_id}</p>
                  </div>
                  <div style={styles.statusBadge}>
                    {getStatusText(selectedCase.approval_status)}
                  </div>
                </div>

                <div style={styles.reasonsBox}>
                  <h4 style={styles.boxTitle}>⚠️ 人工分流路由觸發理由</h4>
                  <ul style={styles.reasonsList}>
                    {selectedCase.review_reason.map((reason, idx) => (
                      <li key={idx} style={styles.reasonLi}>
                        系統判定符合高洗錢風險特徵：<code>{reason}</code>
                      </li>
                    ))}
                  </ul>
                </div>

                <form onSubmit={handleSubmit} style={styles.form}>
                  {/* 審核狀態 */}
                  <div className="form-group">
                    <label>合規覆核決策 (Approval Status)</label>
                    <div style={styles.radioGrid}>
                      {[
                        { id: 'approved', label: '核准並套用覆寫', desc: '准予開戶 / 執行交易' },
                        { id: 'needs_evidence', label: '要求補件 (EDD)', desc: '需上傳額外資產證明' },
                        { id: 'rejected', label: '拒絕開戶業務', desc: '存在重大洗錢制裁嫌疑' }
                      ].map((opt) => (
                        <label 
                          key={opt.id} 
                          style={{
                            ...styles.radioLabel,
                            ...(approvalStatus === opt.id ? styles.radioLabelActive : {}),
                            cursor: selectedCase.approval_status !== 'pending_review' ? 'default' : 'pointer'
                          }}
                        >
                          <input
                            type="radio"
                            name="approvalStatus"
                            value={opt.id}
                            checked={approvalStatus === opt.id}
                            disabled={selectedCase.approval_status !== 'pending_review'}
                            onChange={(e) => setApprovalStatus(e.target.value as any)}
                            style={styles.radioInput}
                          />
                          <div>
                            <div style={styles.radioTitle}>{opt.label}</div>
                            <div style={styles.radioDesc}>{opt.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* CDD 等級覆寫 */}
                  <div className="form-group">
                    <label>人工覆寫最終 CDD 盡職調查等級</label>
                    <select
                      className="form-control"
                      value={decision}
                      disabled={selectedCase.approval_status !== 'pending_review'}
                      onChange={(e) => setDecision(e.target.value as any)}
                    >
                      <option value="simplified_cdd">簡化盡職調查 (Simplified CDD)</option>
                      <option value="standard_cdd">標準盡職調查 (Standard CDD)</option>
                      <option value="enhanced_due_diligence">加強盡職調查 (Enhanced Due Diligence)</option>
                    </select>
                  </div>

                  {/* 合規官 ID */}
                  <div className="form-group">
                    <label>合規官編號 (Reviewer ID)</label>
                    <input
                      type="text"
                      className="form-control"
                      value={officerId}
                      disabled={selectedCase.approval_status !== 'pending_review'}
                      onChange={(e) => setOfficerId(e.target.value)}
                    />
                  </div>

                  {/* 審批筆記 */}
                  <div className="form-group">
                    <label>合規官審核審批意見筆記 (必須包含條款級佐證，至少 5 字元)</label>
                    <textarea
                      className="form-control"
                      rows={4}
                      value={notes}
                      disabled={selectedCase.approval_status !== 'pending_review'}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="請在此輸入審批意見。例如：經查核該客戶雖具備政要PEP暴露，但經實質受益人穿透追溯，符合MAS 626第4.3條所提之低風險排除豁免..."
                    />
                  </div>

                  {errorMsg && (
                    <div style={styles.errorBox}>
                      <AlertCircle size={16} />
                      <span>{errorMsg}</span>
                    </div>
                  )}

                  {successMsg && (
                    <div style={styles.successBox}>
                      <Check size={16} />
                      <span>{successMsg}</span>
                    </div>
                  )}

                  {/* 提交按鈕 */}
                  {selectedCase.approval_status === 'pending_review' ? (
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={submitting}
                      style={styles.submitBtn}
                    >
                      <Send size={16} />
                      {submitting ? '提交決策中...' : '提交審批決策 (安全鎖定且連動 Hash Chain)'}
                    </button>
                  ) : (
                    <div style={styles.archivedBox}>
                      <CheckCircle2 size={16} color="var(--success)" />
                      <span>該案件已完成人工審查並封存於防篡改日誌中。執行人：{selectedCase.reviewed_by}</span>
                    </div>
                  )}
                </form>
              </>
            ) : (
              <div style={styles.loadingWrapper}>請選擇一個案件個案以查看詳情</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '32px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: '2.2rem',
    marginBottom: '8px',
  },
  subtitle: {
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  loadingWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '340px 1fr',
    gap: '24px',
    alignItems: 'start',
  },
  listCard: {
    display: 'flex',
    flexDirection: 'column' as const,
    maxHeight: '600px',
  },
  formCard: {
    display: 'flex',
    flexDirection: 'column' as const,
    minHeight: '500px',
  },
  sectionTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.2rem',
    fontWeight: 700,
    marginBottom: '6px',
  },
  sectionDesc: {
    fontSize: '0.825rem',
    color: 'var(--text-muted)',
    marginBottom: '20px',
  },
  emptyWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
    background: 'rgba(255, 255, 255, 0.01)',
    borderRadius: '10px',
    border: '1px dashed rgba(255, 255, 255, 0.05)',
  },
  listWrapper: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    overflowY: 'auto' as const,
    flex: 1,
  },
  caseItem: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '10px',
    padding: '14px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  caseItemActive: {
    background: 'rgba(0, 242, 254, 0.05)',
    borderColor: 'rgba(0, 242, 254, 0.3)',
  },
  caseItemHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  caseId: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '0.95rem',
    color: 'var(--text-primary)',
  },
  caseStatusWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  caseStatusText: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  caseReasons: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '6px',
    marginBottom: '10px',
  },
  reasonTag: {
    fontSize: '0.7rem',
    background: 'rgba(255, 179, 0, 0.1)',
    color: 'var(--warning)',
    border: '1px solid rgba(255, 179, 0, 0.2)',
    padding: '2px 6px',
    borderRadius: '4px',
    fontFamily: 'monospace',
  },
  caseFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  },
  formHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    paddingBottom: '16px',
    marginBottom: '20px',
  },
  statusBadge: {
    fontSize: '0.85rem',
  },
  reasonsBox: {
    background: 'rgba(255, 179, 0, 0.03)',
    border: '1px solid rgba(255, 179, 0, 0.15)',
    padding: '14px 16px',
    borderRadius: '10px',
    marginBottom: '24px',
  },
  boxTitle: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--warning)',
    marginBottom: '6px',
    fontFamily: 'var(--font-display)',
  },
  reasonsList: {
    paddingLeft: '20px',
  },
  reasonLi: {
    fontSize: '0.825rem',
    color: '#e2e8f0',
    marginBottom: '4px',
    lineHeight: '1.4',
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px',
  },
  radioGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '12px',
    marginTop: '6px',
  },
  radioLabel: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    background: 'rgba(0, 0, 0, 0.2)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    padding: '12px',
    transition: 'var(--transition-smooth)',
  },
  radioLabelActive: {
    borderColor: 'var(--primary)',
    background: 'rgba(0, 242, 254, 0.03)',
    boxShadow: '0 0 10px rgba(0, 242, 254, 0.1)',
  },
  radioInput: {
    marginTop: '4px',
    accentColor: 'var(--primary)',
  },
  radioTitle: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#ffffff',
  },
  radioDesc: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    marginTop: '2px',
  },
  errorBox: {
    background: 'rgba(255, 23, 68, 0.08)',
    border: '1px solid rgba(255, 23, 68, 0.2)',
    color: 'var(--danger)',
    padding: '12px 16px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '0.875rem',
  },
  successBox: {
    background: 'rgba(0, 230, 118, 0.08)',
    border: '1px solid rgba(0, 230, 118, 0.2)',
    color: 'var(--success)',
    padding: '12px 16px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '0.875rem',
  },
  submitBtn: {
    marginTop: '10px',
    width: '100%',
    justifyContent: 'center',
  },
  archivedBox: {
    background: 'rgba(0, 230, 118, 0.05)',
    border: '1px solid rgba(0, 230, 118, 0.2)',
    borderRadius: '8px',
    padding: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '0.875rem',
    color: 'var(--success)',
  }
};
