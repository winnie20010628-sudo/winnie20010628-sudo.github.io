# Stock Watcher（電腦應用）

同時監控多個網頁貨品上架／可購買狀態。當頁面出現你自訂的關鍵字，而且偵測到可購買字樣時，會把**商品名稱 + 購買連結**傳到 WhatsApp。

呢個係 **桌面應用程式**（Tkinter），唔使開瀏覽器。

## 功能

- 電腦視窗輸入多個監控網址
- 自訂關鍵字（例如商品名、顏色、限量）
- 自訂「可購買／售罄」字詞（有預設中英文）
- **只有可購買**先會推送 WhatsApp（避免售罄洗版）
- 應用內直接設定 WhatsApp（CallMeBot）
- 定時自動檢查 + 手動檢查
- 同一狀態唔會重複通知

## 安裝同啟動

### Windows / macOS / Linux

1. 安裝 [Python 3.10+](https://www.python.org/downloads/)  
   - Windows 安裝時請勾選 **tcl/tk**（通常預設已有）同「Add Python to PATH」
2. 打開終端機，進入本資料夾：

```bash
cd stock-watcher
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m app
```

或者直接：

```bash
python run.py
```

Windows 亦可雙擊 `啟動 Stock Watcher.bat`（首次會自動建立虛擬環境同安裝套件）。

## 設定 WhatsApp

1. 程式入面按 **「WhatsApp 設定」**
2. CallMeBot 步驟：
   - 將 `+34 644 21 99 47` 存入手機通訊錄
   - 用 WhatsApp 傳送：`I allow callmebot to send me messages`
   - 把收到的 API key 同電話（例如 `85291234567`）填入並儲存
3. 按 **「測試 WhatsApp」** 確認收到訊息

詳情：https://www.callmebot.com/blog/free-api-whatsapp-messages/

## 使用方法

1. 左邊填監控網址、關鍵字 → 按「開始監控」
2. 可加多幾個網頁
3. 按「立即全部檢查」，或等它自動定時檢查
4. 偵測到可購買 → WhatsApp 會收到商品名同購買連結

### 通知示例

```
🛒 可購買貨品通知
商品：限量特別色 XXX
監控：官方網店
關鍵字：特別色, 限量
購買連結：https://shop.example.com/cart/...
```

## 偵測邏輯

1. 下載網頁 HTML  
2. 若有設關鍵字 → 頁面必須出現至少一個  
3. 出現「可購買」字詞，且沒有「售罄」字詞 → 發送 WhatsApp  
4. 同時有可買同售罄字樣 → 暫不通知，減少誤報  

## 注意

- 大量用 JavaScript 動態載入庫存嘅網站，靜態抓取可能睇唔到；需要可再加 Playwright
- 請遵守目標網站條款，唔好把檢查間隔設得太密
- 設定同監控清單會儲存喺 `data/` 資料夾

## 專案結構

```
stock-watcher/
  run.py                 # 啟動入口
  啟動 Stock Watcher.bat # Windows 一鍵啟動
  app/
    desktop.py           # 桌面介面
    monitor.py           # 檢查流程
    scanner.py           # 抓頁 + 關鍵字判斷
    notifier.py          # WhatsApp
    storage.py           # 監控清單
    config.py            # 設定
```
