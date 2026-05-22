import React, { useState } from 'react';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  History, 
  Network, 
  FileUp, 
  ChevronDown, 
  ChevronUp, 
  BookOpen, 
  Cpu, 
  Layers, 
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';

interface GuideSection {
  id: string;
  title: string;
  subtitle: string;
  icon: React.ComponentType<any>;
  badge: { text: string; type: 'primary' | 'success' | 'warning' | 'danger' };
  summary: string;
  steps: string[];
  techSpec: {
    engine: string;
    details: string;
    provenance: string;
  };
}

export const UserGuide: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string | null>('dashboard');

  const toggleSection = (id: string) => {
    setActiveSection(activeSection === id ? null : id);
  };

  const sections: GuideSection[] = [
    {
      id: 'dashboard',
      title: '工作台總覽 (Dashboard Home)',
      subtitle: '全局合規健康大盤與篡改自檢監控',
      icon: LayoutDashboard,
      badge: { text: '全域總覽', type: 'primary' },
      summary: '作為合規官的每日核心控制台，此頁面提供 CDD (客戶盡職調查) 的全局統計大盤、審查案件積壓狀態，並實時顯示底層日誌鏈的密碼學防篡改健康指引。',
      steps: [
        '檢視「案件審查」與「合規覆蓋率」等核心統計卡片。',
        '觀察「系統完整性防盾」，確認日誌鏈的即時健康度（綠色代表健全，紅色代表受篡改）。',
        '點擊待審查卡片，可直接快速跳轉至「案件審查隊列」進行決策。'
      ],
      techSpec: {
        engine: 'FastAPI 異步統計引擎',
        details: '後端採用 FastAPI 的高效異步協程架構，針對審查隊列與安全審計日誌執行快速的 Aggregate 查詢，為前端提供毫秒級的即時統計反饋。',
        provenance: '系統全局指標 (系統基礎能力支援)'
      }
    },
    {
      id: 'review',
      title: '案件審查隊列 (Review Queue)',
      subtitle: 'AI 義務抽取之人工核准與審查終端',
      icon: ShieldAlert,
      badge: { text: '人機協同', type: 'warning' },
      summary: '為了保障法律法規詮釋的嚴謹性，系統不會在未經授權下自動修改核心圖譜。此頁面實作了「人機協作 (Human-in-the-Loop)」防線，將大模型從法規中抽取的 Obligation (合規義務項目) 呈遞給合規官做最終的人工「核准」或「否決」。',
      steps: [
        '在列表中選擇一項待審查的合規義務項目（Pending Review）。',
        '在右側詳情面板中，核對 AI 抽取的義務內容、實體關聯、以及其精確的法規溯源條款。',
        '點擊「核准導入」將該義務編譯寫入 Neo4j 圖譜；或點擊「否決」將其退回並記錄審查痕跡。'
      ],
      techSpec: {
        engine: 'RESTful Schema 白名單強校驗與人機審查接口',
        details: '所有審查決策經由 Pydantic 強型別進行白名單白盒化校驗，確保入庫數據無 SQL 或 Cypher 注入風險。人工審查邊界機制保障了法律合規的最高詮釋權始終留給合規官。',
        provenance: '合規人工審查邊界限制 (Human Review Guardrail)'
      }
    },
    {
      id: 'timeline',
      title: '防篡改稽核 (Audit Timeline)',
      subtitle: '基於密碼學哈希鏈的不可篡改日誌防線',
      icon: History,
      badge: { text: '密碼安全', type: 'success' },
      summary: '為應對外部審計與金融監管要求，本系統內建了一套高級的密碼學審計日誌鏈。任何系統操作（如法規導入、合規官核准/否決）都會被永久寫入該日誌鏈，且日誌鏈具備極強的防篡改自檢報警能力。',
      steps: [
        '檢視系統歷史操作時間線，每一條日誌都附帶其密碼學 Hash 簽名。',
        '點擊「驗證日誌鏈 (Verify Integrity)」按鈕，系統將從鏈頭至鏈尾逐一計算並核對雜湊值。',
        '若檢測到篡改，系統會立即使「系統完整性防盾」亮起紅色霓虹警報，並指出具體的篡改位置。'
      ],
      techSpec: {
        engine: 'Python hashlib SHA-256 密碼學哈希鏈 (Hash Chain)',
        details: '每條日誌的雜湊計算公式為：H(i) = SHA-256(H(i-1) + Data(i))。若有人直接修改數據庫中的操作紀錄，將因無法偽造後續所有節點的雜湊值而立刻曝露。',
        provenance: 'MAS Notice 626 內部稽核與資訊安全規範對齊'
      }
    },
    {
      id: 'graph',
      title: '法規可視化圖譜 (Regulatory Graph)',
      subtitle: '力導向交互式法規實體關係網絡',
      icon: Network,
      badge: { text: '知識圖譜', type: 'primary' },
      summary: '本系統的核心知識庫。它打破了傳統 RAG 資料破碎的限制，將法規（如 FATF, MAS 626）的條款、內控政策、金融產品、合規義務與風險實體，編譯成一張高度互聯的語意圖譜，供合規官直觀探索。',
      steps: [
        '在搜索框輸入法規關鍵字（如「CDD」或「KYC」），圖譜將高亮相關實體。',
        '使用滑鼠滾輪縮放圖譜，或拖曳節點改變布局。點擊節點可展開其關聯的合規項目與底層溯源資訊。',
        '右側資訊面板將動態呈現當前點選實體的完整合規鏈結。'
      ],
      techSpec: {
        engine: 'Neo4j 圖資料庫 & D3.js 力導向渲染',
        details: '底層使用 Neo4j NoSQL 屬性圖模型，配合高度優化的 Cypher 圖查詢語言進行多度關係檢索；前端使用 D3.js 的力學模擬器與 React 包裝進行流暢的高幀率關係網絡渲染。',
        provenance: '合規實體混合元模型架構 (ADR-0004 決策對齊)'
      }
    },
    {
      id: 'ingestion',
      title: '法規自主導入 (Ingestion Console)',
      subtitle: '拖曳 PDF 上傳與 AI 雙層防護編譯終端',
      icon: FileUp,
      badge: { text: 'AI 編譯', type: 'danger' },
      summary: '本系統引以為傲的法規自主編譯中心。合規官可在此直接上傳金融監管機構發布的法規 PDF（例如 MAS 626 Notice）。系統將會啟動尖端的 AI 雙層抽取防線，實時將非結構化的法規文本編譯為結構化的合規條款物件。',
      steps: [
        '將合規 PDF 拖放至發光上傳區域，或點擊選擇檔案。',
        '上傳成功後，右側的「炫彩終端 (Neon Terminal)」會實時滾動輸出 AI 的處理日誌與分析進度。',
        '處理完畢後，系統會將抽取的合規項目送入「案件審查隊列」等待您的核准。'
      ],
      techSpec: {
        engine: 'NVIDIA NIM 平台 & DeepSeek V4 Pro 雙層防護抽取',
        details: '1. PyPDF 跨行拼寫平滑重組：消除非結構化 PDF 的排版噪聲。\n2. Llama 3.3 (meta/llama-3.3-70b-instruct) 智慧樹狀分片：確保語意上下文的完整性。\n3. DeepSeek V4 Pro (deepseek-ai/deepseek-v4-pro) 雙層嚴格結構化抽取：依據 Pydantic 強型別 Schema 輸出，具備極高的推理精準度與 Clause 級溯源能力。',
        provenance: '條款級溯源規範對齊 (FATF Recommendation 10, MAS Notice 626)'
      }
    }
  ];

  return (
    <div style={styles.container}>
      {/* 頂部標題與核心架構 */}
      <div style={styles.headerSection}>
        <div style={styles.titleWrapper}>
          <BookOpen size={36} style={{ color: 'var(--primary)', filter: 'drop-shadow(0 0 10px var(--primary-glow))' }} />
          <h1 className="display-title" style={styles.mainTitle}>系統使用教學手冊</h1>
        </div>
        <p style={styles.subtitle}>
          歡迎使用 CDD-GraphWiki 合規知識編譯與推理平台。本手冊旨在引導您掌握系統的五大核心模組，並理解其背後的卓越技術實力。
        </p>

        {/* 核心理念：防範通用 RAG 宣示 */}
        <div style={styles.philosophyCard}>
          <div style={styles.philosophyHeader}>
            <ShieldCheck size={20} style={{ color: 'var(--primary)' }} />
            <h3 style={styles.philosophyTitle}>核心設計哲學：編譯型合規 (Compiled Compliance)</h3>
          </div>
          <p style={styles.philosophyText}>
            🛡️ <strong>本系統絕非通用的「PDF 聊天機器人 (RAG)」！</strong> 傳統的 RAG 僅對文本做向量切割，無法理解法規間的嚴謹邏輯，極易產生幻覺。
            <br />
            CDD-GraphWiki 採用先進的<strong>知識圖譜編譯與推理架構</strong>，將非結構化條款編譯為具備<strong>條款級溯源 (Clause-level Provenance)</strong>的語意對象，並通過人工審查安全邊界，真正實現金融級的嚴謹合規推理。
          </p>
        </div>
      </div>

      {/* 系統核心數據編譯流 */}
      <div className="glass-card" style={styles.flowCard}>
        <h3 style={styles.sectionTitle}>
          <Layers size={18} style={{ color: 'var(--primary)' }} />
          系統核心數據合規編譯流 (Data Compilation Pipeline)
        </h3>
        
        <div style={styles.pipelineContainer}>
          {[
            { step: '1', title: '法規 PDF 導入', desc: 'Ingestion Console 拖曳上傳，PyPDF 平滑重組', icon: FileUp },
            { step: '2', title: '大模型智慧切片', desc: 'Llama 3.3 進行高品質樹狀分片與上下文保留', icon: Cpu },
            { step: '3', title: '條款雙層抽取', desc: 'DeepSeek V4 Pro 嚴格 Schema 抽取與 Clause 級溯源', icon: Cpu },
            { step: '4', title: '人機核准邊界', desc: 'Review Queue 合規官人工決策，核准 / 否決', icon: ShieldAlert },
            { step: '5', title: '圖譜與安全日誌', desc: 'Neo4j 語意編譯入庫，SHA-256 哈希日誌防篡改鎖定', icon: History }
          ].map((node, index, arr) => (
            <React.Fragment key={index}>
              <div style={styles.pipelineNode}>
                <div style={styles.nodeStepBadge}>{node.step}</div>
                <div style={styles.nodeContent}>
                  <div style={styles.nodeTitle}>
                    <node.icon size={14} style={{ color: 'var(--primary)', marginRight: 6 }} />
                    {node.title}
                  </div>
                  <div style={styles.nodeDesc}>{node.desc}</div>
                </div>
              </div>
              {index < arr.length - 1 && (
                <div style={styles.pipelineArrow}>
                  <span style={styles.arrowGlow}>➔</span>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 互動式 Accordion 摺疊面板 */}
      <div style={styles.accordionContainer}>
        <h2 style={styles.accordionMainTitle}>
          <Cpu size={22} style={{ color: 'var(--primary)' }} />
          分頁模組功能與使用指南
        </h2>

        <div style={styles.accordionList}>
          {sections.map((section) => {
            const Icon = section.icon;
            const isOpen = activeSection === section.id;
            
            // 根據 badge 的 type 設定色彩
            let badgeStyle = {};
            if (section.badge.type === 'primary') badgeStyle = styles.badgePrimary;
            else if (section.badge.type === 'success') badgeStyle = styles.badgeSuccess;
            else if (section.badge.type === 'warning') badgeStyle = styles.badgeWarning;
            else if (section.badge.type === 'danger') badgeStyle = styles.badgeDanger;

            return (
              <div 
                key={section.id} 
                className="glass-card" 
                style={{
                  ...styles.accordionItem,
                  borderColor: isOpen ? 'rgba(0, 242, 254, 0.35)' : 'rgba(255, 255, 255, 0.08)',
                  boxShadow: isOpen ? '0 12px 40px 0 rgba(0, 242, 254, 0.15)' : '0 8px 32px 0 rgba(0, 0, 0, 0.4)'
                }}
              >
                {/* 標題頭部（可點擊摺疊） */}
                <div 
                  onClick={() => toggleSection(section.id)}
                  style={styles.accordionHeader}
                >
                  <div style={styles.accordionHeaderLeft}>
                    <div style={{
                      ...styles.iconWrapper,
                      background: isOpen ? 'linear-gradient(135deg, rgba(0,242,254,0.15), rgba(79,172,254,0.15))' : 'rgba(255, 255, 255, 0.03)',
                      borderColor: isOpen ? 'rgba(0, 242, 254, 0.4)' : 'rgba(255, 255, 255, 0.1)'
                    }}>
                      <Icon size={20} style={{ color: isOpen ? 'var(--primary)' : 'var(--text-muted)' }} />
                    </div>
                    <div>
                      <div style={styles.accordionTitleRow}>
                        <h3 style={{
                          ...styles.accordionItemTitle,
                          color: isOpen ? '#ffffff' : 'var(--text-primary)'
                        }}>{section.title}</h3>
                        <span style={{ ...styles.badgeBase, ...badgeStyle }}>{section.badge.text}</span>
                      </div>
                      <p style={styles.accordionItemSubtitle}>{section.subtitle}</p>
                    </div>
                  </div>
                  <div>
                    {isOpen ? (
                      <ChevronUp size={20} style={{ color: 'var(--primary)' }} />
                    ) : (
                      <ChevronDown size={20} style={{ color: 'var(--text-muted)' }} />
                    )}
                  </div>
                </div>

                {/* 內容區（帶動畫與毛玻璃過渡） */}
                {isOpen && (
                  <div style={styles.accordionContent}>
                    <div style={styles.divider} />
                    
                    <div style={styles.contentGrid}>
                      {/* 功能說明與步驟 */}
                      <div style={styles.leftCol}>
                        <div style={styles.infoSection}>
                          <h4 style={styles.contentSectionTitle}>
                            <CheckCircle2 size={15} style={{ color: 'var(--primary)', marginRight: 6 }} />
                            功能簡介
                          </h4>
                          <p style={styles.summaryText}>{section.summary}</p>
                        </div>

                        <div style={styles.infoSection}>
                          <h4 style={styles.contentSectionTitle}>
                            <Cpu size={15} style={{ color: 'var(--primary)', marginRight: 6 }} />
                            合規官操作指南
                          </h4>
                          <ul style={styles.stepsList}>
                            {section.steps.map((step, idx) => (
                              <li key={idx} style={styles.stepItem}>
                                <span style={styles.stepNumber}>{idx + 1}</span>
                                <span style={styles.stepText}>{step}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* 底層核心技術簡述 */}
                      <div style={styles.rightCol}>
                        <div style={styles.techCard}>
                          <div style={styles.techHeader}>
                            <Cpu size={16} style={{ color: 'var(--primary)' }} />
                            <h4 style={styles.techTitle}>底層核心技術簡述</h4>
                          </div>
                          
                          <div style={styles.techMeta}>
                            <span style={styles.techLabel}>引擎名稱：</span>
                            <span style={styles.techValue}>{section.techSpec.engine}</span>
                          </div>

                          <div style={styles.techMeta} className="form-group">
                            <span style={styles.techLabel}>實現細節：</span>
                            <p style={styles.techDetails}>{section.techSpec.details}</p>
                          </div>

                          <div style={styles.techProvenance}>
                            <span style={styles.provenanceTag}>法規溯源基準：</span>
                            <p style={styles.provenanceValue}>{section.techSpec.provenance}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '12px 24px',
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '32px'
  },
  headerSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px'
  },
  titleWrapper: {
    display: 'flex',
    alignItems: 'center',
    gap: '14px'
  },
  mainTitle: {
    fontSize: '2.2rem',
    fontWeight: 800
  },
  subtitle: {
    fontSize: '1.05rem',
    color: 'var(--text-muted)',
    lineHeight: 1.6
  },
  philosophyCard: {
    background: 'rgba(0, 242, 254, 0.04)',
    border: '1px solid rgba(0, 242, 254, 0.15)',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 4px 20px rgba(0, 242, 254, 0.03)',
    marginTop: '8px'
  },
  philosophyHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    marginBottom: '10px'
  },
  philosophyTitle: {
    fontSize: '1.05rem',
    fontWeight: 700,
    color: '#ffffff',
    fontFamily: 'var(--font-display)'
  },
  philosophyText: {
    fontSize: '0.92rem',
    color: 'var(--text-muted)',
    lineHeight: 1.7
  },
  flowCard: {
    padding: '24px',
    background: 'rgba(18, 20, 30, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '16px'
  },
  sectionTitle: {
    fontSize: '1.15rem',
    fontWeight: 700,
    color: '#ffffff',
    marginBottom: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontFamily: 'var(--font-display)'
  },
  pipelineContainer: {
    display: 'flex',
    flexDirection: 'row' as const,
    alignItems: 'stretch',
    gap: '12px',
    overflowX: 'auto' as const,
    paddingBottom: '8px'
  },
  pipelineNode: {
    flex: 1,
    minWidth: '180px',
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px',
    position: 'relative' as const
  },
  nodeStepBadge: {
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    color: 'var(--text-dark)',
    fontSize: '0.75rem',
    fontWeight: 800,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute' as const,
    top: '-8px',
    left: '-8px',
    boxShadow: '0 0 8px var(--primary-glow)'
  },
  nodeContent: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px'
  },
  nodeTitle: {
    fontSize: '0.9rem',
    fontWeight: 700,
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center'
  },
  nodeDesc: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    lineHeight: 1.4
  },
  pipelineArrow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'rgba(0, 242, 254, 0.3)',
    fontWeight: 800,
    fontSize: '1.2rem'
  },
  arrowGlow: {
    textShadow: '0 0 8px var(--primary-glow)',
    animation: 'pulse-glow 2s infinite ease-in-out'
  },
  accordionContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px'
  },
  accordionMainTitle: {
    fontSize: '1.4rem',
    fontWeight: 700,
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontFamily: 'var(--font-display)'
  },
  accordionList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '16px'
  },
  accordionItem: {
    padding: '0px',
    overflow: 'hidden',
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)'
  },
  accordionHeader: {
    padding: '20px 24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    cursor: 'pointer',
    userSelect: 'none' as const
  },
  accordionHeaderLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  iconWrapper: {
    width: '44px',
    height: '44px',
    borderRadius: '10px',
    border: '1px solid',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease'
  },
  accordionTitleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  accordionItemTitle: {
    fontSize: '1.05rem',
    fontWeight: 700,
    fontFamily: 'var(--font-display)',
    transition: 'color 0.2s ease'
  },
  badgeBase: {
    fontSize: '0.7rem',
    fontWeight: 700,
    padding: '2px 8px',
    borderRadius: '99px',
    letterSpacing: '0.03em'
  },
  badgePrimary: {
    background: 'rgba(0, 242, 254, 0.1)',
    color: 'var(--primary)',
    border: '1px solid rgba(0, 242, 254, 0.25)',
    boxShadow: '0 0 8px rgba(0, 242, 254, 0.08)'
  },
  badgeSuccess: {
    background: 'rgba(0, 230, 118, 0.1)',
    color: 'var(--success)',
    border: '1px solid rgba(0, 230, 118, 0.25)',
    boxShadow: '0 0 8px rgba(0, 230, 118, 0.08)'
  },
  badgeWarning: {
    background: 'rgba(255, 179, 0, 0.1)',
    color: 'var(--warning)',
    border: '1px solid rgba(255, 179, 0, 0.25)',
    boxShadow: '0 0 8px rgba(255, 179, 0, 0.08)'
  },
  badgeDanger: {
    background: 'rgba(255, 23, 68, 0.1)',
    color: 'var(--danger)',
    border: '1px solid rgba(255, 23, 68, 0.25)',
    boxShadow: '0 0 8px rgba(255, 23, 68, 0.08)'
  },
  accordionItemSubtitle: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    marginTop: '4px'
  },
  accordionContent: {
    padding: '0 24px 24px 24px',
    animation: 'fadeIn 0.3s ease'
  },
  divider: {
    height: '1px',
    background: 'rgba(255, 255, 255, 0.06)',
    marginBottom: '20px'
  },
  contentGrid: {
    display: 'grid',
    gridTemplateColumns: '1.2fr 1fr',
    gap: '24px'
  },
  leftCol: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '20px'
  },
  rightCol: {
    display: 'flex',
    flexDirection: 'column' as const
  },
  infoSection: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px'
  },
  contentSectionTitle: {
    fontSize: '0.9rem',
    fontWeight: 700,
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    fontFamily: 'var(--font-display)'
  },
  summaryText: {
    fontSize: '0.88rem',
    color: 'var(--text-muted)',
    lineHeight: 1.6
  },
  stepsList: {
    listStyle: 'none',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px'
  },
  stepItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '10px'
  },
  stepNumber: {
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    background: 'rgba(0, 242, 254, 0.12)',
    border: '1px solid rgba(0, 242, 254, 0.3)',
    color: 'var(--primary)',
    fontSize: '0.72rem',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: '2px'
  },
  stepText: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
    flex: 1
  },
  techCard: {
    background: 'rgba(0, 0, 0, 0.25)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    borderRadius: '12px',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '14px',
    height: '100%'
  },
  techHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
    paddingBottom: '10px',
    marginBottom: '2px'
  },
  techTitle: {
    fontSize: '0.9rem',
    fontWeight: 700,
    color: '#ffffff',
    fontFamily: 'var(--font-display)'
  },
  techMeta: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px'
  },
  techLabel: {
    fontSize: '0.78rem',
    color: 'var(--text-muted)',
    fontWeight: 500
  },
  techValue: {
    fontSize: '0.85rem',
    color: 'var(--primary)',
    fontWeight: 600,
    fontFamily: 'var(--font-display)'
  },
  techDetails: {
    fontSize: '0.8rem',
    color: 'var(--text-muted)',
    lineHeight: 1.5,
    whiteSpace: 'pre-line' as const
  },
  techProvenance: {
    marginTop: 'auto',
    paddingTop: '12px',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px'
  },
  provenanceTag: {
    fontSize: '0.72rem',
    color: 'rgba(255, 255, 255, 0.3)',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.02em'
  },
  provenanceValue: {
    fontSize: '0.78rem',
    color: 'var(--secondary)',
    fontWeight: 500
  }
};
