import React from 'react';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  History, 
  Network,
  FileUp,
  BookOpen,
  ShieldAlert as ShieldIcon
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount: number;
  isLogsIntact: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  activeTab, 
  setActiveTab,
  pendingCount,
  isLogsIntact
}) => {
  const menuItems = [
    { id: 'dashboard', label: '工作台總覽', icon: LayoutDashboard },
    { id: 'review', label: '案件審查隊列', icon: ShieldAlert, badge: pendingCount > 0 ? pendingCount : undefined },
    { id: 'timeline', label: '防篡改稽核', icon: History, statusDot: true },
    { id: 'graph', label: '法規可視化圖譜', icon: Network },
    { id: 'ingestion', label: '法規自主導入', icon: FileUp },
    { id: 'guide', label: '系統使用手冊', icon: BookOpen },
  ];

  return (
    <aside style={styles.sidebar}>
      {/* 標題區域 */}
      <div style={styles.brandContainer}>
        <div style={styles.logoWrapper}>
          <span style={styles.logoIcon}>🛡️</span>
        </div>
        <div style={styles.brandText}>
          <h2 style={styles.brandTitle}>GraphWiki</h2>
          <span style={styles.brandSubtitle}>Compliance Suite</span>
        </div>
      </div>

      {/* 系統完整性徽章 */}
      <div style={styles.integrityPanel}>
        <div style={{
          ...styles.integrityStatus,
          color: isLogsIntact ? 'var(--success)' : 'var(--danger)'
        }}>
          <span style={{
            ...styles.statusDot,
            backgroundColor: isLogsIntact ? 'var(--success)' : 'var(--danger)',
            boxShadow: isLogsIntact ? '0 0 8px var(--success)' : '0 0 8px var(--danger)'
          }} />
          <span style={styles.integrityText}>
            {isLogsIntact ? '日誌鏈：未受篡改' : '警告：檢測到篡改'}
          </span>
        </div>
      </div>

      {/* 導航選單 */}
      <nav style={styles.navMenu}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {})
              }}
              className="nav-hover-effect"
            >
              <div style={styles.navItemLeft}>
                <Icon size={18} style={isActive ? { color: 'var(--primary)' } : { color: 'var(--text-muted)' }} />
                <span style={{
                  ...styles.navLabel,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-muted)'
                }}>{item.label}</span>
              </div>
              
              {item.badge !== undefined && (
                <span style={styles.badgeCount}>{item.badge}</span>
              )}

              {item.id === 'timeline' && (
                <span style={{
                  ...styles.integrityMiniDot,
                  backgroundColor: isLogsIntact ? 'var(--success)' : 'var(--danger)'
                }} />
              )}
            </button>
          );
        })}
      </nav>

      {/* 頁腳 */}
      <div style={styles.sidebarFooter}>
        <span style={styles.version}>v1.0.0 (Production)</span>
      </div>
    </aside>
  );
};

const styles = {
  sidebar: {
    width: '280px',
    background: 'rgba(11, 12, 16, 0.8)',
    borderRight: '1px solid rgba(255, 255, 255, 0.08)',
    display: 'flex',
    flexDirection: 'column' as const,
    padding: '24px',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    height: '100vh',
    position: 'sticky' as const,
    top: 0,
  },
  brandContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '32px',
  },
  logoWrapper: {
    width: '42px',
    height: '42px',
    borderRadius: '12px',
    background: 'linear-gradient(135deg, rgba(0,242,254,0.1), rgba(79,172,254,0.1))',
    border: '1px solid rgba(0, 242, 254, 0.25)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 4px 12px rgba(0, 242, 254, 0.1)',
  },
  logoIcon: {
    fontSize: '22px',
  },
  brandText: {
    display: 'flex',
    flexDirection: 'column' as const,
  },
  brandTitle: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.25rem',
    fontWeight: 700,
    letterSpacing: '-0.02em',
    color: '#ffffff',
  },
  brandSubtitle: {
    fontFamily: 'var(--font-sans)',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  integrityPanel: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '10px',
    padding: '10px 14px',
    marginBottom: '28px',
  },
  integrityStatus: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.8rem',
    fontWeight: 600,
  },
  statusDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
  },
  integrityText: {
    fontFamily: 'var(--font-sans)',
  },
  navMenu: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
    flex: 1,
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: '12px',
    paddingRight: '16px',
    paddingBottom: '12px',
    paddingLeft: '16px',
    borderRadius: '10px',
    background: 'transparent',
    borderTop: 'none',
    borderRight: 'none',
    borderBottom: 'none',
    borderLeft: '3px solid transparent',
    cursor: 'pointer',
    width: '100%',
    textAlign: 'left' as const,
    transition: 'all 0.2s ease',
  },
  navItemActive: {
    background: 'rgba(0, 242, 254, 0.08)',
    borderLeft: '3px solid var(--primary)',
    paddingLeft: '13px',
  },
  navItemLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  navLabel: {
    fontSize: '0.9rem',
    fontWeight: 500,
    fontFamily: 'var(--font-sans)',
  },
  badgeCount: {
    background: 'var(--danger)',
    color: '#ffffff',
    fontSize: '0.75rem',
    fontWeight: 700,
    padding: '2px 8px',
    borderRadius: '99px',
    boxShadow: '0 0 10px rgba(255, 23, 68, 0.4)',
  },
  integrityMiniDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  sidebarFooter: {
    paddingTop: '16px',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
  },
  version: {
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-sans)',
  }
};
