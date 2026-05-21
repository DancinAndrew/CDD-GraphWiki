# ADR 0004: Schema 表示法與 Python Dataclass 策略

狀態：已接受 (Accepted)  
日期：2026-05-21  

## 背景 (Context)

在 Phase 1 (資料合約) 中，CDD-GraphWiki 需要定義核心合規對象的 Schemas：`SourceDocument`、`Clause`、`Obligation`、`CustomerContext`、`Conflict` 和 `CDDChecklist`。

我們必須解決 `SPEC.md` 與 `design.md` 中的**開放性問題 (Open Question)**：這些 Schemas 應以 JSON Schema、Python dataclasses、Pydantic 模型還是兩者混合形式存在？

### 來自文獻研究的關鍵考量：
1. **Python 可執行元模型 (Python-Executable Metamodels)**：*[Legal Requirements Translation 25]* 證實，將法律編譯為可執行的 Python 類別，能顯著提升推理的正確性與精準度，有效解決自然語言的歧義性。
2. **Schema-Light 模組化**：*[KG Rep 26]* 與 *[RAGulating Compliance 26]* 警告，應避免使用剛性、難以維護的本體 (Ontology)。資料合約必須保持彈性、扁平化，並支持豐富的元數據（如雙向 provenance 連結 $\Lambda(t_i)$）。
3. **跨系統互操作性**：雖然 Python 類別非常適合推理執行，但標準的 JSON/YAML Schema 對於資料序列化、前端 UI 整合以及聲明式校驗是必不可少的。

---

## 決定 (Decision)

我們將在 CDD-GraphWiki 中實作 **「混合元模型策略 (Hybrid Metamodel Strategy)」**：

1. **具權威性的代碼模型 (Authoritative Code Model)**：在 `src/contracts/` 底下，使用強型別的 **Python Dataclasses**（配備標準類型提示與 Docstrings）實作首要 schemas。這將作為可執行的合規推理引擎層。
2. **聲明式契約 (Declarative Contracts)**：在 `schemas/*.schema.json` 底下導出等效的 **JSON Schemas**，作為與語言無關的資料校驗契約。
3. **單一事實來源（自動生成）**：與其手動維護雙向重複的程式碼（這會導致漂移與校驗錯誤），我們將撰寫一個輕量級的 Python 編譯/導出指令碼，從 Python 資料模型中動態提取並導出 JSON Schemas。

---

## 曾考慮的替代方案 (Alternatives Considered)

### 方案 A：僅使用 JSON Schema
* **優點**：與語言無關，高度標準，易於使用現成函式庫進行校驗。
* **缺點**：不可執行。在原生字典 (Dict) 上撰寫複雜的合規邏輯（例如動態缺口匹配 $f_{\text{type}}$ 或雙圖對齊），極易出錯，且缺乏 *[Translation 25]* 中強調的 IDE 自動補全與類型安全優勢。

### 方案 B：僅使用 Pydantic 模型
* **優點**：內置運行時校驗，易於導出 JSON Schema。
* **缺點**：在 bootstrap 階段引入了外部套件依賴 (`pydantic`)，這違反了我們「在獲得批准前，保持運行時設定極簡且減少依賴」的原則。我們傾向於優先使用 Python 標準庫的 `dataclasses` 和 `typing`。

---

## 後果 (Consequences)

- **開發者體驗**：開發者在編寫 Python 演算法時（Phase 4、Phase 7、Phase 8），能享有強大的自動補全、靜態類型檢查 (mypy) 以及繼承支持。
- **規格優先驗證**：其他系統或手動標記的黃金 YAML 數據，仍能通過編譯出的 JSON Schemas 進行確定性的合規校驗。
- **依賴隔離**：我們保持 core logic 的標準庫依賴，完全符合專案的依賴 consent 規定。
