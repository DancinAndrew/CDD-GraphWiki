import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { DashboardHome } from './pages/DashboardHome';
import { ReviewQueue } from './pages/ReviewQueue';
import { AuditTimeline } from './pages/AuditTimeline';
import { InteractiveGraph } from './components/InteractiveGraph';
import { IngestionConsole } from './components/IngestionConsole';
import { UserGuide } from './components/UserGuide';

function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [isLogsIntact, setIsLogsIntact] = useState<boolean>(true);
  const [logsCount, setLogsCount] = useState<number>(0);

  // 獲取全局合規統計狀態
  const fetchGlobalStats = () => {
    // 1. 抓取待人工審查案件數
    fetch('http://localhost:8000/api/v1/cases?status=pending_review')
      .then(res => res.json())
      .then(data => {
        setPendingCount(data.length);
      })
      .catch(err => console.error('Error fetching pending cases count:', err));

    // 2. 抓取防篡改自檢健全狀態
    fetch('http://localhost:8000/api/v1/audit/verify')
      .then(res => res.json())
      .then(data => {
        setIsIntactState(data.is_intact);
        setLogsCount(data.total_entries);
      })
      .catch(err => console.error('Error verifying integrity:', err));
  };

  // 獨立包裹，防止 verify 和 logs 狀態在未掛載時出錯
  const setIsIntactState = (val: boolean) => {
    setIsLogsIntact(val);
  };

  useEffect(() => {
    fetchGlobalStats();
    
    // 每隔 10 秒自動同步一下（實時感）
    const interval = setInterval(fetchGlobalStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <DashboardHome 
            onNavigate={setActiveTab} 
            pendingCount={pendingCount}
            isLogsIntact={isLogsIntact}
            logsCount={logsCount}
          />
        );
      case 'review':
        return (
          <ReviewQueue 
            onReviewSubmitted={fetchGlobalStats}
          />
        );
      case 'timeline':
        return (
          <AuditTimeline 
            isIntact={isLogsIntact}
            setIsIntact={setIsLogsIntact}
            setLogsCount={setLogsCount}
          />
        );
      case 'graph':
        return <InteractiveGraph />;
      case 'ingestion':
        return <IngestionConsole onNavigate={setActiveTab} />;
      case 'guide':
        return <UserGuide />;
      default:
        return (
          <DashboardHome 
            onNavigate={setActiveTab} 
            pendingCount={pendingCount}
            isLogsIntact={isLogsIntact}
            logsCount={logsCount}
          />
        );
    }
  };

  return (
    <div className="app-layout">
      {/* 玻璃磨砂側邊導航欄 */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        pendingCount={pendingCount}
        isLogsIntact={isLogsIntact}
      />

      {/* 主體展示區域 */}
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
