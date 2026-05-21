# [論文筆記] GraphCompliance: Aligning Policy and Context Graphs for LLM-Based Regulatory Compliance

> **文獻簡稱**：[GraphCompliance 25]  
> **關聯本專案架構**：第 3 層 (Contradiction / Supersession Engine)、第 4 層 (CDD Decision Layer / Customer Graph)  
> **關聯本專案路線圖**：Phase 1 (Data Contracts), Phase 7 (Contradiction Log), Phase 8 (CDD Decision Engine)

---

## 1. 論文基本資訊
- **標題**：GraphCompliance: Aligning Policy and Context Graphs for LLM-Based Regulatory Compliance (圖合規：用於基於大語言模型監管合規的政策圖與事实圖對齊)
- **作者**：Jiseong Chung (首爾大學), Ronny Ko (大阪大學), Wonchul Yoo (首爾大學), Makoto Onizuka (大阪大學), Sungmok Kim (首爾大學), Tae-Wan Kim (首爾大學), Won-Yong Shin (延世大學)
- **年份/發表管道**：2025 年 10 月 30 日發表於 arXiv (arXiv:2510.26309v1 [cs.AI])
- **研究領域**：神經符號合規推理 (Neuro-Symbolic Compliance Reasoning), 雙圖對齊與合規門 (Dual-Graph Alignment & Compliance Gate)

---

## 2. 核心研究命題與方法
### 2.1 傳統 RAG 與 LLM 合規判定的三種典型失效模式
法律和監管規範是密集關聯、高度敏感且充滿例外的。傳統基於檢索的 RAG 管道或端到端 LLM 在處理合規時，存在三種致命痛點（見論文 Figure 1）：
1. **跨條款參照丟失 (Missed Cross-References)**：RAG 檢索是以查詢語意相似度為中心，往往會因為段落切分而漏掉整個引用鏈（例如：Article A 參照 Article B，但 RAG 只檢索到了 A）。
2. **決策樹邏輯斷裂 (Broken Decision-Tree Logic)**：法規條文常包含順序相關的 `Yes/No` 判定路徑（如歐盟 GDPR 國際數據傳輸判定鏈）。RAG 無法維持這種具有邏輯優先級的順序分支，導致模型得出錯誤的終態結論。
3. **多重清單混淆 (Checklist Conflation)**：面對互斥的義務清單（如「直接收集數據」與「間接獲取數據」的申報義務清單），複雜事實常導致 LLM 將兩張清單混為一談，造成重複或遺漏。

### 2.2 雙圖對齊 (Dual-Graph Alignment) 與合規門框架
為了解決上述痛點，論文提出了 **GraphCompliance**，其核心哲學是**將法規知識與運行時事實分開建模，並通過合規門進行決定性的邏輯約束**。
- **組件 1：政策圖 (Policy Graph, $G_P$)**
  - 將法規文本切分為 `Premise`（定義、範圍等非 deontic 條文）與可執行的 `Compliance Unit (CU)`（合規單元）。
  - 將 CU 形式化建模為 4 元組：$r = \langle S, \Theta, \Pi, \kappa \rangle$，分別代表受規範主體 (Subject $S$)、約束 (Constraint $\Pi$)、上下文環境 (Context $\kappa$) 以及適用條件 (Conditions $\Theta$)。
  - 通過 `REFERS_TO` 邊將具有引用關係的 CU 進行圖譜連接。
- **組件 2：事實圖 (Context Graph, $G_C$)**
  - 將運行時事實（如 incident report 或企業客戶背景）抽取為 `(Subject, Predicate, Object)` 的實體關係三元組。
  - **上位詞映射 (Hypernym Mapping)**：透過 policy-level hypernyms 將事實中的非標準術語（如 "IT manager"）顯式對齊到法規的主體概念（如 "controller"），以穩定語意。
- **組件 3：合規門推理 (Compliance Gate)**
  1. **Anchor 生成與前置檢索**：找出事實圖中的核心主體實體（Anchors，如某家醫院），利用雙邊編碼器計算相似度得分，初篩出相關的候選合規單元。
  2. **Cross-Encoder 重排序與 Plan 生成**：精準排序後產生專屬的合規規則計畫表：`CU Plan`。
  3. **例外覆寫機制 (Exception Override / Defeasible Logic)**：法律邏輯屬於「可擊敗邏輯」（即一條規則被違反了，如果有適用的例外條款成立，則該違規可以被駁回）。
     - 若第一階段 LLM 判定某條 CU 為 `NON_COMPLIANT`。
     - 系統會自動計算該條款在 Policy Graph 中的 **「引用閉包 (Reference Closure, $\mathcal{R}(c)$)」**，即所有可達的參照條款。
     - 第二個 LLM 調用專門在 Evidence Window 中判斷是否存在符合 $\mathcal{R}(c)$ 的例外或豁免條款。若存在，則覆寫判定為 `COMPLIANT`。
  4. **違規優先聚合 (Violation-First Aggregation)**：最終決策時，只要任何一個合規單元被判定為實質違規，整篇文章即標記為違規。

---

## 3. 可作為 Reference 的關鍵數據與指標 (Metrics & Evaluation)

### 3.1 核心實驗數據 (基於 GDPR GCS-300 基準)
- **整體效果提升**：GraphCompliance 在 300 個真實 GDPR 案例場景上，比 Raw LLM 與 RAG 基線高出了 **4.1 至 7.2 pp** 的 micro-F1 得分。
- **F2-score 的巨大躍升（降低漏報率）**：
  - 在合規實戰中，漏判違規（False Negative）的風險遠高於誤判。因此採用 **F2-score**（Recall 權重是 Precision 的兩倍）作為核心評估。
  - GraphCompliance 相比傳統 RAG，使 **F2-score 提升了 12 至 20 個百分點 (pp)**，證明其能極其穩健地攔截合規風險。
- **對小模型的巨大增強作用**：
  - 在 LLaMA-3-8B-Instruct 小模型上，傳統 RAG 幾乎無法進行合規判定。而引進合規門後，小模型在高度複雜的國際傳輸 (Chapter V) 場景中，**Recall 從 57.1% 提升至 84.4%，誤報率 (FPR) 從 95.9% 驟降至 28.9%**。證明了該框架能將複雜邏輯從模型端「卸載」到圖結構端，大幅降低了對模型推理規模的依賴。
- **決策樹場景的完美表現 (Chapter V)**：
  - 在具有典型決策樹邏輯的 GDPR Chapter V 國際傳輸合規檢驗中，配合大模型（GPT-like），GraphCompliance 達到了 **99.2% 的 Recall，且誤報率 (FPR) 降至極低的 4.4%**（對比 Raw LLM 基線的 52.2% 誤報率）。

### 3.2 消融實驗分析 (Ablation Study - Table 7)
- 完整模型 F1 Score：**55.4**。
- **S2：移除 Context Graph (w/o CG)**：F1 暴跌 **10.2 pp**（降至 45.2）。這說明「將非結構化事實轉化為結構化三元組圖譜並與 Hypernym 對齊」是過濾噪聲、避免模型被無關字眼干擾的最關鍵組件。
- **S4：移除引用遍歷與例外處理 (w/o Ref. Trav.)**：F1 大幅下降 **9.6 pp**（降至 45.8）。這強力證實了「例外覆寫與引用閉包」在法律 defeasible reasoning 中的決定性地位。
- **S3：移除 Anchoring 機制 (w/o Anchoring)**：F1 下降 **8.1 pp**。
- **S1：移除 Policy Graph (w/o PG)**：F1 下降 **4.0 pp**。

---

## 4. 具體實作方法與技術細節 (Implementation Details)

### 4.1 政策圖合規單元 (CU) 的 JSON 表示格式 (Listing 1)
論文展示了 Policy Graph 節點在實作中的 schema 範例：
```json
{
  "id": "DOC:GDPR/CHAPTER:IV/SECTION:4/ARTICLE:37/POINT:1/CU:397313605152",
  "kind": "compliance_unit",
  "type": "actor_cu",
  "attrs": {
    "subject": "controller and processor",
    "condition": {
      "any": [
        "processing is carried out by a public authority or body, except for courts...",
        "core activities consist of processing operations requiring regular and systematic monitoring...",
        "core activities consist of processing on a large scale of special categories of data..."
      ]
    },
    "constraint": ["shall designate a data protection officer"],
    "context": null,
    "char_span": {
      "subject": [4, 25],
      "condition": [78, 478],
      "constraint": [26, 70]
    },
    "references": ["A9", "A10"]
  }
}
```

### 4.2 強/弱上位詞映射得分公式 (Hypernym Mapping - Equation 1)
為了將客戶事實的任意字詞映射到法規標準實體 hypernym $h$，當提案與 RKG 中的 `Premise`（定義條款）相符時標記為 `STRONG`，否則為 `WEAK`。累計信賴度公式如下：
$$\widehat{s}_e(h) = \min \left( 1, \max_{r \in R_e: h(r)=h} (s(r) + \beta \cdot \mathbf{1}\{\text{STRONG}(r)\}) \right)$$
其中 $\beta = 0.3$ 是給予 STRONG 定義對齊的獎勵 Bonus。

### 4.3 引用閉包與例外 Override 算法 (Algorithm 3)
```text
對於判定為 NON_COMPLIANT 的條款 c:
1. 計算引用閉包 R(c) = 所有在 Policy Graph 中可通過 REFERS_TO 邊直達或多跳到達的 CUs。
2. 收集 Context Subgraph 構成 Evidence Window W(a)。
3. 調用 LLM Judge：IsException(r, W(a)) 對於每個 r 屬於 R(c)。
4. 如果任何例外條款 r 的條件在 W(a) 中成立，則將判決覆寫為 COMPLIANT。
```

---

## 5. 對 CDD-GraphWiki 系統的具體貢獻與改進建議

### 5.1 架構與實作對齊
- **第 4 層 (CDD Decision Layer)**：本論文提供了該層的理論與工程核心。**客戶 onboarding 的事實背景不是 prompt，而是 `Customer Context Graph`；而法規與內規被編譯為 `Regulatory Policy Graph`**。合規判定就是這兩張圖的語義與結構對齊。
- **第 3 層 (Contradiction/Supersession)**：例外覆寫（Exception Handling）與可擊敗邏輯（Defeasible Logic）提供了解決法規與內規衝突的實作架構。

### 5.2 我們可以直接「抄」的設計 (直接借鑒)
1. **例外覆寫與引用閉包機制**：
   - 在 AML/CDD 中，例外極其普遍（例如：上市公司或政府實體享有簡化盡職調查 Simplified CDD 免除，這就是標準 CDD 義務的例外）。我們可以利用其「尋找 Policy Graph 中的引用閉包並進行 Exception Override」的算法，優雅地實作 AML 的豁免判斷。
2. **Hypernym Mapping (上位詞映射)**：
   - 客戶在 Onboarding 時輸入的職業或行業極其雜亂。我們應建立一個 Policy-level Hypernym map，將 unstructured text 映射到法規標準實體（例如將 "crypto exchange" 映射到 `VASP (Virtual Asset Service Provider)` 或 `REGULATED_ENTITY`），這能極大地提高後續合規推理的穩定度。
3. **雙向對齊的 Cross-Encoder 算式**：
   - 採用公式 (4) 的精細重排序，將主體/約束/條件打包比對，這是我們 Ingestion 和 Graph 檢索的極佳實作方法。

### 5.3 我們需要調整或避免的坑 (警告與改進)
1. **簡化 Policy Graph 節點**：
   - 論文的 CUs 設計了繁瑣的 Meta-CUs。對我們的專案 MVP 而言，我們應該簡化，將法規節點限制為 `Obligation` 與 `EvidenceRequirement`（如股權圖、身分證），避免過度工程化。
2. **推理 LLM 的規模選擇**：
   - 雖然合規門大幅強化了小模型的性能，但 8B 小模型的 F1 (26.6) 在生產環境仍難以接受。因此，我們的 CDD-GraphWiki **決策核心必須使用強推理模型（如 Gemini 3.5 Pro 或 GPT-4o）**，小模型只用於三元組提取或 Hypernym Mapping。

---

## 6. 精選核心引用句庫 (Core Quotes for Citation)

- **論檢索式 RAG 在合規場景下的邏輯失效**：
  > *"Such retrieval-centric approaches falter when compliance hinges on deep structural logic... missed cross-references, broken decision-tree logic, and checklist conflation."* (Section 1, p. 1)

- **論雙圖對齊的設計哲學**：
  > *"We propose GraphCompliance... [which] constructs two knowledge graphs (KGs) from policy documents and a given context: a policy graph that captures the logical structure of regulations, and a context graph that formalizes the situational facts."* (Section 1, p. 2)

- **論可擊敗邏輯與例外覆寫機制 (Defeasible Logic)**：
  > *"To handle the complexity of regulatory reasoning, we introduce a crucial post-processing step for any judgment initially deemed NON_COMPLIANT... A second LLM call then determines whether any CU within this R(c) constitutes a valid exception that overrides the initial violation."* (Section 3.3, p. 5)

- **論金融與法律合規中 Recall 權重高於 Precision (F2-score)**：
  > *"To reflect practical utility in human-in-the-loop compliance environments—where minimizing false negatives is critical—we also adopt the F2-score (beta = 2) as a key metric, which weighs recall twice as heavily as precision."* (Section 4, p. 6)
