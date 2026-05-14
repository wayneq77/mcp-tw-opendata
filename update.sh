#!/bin/bash
set -e

echo "🔄 更新 MCP-TW-OpenData..."

# 確認目錄
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 請在 mcp-tw-opendata 專案目錄中執行此腳本。"
    exit 1
fi

# 拉取最新程式碼
echo "📥 拉取最新版本..."
git pull origin main

# 重建並重啟容器（保留資料庫）
echo "🐳 重建容器..."
docker compose build
docker compose up -d

echo ""
echo "✅ 更新完成！"
echo "📌 MCP 伺服器：http://localhost:9527/mcp"
echo "💡 資料庫已保留，不需要重新同步。"
