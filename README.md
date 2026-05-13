# Twinkle Hub 本地自託管版 (MCP-TW-OpenData)

完全本地化、免費、保護隱私的 **台灣專屬 MCP Server**。
串接台灣政府開放資料（data.gov.tw）與 37 款台灣專屬實用工具，完全不依賴外部付費 API。

## ✨ 核心特色
- **台灣專屬工具 (37 款)**：身分證/統編驗證、地址正規化、郵遞區號轉換、民國/西元年轉換、農曆節氣、簡繁轉換、網頁抓取等。
- **政府開放資料 (5 款)**：內建 53,000+ 筆政府資料集索引，涵蓋交通、醫療、不動產等 20 個領域。
- **完全隱私安全**：資料在本地 Docker 處理，敏感資訊不外洩。
- **離線可用**：資料庫自動每日背景同步。

---

## 🚀 安裝教學 (Installation Guide)

### 系統需求
- **Docker** 與 **Docker Compose**
- 至少 2GB 可用記憶體與 5GB 硬碟空間（用於儲存 PostgreSQL 資料庫）

### 步驟 1：取得程式碼
```bash
git clone https://github.com/你的帳號/mcp-tw-opendata.git
cd mcp-tw-opendata
```
*(如果你的朋友是拿到壓縮包，請直接解壓縮並進入該資料夾)*

### 步驟 2：環境設定
複製範例環境變數檔，並根據需求修改密碼（預設 Port 為 `9527` 避免衝突）：
```bash
cp .env.example .env
```
*(請確保 `.env` 內的資料庫密碼已設定，預設的配置可直接使用)*

### 步驟 3：啟動服務
使用 Docker Compose 在背景啟動三層架構（資料庫、MCP 伺服器、同步 Worker）：
```bash
docker compose up -d
```

### 步驟 4：驗證服務狀態
```bash
# 查看容器是否正常運行
docker ps

# 查看 MCP 伺服器日誌
docker logs mcp-tw-server
```
當看到 `http server listening` 時，代表伺服器已成功運行在 `http://localhost:9527`。

---

## 🔌 串接指南 (Client Configuration)

### 方法 A：串接 Claude Desktop
編輯 Claude 的設定檔：
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
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
*(存檔後，請完全退出並重新啟動 Claude Desktop。點擊對話框右下角的 🔨 鐵鎚圖示即可看到 42 個工具)*

### 方法 B：串接 OpenClaw
在 `~/.openclaw/openclaw.json` 的 `mcp.servers` 區塊中加入：
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
修改後重啟 OpenClaw 即可生效 (`openclaw gateway restart`)。

---

## 📁 專案架構
本專案採用三容器微服務架構：
1. **PostgreSQL (`mcp-tw-db`)**: 儲存 53,000+ 筆資料集索引。
2. **FastMCP Server (`mcp-tw-server`)**: 運行在 Port 9527，提供 42 個 MCP 工具介面。
3. **Sync Worker (`mcp-tw-sync`)**: 每日背景執行，自動從 data.gov.tw 同步最新的資料集清單。

---

## ⚠️ 常見問題
1. **為什麼剛啟動時搜尋不到開放資料？**
   首次啟動時，`mcp-tw-sync` 需要約 1-2 分鐘從政府網站下載並建立 5 萬筆資料的索引，請稍候片刻。
2. **如何強制手動更新資料庫？**
   ```bash
   docker exec -it mcp-tw-sync python main.py
   ```
3. **遇到 Port 衝突怎麼辦？**
   修改 `.env` 檔案中的 `MCP_HOST_PORT` 與 `DB_HOST_PORT`，然後執行 `docker compose up -d` 重新套用。

## 📜 授權
MIT License