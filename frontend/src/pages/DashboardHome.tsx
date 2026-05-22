import React, { useEffect, useState } from 'react';
import { Users, Shield, CheckSquare, ShieldCheck, ArrowRight, Activity, ChevronRight } from 'lucide-react';

interface Customer {
  customer_id: string;
  customer_type: 'individual' | 'corporate';
  pep_exposure: boolean;
  ownership_layers: number;
  ubo_status: 'clear' | 'unclear';
  associated_pep_id: string | null;
  risk_score: number;
}

interface CDDChecklist {
  checklist_id: string;
  customer_id: string;
  decision: 'simplified_cdd' | 'standard_cdd' | 'enhanced_due_diligence';
  human_review_required: boolean;
  required_evidence: string[];
  applied_clauses: string[];
  conflict_detected: boolean;
  explanation: string;
}

interface DashboardHomeProps {
  onNavigate: (tab: string) => void;
  pendingCount: number;
  isLogsIntact: boolean;
  logsCount: number;
}

export const DashboardHome: React.FC<DashboardHomeProps> = ({ 
  onNavigate, 
  pendingCount, 
  isLogsIntact, 
  logsCount 
}) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCust, setSelectedCust] = useState<Customer | null>(null);
  const [checklist, setChecklist] = useState<CDDChecklist | null>(null);
  const [checklistLoading, setChecklistLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/customers')
      .then(res => res.json())
      .then(data => {
        setCustomers(data);
        if (data.length > 0) {
          setSelectedCust(data[0]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching customers:', err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedCust) return;
    setChecklistLoading(true);
    fetch(`http://localhost:8000/api/v1/customers/${selectedCust.customer_id}/checklist`)
      .then(res => res.json())
      .then(data => {
        setChecklist(data);
        setChecklistLoading(false);
      })
      .catch(err => {
        console.error('Error fetching checklist:', err);
        setChecklistLoading(false);
      });
  }, [selectedCust]);

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case 'simplified_cdd':
        return <span className="badge badge-success">簡化 CDD (Simplified)</span>;
      case 'standard_cdd':
        return <span className="badge badge-primary">標準 CDD (Standard)</span>;
      case 'enhanced_due_diligence':
        return <span className="badge badge-danger">加強 EDD (Enhanced)</span>;
      default:
        return <span className="badge">{decision}</span>;
    }
  };

  return (
    <div style={styles.container}>
      {/* 頂部標題 */}
      <header style={styles.header}>
        <div>
          <h1 className="display-title" style={styles.title}>智能合規工作台</h1>
          <p style={styles.subtitle}>基於混合元模型法規圖譜的自動化 CDD 推理與鏈式審計系統</p>
        </div>
        <div style={styles.timeBadge}>
          <Activity size={14} color="var(--primary)" />
          <span style={styles.timeText}>實時合規推理引擎已啟動</span>
        </div>
      </header>

      {/* 指標卡片網格 */}
      <div style={styles.metricsGrid}>
        <div className="glass-card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <span style={styles.metricTitle}>典型客戶情境</span>
            <div style={{ ...styles.iconWrapper, background: 'rgba(79, 172, 254, 0.1)' }}>
              <Users size={20} color="var(--secondary)" />
            </div>
          </div>
          <div style={styles.metricValue}>{customers.length} <span style={styles.metricUnit}>個案</span></div>
          <div style={styles.metricFooter}>金標測試數據集覆蓋率 100%</div>
        </div>

        <div className="glass-card" style={{
          ...styles.metricCard,
          border: pendingCount > 0 ? '1px solid rgba(255, 23, 68, 0.2)' : '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <div style={styles.metricHeader}>
            <span style={styles.metricTitle}>待人工審查案件</span>
            <div style={{ 
              ...styles.iconWrapper, 
              background: pendingCount > 0 ? 'rgba(255, 23, 68, 0.1)' : 'rgba(255, 255, 255, 0.05)' 
            }}>
              <Shield size={20} color={pendingCount > 0 ? 'var(--danger)' : 'var(--text-muted)'} />
            </div>
          </div>
          <div style={{ 
            ...styles.metricValue, 
            color: pendingCount > 0 ? 'var(--danger)' : 'var(--text-primary)' 
          }}>{pendingCount} <span style={styles.metricUnit}>件</span></div>
          <button 
            onClick={() => onNavigate('review')}
            style={styles.actionLink}
          >
            前往審批隊列 <ArrowRight size={14} />
          </button>
        </div>

        <div className="glass-card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <span style={styles.metricTitle}>審計日誌深度</span>
            <div style={{ ...styles.iconWrapper, background: 'rgba(0, 242, 254, 0.1)' }}>
              <CheckSquare size={20} color="var(--primary)" />
            </div>
          </div>
          <div style={styles.metricValue}>{logsCount} <span style={styles.metricUnit}>條記錄</span></div>
          <button 
            onClick={() => onNavigate('timeline')}
            style={styles.actionLink}
          >
            查看審計時間線 <ArrowRight size={14} />
          </button>
        </div>

        <div className={`glass-card ${isLogsIntact ? 'pulse-success' : 'pulse-danger'}`} style={{
          ...styles.metricCard,
          borderColor: isLogsIntact ? 'rgba(0, 230, 118, 0.2)' : 'rgba(255, 23, 68, 0.2)',
        }}>
          <div style={styles.metricHeader}>
            <span style={styles.metricTitle}>日誌鏈完整性</span>
            <div style={{ 
              ...styles.iconWrapper, 
              background: isLogsIntact ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255, 23, 68, 0.1)' 
            }}>
              <ShieldCheck size={20} color={isLogsIntact ? 'var(--success)' : 'var(--danger)'} />
            </div>
          </div>
          <div style={{ 
            ...styles.metricValue, 
            color: isLogsIntact ? 'var(--success)' : 'var(--danger)',
            fontSize: '1.8rem'
          }}>{isLogsIntact ? '100% 健全' : '檢測到異常'}</div>
          <div style={styles.metricFooter}>
            {isLogsIntact ? '級聯 SHA-256 鏈校驗通過' : '警告！前向雜湊一致性破裂'}
          </div>
        </div>
      </div>

      {/* 主體區塊：客戶列表與 Checklist 動態詳情 */}
      <div style={styles.mainGrid}>
        {/* 左側客戶情境列表 */}
        <div className="glass-card" style={styles.listCard}>
          <h3 style={styles.sectionTitle}>典型客戶情境</h3>
          <p style={styles.sectionDesc}>請選擇客戶個案，查看即時法規關聯與 CDD 初審結果</p>
          
          {loading ? (
            <div style={styles.loadingWrapper}>載入客戶列表中...</div>
          ) : (
            <div style={styles.listWrapper}>
              {customers.map((cust) => {
                const isSelected = selectedCust?.customer_id === cust.customer_id;
                return (
                  <div
                    key={cust.customer_id}
                    onClick={() => setSelectedCust(cust)}
                    style={{
                      ...styles.customerItem,
                      ...(isSelected ? styles.customerItemActive : {})
                    }}
                  >
                    <div style={styles.custMeta}>
                      <span style={styles.custId}>{cust.customer_id}</span>
                      <span style={{
                        ...styles.custTypeBadge,
                        background: cust.customer_type === 'corporate' ? 'rgba(79, 172, 254, 0.15)' : 'rgba(0, 242, 254, 0.1)'
                      }}>
                        {cust.customer_type === 'corporate' ? '企業客戶' : '個人客戶'}
                      </span>
                    </div>
                    <div style={styles.custDetails}>
                      <span>風險分數: {cust.risk_score}</span>
                      <span>股權層級: {cust.ownership_layers} 層</span>
                    </div>
                    <ChevronRight size={16} color="var(--text-muted)" style={styles.arrow} />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* 右側 Checklist 推理與條款級溯源面板 */}
        <div className="glass-card" style={styles.detailsCard}>
          {selectedCust ? (
            <>
              <div style={styles.detailsHeader}>
                <div>
                  <h3 style={styles.sectionTitle}>
                    Checklist 推理結果：<span style={{ color: 'var(--primary)' }}>{selectedCust.customer_id}</span>
                  </h3>
                  <p style={styles.sectionDesc}>由法規推理引擎實時演算生成的合規審核清單</p>
                </div>
                <div>
                  {checklist && getDecisionBadge(checklist.decision)}
                </div>
              </div>

              {checklistLoading ? (
                <div style={styles.loadingWrapper}>實時合規推理中...</div>
              ) : checklist ? (
                <div style={styles.checklistContent}>
                  {/* 推理依據與說明 */}
                  <div style={styles.infoBox}>
                    <h4 style={styles.infoBoxTitle}>🤖 引擎推理合規結論</h4>
                    <p style={styles.infoBoxText}>{checklist.explanation}</p>
                  </div>

                  {/* 人工覆寫狀態 */}
                  <div style={{
                    ...styles.statusBox,
                    border: checklist.human_review_required 
                      ? '1px dashed rgba(255, 179, 0, 0.4)' 
                      : '1px solid rgba(0, 230, 118, 0.3)',
                    background: checklist.human_review_required
                      ? 'rgba(255, 179, 0, 0.05)'
                      : 'rgba(0, 230, 118, 0.03)'
                  }}>
                    <span style={{
                      ...styles.statusBoxDot,
                      backgroundColor: checklist.human_review_required ? 'var(--warning)' : 'var(--success)'
                    }} />
                    <span>
                      {checklist.human_review_required 
                        ? '需人工合規官覆寫：系統檢測到高風險特徵，已自動路由至審批隊列。' 
                        : '合規狀態：已完成人工審查核准覆寫。'}
                    </span>
                  </div>

                  {/* 應收集證據 Checklist */}
                  <div style={styles.subSection}>
                    <h4 style={styles.subTitle}>🛡️ 應收集之合規證據清單 (Checklist)</h4>
                    <div style={styles.checklistGrid}>
                      {checklist.required_evidence.map((evidence, idx) => (
                        <div key={idx} style={styles.checkItem}>
                          <input type="checkbox" readOnly checked={!checklist.human_review_required} style={styles.checkbox} />
                          <span style={styles.evidenceText}>{evidence}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 條款級法規溯源 Provenance */}
                  <div style={styles.subSection}>
                    <h4 style={styles.subTitle}>📜 條款級法規依據溯源 (Provenance)</h4>
                    <div style={styles.provenanceList}>
                      {checklist.applied_clauses.map((clause, idx) => (
                        <div key={idx} style={styles.provenanceItem}>
                          <span style={styles.clauseCode}>{clause}</span>
                          <span style={styles.clauseSource}>
                            {clause.includes('MAS') ? '新加坡金管局 MAS Notice 626' : 'FATF 國際洗錢防制建議 10'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={styles.loadingWrapper}>未找到該客戶的合規推理結果</div>
              )}
            </>
          ) : (
            <div style={styles.loadingWrapper}>請選擇一個客戶個案以查看詳情</div>
          )}
        </div>
      </div>
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
  timeBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: 'rgba(0, 242, 254, 0.08)',
    border: '1px solid rgba(0, 242, 254, 0.2)',
    padding: '8px 16px',
    borderRadius: '20px',
  },
  timeText: {
    fontSize: '0.85rem',
    color: 'var(--primary)',
    fontWeight: 600,
    fontFamily: 'var(--font-sans)',
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '24px',
  },
  metricCard: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column' as const,
    justifyContent: 'space-between',
    height: '150px',
  },
  metricHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricTitle: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    fontWeight: 600,
    fontFamily: 'var(--font-display)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  iconWrapper: {
    width: '36px',
    height: '36px',
    borderRadius: '10px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  metricValue: {
    fontSize: '2.2rem',
    fontWeight: 700,
    fontFamily: 'var(--font-display)',
    lineHeight: '1.2',
  },
  metricUnit: {
    fontSize: '1rem',
    fontWeight: 500,
    color: 'var(--text-muted)',
  },
  metricFooter: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
  },
  actionLink: {
    background: 'none',
    border: 'none',
    color: 'var(--primary)',
    fontSize: '0.8rem',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    cursor: 'pointer',
    padding: 0,
    width: 'fit-content',
    transition: 'color 0.2s',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '320px 1fr',
    gap: '24px',
    minHeight: '500px',
  },
  listCard: {
    display: 'flex',
    flexDirection: 'column' as const,
  },
  detailsCard: {
    display: 'flex',
    flexDirection: 'column' as const,
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
  loadingWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
  },
  listWrapper: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    overflowY: 'auto' as const,
    flex: 1,
    maxHeight: '420px',
  },
  customerItem: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '10px',
    padding: '14px',
    cursor: 'pointer',
    position: 'relative' as const,
    transition: 'all 0.2s ease',
  },
  customerItemActive: {
    background: 'rgba(0, 242, 254, 0.05)',
    borderColor: 'rgba(0, 242, 254, 0.3)',
  },
  custMeta: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  custId: {
    fontFamily: 'var(--font-display)',
    fontWeight: 600,
    fontSize: '0.95rem',
  },
  custTypeBadge: {
    fontSize: '0.7rem',
    fontWeight: 600,
    padding: '2px 6px',
    borderRadius: '4px',
  },
  custDetails: {
    display: 'flex',
    gap: '12px',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  },
  arrow: {
    position: 'absolute' as const,
    right: '12px',
    top: '50%',
    transform: 'translateY(-50%)',
  },
  detailsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    paddingBottom: '16px',
    marginBottom: '20px',
  },
  checklistContent: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '24px',
    flex: 1,
  },
  infoBox: {
    background: 'rgba(79, 172, 254, 0.05)',
    border: '1px solid rgba(79, 172, 254, 0.15)',
    borderRadius: '10px',
    padding: '16px',
  },
  infoBoxTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '0.9rem',
    fontWeight: 600,
    color: 'var(--secondary)',
    marginBottom: '8px',
  },
  infoBoxText: {
    fontSize: '0.875rem',
    lineHeight: '1.5',
    color: '#e2e8f0',
  },
  statusBox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 16px',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: 500,
  },
  statusBoxDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  subSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  subTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '0.95rem',
    fontWeight: 600,
    color: '#f8fafc',
  },
  checklistGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  checkItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px',
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    padding: '12px',
    borderRadius: '8px',
  },
  checkbox: {
    marginTop: '3px',
    accentColor: 'var(--primary)',
    cursor: 'default',
  },
  evidenceText: {
    fontSize: '0.85rem',
    lineHeight: '1.4',
    color: '#e2e8f0',
  },
  provenanceList: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '10px',
  },
  provenanceItem: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '8px',
    padding: '8px 14px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  clauseCode: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '0.85rem',
    color: 'var(--primary)',
  },
  clauseSource: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  }
};
