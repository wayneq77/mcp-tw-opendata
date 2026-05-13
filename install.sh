#!/bin/bash
set -e

echo "🚀 開始安裝 MCP-TW-OpenData (Twinkle Hub Local Replica)..."

# 檢查指令
if ! command -v git &> /dev/null; then
    echo "❌ 找不到 git。請先安裝 git。"
    exit 1
fi
if ! command -v docker &> /dev/null; then
    echo "❌ 找不到 docker。請先安裝 docker。"
    exit 1
fi

# 下載程式碼
if [ -d "mcp-tw-opendata" ]; then
    echo "⚠️ 目錄 mcp-tw-opendata 已存在，進入該目錄更新..."
    cd mcp-tw-opendata
    git pull
else
    git clone https://github.com/wayneq77/mcp-tw-opendata.git
    cd mcp-tw-opendata
fi

# 設定環境變數
if [ ! -f ".env" ]; then
    echo "📝 建立 .env 設定檔..."
    cp .env.example .env
    # 產生隨機密碼取代預設字串 (macOS 與 Linux sed 語法相容處理)
    NEW_PASSWORD=$(openssl rand -hex 16)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/CHANGE_TO_A_STRONG_PASSWORD_HERE/$NEW_PASSWORD/g" .env
    else
        sed -i "s/CHANGE_TO_A_STRONG_PASSWORD_HERE/$NEW_PASSWORD/g" .env
    fi
    echo "✅ 已自動生成安全的資料庫密碼。"
else
    echo "✅ .env 檔案已存在，保留現有設定。"
fi

# 啟動容器
echo "🐳 啟動系統..."
docker compose up -d

echo ""
echo "🎉 系統已成功啟動！"
echo "📌 MCP 伺服器正在運行於: http://localhost:9527/mcp"
echo ""
echo "💡 【進階功能】主動推播更新通知："
echo "   如果你希望系統抓到新資料（如政府採購網、立法院等）時主動用 Telegram 通知你："
echo "   1. 請編輯 mcp-tw-opendata/.env 檔案"
echo "   2. 填入你的 TELEGRAM_BOT_TOKEN 與 TELEGRAM_CHAT_ID"
echo "   3. 執行 docker compose up -d 套用設定"
