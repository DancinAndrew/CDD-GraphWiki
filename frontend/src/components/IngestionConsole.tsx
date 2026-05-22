import React, { useState, useRef, useEffect } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Settings, 
  Terminal, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  ArrowRight,
  RefreshCw,
  Info
} from 'lucide-react';

interface IngestionConsoleProps {
  onNavigate: (tab: string) => void;
}

export const IngestionConsole: React.FC<IngestionConsoleProps> = ({ onNavigate }) => {
  // 表單狀態
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [issuer, setIssuer] = useState('MAS');
  const [customIssuer, setCustomIssuer] = useState('');
  const [jurisdiction, setJurisdiction] = useState('Singapore');
  const [version, setVersion] = useState('2026 Edition');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [apiKey, setApiKey] = useState('');

  // 任務執行狀態
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string>('idle'); // idle, pending, parsing_pdf, extracting_clauses, extracting_obligations, merging_data, completed, failed
  const [progress, setProgress] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // 終端日誌框引用，用於自動滾動
  const logEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 當日誌更新時自動滾動到底部
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // 輪詢背景任務狀態的 Effect
  useEffect(() => {
    if (!taskId || taskStatus === 'completed' || taskStatus === 'failed') return;

    const pollInterval = setInterval(() => {
      fetch(`http://localhost:8000/api/v1/ingest/task/${taskId}`)
        .then(res => {
          if (!res.ok) throw new Error('無法取得任務進度');
          return res.json();
        })
        .then(data => {
          setTaskStatus(data.status);
          setProgress(data.progress || 0);
          setLogs(data.logs || []);
          if (data.status === 'completed') {
            clearInterval(pollInterval);
          } else if (data.status === 'failed') {
            setErrorMessage(data.error || '導入管線執行失敗，請檢查 API Key 或日誌。');
            clearInterval(pollInterval);
          }
        })
        .catch(err => {
          console.error('Polling error:', err);
          clearInterval(pollInterval);
        });
    }, 1500); // 每 1.5 秒輪詢一次

    return () => clearInterval(pollInterval);
  }, [taskId, taskStatus]);

  // 拖曳上傳處理
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile);
        // 自動嘗試填充 Title
        if (!title) {
          const cleanName = droppedFile.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
          setTitle(cleanName);
        }
      } else {
        alert("僅支援上傳 PDF 格式的法規文件。");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      if (!title) {
        const cleanName = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
        setTitle(cleanName);
      }
    }
  };

  // 提交 Ingestion 請求
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert("請先選擇或拖入一個 PDF 檔案！");
      return;
    }
    if (!title.strip && !title) {
      alert("請輸入法規標題！");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setTaskId(null);
    setTaskStatus('pending');
    setProgress(5);
    setLogs(["[SYSTEM] 正在準備法規 Ingestion 負載..."]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    const finalIssuer = issuer === 'CUSTOM' ? customIssuer : issuer;
    formData.append('issuer', finalIssuer);
    formData.append('jurisdiction', jurisdiction);
    formData.append('version', version);
    if (effectiveDate) formData.append('effective_date', effectiveDate);
    if (sourceUrl) formData.append('source_url', sourceUrl);
    if (apiKey) formData.append('api_key', apiKey);

    try {
      const response = await fetch('http://localhost:8000/api/v1/ingest/pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || '發送 PDF 導入請求失敗');
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setTaskStatus(data.status);
      setLogs(prev => [...prev, `[SYSTEM] 任務已註冊，已受理 Task ID: ${data.task_id}`]);
    } catch (err: any) {
      console.error(err);
      setTaskStatus('failed');
      setErrorMessage(err.message || '無法連接後端 Ingestion API 端點');
      setLogs(prev => [...prev, `[ERROR] 啟動失敗: ${err.message || '連線錯誤'}`]);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 渲染狀態標籤
  const renderStatusBadge = () => {
    switch (taskStatus) {
      case 'idle':
        return <span style={{ ...styles.badge, color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)' }}>空閒</span>;
      case 'pending':
        return <span style={{ ...styles.badge, color: '#f59e0b', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>等待佇列</span>;
      case 'parsing_pdf':
        return <span style={{ ...styles.badge, color: '#06b6d4', background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.2)' }}>解析 PDF 中</span>;
      case 'extracting_clauses':
        return <span style={{ ...styles.badge, color: '#6366f1', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)' }}>LLM 條款切片中</span>;
      case 'extracting_obligations':
        return <span style={{ ...styles.badge, color: '#a855f7', background: 'rgba(168,85,247,0.1)', border: '1px solid rgba(168,85,247,0.2)' }}>LLM 義務抽取中</span>;
      case 'merging_data':
        return <span style={{ ...styles.badge, color: '#e0f2fe', background: 'rgba(224,242,254,0.1)', border: '1px solid rgba(224,242,254,0.2)' }}>增量合併圖譜</span>;
      case 'completed':
        return <span style={{ ...styles.badge, color: 'var(--success)', background: 'rgba(16,185,129,0.1)', border: '1px solid var(--success)', boxShadow: '0 0 10px rgba(16,185,129,0.2)' }}>導入成功</span>;
      case 'failed':
        return <span style={{ ...styles.badge, color: 'var(--danger)', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--danger)', boxShadow: '0 0 10px rgba(239,68,68,0.2)' }}>導入失敗</span>;
      default:
        return <span style={{ ...styles.badge }}>{taskStatus}</span>;
    }
  };

  // 重置表單
  const handleReset = () => {
    setFile(null);
    setTitle('');
    setIssuer('MAS');
    setCustomIssuer('');
    setJurisdiction('Singapore');
    setVersion('2026 Edition');
    setEffectiveDate('');
    setSourceUrl('');
    setApiKey('');
    setTaskId(null);
    setTaskStatus('idle');
    setProgress(0);
    setLogs([]);
    setErrorMessage(null);
  };

  // 格式化日誌行
  const formatLogLine = (log: string) => {
    if (log.includes("[ERROR]") || log.includes("❌")) {
      return <span style={{ color: 'var(--danger)' }}>{log}</span>;
    } else if (log.includes("[SUCCESS]") || log.includes("✓") || log.includes("恭喜")) {
      return <span style={{ color: 'var(--success)' }}>{log}</span>;
    } else if (log.includes("[SYSTEM]")) {
      return <span style={{ color: 'var(--primary)' }}>{log}</span>;
    } else if (log.includes("extracting_obligations") || log.includes("Obligation")) {
      return <span style={{ color: '#a855f7' }}>{log}</span>;
    } else if (log.includes("extracting_clauses") || log.includes("Clause")) {
      return <span style={{ color: '#6366f1' }}>{log}</span>;
    } else if (log.includes("parsing_pdf") || log.includes("PDF")) {
      return <span style={{ color: '#06b6d4' }}>{log}</span>;
    }
    return <span>{log}</span>;
  };

  return (
    <div style={styles.container}>
      {/* 標題與簡介 */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.mainTitle}>真實法規 Inflow Ingestion 工作台</h1>
          <p style={styles.subtitle}>
            透過大語言模型 (LLM) 對法規 PDF 進行二階段智能段落切片與強型別合規義務抽取，熱更新決策 Checklist 並同步至 Neo4j。
          </p>
        </div>
        {taskStatus !== 'idle' && (
          <button onClick={handleReset} style={styles.resetButton}>
            <RefreshCw size={14} style={{ marginRight: '6px' }} />
            重新導入新法規
          </button>
        )}
      </div>

      <div style={styles.grid}>
        {/* 左側：法規表單與上傳 */}
        <div style={styles.cardLeft}>
          <h2 style={styles.sectionTitle}>
            <FileText size={18} style={{ color: 'var(--primary)' }} />
            法規元數據與檔案載荷
          </h2>

          <form onSubmit={handleSubmit} style={styles.form}>
            {/* 檔案拖曳上傳區 */}
            <div 
              style={{
                ...styles.dragArea,
                ...(dragActive ? styles.dragAreaActive : {}),
                ...(file ? styles.dragAreaHasFile : {}),
                pointerEvents: taskStatus !== 'idle' && taskStatus !== 'completed' && taskStatus !== 'failed' ? 'none' : 'auto'
              }}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf" 
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <UploadCloud size={48} style={{
                color: file ? 'var(--success)' : (dragActive ? 'var(--primary)' : 'rgba(255,255,255,0.2)'),
                transition: 'all 0.3s ease',
                marginBottom: '12px'
              }} />
              {file ? (
                <div>
                  <p style={styles.fileName}>{file.name}</p>
                  <p style={styles.fileSize}>{(file.size / 1024 / 1024).toFixed(2)} MB • PDF 格式</p>
                  <span style={styles.changeFileText}>點擊或拖曳以更換檔案</span>
                </div>
              ) : (
                <div>
                  <p style={styles.dragText}>將官方合規 PDF 法規拖曳至此，或 <span style={{ color: 'var(--primary)', fontWeight: 600 }}>瀏覽本機檔案</span></p>
                  <p style={styles.dragSubtext}>僅支援標準 PDF 格式，檔案大小建議 10MB 以內</p>
                </div>
              )}
            </div>

            <div style={styles.formRow}>
              {/* 法規標題 */}
              <div style={styles.formGroupFull}>
                <label style={styles.label}>法規官方標題 (Title) *</label>
                <input 
                  type="text" 
                  value={title} 
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="例如：MAS Notice 626 (Prevention of Money Laundering)"
                  required
                  disabled={taskStatus !== 'idle'}
                  style={styles.input}
                />
              </div>
            </div>

            <div style={styles.formRow}>
              {/* 頒布機構 */}
              <div style={styles.formGroup}>
                <label style={styles.label}>頒布機構 (Issuer) *</label>
                <select 
                  value={issuer} 
                  onChange={(e) => setIssuer(e.target.value)}
                  disabled={taskStatus !== 'idle'}
                  style={styles.select}
                >
                  <option value="MAS">MAS (新加坡金融管理局)</option>
                  <option value="FATF">FATF (金融行動特別工作組)</option>
                  <option value="HKMA">HKMA (香港金融管理局)</option>
                  <option value="INTERNAL">Internal (內部合規政策)</option>
                  <option value="CUSTOM">其他 (自定義)</option>
                </select>
                {issuer === 'CUSTOM' && (
                  <input 
                    type="text" 
                    value={customIssuer} 
                    onChange={(e) => setCustomIssuer(e.target.value)}
                    placeholder="請輸入機構英文縮寫"
                    required
                    disabled={taskStatus !== 'idle'}
                    style={{ ...styles.input, marginTop: '8px' }}
                  />
                )}
              </div>

              {/* 管轄區 */}
              <div style={styles.formGroup}>
                <label style={styles.label}>管轄權司法區 (Jurisdiction) *</label>
                <input 
                  type="text" 
                  value={jurisdiction} 
                  onChange={(e) => setJurisdiction(e.target.value)}
                  placeholder="例如：Singapore"
                  required
                  disabled={taskStatus !== 'idle'}
                  style={styles.input}
                />
              </div>
            </div>

            <div style={styles.formRow}>
              {/* 法規版本 */}
              <div style={styles.formGroup}>
                <label style={styles.label}>法規修訂版本 (Version) *</label>
                <input 
                  type="text" 
                  value={version} 
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="例如：Last Revised 2026"
                  required
                  disabled={taskStatus !== 'idle'}
                  style={styles.input}
                />
              </div>

              {/* 生效日期 */}
              <div style={styles.formGroup}>
                <label style={styles.label}>生效日期 (Effective Date)</label>
                <input 
                  type="date" 
                  value={effectiveDate} 
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  disabled={taskStatus !== 'idle'}
                  style={styles.input}
                />
              </div>
            </div>

            {/* 進階設定抽屜 */}
            <div style={styles.settingsGroup}>
              <div style={styles.settingsHeader}>
                <Settings size={14} style={{ marginRight: '6px', color: 'var(--primary)' }} />
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>進階 LLM 與溯源配置</span>
              </div>
              
              <div style={{ marginTop: '12px' }}>
                <label style={styles.label}>法規來源下載 URL (Source URL)</label>
                <input 
                  type="url" 
                  value={sourceUrl} 
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="例如：https://www.mas.gov.sg/-/media/mas/notices/pdf/notice-626.pdf"
                  disabled={taskStatus !== 'idle'}
                  style={styles.inputCompact}
                />
              </div>

              <div style={{ marginTop: '12px' }}>
                <label style={styles.label}>專屬 Gemini API 金鑰 (選填)</label>
                <input 
                  type="password" 
                  value={apiKey} 
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="留空將使用系統內置環境變數的 GEMINI_API_KEY (離線時自動 Mock)"
                  disabled={taskStatus !== 'idle'}
                  style={styles.inputCompact}
                />
                <div style={styles.infoAlert}>
                  <Info size={12} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    為確保單元測試健全，當系統檢測到 API Key 留空且伺服器無環境變數時，後端會自動 Fallback 至離線 Mock 模式。
                  </span>
                </div>
              </div>
            </div>

            {taskStatus === 'idle' && (
              <button 
                type="submit" 
                disabled={isSubmitting || !file} 
                style={{
                  ...styles.submitButton,
                  opacity: !file ? 0.5 : 1,
                  cursor: !file ? 'not-allowed' : 'pointer'
                }}
              >
                {isSubmitting ? '正在啟動導入佇列...' : '啟動大模型 Ingestion Pipeline'}
                <ArrowRight size={16} style={{ marginLeft: '8px' }} />
              </button>
            )}
          </form>
        </div>

        {/* 右側：狀態展示、進度條與滾動終端 */}
        <div style={styles.cardRight}>
          <div style={styles.rightHeader}>
            <h2 style={styles.sectionTitle}>
              <Terminal size={18} style={{ color: 'var(--success)' }} />
              管線執行狀態與日誌
            </h2>
            {renderStatusBadge()}
          </div>

          {taskStatus === 'idle' ? (
            <div style={styles.idlePanel}>
              <Terminal size={48} style={{ color: 'rgba(255,255,255,0.08)', marginBottom: '16px' }} />
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>
                等待合規官上傳 PDF。大模型導入啟動後，<br />
                此處將以發光霓虹終端形式展現智能切片與義務抽取的即時日誌。
              </p>
            </div>
          ) : (
            <div style={styles.runningPanel}>
              {/* 進度條 */}
              <div style={styles.progressContainer}>
                <div style={styles.progressTextRow}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>當前執行進度</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--primary)' }}>{progress}%</span>
                </div>
                <div style={styles.progressBarBg}>
                  <div style={{
                    ...styles.progressBarFill,
                    width: `${progress}%`,
                  }} />
                </div>
              </div>

              {/* 終端日誌框 */}
              <div style={styles.terminal}>
                <div style={styles.terminalHeader}>
                  <span style={styles.terminalDotRed} />
                  <span style={styles.terminalDotYellow} />
                  <span style={styles.terminalDotGreen} />
                  <span style={styles.terminalTitle}>ingest-worker-console.log</span>
                </div>
                <div style={styles.terminalContent}>
                  {logs.map((log, index) => (
                    <div key={index} style={styles.logLine}>
                      {formatLogLine(log)}
                    </div>
                  ))}
                  <div ref={logEndRef} />
                </div>
              </div>

              {/* 成功卡片 (當 status === 'completed') */}
              {taskStatus === 'completed' && (
                <div style={styles.successBox}>
                  <CheckCircle2 size={24} style={{ color: 'var(--success)', flexShrink: 0 }} />
                  <div>
                    <h4 style={styles.successTitle}>法規導入與合規圖譜更新成功！</h4>
                    <p style={styles.successText}>
                      此法規已成功經過二階段 LLM 樹狀切片與 packaged-section 義務抽取。本地 YAML 檔案已實現安全增量合併，API 推理決策引擎已熱加載完成。
                    </p>
                    <button onClick={() => onNavigate('graph')} style={styles.successNavButton}>
                      前往可視化圖譜查看新霓虹節點
                      <ArrowRight size={14} style={{ marginLeft: '6px' }} />
                    </button>
                  </div>
                </div>
              )}

              {/* 失敗卡片 (當 status === 'failed') */}
              {taskStatus === 'failed' && (
                <div style={styles.errorBox}>
                  <XCircle size={24} style={{ color: 'var(--danger)', flexShrink: 0 }} />
                  <div>
                    <h4 style={styles.errorTitle}>導入管線執行失敗</h4>
                    <p style={styles.errorText}>
                      {errorMessage || '後端執行拋出異常。可能原因包括 API Key 授權失效、網路逾時或 PDF 損毀。'}
                    </p>
                    <button onClick={handleReset} style={styles.errorRetryButton}>
                      重置並重新嘗試
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '28px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '24px',
    height: '100%',
    overflowY: 'auto' as const,
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    paddingBottom: '20px',
  },
  mainTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.8rem',
    fontWeight: 700,
    color: '#ffffff',
    marginBottom: '6px',
    textShadow: '0 0 15px rgba(0, 242, 254, 0.15)',
  },
  subtitle: {
    fontFamily: 'var(--font-sans)',
    fontSize: '0.9rem',
    color: 'var(--text-muted)',
    maxWidth: '850px',
  },
  resetButton: {
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    padding: '8px 16px',
    color: '#ffffff',
    fontSize: '0.85rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    transition: 'all 0.2s ease',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1.2fr 1fr',
    gap: '24px',
    flex: 1,
    minHeight: '0', // 允許在 flex layout 中縮小
  },
  cardLeft: {
    background: 'rgba(17, 18, 26, 0.65)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '16px',
    padding: '24px',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    display: 'flex',
    flexDirection: 'column' as const,
    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
  },
  cardRight: {
    background: 'rgba(17, 18, 26, 0.65)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '16px',
    padding: '24px',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    display: 'flex',
    flexDirection: 'column' as const,
    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
  },
  rightHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: 700,
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  badge: {
    fontSize: '0.75rem',
    fontWeight: 700,
    padding: '4px 10px',
    borderRadius: '6px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.02em',
  },
  form: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
    flex: 1,
    overflowY: 'auto' as const,
    paddingRight: '4px',
  },
  dragArea: {
    border: '2px dashed rgba(255, 255, 255, 0.15)',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center' as const,
    cursor: 'pointer',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    background: 'rgba(255, 255, 255, 0.01)',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dragAreaActive: {
    borderColor: 'var(--primary)',
    background: 'rgba(0, 242, 254, 0.03)',
    boxShadow: '0 0 20px rgba(0, 242, 254, 0.1) inset',
    transform: 'scale(1.01)',
  },
  dragAreaHasFile: {
    borderColor: 'var(--success)',
    background: 'rgba(16, 185, 129, 0.02)',
  },
  dragText: {
    fontSize: '0.9rem',
    color: '#ffffff',
    fontWeight: 500,
    marginBottom: '4px',
  },
  dragSubtext: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
  },
  fileName: {
    fontSize: '0.95rem',
    color: '#ffffff',
    fontWeight: 600,
    marginBottom: '2px',
  },
  fileSize: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    marginBottom: '8px',
  },
  changeFileText: {
    fontSize: '0.75rem',
    color: 'var(--primary)',
    fontWeight: 600,
    textDecoration: 'underline',
  },
  formRow: {
    display: 'flex',
    gap: '16px',
  },
  formGroup: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
  },
  formGroupFull: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
  },
  label: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.03em',
  },
  input: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    padding: '10px 14px',
    color: '#ffffff',
    fontSize: '0.9rem',
    transition: 'all 0.2s ease',
    outline: 'none',
    width: '100%',
  },
  inputCompact: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '6px',
    padding: '8px 12px',
    color: '#ffffff',
    fontSize: '0.85rem',
    transition: 'all 0.2s ease',
    outline: 'none',
    width: '100%',
  },
  select: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '8px',
    padding: '10px 14px',
    color: '#ffffff',
    fontSize: '0.9rem',
    transition: 'all 0.2s ease',
    outline: 'none',
    cursor: 'pointer',
    width: '100%',
  },
  settingsGroup: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '10px',
    padding: '16px',
    marginTop: '8px',
  },
  settingsHeader: {
    display: 'flex',
    alignItems: 'center',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    paddingBottom: '8px',
  },
  infoAlert: {
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-start',
    background: 'rgba(0, 242, 254, 0.04)',
    border: '1px solid rgba(0, 242, 254, 0.1)',
    borderRadius: '6px',
    padding: '8px 10px',
    marginTop: '8px',
  },
  submitButton: {
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    border: 'none',
    borderRadius: '10px',
    padding: '14px 20px',
    color: '#11121a',
    fontSize: '0.95rem',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 15px rgba(0, 242, 254, 0.2)',
    transition: 'all 0.2s ease',
    marginTop: '8px',
  },
  idlePanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px dashed rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    background: 'rgba(255, 255, 255, 0.01)',
  },
  runningPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px',
    minHeight: '0',
  },
  progressContainer: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '10px',
    padding: '14px 16px',
  },
  progressTextRow: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '8px',
  },
  progressBarBg: {
    background: 'rgba(255, 255, 255, 0.05)',
    height: '8px',
    borderRadius: '99px',
    overflow: 'hidden',
  },
  progressBarFill: {
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
    height: '100%',
    borderRadius: '99px',
    transition: 'width 0.4s ease-out',
    boxShadow: '0 0 10px rgba(0, 242, 254, 0.4)',
  },
  terminal: {
    flex: 1,
    background: '#090a0f',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '12px',
    display: 'flex',
    flexDirection: 'column' as const,
    overflow: 'hidden',
    minHeight: '220px',
    boxShadow: '0 0 20px rgba(0, 0, 0, 0.5) inset',
  },
  terminalHeader: {
    background: '#151722',
    borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
    padding: '10px 14px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  terminalDotRed: { width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' },
  terminalDotYellow: { width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' },
  terminalDotGreen: { width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' },
  terminalTitle: {
    marginLeft: '8px',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontFamily: 'monospace',
  },
  terminalContent: {
    flex: 1,
    padding: '16px',
    overflowY: 'auto' as const,
    fontFamily: '"JetBrains Mono", "Courier New", Courier, monospace',
    fontSize: '0.82rem',
    lineHeight: '1.5',
    color: 'rgba(255, 255, 255, 0.85)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
    textAlign: 'left' as const,
  },
  logLine: {
    wordBreak: 'break-all' as const,
  },
  successBox: {
    background: 'rgba(16, 185, 129, 0.04)',
    border: '1px solid rgba(16, 185, 129, 0.15)',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    gap: '14px',
    boxShadow: '0 4px 20px rgba(16, 185, 129, 0.05)',
  },
  successTitle: {
    fontSize: '0.95rem',
    fontWeight: 700,
    color: 'var(--success)',
    marginBottom: '4px',
  },
  successText: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    lineHeight: '1.4',
    marginBottom: '12px',
  },
  successNavButton: {
    background: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid var(--success)',
    borderRadius: '6px',
    padding: '6px 12px',
    color: '#ffffff',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    transition: 'all 0.2s ease',
  },
  errorBox: {
    background: 'rgba(239, 68, 68, 0.04)',
    border: '1px solid rgba(239, 68, 68, 0.15)',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    gap: '14px',
  },
  errorTitle: {
    fontSize: '0.95rem',
    fontWeight: 700,
    color: 'var(--danger)',
    marginBottom: '4px',
  },
  errorText: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    lineHeight: '1.4',
    marginBottom: '12px',
  },
  errorRetryButton: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid var(--danger)',
    borderRadius: '6px',
    padding: '6px 12px',
    color: '#ffffff',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  }
};
