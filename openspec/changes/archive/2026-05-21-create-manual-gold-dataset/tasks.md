## 1. Environment Setup

- [ ] 1.1 創建黃金數據集存放目錄 `data/gold/` 與概念百科子目錄 `data/gold/concepts/`

## 2. Compile Regulatory Sources and Clauses

- [ ] 2.1 手動編譯 `data/gold/source_documents.yaml`，定義 3 份源文件（FATF Rec 10, MAS Notice 626, Mock Internal Policy）的元數據
- [ ] 2.2 手動編譯 `data/gold/clauses.yaml`，對前述源文件進行精準的段落切分，建立至少 10 個核心法規條款

## 3. Extract Obligations and Define Conflicts

- [ ] 3.1 手動編寫 `data/gold/obligations.yaml`，從條款中抽取出至少 10 個核心合規義務，並確保 `source_clause_ids` 雙向溯源連結
- [ ] 3.2 手動編寫 `data/gold/conflicts.yaml`，設計並結構化至少 3 個法規與政策衝突對象

## 4. Draft Wiki Concept Pages

- [ ] 4.1 撰寫 `data/gold/concepts/ubo.md` 百科頁面，闡述「實質受益人（Ultimate Beneficial Owner）」的判定標準
- [ ] 4.2 撰寫 `data/gold/concepts/pep.md` 百科頁面，說明「政治曝險人物（Politically Exposed Person）」審查要求
- [ ] 4.3 撰寫 `data/gold/concepts/edd.md` 百科頁面，說明「加強型盡職調查（Enhanced Due Diligence）」觸發與程序
- [ ] 4.4 撰寫 `data/gold/concepts/cdd.md` 百科頁面，說明「標準客戶盡職調查（Customer Due Diligence）」規範
- [ ] 4.5 撰寫 `data/gold/concepts/sofw.md` 百科頁面，說明「資金來源（Source of Funds）」與「財富來源（Source of Wealth）」驗證要求

## 5. Define Customer Scenarios and expected Decisions

- [ ] 5.1 手動編寫 `data/gold/customer_contexts.yaml`，設計至少 5 個測試客戶情境（涵蓋法人、個人、PEP、高風險國家、複雜多層股權等畫像）
- [ ] 5.2 手動編寫 `data/gold/checklists.yaml`，手動演算出預期的 CDDChecklist 決策（標準 CDD / 簡化 CDD / EDD）、適用義務、必備文件與風險觸發器

## 6. Automated Validation and Verification

- [ ] 6.1 撰寫 `tests/test_gold_dataset.py` 單元測試，載入並使用 Pydantic 對所有 YAML 檔案進行資料合約驗證
- [ ] 6.2 在 `tests/test_gold_dataset.py` 中實作語意關係完整性檢查（驗證 `source_clause_ids`、`customer_id` 等全局存在性與雙向溯源閉環）
- [ ] 6.3 執行 `pytest tests/test_gold_dataset.py` 單元測試套件，確保所有黃金數據 100% 透過驗證
