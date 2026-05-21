# 加強型盡職調查 (Enhanced Due Diligence, EDD) 程序

加強型盡職調查 (EDD) 是一種針對被評估為具有**高洗錢或資助恐怖主義風險**的客戶所適用的深層 KYC 程序。相較於標準的 CDD，EDD 要求金融機構收集更廣泛、更深層的背景資料，並對交易進行更頻繁的持續監控，以有效緩釋高風險因素。

## 1. EDD 觸發因素 (Triggers)

當客戶滿足以下任一 factual 條件時，系統必須自動或由合規人員手動觸發 EDD：

- **客戶身份屬性**：被識別為政治曝險人物 (PEP) 或其關係密切者。
- **地理與管轄區風險**：客戶註冊地位於、或主要業務關聯於受 FATF 黑名單/灰名單制裁之高風險管轄區。
- **複雜股權與 layering**：法人客戶具有不尋常或極度複雜的多層股權結構，且無明顯之合理商業理由。
- **交易異常與可疑跡象**：發生大額、異常、無明顯經濟或合法目的之偶發交易，或發現先前獲得的 KYC 資料存在重大疑慮。

## 2. EDD 核心執行步驟

執行 EDD 時，合規團隊必須完成並留存以下「黃金核對清單」：

| 步驟 | 具體執行行動 (Action Elements) | 必備佐證/證據 (Required Evidence) |
|---|---|---|
| **1. 管理層簽核** | 取得高級管理人員的正式書面核准。 | Senior Management Sign-off Form |
| **2. 財富來源驗證 (SoW)** | 調查並核實客戶的整體財富是如何積累的（例如繼承、企業經營利潤、投資回報等）。 | 稅單、審計財務報表、股權出售協議、土地權狀等 |
| **3. 資金來源驗證 (SoF)** | 驗證具體開戶資金或重大交易所用資金的合法來源。 | 銀行流水對帳單、交易結算憑證 |
| **4. UBO 深度穿透** | 對股權結構進行無死角穿透，追溯至自然人，或判定其背後控制協議。 | 完整持股架構圖、合夥契約、UBO 身份證明 |
| **5. 持續增強型監控** | 提高該帳戶的交易覆蓋審查頻率，通常為每半年（或更短時間）重新評估。 | 交易監控警示審查記錄、定期覆蓋覆核單 |

## 3. 防禦性合規控制

> [!IMPORTANT]
> - **拒絕交易權限**：如果客戶拒絕提供、或金融機構無法在合理時間內驗證完成 EDD 所需的關鍵證據（如 SoW/SoF 佐證文件），金融機構**必須 (MUST)** 停止開戶、暫停或終止該業務關係，並考慮向監管當局提交可疑交易報告 (STR/STR Form)。
- **兩級簽核 (Double Sign-off)**：在 Global Bank 的實踐中，任何 PEP 客戶或高風險客戶的 onboard 必須經過 Compliance Manager 與 Business Head 的雙重共同核簽，單一經辦人員無權單獨核准。

## 4. 溯源條款對照

- **FATF Rec 10**: [Recommendation 10, Paragraph 3 & Interpretive Note](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/data/gold/clauses.yaml#L21-L32)
- **MAS Notice 626**: [Paragraph 7.2](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/data/gold/clauses.yaml#L81-L92)
- **Global Bank Policy**: [Section 4.5.3](file:///Users/andrew-ideaslab/Documents/CDD-GraphWiki/data/gold/clauses.yaml#L105-L116)
