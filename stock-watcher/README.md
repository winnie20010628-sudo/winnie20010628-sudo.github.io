# Stock Watcher

同時監控多個網頁貨品上架／可購買狀態。當頁面出現你自訂的關鍵字，而且偵測到可購買字樣時，會把**商品名稱 + 購買連結**傳到 WhatsApp，方便一撳入去填地址同付款。

## 功能

- 網頁介面輸入多個監控網址
- 自訂關鍵字（例如商品名、顏色、限量）
- 自訂「可購買／售罄」字詞（有預設中英文）
- **只有可購買**先會推送通知（避免售罄洗版）
- WhatsApp 通知（預設 CallMeBot，可選 Twilio）
- 定時自動檢查 + 手動立即檢查
- 同一狀態唔會重複通知

## 快速開始

```bash
cd stock-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

編輯 `.env`：

```env
WHATSAPP_PHONE=852xxxxxxxx
WHATSAPP_API_KEY=your_callmebot_api_key
CHECK_INTERVAL_SECONDS=60
```

### 設定 CallMeBot（免費個人 WhatsApp）

1. 將 `+34 644 21 99 47` 存入手機通訊錄  
2. 用 WhatsApp 傳送：`I allow callmebot to send me messages`  
3. 機器人會回傳 API key，填入 `.env` 的 `WHATSAPP_API_KEY`  
4. `WHATSAPP_PHONE` 用國際格式、唔使 `+` 號，例如香港：`85291234567`

詳情：https://www.callmebot.com/blog/free-api-whatsapp-messages/

啟動：

```bash
python -m app
```

瀏覽器打開：http://127.0.0.1:8000

## 使用方法

1. 在介面填「監控網址」同「自訂關鍵字」
2. （可選）自訂可購買／售罄字詞；留空會用預設
3. 按「開始監控」
4. 按「測試 WhatsApp」確認通知正常
5. 程式會定時檢查；偵測到可購買就會推訊息

### 通知內容示例

```
🛒 可購買貨品通知
商品：限量特別色 XXX
監控：官方網店
關鍵字：特別色, 限量
購買連結：https://shop.example.com/cart/...
```

## 偵測邏輯（簡要）

1. 下載網頁 HTML  
2. 若你有設關鍵字 → 頁面必須出現至少一個  
3. 出現「可購買」字詞，且**沒有**「售罄」字詞 → 視為可買，發送 WhatsApp  
4. 同時有可買同售罄字樣 → 暫不通知，減少誤報  

## 注意

- 多數靜態／伺服器渲染頁面可用；大量用 JavaScript 動態載入庫存嘅網站可能抓唔到，需要再加瀏覽器自動化（Playwright）
- 請遵守目標網站條款，唔好把檢查間隔設得太密
- CallMeBot 係第三方服務，適合個人用途；商業用途建議改 Twilio WhatsApp

## 專案結構

```
stock-watcher/
  app/
    main.py       # Web 介面 + API
    monitor.py    # 排程檢查
    scanner.py    # 抓頁 + 關鍵字／可購買判斷
    notifier.py   # WhatsApp
    storage.py    # 監控清單（data/watchlist.json）
  .env.example
  requirements.txt
```
