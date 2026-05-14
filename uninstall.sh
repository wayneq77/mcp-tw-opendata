#!/bin/bash
set -e

echo "🗑️  準備解除安裝 MCP-TW-OpenData..."
echo ""

# 確認目錄
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 請在 mcp-tw-opendata 專案目錄中執行此腳本。"
    exit 1
fi

# 確認
read -p "⚠️  這會停止所有容器並刪除資料庫，確定要繼續嗎？(y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "已取消。"
    exit 0
fi

# 停止並移除容器、網路、Volume
echo "🐳 停止並移除容器..."
docker compose down -v 2>/dev/null || true

# 移除 Docker image
echo "🧹 移除 Docker Image..."
docker rmi mcp-tw-opendata-sync_worker mcp-tw-opendata-mcp_server 2>/dev/null || true

# 回到上層目錄，刪除專案資料夾
echo "📁 刪除專案目錄..."
PROJECT_DIR=$(pwd)
cd ..
rm -rf "$PROJECT_DIR"

echo ""
echo "✅ 解除安裝完成！以下項目已清除："
echo "   • Docker 容器與網路"
echo "   • PostgreSQL 資料庫 (Volume)"
echo "   • Docker Image"
echo "   • 專案目錄"
