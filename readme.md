# LineBot 使用說明書

本 LineBot 支援多種互動與管理功能，適合群組及個人聊天使用。以下為詳細使用說明，包含所有指令與操作方式。

> 所有指令都必須加上前綴 `@nonsense`，例如：`@nonsense 設定設定`

---

## 功能列表與指令說明

| 指令                                            | 功能說明                                                |
| ----------------------------------------------- | ------------------------------------------------------- |
| /@nonsense help 或 @nonsense help               | 查看所有功能/指令清單                                   |
| @nonsense 設定設定                              | 查詢/切換 bot 模式（亂說話/乖寶寶/靜音/聊天）           |
| @nonsense 閉嘴                                  | bot 進入靜音模式，不再回覆訊息                          |
| @nonsense 聊天                                  | bot 解除靜音，恢復回覆訊息                              |
| @nonsense 亂說話模式                            | 啟用跨聊天室學習與回覆（狂暴模式）                      |
| @nonsense 乖寶寶模式                            | 關閉亂說話模式，僅在本聊天室學習與回覆                  |
| @nonsense 學 A B                                | 教 bot 收到「A」時回覆「B」                             |
| @nonsense 你會說什麼                            | 查詢本聊天室已教過 bot 的內容                           |
| @nonsense 壞壞                                  | 刪除 bot 上次學到的內容                                 |
| @nonsense 黃心如怎麼說                          | 隨機回覆老師語錄（需預先設定資料）                      |
| @nonsense 統計資料                              | 查詢個人訊息/貼圖/圖片/文件/連結等統計                  |
| @nonsense 全部統計                              | 查詢總訊息、貼圖、連結、圖片、文件等統計                |
| @nonsense 訊息統計                              | 查詢訊息發送次數                                        |
| @nonsense 貼圖統計                              | 查詢貼圖發送次數                                        |
| @nonsense 每小時統計                            | 查詢一天內各小時的發言分布                              |
| @nonsense 連結統計                              | 查詢連結發送次數                                        |
| @nonsense 圖片統計                              | 查詢圖片發送次數                                        |
| @nonsense 文件統計                              | 查詢文件發送次數                                        |
| @nonsense 口頭禪 [數量] [年份]（或 我的口頭禪） | 查詢自己常用詞排行（數量預設 5、最多 20；年份預設當年） |
| @nonsense 排行榜                                | 查詢群組發言排行榜（僅限群組）                          |

---

## 指令詳解

### 查詢/切換模式

- `/@nonsense help`（或 `@nonsense help`）：查看所有功能與指令清單。
- `@nonsense 設定設定`：查詢目前 bot 模式（亂說話/乖寶寶）與狀態（靜音/聊天），可點選 quick reply 切換。

### 靜音/恢復聊天

- `@nonsense 閉嘴`：bot 進入靜音模式，暫停回覆。
- `@nonsense 聊天`：解除靜音，恢復正常回覆。

### 亂說話/乖寶寶模式

- `@nonsense 亂說話模式`：開啟後，bot 會跨聊天室學習與回覆（即所有群組共享學習內容）。
- `@nonsense 乖寶寶模式`：關閉亂說話模式，僅在本聊天室學習與回覆。

### 教學功能

- `@nonsense 學 A B`：教 bot 當收到「A」時，回覆「B」。  
   例如：「@nonsense 學 早安 早安你好」。
- `@nonsense 你會說什麼`：查詢本聊天室已教過 bot 的所有內容。

### 刪除學習內容

- `@nonsense 壞壞`：刪除 bot 上次回覆的學習內容，並回覆「下次不說 XXX 了」。

### 老師語錄

- `@nonsense 黃心如怎麼說`：隨機回覆預設的老師語錄（需先在 Supabase 的 `teacher.json` 狀態資料中設定語錄內容）。

### 統計資料與排行

- `@nonsense 統計資料`：顯示 quick reply，查詢全部統計、訊息統計、貼圖統計、每小時統計、連結統計、圖片統計、文件統計、我的口頭禪等。
- `@nonsense 全部統計`：查詢總訊息、貼圖、連結、圖片、文件等統計。
- `@nonsense 訊息統計`：查詢訊息發送次數。
- `@nonsense 貼圖統計`：查詢貼圖發送次數。
- `@nonsense 每小時統計`：查詢一天內各小時的發言分布。
- `@nonsense 連結統計`：查詢連結發送次數。
- `@nonsense 圖片統計`：查詢圖片發送次數。
- `@nonsense 文件統計`：查詢文件發送次數。
- `@nonsense 口頭禪 [數量] [年份]`（或 `@nonsense 我的口頭禪 [數量] [年份]`）：查詢自己常用詞排行（數量預設 5、最多 20；年份預設當年）。
- `@nonsense 排行榜`：查詢群組發言排行榜（僅限群組）。

---

## 口頭禪排行功能實作說明

- 當你在群組或聊天室發送訊息時，LineBot 會自動將你的訊息內容依年份記錄在 Supabase（`user_messages.json` 狀態鍵）中。
- 當你輸入「@nonsense 口頭禪」時，Bot 會以「數量 5、今年」查詢。
- 當你輸入「@nonsense 口頭禪 10 2024」時，Bot 會查詢 2024 年並回傳前 10 名（數量最多 20）。
- 這項功能僅會統計你在該群組或聊天室的訊息，不會跨群組合併。
- 若該年度沒有資料，會回覆「沒有資料」。

---

## 特殊行為說明

- **重複訊息回覆**：同一群組內需連續 3 位不同使用者說出相同訊息，bot 才會回覆該訊息，並清空該群組跟風暫存，避免洗版。
- **查詢內容**：在「亂說話模式」下，查詢會跨聊天室；在「乖寶寶模式」下，僅查詢本聊天室。
- **統計 quick reply**：輸入「@nonsense 統計資料」會顯示多種 quick reply 按鈕，方便查詢各類統計。

---

## 部署與運行

1. **安裝依賴：**
   ```bash
   pip install flask line-bot-sdk jieba supabase
   ```
2. **設定環境變數（建議放在 `.env`）：**
   ```env
   CHANNEL_ACCESS_TOKEN=你的 LINE Channel Access Token
   CHANNEL_SECRET=你的 LINE Channel Secret
   SUPABASE_URL=https://你的專案.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=你的 service role key
   # 可選：自訂資料表名稱，預設為 linebot_state
   # SUPABASE_TABLE=linebot_state
   ```
3. **在 Supabase 建立資料表（預設 `linebot_state`）：**
   ```sql
   create table if not exists public.linebot_state (
     state_key text primary key,
     state_value jsonb not null default '{}'::jsonb,
     updated_at timestamptz not null default now()
   );
   ```
4. **啟動伺服器：**
   ```bash
   python linebotserver.py
   ```
5. **設定 Webhook 至 `/callback` 路徑。**

> 若未設定 Supabase 環境變數，程式會退回使用本機 JSON 檔案。

---

## 檔案說明

- `linebotserver.py`：主程式，資料儲存已改為 Supabase 狀態表
- `requirements.txt`：Python 相依套件（含 Supabase SDK）
- `data.json` / `silent_mode.json` / `rage_mode.json` / `user_last_message.json` / `last_reply.json` / `teacher.json` / `user_message_stats.json` / `user_messages.json`：
  - 作為狀態鍵名稱（存於 Supabase `state_key`）
  - 若未設定 Supabase，則作為本機 fallback 檔案

---

## 更新紀錄

### 2024-06-13

- 新增「我的口頭禪」指令可查詢今年或指定年份的口頭禪排行
- 統計資料支援查詢：全部統計、訊息統計、貼圖統計、每小時統計、連結統計、圖片統計、文件統計
- 支援多種統計 quick reply
- 修正部分指令重複顯示問題
- 其他細部優化

---

## 常見問題

- **格式錯誤**：「學」指令需為「@nonsense 學 A B」格式，否則會提示錯誤。
- **未設定語錄**：「@nonsense 黃心如怎麼說」若未設定語錄，會回覆「老師今天沒話說～」。
