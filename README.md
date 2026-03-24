# 🏫 國小課後社團自動報名系統

響應式網頁應用程式，讓家長預先填寫報名資料，系統於開放報名時間自動送出報名。  
**目標頁面**：[廍子國小 114學年度第2學期課後社團](https://www.beclass.com/rid=3052575698eccf04320a)

---

## 📁 專案結構

```
Automatic registration system/
├── app.py                  # Flask 後端（路由 + APScheduler 排程）
├── beclass_submitter.py    # Selenium 自動填表模組
├── requirements.txt        # Python 相依套件
├── Procfile                # Railway / Heroku 啟動指令
├── railway.json            # Railway 部署設定
├── nixpacks.toml           # Railway nixpacks 安裝 Chromium
├── templates/
│   └── index.html          # 主頁面（Jinja2 模板）
├── static/
│   ├── css/style.css       # 響應式 CSS
│   └── js/main.js          # 前端邏輯
└── data/                   # 報名記錄（自動產生，不上傳 Git）
```

---

## ⚡ 本機快速開始

### 1. 建立虛擬環境並安裝套件

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. 啟動伺服器

```bash
python app.py
```

### 3. 開啟瀏覽器

前往 [http://localhost:5000](http://localhost:5000)

---

## 🚀 Railway 雲端部署（方案四）

### 步驟 1：上傳到 GitHub

```bash
git add .
git commit -m "init: auto registration system"
git push origin main
```

### 步驟 2：在 Railway 建立專案

1. 前往 [railway.app](https://railway.app) 並登入（可用 GitHub 帳號）
2. 點擊 **New Project → Deploy from GitHub repo**
3. 選擇本專案的 GitHub 倉庫

### 步驟 3：設定環境變數

在 Railway 專案 → **Variables** 頁籤，新增以下變數：

| 變數名稱 | 值 | 說明 |
|---|---|---|
| `FLASK_ENV` | `production` | 關閉 debug 模式 |
| `RAILWAY_ENVIRONMENT` | `production` | 告知程式使用雲端 Chromium |
| `CHROME_BIN` | `/usr/bin/chromium` | Chromium 路徑（nixpacks 安裝） |
| `CHROMEDRIVER_BIN` | `/usr/bin/chromedriver` | Chromedriver 路徑 |
| `DATA_FILE` | `/tmp/registrations.json` | 暫存報名資料（重啟後重置） |
| `TZ` | `Asia/Taipei` | 時區設定 |

### 步驟 4：等待部署完成

Railway 會自動：
- 用 nixpacks 安裝 Chromium + chromedriver
- 安裝 `requirements.txt` 所有套件
- 以 `Procfile` 啟動 gunicorn

部署完成後，Railway 會提供一個公開網址（如 `https://your-app.up.railway.app`），即可從任何地方存取！

### ⚠️ Railway 雲端注意事項

| 項目 | 說明 |
|------|------|
| 🗄️ 資料儲存 | 服務重啟後 `/tmp` 資料會消失，建議在報名前不要重啟 |
| 🤖 Cloudflare | 雲端 IP 較易被 Cloudflare 擋住；若報名失敗可改用本機執行 |
| 💤 睡眠模式 | Railway 免費版閒置 30 分鐘會暫停，建議在報名前先開啟頁面喚醒服務 |
| ⏰ 時區 | 已設定 `TZ=Asia/Taipei`，排程時間以台灣時間為準 |

---

## 📋 功能說明

| 功能 | 說明 |
|------|------|
| 📝 報名表單 | 填寫學生姓名、身分證、性別、班級座號（5碼）|
| 📧 家長資訊 | 輸入家長 Email 及行動電話 |
| 🎯 社團選擇 | 按星期分組，60 個社團，最多選 2 個 |
| ⏰ 自動報名 | 設定開放時間，系統自動在該時間以 Selenium 送出 |
| ⏳ 倒數計時 | 即時顯示距離報名時間的天/時/分/秒 |
| 🔍 狀態查詢 | 憑報名編號查詢目前狀態 |
| ❌ 取消排程 | 可在時間到達前取消自動報名 |

---

## 📱 響應式設計

- **桌機**：雙欄表單格線，社團卡片多欄排列
- **平板**：自適應欄位寬度
- **手機**：單欄佈局，大按鈕易於點擊

---

## ⚠️ 注意事項

1. **伺服器須保持運行**：自動報名由後端 APScheduler 執行，關閉服務後排程消失。
2. **班級座號格式**：5碼數字，如 `10101` 代表一年一班1號。
3. **Cloudflare 防護**：本機使用 `undetected-chromedriver`；雲端使用 headless Chromium。



