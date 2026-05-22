import React, { useState } from 'react';
import { ShieldCheck, ShieldAlert, Shield } from 'lucide-react';

interface TamperShieldProps {
  isIntact: boolean;
  onVerifyRequested: () => Promise<{ is_intact: boolean; total_entries: number; tampered_index: number }>;
}

export const TamperShield: React.FC<TamperShieldProps> = ({ isIntact, onVerifyRequested }) => {
  const [verifying, setVerifying] = useState(false);
  const [statusText, setStatusText] = useState<'idle' | 'success' | 'failed'>('idle');
  const [tamperedIdx, setTamperedIdx] = useState<number | null>(null);

  const handleShieldClick = async () => {
    if (verifying) return;
    setVerifying(true);
    setStatusText('idle');
    setTamperedIdx(null);

    // 延遲 800ms，製造出高科技計算與驗證的科幻感
    setTimeout(async () => {
      try {
        const result = await onVerifyRequested();
        if (result.is_intact) {
          setStatusText('success');
        } else {
          setStatusText('failed');
          setTamperedIdx(result.tampered_index);
        }
      } catch (err) {
        console.error('Verify failed:', err);
        setStatusText('failed');
      } finally {
        setVerifying(false);
      }
    }, 900);
  };

  const getShieldColor = () => {
    if (verifying) return 'var(--primary)';
    if (statusText === 'success' || (statusText === 'idle' && isIntact)) return 'var(--success)';
    if (statusText === 'failed' || !isIntact) return 'var(--danger)';
    return 'var(--text-muted)';
  };

  const getGlowClass = () => {
    if (verifying) return 'pulse-primary';
    if (statusText === 'success' || (statusText === 'idle' && isIntact)) return 'pulse-success';
    if (statusText === 'failed' || !isIntact) return 'pulse-danger';
    return '';
  };

  return (
    <div style={styles.container}>
      <div 
        onClick={handleShieldClick}
        style={{
          ...styles.shieldCircle,
          borderColor: getShieldColor(),
          cursor: verifying ? 'default' : 'pointer'
        }}
        className={getGlowClass()}
      >
        <div style={styles.innerCircle}>
          {verifying ? (
            <Shield size={64} color="var(--primary)" style={styles.rotatingShield} />
          ) : (statusText === 'success' || (statusText === 'idle' && isIntact)) ? (
            <ShieldCheck size={64} color="var(--success)" />
          ) : (
            <ShieldAlert size={64} color="var(--danger)" />
          )}
        </div>
      </div>

      <div style={styles.textContainer}>
        <h3 style={styles.title}>
          {verifying ? '正在計算級聯 SHA-256 哈希鏈...' : 
           (statusText === 'success' || (statusText === 'idle' && isIntact)) ? '防篡改雜湊鏈 100% 健全' : 
           '警告！檢測到數據篡改破壞！'}
        </h3>
        <p style={styles.desc}>
          {verifying ? '穿透校驗歷史決策日誌、人工覆寫雜湊、以及 Rule Version 錨定...' : 
           (statusText === 'success' || (statusText === 'idle' && isIntact)) ? '點擊盾牌可實時觸發完整前向鏈式誠信校驗自檢' : 
           `哈希鏈在第 #${tamperedIdx !== null ? tamperedIdx : '?'} 筆日誌處斷裂。數據遭到非法篡改！`}
        </p>
        
        {!verifying && (
          <button 
            onClick={handleShieldClick}
            style={{
              ...styles.verifyBtn,
              background: verifying ? 'rgba(255,255,255,0.05)' : 'transparent',
              color: getShieldColor(),
              borderColor: getShieldColor()
            }}
          >
            {verifying ? '計算校驗中...' : '實時觸發誠信度自檢'}
          </button>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
    padding: '30px',
    background: 'rgba(255,255,255,0.01)',
    borderRadius: '20px',
    border: '1px solid rgba(255,255,255,0.04)',
    textAlign: 'center' as const,
  },
  shieldCircle: {
    width: '140px',
    height: '140px',
    borderRadius: '50%',
    border: '3px solid',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.3s ease',
    background: 'rgba(0,0,0,0.3)',
  },
  innerCircle: {
    width: '110px',
    height: '110px',
    borderRadius: '50%',
    background: 'rgba(18, 20, 30, 0.9)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: 'inset 0 0 20px rgba(0,0,0,0.8)',
  },
  rotatingShield: {
    animation: 'spin 2s linear infinite',
  },
  textContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    gap: '8px',
  },
  title: {
    fontFamily: 'var(--font-display)',
    fontSize: '1.25rem',
    fontWeight: 700,
  },
  desc: {
    fontSize: '0.85rem',
    color: 'var(--text-muted)',
    maxWidth: '320px',
    lineHeight: '1.4',
  },
  verifyBtn: {
    background: 'transparent',
    border: '1px solid',
    borderRadius: '20px',
    padding: '6px 20px',
    fontSize: '0.8rem',
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: '8px',
    transition: 'all 0.2s',
  }
};
