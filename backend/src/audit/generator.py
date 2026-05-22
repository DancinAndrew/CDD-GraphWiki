import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.contracts.models import CustomerContext, CDDChecklist, ReviewCase, AuditLogEntry
from src.audit.logger import AuditLogger

class AuditReportGenerator:
    """
    合規稽核審計報告生成器 AuditReportGenerator。
    提供一鍵導出客戶的完整合規稽核包，支持 Markdown 報告與極具現代感的暗黑磨砂玻璃美學 (Dark Glassmorphic UI) HTML 報告，
    並對客戶 PII 敏感數據進行脫敏，展示決策 Citation 溯源與防篡改日誌鏈自檢簽名。
    """
    def __init__(self, logger: AuditLogger):
        """
        初始化報告生成器。
        :param logger: 關聯的 AuditLogger 實例，用以讀取日誌鏈並檢驗其完整性。
        """
        self.logger = logger

    def redact_id(self, text: str) -> str:
        """
        對敏感個資 (PII) 如客戶 ID 或其他敏感資料進行脫敏去識別化。
        例如 "cust_individual_pep" -> "CUST-INDIV-****-PEP" 或 "cust_01" -> "CUST****01"
        """
        if not text:
            return ""
        if text.startswith("cust_"):
            parts = text.split("_")
            if len(parts) >= 2:
                # 企業或個人類別遮罩
                category = parts[1].upper()
                if len(parts) > 2:
                    suffix = parts[-1].upper()
                    return f"CUST-{category}-****-{suffix}"
                return f"CUST-****-{category}"
            return f"CUST-****-{text[-2:]}"
        return text

    def _generate_markdown(
        self,
        customer: CustomerContext,
        checklist: CDDChecklist,
        review_case: Optional[ReviewCase] = None,
        integrity_ok: bool = True
    ) -> str:
        """
        內部生成 Markdown 格式的審計報告。
        """
        redacted_cust_id = self.redact_id(customer.customer_id)
        
        md = []
        md.append(f"# CDD 合規稽核審計報告 - 客戶 {redacted_cust_id}")
        md.append(f"*報告產出時間: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*")
        md.append("")
        
        md.append("## 1. 完整性自檢與合規簽名")
        status_emoji = "🟢 通過" if integrity_ok else "🔴 異常 (雜湊鏈斷裂)"
        md.append(f"- **防篡改審計鏈完整性驗證狀態**: {status_emoji}")
        md.append(f"- **系統審計日誌總條數**: {len(self.logger.entries)} 條")
        md.append("")
        
        md.append("## 2. 客戶合規畫像 (去敏感)")
        md.append(f"- **客戶標識**: `{redacted_cust_id}`")
        md.append(f"- **客戶類型**: `{customer.customer_type.upper()}`")
        md.append(f"- **註冊法域**: `{customer.registration_jurisdiction}`")
        md.append(f"- **股權嵌套層級**: `{customer.ownership_layers}` 層")
        md.append(f"- **UBO 身份確認**: `{customer.ubo_status.upper()}`")
        md.append(f"- **UBO 關聯國家風險**: `{customer.ubo_country_risk.upper()}`")
        md.append(f"- **政要曝險 (PEP Exposure)**: `{customer.pep_exposure}`")
        md.append(f"- **資金來源證明**: `{'已具備' if customer.source_of_funds_available else '未具備'}`")
        md.append(f"- **財富來源證明**: `{'已具備' if customer.source_of_wealth_available else '未具備'}`")
        md.append("")
        
        md.append("## 3. 最終合規檢核決策 (CDD Checklist)")
        decision_label = checklist.decision.upper().replace("_", " ")
        md.append(f"- **CDD 審批等級**: **`{decision_label}`**")
        md.append(f"- **是否需要人工介入審核**: `{'是' if checklist.human_review_required else '否'}`")
        md.append("")
        
        md.append("### 3.1 激活之風險觸發器 (Risk Triggers)")
        if checklist.risk_triggers:
            for trigger in checklist.risk_triggers:
                md.append(f"  - ⚠️ {trigger}")
        else:
            md.append("  - *無顯著風險觸發器*")
        md.append("")
        
        md.append("### 3.2 應收集之合規證據清單")
        if checklist.required_documents:
            for doc in checklist.required_documents:
                md.append(f"  - [ ] 📄 {doc}")
        else:
            md.append("  - *無特定文件要求*")
        md.append("")
        
        md.append("### 3.3 法規與政策法理溯源 (Citations)")
        if checklist.citations:
            for cit in checklist.citations:
                md.append(f"  - 🔗 {cit}")
        else:
            md.append("  - *無引用法源*")
        md.append("")

        if review_case:
            md.append("## 4. 人機協同人工審批詳情")
            md.append(f"- **審查案件 ID**: `{review_case.case_id}`")
            md.append(f"- **案件審批狀態**: **`{review_case.approval_status.upper()}`**")
            md.append(f"- **合規官最終決策**: `{review_case.reviewer_decision.upper() if review_case.reviewer_decision else '無'}`")
            md.append(f"- **合規官審批意見**: `\"{review_case.reviewer_notes or '無'}\"`")
            md.append(f"- **審批人簽名**: `{review_case.reviewed_by or '未分配'}`")
            md.append(f"- **審批操作時間**: `{review_case.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC`")
            md.append("")

        md.append("## 5. 防篡改審計鏈日誌細節 (Audit Trail)")
        md.append("| 日誌 ID | 時間戳 (UTC) | 事件類型 | 執行角色/模組 | 關聯客戶 | 雜湊值 (Current Hash) |")
        md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for entry in self.logger.entries:
            if entry.customer_id == customer.customer_id:
                redacted_entry_cust_id = self.redact_id(entry.customer_id)
                short_hash = f"{entry.current_hash[:8]}...{entry.current_hash[-8:]}"
                md.append(f"| `{entry.log_id}` | `{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}` | `{entry.event_type}` | `{entry.operator}` | `{redacted_entry_cust_id}` | `{short_hash}` |")
        
        return "\n".join(md)

    def _generate_html(
        self,
        customer: CustomerContext,
        checklist: CDDChecklist,
        review_case: Optional[ReviewCase] = None,
        integrity_ok: bool = True
    ) -> str:
        """
        內部生成暗黑磨砂玻璃美學 (Dark Glassmorphic UI) 的 HTML 稽核審計報告。
        """
        redacted_cust_id = self.redact_id(customer.customer_id)
        status_class = "status-pass" if integrity_ok else "status-fail"
        status_text = "完整性驗證通過 🟢" if integrity_ok else "鏈式雜湊損壞 🔴"
        
        # Risk triggers 渲染
        triggers_html = ""
        if checklist.risk_triggers:
            for t in checklist.risk_triggers:
                triggers_html += f'<div class="trigger-badge">⚠️ {t}</div>'
        else:
            triggers_html = '<span class="empty-text">無顯著風險觸發器</span>'
            
        # Required documents 渲染
        docs_html = ""
        if checklist.required_documents:
            for d in checklist.required_documents:
                docs_html += f'<li><span class="checkbox-box"></span> 📄 {d}</li>'
        else:
            docs_html = '<span class="empty-text">無特定文件要求</span>'
            
        # Citations 渲染
        citations_html = ""
        if checklist.citations:
            for c in checklist.citations:
                citations_html += f'<div class="citation-item">🔗 {c}</div>'
        else:
            citations_html = '<span class="empty-text">無法理引用</span>'
            
        # Review Case 渲染
        case_html = ""
        if review_case:
            decision_val = review_case.reviewer_decision.upper().replace("_", " ") if review_case.reviewer_decision else "PENDING"
            case_html = f"""
            <div class="glass-card neon-border-purple" style="margin-top: 30px;">
                <h2 style="color: #c084fc; border-bottom: 1px solid rgba(192, 132, 252, 0.2); padding-bottom: 10px; margin-top: 0;">🧑‍⚖️ 人機協同人工審查詳情</h2>
                <div class="info-grid">
                    <div class="info-item"><span class="info-label">審查案件 ID:</span> <span class="info-value text-purple">{review_case.case_id}</span></div>
                    <div class="info-item"><span class="info-label">案件審批狀態:</span> <span class="info-value status-badge badge-{review_case.approval_status}">{review_case.approval_status.upper()}</span></div>
                    <div class="info-item"><span class="info-label">合規官最終決策:</span> <span class="info-value text-purple" style="font-weight: bold;">{decision_val}</span></div>
                    <div class="info-item"><span class="info-label">審批操作人員:</span> <span class="info-value">{review_case.reviewed_by or '未分配'}</span></div>
                    <div class="info-item" style="grid-column: span 2;"><span class="info-label">合規審批意見:</span> <span class="info-value reviewer-notes">"{review_case.reviewer_notes or '無'}"</span></div>
                    <div class="info-item" style="grid-column: span 2;"><span class="info-label">審核完成時間:</span> <span class="info-value">{review_case.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC</span></div>
                </div>
            </div>
            """
            
        # Audit logs 渲染
        logs_html = ""
        for entry in self.logger.entries:
            if entry.customer_id == customer.customer_id:
                redacted_log_cust = self.redact_id(entry.customer_id)
                payload_pretty = json.dumps(entry.payload, indent=2, ensure_ascii=False)
                logs_html += f"""
                <tr class="log-row">
                    <td class="text-cyan">{entry.log_id}</td>
                    <td>{entry.timestamp.strftime('%H:%M:%S')}</td>
                    <td><span class="event-badge badge-{entry.event_type}">{entry.event_type}</span></td>
                    <td>{entry.operator}</td>
                    <td>{redacted_log_cust}</td>
                    <td class="font-mono hash-cell" title="{entry.current_hash}">{entry.current_hash[:12]}...{entry.current_hash[-12:]}</td>
                </tr>
                <tr class="payload-row" id="payload-{entry.log_id}">
                    <td colspan="6">
                        <pre class="payload-pre">{payload_pretty}</pre>
                    </td>
                </tr>
                """

        html_template = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDD 合規稽核審計報告 - 客戶 {redacted_cust_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: radial-gradient(circle at 50% 50%, #0d0f19, #050608);
            --glass-bg: rgba(17, 24, 39, 0.55);
            --glass-border: rgba(255, 255, 255, 0.08);
            --neon-blue: #06b6d4;
            --neon-green: #10b981;
            --neon-purple: #a855f7;
            --neon-red: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background: var(--bg-gradient);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            min-height: 100vh;
            padding: 40px 20px;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            position: relative;
        }}

        /* Glow effects in background */
        .glow-sphere-1 {{
            position: absolute;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
            top: -100px;
            left: -100px;
            z-index: -1;
            pointer-events: none;
        }}
        .glow-sphere-2 {{
            position: absolute;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.12) 0%, rgba(0, 0, 0, 0) 70%);
            bottom: 100px;
            right: -150px;
            z-index: -1;
            pointer-events: none;
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
            animation: fadeIn 1s ease-out;
        }}

        h1 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 2.2rem;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #fff 30%, #a5f3fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}

        .timestamp {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}

        /* Glassmorphism Cards */
        .glass-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(6, 182, 212, 0.1);
        }}

        /* Neon Borders */
        .neon-border-blue {{
            border-left: 5px solid var(--neon-blue);
        }}
        .neon-border-green {{
            border-left: 5px solid var(--neon-green);
        }}
        .neon-border-purple {{
            border-left: 5px solid var(--neon-purple);
        }}

        /* Integrity Header Card */
        .integrity-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 30px;
        }}

        .integrity-title {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .integrity-title h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.3rem;
            color: #fff;
        }}

        .status-badge {{
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .status-pass {{
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
        }}

        .status-fail {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
        }}

        /* Grid layouts */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px 30px;
        }}

        .info-item {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .info-label {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .info-value {{
            font-size: 1.05rem;
            font-weight: 500;
        }}

        .font-mono {{
            font-family: 'Courier New', Courier, monospace;
        }}

        .text-cyan {{ color: var(--neon-blue); }}
        .text-purple {{ color: #d8b4fe; }}
        
        .badge-pending_review {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .badge-approved {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .badge-rejected {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

        /* Checklist tier big display */
        .decision-display {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 25px;
        }}

        .decision-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* Document checklist */
        .doc-list {{
            list-style: none;
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .doc-list li {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.95rem;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }}

        .checkbox-box {{
            width: 16px;
            height: 16px;
            border: 1px solid var(--neon-blue);
            border-radius: 4px;
            background: rgba(6, 182, 212, 0.05);
        }}

        /* Risk triggers */
        .triggers-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }}

        .trigger-badge {{
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: #f87171;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        /* Citations list */
        .citation-container {{
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .citation-item {{
            font-size: 0.9rem;
            color: #a5f3fc;
            padding: 8px 12px;
            background: rgba(6, 182, 212, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(6, 182, 212, 0.1);
        }}

        .reviewer-notes {{
            font-style: italic;
            color: #e9d5ff;
            background: rgba(168, 85, 247, 0.05);
            padding: 10px 15px;
            border-radius: 8px;
            border-left: 3px solid var(--neon-purple);
            margin-top: 5px;
            display: inline-block;
            width: 100%;
        }}

        /* Table */
        .table-container {{
            width: 100%;
            overflow-x: auto;
            margin-top: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}

        th {{
            color: var(--text-muted);
            font-weight: 500;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.9rem;
        }}

        .log-row:hover {{
            background: rgba(255, 255, 255, 0.02);
            cursor: pointer;
        }}

        .event-badge {{
            font-size: 0.75rem;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .badge-reasoning_triggered {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
        .badge-case_created {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; }}
        .badge-case_reviewed {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; }}
        .badge-conflict_detected {{ background: rgba(239, 68, 68, 0.15); color: #f87171; }}

        .hash-cell {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        /* Details JSON code view */
        .payload-row {{
            background: rgba(0, 0, 0, 0.2);
        }}

        .payload-pre {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.8rem;
            color: #38bdf8;
            padding: 15px;
            overflow-x: auto;
            max-height: 200px;
            white-space: pre-wrap;
        }}

        .empty-text {{
            font-size: 0.9rem;
            color: var(--text-muted);
            font-style: italic;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @media (max-width: 768px) {{
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            .decision-display {{
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="glow-sphere-1"></div>
    <div class="glow-sphere-2"></div>
    
    <div class="container">
        <header>
            <h1>🛡️ CDD 合規稽核審計報告</h1>
            <div class="timestamp">報告產出時間: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
        </header>

        <!-- 完整性自檢 -->
        <div class="glass-card integrity-header {status_class}">
            <div class="integrity-title">
                <h2>🔐 防篡改審計鏈完整性自檢</h2>
            </div>
            <div class="status-badge {status_class}">
                {status_text}
            </div>
        </div>

        <div class="info-grid">
            <!-- 客戶情境 -->
            <div class="glass-card neon-border-blue">
                <h2 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; margin-bottom: 20px;">👤 客戶去敏感合規畫像</h2>
                <div class="info-grid" style="grid-template-columns: 1fr; gap: 15px;">
                    <div class="info-item"><span class="info-label">客戶識別標識:</span> <span class="info-value text-cyan font-mono">{redacted_cust_id}</span></div>
                    <div class="info-item"><span class="info-label">客戶主體類型:</span> <span class="info-value">{customer.customer_type.upper()}</span></div>
                    <div class="info-item"><span class="info-label">註冊及經營法域:</span> <span class="info-value">{customer.registration_jurisdiction}</span></div>
                    <div class="info-item"><span class="info-label">股權嵌套結構:</span> <span class="info-value">{customer.ownership_layers} 層</span></div>
                    <div class="info-item"><span class="info-label">UBO 實質受益人狀態:</span> <span class="info-value">{customer.ubo_status.upper()}</span></div>
                    <div class="info-item"><span class="info-label">UBO 國家風險評級:</span> <span class="info-value">{customer.ubo_country_risk.upper()}</span></div>
                    <div class="info-item"><span class="info-label">政治曝險人物 (PEP):</span> <span class="info-value">{"是" if customer.pep_exposure else "否"}</span></div>
                </div>
            </div>

            <!-- 合規決策 -->
            <div class="glass-card neon-border-green">
                <h2 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; margin-bottom: 20px;">📋 最終合規檢核決策</h2>
                <div class="decision-display">
                    <span class="decision-title">{checklist.decision.upper().replace("_", " ")}</span>
                    <span class="status-badge" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff;">
                        人工介入: {"是" if checklist.human_review_required else "否"}
                    </span>
                </div>
                
                <div class="info-item" style="margin-bottom: 15px;">
                    <span class="info-label">⚠️ 風險觸發因子:</span>
                    <div class="triggers-container">
                        {triggers_html}
                    </div>
                </div>

                <div class="info-item" style="margin-bottom: 15px;">
                    <span class="info-label">📄 應收集之合規證據:</span>
                    <ul class="doc-list">
                        {docs_html}
                    </ul>
                </div>
            </div>
        </div>

        <!-- 人工審批細節 -->
        {case_html}

        <!-- 決策法理溯源 -->
        <div class="glass-card" style="margin-top: 10px;">
            <h2 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 10px; margin-bottom: 15px;">🔗 條款級法理溯源與引用</h2>
            <div class="citation-container">
                {citations_html}
            </div>
        </div>

        <!-- 審計日誌列表 -->
        <div class="glass-card" style="margin-top: 10px;">
            <h2 style="font-family: 'Outfit', sans-serif; font-size: 1.3rem; margin-bottom: 20px;">⛓️ 防篡改鏈式審計日誌軌跡</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>日誌 ID</th>
                            <th>時間 (UTC)</th>
                            <th>事件類型</th>
                            <th>執行角色/模組</th>
                            <th>關聯客戶</th>
                            <th>防篡改哈希簽名</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html_template

    def generate_report_package(
        self,
        customer: CustomerContext,
        checklist: CDDChecklist,
        review_case: Optional[ReviewCase] = None
    ) -> Dict[str, str]:
        """
        一鍵生成完整的合規稽核包（包含 Markdown 與 HTML 格式報告）。
        它會自動校驗 AuditLogger 雜湊鏈的完整性。
        
        :param customer: 客戶情境
        :param checklist: 客戶的最終 Checklist
        :param review_case: 關聯的人機審查案件（若有）
        :return: 字典，包含 "markdown" 與 "html" 對應的報告字串內容。
        """
        # 校驗日誌鏈完整性
        integrity_ok = self.logger.verify_integrity()
        
        md_content = self._generate_markdown(customer, checklist, review_case, integrity_ok)
        html_content = self._generate_html(customer, checklist, review_case, integrity_ok)
        
        return {
            "markdown": md_content,
            "html": html_content
        }
