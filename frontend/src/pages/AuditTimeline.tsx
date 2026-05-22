import React, { useState, useEffect } from 'react';
import { TamperShield } from '../components/TamperShield';
import { History, Copy, ArrowRight, ShieldCheck, Key, Clock, User, HardDrive } from 'lucide-react';

interface AuditLogEntry {
  log_id: string;
  timestamp: string;
  event_type: 'reasoning_triggered' | 'case_created' | 'case_reviewed' | 'tamper_alert';
  operator: string;
  customer_id: string;
  payload: Record<string, any>;
  previous_hash: string;
  current_hash: string;
}

interface AuditTimelineProps {
  isIntact: boolean;
  setIsIntact: (val: boolean) => void;
  setLogsCount: (val: number) => void;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ 
  isIntact, 
  setIsIntact,
  setLogsCount
}) => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const fetchLogs = () => {
    setLoading(true);
    fetch('http://localhost:8000/api/v1/audit/logs')
      .then(res => res.json())
      .then(data => {
        // 由新到舊排序
        const sorted = data.sort((a: any, b: any) => b.log_id.localeCompare(a.log_id));
        setLogs(sorted);
        setLogsCount(sorted.length);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching logs:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleVerify = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/audit/verify');
      const data = await res.json();
      setIsIntact(data.is_intact);
      return data;
    } catch (err) {
      console.error('Error during self verification:', err);
      throw err;
    }
  };

  const handleCopy = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 1500);
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'reasoning_triggered':
        return <span className="badge badge-primary">引擎初審 (Reasoning)</span>;
      case 'case_created':
        return <span className="badge badge-warning">案件路由 (Auto-Route)</span>;
      case 'case_reviewed':
        return <span className="badge badge-success">人工審查覆寫 (HITL)</span>;
      case 'tamper_alert':
        return <span className="badge badge-danger">篡改警報 (TAMPER ALERT)</span>;
      default:
        return <span className="badge">{type}</span>;
    }
  };

  const formatHash = (hash: string) => {
    if (hash === '0'.repeat(64)) return 'GENESIS_HASH (00000000)';
    return `${hash.slice(0, 10)}...${hash.slice(-10)}`;
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div>
          <h1 className="display-title" style={styles.title}>防篡改日誌審計稽核</h1>
          <p style={styles.subtitle}>基於前向安全雜湊鏈 (Tamper-evident Hash Chain) 的法規與人工覆寫鏈式溯源存證</p>
        </div>
      </header>

      <div style={styles.mainGrid}>
        {/* 左側：3D 科幻自檢盾牌 */}
        <div style={styles.shieldWrapper}>
          <TamperShield isIntact={isIntact} onVerifyRequested={handleVerify} />
          
          <div className="glass-card" style={styles.theoryBox}>
            <h4 style={styles.theoryTitle}>🛡️ 級聯雜湊鏈防篡改機制</h4>
            <p style={styles.theoryText}>
              系統中發生的每一次決策推理與合規覆寫事件，其日誌內容都將與前一筆記錄的哈希值級聯，生成不可篡改的加密雜湊鏈。
              任何對歷史 JSON 檔案的惡意變更（如修改審批意見或降低風險等級），都將引發前向雜湊鏈破裂，在下一次完整性自檢中即刻觸發系統報警。
            </p>
          </div>
        </div>

        {/* 右側：防篡改時間線卡片流 */}
        <div className="glass-card" style={styles.timelineCard}>
          <div style={styles.timelineHeader}>
            <h3 style={styles.sectionTitle}>審計日誌時間線 (Audit Trail)</h3>
            <span style={styles.logCount}>共 {logs.length} 筆加密存證</span>
          </div>

          {loading ? (
            <div style={styles.loadingWrapper}>正在解析日誌鏈時間線...</div>
          ) : (
            <div style={styles.timelineWrapper}>
              {logs.map((log, idx) => {
                const isExpanded = expandedLogId === log.log_id;
                return (
                  <div 
                    key={log.log_id} 
                    style={{
                      ...styles.timelineItem,
                      borderLeft: `2px solid ${
                        log.event_type === 'case_reviewed' ? 'var(--success)' : 
                        log.event_type === 'tamper_alert' ? 'var(--danger)' : 'var(--primary)'
                      }`
                    }}
                  >
                    {/* 時間線圓點 */}
                    <div style={{
                      ...styles.timelineDot,
                      backgroundColor: 
                        log.event_type === 'case_reviewed' ? 'var(--success)' : 
                        log.event_type === 'tamper_alert' ? 'var(--danger)' : 'var(--primary)'
                    }} />

                    {/* 日誌卡片 */}
                    <div 
                      onClick={() => setExpandedLogId(isExpanded ? null : log.log_id)}
                      style={{
                        ...styles.logCard,
                        background: isExpanded ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.01)',
                        borderColor: isExpanded ? 'rgba(0, 242, 254, 0.2)' : 'rgba(255, 255, 255, 0.05)'
                      }}
                    >
                      <div style={styles.logCardHeader}>
                        <div style={styles.logMeta}>
                          <span style={styles.logId}>{log.log_id}</span>
                          {getEventBadge(log.event_type)}
                        </div>
                        <span style={styles.logTime}>
                          <Clock size={12} /> {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>

                      <div style={styles.logBrief}>
                        <div style={styles.briefCol}>
                          <User size={13} color="var(--text-muted)" />
                          <span>執行主體: <strong>{log.operator}</strong></span>
                        </div>
                        <div style={styles.briefCol}>
                          <HardDrive size={13} color="var(--text-muted)" />
                          <span>關聯客戶: <strong>{log.customer_id}</strong></span>
                        </div>
                      </div>

                      {/* 級聯哈希預覽 */}
                      <div style={styles.hashRow}>
                        <div style={styles.hashWrap}>
                          <Key size={11} color="var(--text-muted)" />
                          <span style={styles.hashLabel}>當前雜湊:</span>
                          <code style={styles.hashCode}>{formatHash(log.current_hash)}</code>
                        </div>
                        <button 
                          onClick={(e) => handleCopy(log.current_hash, e)}
                          style={styles.copyBtn}
                        >
                          <Copy size={11} /> {copiedText === log.current_hash ? '已複製' : '複製'}
                        </button>
                      </div>

                      {/* 展開之日誌詳細 Payload 與 Previous Hash 內容 */}
                      {isExpanded && (
                        <div style={styles.expandedContent} onClick={(e) => e.stopPropagation()}>
                          <div style={styles.divider} />
                          
                          <div style={styles.expandedSection}>
                            <span style={styles.expandedLabel}>前向雜湊 (Previous SHA-256):</span>
                            <code style={styles.hashCodeFull}>{log.previous_hash}</code>
                          </div>

                          <div style={styles.expandedSection}>
                            <span style={styles.expandedLabel}>完整加密雜湊 (Current SHA-256):</span>
                            <code style={styles.hashCodeFull}>{log.current_hash}</code>
                          </div>

                          <div style={styles.expandedSection}>
                            <span style={styles.expandedLabel}>事件 Payload (JSON 數據載荷):</span>
                            <pre style={styles.jsonBlock}>
                              {JSON.stringify(log.payload, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
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
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '380px 1fr',
    gap: '24px',
    alignItems: 'start',
  },
  shieldWrapper: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '24px',
  },
  theoryBox: {
    padding: '20px',
    background: 'rgba(255,255,255,0.01)',
  },
  theoryTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '0.9rem',
    fontWeight: 600,
    marginBottom: '8px',
    color: '#ffffff',
  },
  theoryText: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    lineHeight: '1.5',
  },
  timelineCard: {
    display: 'flex',
    flexDirection: 'column' as const,
    minHeight: '600px',
    maxHeight: '800px',
  },
  timelineHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    paddingBottom: '16px',
  },
  sectionTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.2rem',
    fontWeight: 700,
  },
  logCount: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  loadingWrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    color: 'var(--text-muted)',
    fontSize: '0.95rem',
  },
  timelineWrapper: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
    overflowY: 'auto' as const,
    flex: 1,
    paddingLeft: '12px',
  },
  timelineItem: {
    position: 'relative' as const,
    paddingLeft: '24px',
    paddingBottom: '20px',
  },
  timelineDot: {
    position: 'absolute' as const,
    left: '-5px',
    top: '20px',
    width: '9px',
    height: '9px',
    borderRadius: '50%',
    boxShadow: '0 0 8px currentColor',
  },
  logCard: {
    border: '1px solid rgba(255,255,255,0.05)',
    borderRadius: '12px',
    padding: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  logCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  logMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  logId: {
    fontFamily: 'var(--font-display)',
    fontWeight: 700,
    fontSize: '0.9rem',
    color: '#ffffff',
  },
  logTime: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  logBrief: {
    display: 'flex',
    gap: '24px',
    fontSize: '0.8rem',
    color: '#cbd5e1',
    marginBottom: '12px',
  },
  briefCol: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  hashRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: 'rgba(0,0,0,0.2)',
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid rgba(255, 255, 255, 0.03)',
  },
  hashWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  hashLabel: {
    fontSize: '0.7rem',
    color: 'var(--text-muted)',
    textTransform: 'uppercase' as const,
  },
  hashCode: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: 'var(--primary)',
    fontWeight: 600,
  },
  copyBtn: {
    background: 'transparent',
    border: 'none',
    color: 'var(--text-muted)',
    fontSize: '0.7rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '2px 6px',
    borderRadius: '4px',
    transition: 'all 0.2s',
  },
  expandedContent: {
    marginTop: '16px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  divider: {
    height: '1px',
    background: 'rgba(255,255,255,0.06)',
    width: '100%',
  },
  expandedSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  expandedLabel: {
    fontSize: '0.725rem',
    color: 'var(--text-muted)',
    fontWeight: 500,
  },
  hashCodeFull: {
    fontFamily: 'monospace',
    fontSize: '0.725rem',
    color: 'var(--secondary)',
    background: 'rgba(0,0,0,0.3)',
    padding: '8px 12px',
    borderRadius: '6px',
    wordBreak: 'break-all' as const,
    border: '1px solid rgba(255,255,255,0.02)',
  },
  jsonBlock: {
    fontFamily: 'monospace',
    fontSize: '0.75rem',
    color: '#e2e8f0',
    background: 'rgba(0,0,0,0.4)',
    padding: '12px',
    borderRadius: '6px',
    overflowX: 'auto' as const,
    border: '1px solid rgba(255,255,255,0.02)',
    lineHeight: '1.4',
  }
};
