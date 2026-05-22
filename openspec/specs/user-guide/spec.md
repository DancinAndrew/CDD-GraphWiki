# user-guide Specification

## Purpose
TBD - created by archiving change user-guide-page. Update Purpose after archive.
## Requirements
### Requirement: User Guide Navigation and Panel Display
側邊欄與路由分發模組應提供一個明確的「系統使用手冊」入口，點擊後，系統 **SHALL** 渲染一個具備奢華暗色霓虹美學與互動 Accordion 的教學手冊頁面。該手冊 **MUST** 以繁體中文向合規官展示系統五大核心模組（工作台總覽、案件審查隊列、防篡改稽核、法規可視化圖譜、法規自主導入）的功能、使用指引與底層技術簡述。

#### Scenario: Switching to User Guide Page
- **GIVEN** 使用者目前位於系統工作台（`activeTab` 為 `dashboard`）。
- **WHEN** 使用者點擊側邊欄中排在「法規自主導入」正下方的「系統使用手冊」按鈕。
- **THEN** 側邊欄按鈕 **SHALL** 轉為選中態（左邊框顯示青色發光條），且主體展示區域 **MUST** 以毛玻璃卡片（`backdropFilter: 'blur(20px)'`）渲染系統使用手冊內容。

#### Scenario: Interacting with User Guide Sections
- **GIVEN** 使用者已進入「系統使用手冊」頁面。
- **WHEN** 使用者點擊其中一個核心模組的標題列（例如「法規自主導入」）。
- **THEN** 系統 **SHALL** 以流暢的折疊動畫展開該模組的詳細教學卡片，展示「功能簡介」、「使用指引」與「底層技術簡述」，並 **MUST** 確保繁體中文說明的字體清晰度與排版結構對齊。

