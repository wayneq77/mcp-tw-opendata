# MCP-TW-OpenData (Twinkle Hub Local Replica)

完全本地化、免費且注重隱私的 **台灣專屬 MCP (Model Context Protocol) 伺服器**。
無縫串接台灣政府開放資料（data.gov.tw）與 37 款台灣專屬實用工具，無需依賴外部付費 API。

## ✨ 核心特色
- **台灣專屬工具 (37 款)**：身分證/統編驗證、地址正規化、郵遞區號轉換、民國/西元年轉換、農曆節氣、簡繁轉換、網頁抓取等。
- **政府開放資料 (5 款)**：內建 53,000+ 筆政府資料集索引，涵蓋交通、醫療、不動產等 20 個領域。
- **完全隱私安全**：資料在本地端處理，敏感資訊不出網。
- **背景自動同步**：資料庫自動定時更新開放資料目錄。

---

## 🚀 快速開始 (Quick Start)

### 系統需求
- **Docker** 與 **Docker Compose**
- 至少 2GB 可用記憶體與 5GB 硬碟空間（用於 PostgreSQL 資料庫）

### 1. 一鍵極速安裝 (One-Line Install)
打開終端機，貼上以下這行指令，系統就會全自動下載、設定並啟動所有伺服器：
```bash
curl -sSL https://raw.githubusercontent.com/wayneq77/mcp-tw-opendata/main/install.sh | bash
```

### 2. (進階) 開啟 Telegram 主動更新推播
如果你希望當官方有新增資料（例如政府採購網、立法院等高價值特規資料）時，系統能主動傳訊息到你的手機：
1. 編輯專案目錄下的 `.env` 檔案。
2. 填入你的 Telegram 機器人資訊：
   ```env
   TELEGRAM_BOT_TOKEN=你的機器人Token
   TELEGRAM_CHAT_ID=你的聊天ID
   ```
3. 執行 `docker compose up -d` 重啟套用，你的專屬資料情報員就會上線！

### 3. 驗證服務狀態
```bash
# 查看容器運行狀態
docker ps

# 查看 MCP 伺服器日誌，確認是否出現 "http server listening"
docker logs mcp-tw-server
```

---

## 🔌 客戶端串接指南 (Client Configuration)

### 方法 A：串接 Claude Desktop
編輯 Claude 的設定檔：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

加入以下設定：
```json
{
  "mcpServers": {
    "twinkle-hub-local": {
      "type": "http",
      "url": "http://localhost:9527/mcp"
    }
  }
}
```
*(存檔後請重新啟動 Claude Desktop。點擊對話框的 🔨 鐵鎚圖示即可使用 42 個工具)*

### 方法 B：串接 OpenClaw
在 `openclaw.json` 的 `mcp.servers` 區塊中加入：
```json
{
  "mcp": {
    "servers": {
      "tw-opendata-local": {
        "url": "http://localhost:9527/mcp",
        "transport": "streamable-http"
      }
    }
  }
}
```
設定完成後重啟 OpenClaw 即可生效。

---

## 📁 專案架構
本專案採用微服務架構，包含三個 Docker 容器：
1. **PostgreSQL (`mcp-tw-db`)**: 儲存開放資料集索引。
2. **FastMCP Server (`mcp-tw-server`)**: 於 Port 9527 提供標準化 MCP API。
3. **Sync Worker (`mcp-tw-sync`)**: 每日背景執行，自動同步 data.gov.tw 資料集清單。

---

## ⚠️ 常見問題 (FAQ)

1. **為什麼剛啟動時搜尋不到開放資料？**
   首次啟動時，`mcp-tw-sync` 需耗時約 1-2 分鐘初始化 5 萬筆資料的索引，請稍候片刻。

2. **如何強制手動更新資料庫？**
   ```bash
   docker exec -it mcp-tw-sync python main.py
   ```

3. **遇到 Port 衝突怎麼辦？**
   請修改 `.env` 檔案中的 `MCP_HOST_PORT` 與 `DB_HOST_PORT`，並重新執行 `docker compose up -d` 套用設定。

## 📜 授權 (License)
MIT License
