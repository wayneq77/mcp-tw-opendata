# 🎯 Twinkle Hub 本地複製計畫

## 📋 專案目標

**建立一個完全本地化的 MCP Server，複製 Twinkle Hub 的所有功能，不依賴任何外部 API 或付費服務。**

---

## 🎯 背景故事（給AI理解）

你是一個有靈魂的數位伴侶（龍蝦小乖），正在幫使用者建立一個本地化的台灣開放資料查詢系統。

### 為什麼要做這個？
- Twinkle Hub 是一個 MCP 服務，串接台灣政府開放資料（data.gov.tw）
- 目前處於 Alpha 免費階段，但未來會收費
- 使用者想要**完全本地版本**，不依賴 Twinkle Hub，也不想要 API Key
- 目標：讓 AI 能像使用 Twinkle Hub 一樣查詢台灣的各種開放資料

### 目前已經有的資源
- Linux 主機（AMD Ryzen 2600X）
- OpenClaw 已經在主機上運行
- Docker 和 Docker Compose 已安装
- 已經學會使用 Twinkle Hub 的 5 個 MCP 工具：
  - `list_domains` - 列出 19 個領域
  - `search_datasets` - 搜尋資料集
  - `get_dataset` - 取得資料集詳細資訊
  - `query_rows` - SQL 查詢資料列
  - `materialize_dataset` - 下載並快取資料集

### Twinkle Hub 的規格（必須完全相容）
- 52,960 筆資料集
- 19 個領域分類
- 50ms 等級的 SQL 查詢速度
- 每天與政府資料同步
- 格式處理：CSV、JSON、XML、PDF、GeoJSON 等
- MCP 傳輸協定：streamable-http（非 stdio）

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐        │
│  │  PostgreSQL │  │   FastMCP   │  │     Sync     │        │
│  │  (資料庫)   │  │   Server    │  │    Worker    │        │
│  │             │  │             │  │  (每日排程)  │        │
│  │  port:5432  │  │  port:8000  │  │              │        │
│  └─────────────┘  └─────────────┘  └──────────────┘        │
│         ↑                ↑                ↓                  │
│         └────────────────┼────────────────┘                  │
│                          ↓                                    │
│                   ┌─────────────┐                           │
│                   │ data.gov.tw │                           │
│                   │  (外部來源)  │                           │
│                   └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 專案目錄結構

```
~/mcp-tw-opendata/
├── docker-compose.yml              ← Docker 佈署設定
├── Dockerfile.mcp                 ← MCP Server 映像
├── Dockerfile.sync                ← Sync Worker 映像
├── postgres/
│   └── init.sql                   ← 資料庫初始化腳本
├── sync/
│   ├── main.py                    ← 同步主程式
│   ├── classifiers/
│   │   └── domain_classifier.py   ← 19領域自動分類器
│   ├── normalizers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            ← 正規化基底類別
│   │   │   ├── csv_normalizer.py  ← CSV 處理
│   │   │   ├── json_normalizer.py ← JSON 處理
│   │   │   ├── xml_normalizer.py  ← XML 處理
│   │   │   └── pdf_normalizer.py ← PDF 處理
│   ├── fetchers/
│   │   │   ├── __init__.py
│   │   │   └── data_gov_fetcher.py ← data.gov.tw API 抓取
│   └── requirements.txt
├── mcp_server/
│   ├── main.py                    ← FastMCP Server 進入點
│   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── list_domains.py    ← list_domains 工具
│   │   │   ├── search_datasets.py ← search_datasets 工具
│   │   │   ├── get_dataset.py     ← get_dataset 工具
│   │   │   ├── query_rows.py      ← query_rows 工具
│   │   │   └── materialize_dataset.py ← materialize_dataset 工具
│   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── connection.py      ← PostgreSQL 連線管理
│   └── requirements.txt
└── README.md
```

---

## 🗄️ 資料庫 Schema (PostgreSQL)

### 資料集目錄表
```sql
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(50) UNIQUE NOT NULL,
    name_zh TEXT NOT NULL,
    name_en TEXT,
    description TEXT,
    agency VARCHAR(100),
    primary_domain VARCHAR(50),
    domains TEXT[],
    update_freq VARCHAR(20),
    quality_tier VARCHAR(20),
    formats TEXT[],
    license VARCHAR(100),
    source_url TEXT,
    row_count BIGINT,
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 已正規化的資料列
```sql
CREATE TABLE dataset_rows (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(50) NOT NULL,
    row_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE CASCADE
);
```

### 領域定義表
```sql
CREATE TABLE domains (
    key VARCHAR(50) PRIMARY KEY,
    name_zh VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    role VARCHAR(20),
    scope TEXT,
    typical_questions TEXT[],
    anchor_examples TEXT[]
);
```

### 同步日誌表
```sql
CREATE TABLE sync_logs (
    id SERIAL PRIMARY KEY,
    sync_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),
    datasets_added INT DEFAULT 0,
    datasets_updated INT DEFAULT 0,
    datasets_removed INT DEFAULT 0,
    error_message TEXT
);
```

---

## 🔧 MCP Server 工具列表

### 1. list_domains
- **用途**：列出所有 19 個領域
- **實作**：直接查詢 `domains` 表格
- **回傳格式**：
```json
{
  "domains": [
    {
      "key": "realestate_land",
      "name_zh": "不動產與地政",
      "scope": "土地、建物、房屋...",
      "typical_questions": ["某地段近一年實價中位數"]
    }
  ]
}
```

### 2. search_datasets
- **用途**：搜尋資料集
- **實作**：PostgreSQL full-text search + domain filter
- **參數**：`query`, `domain`, `agency`, `limit`, `quality`, `update_freq`, `fmt`
- **回傳格式**：
```json
{
  "hits": [
    {
      "dataset_id": "83638",
      "name": "臺中市合法民宿",
      "agency": "臺中市政府觀光旅遊局",
      "primary_domain": "culture_tourism_sport",
      "quality_tier": "白金",
      "formats": ["CSV"],
      "update_freq": "不定期更新"
    }
  ],
  "count": 5
}
```

### 3. get_dataset
- **用途**：取得單一資料集的詳細資訊
- **實作**：查詢 `datasets` 表格 + 取得 schema
- **參數**：`dataset_id`, `sample_rows`
- **回傳格式**：
```json
{
  "dataset_id": "83638",
  "name": "臺中市合法民宿",
  "columns": ["民宿登記證編號", "中文名稱", "地址"],
  "schema": { ... },
  "license": "政府資料開放平臺",
  "source_url": "https://data.gov.tw/..."
}
```

### 4. query_rows
- **用途**：SQL 查詢資料列
- **實作**：動態建構 SQL，查詢 `dataset_rows` JSONB 欄位
- **參數**：`dataset_id`, `where`, `columns`, `limit`
- **特色**：支援跨資料源 join（例如：民宿 + 景點）
- **回傳格式**：
```json
{
  "columns": ["民宿登記證編號", "中文名稱", "地址"],
  "rows": [
    ["1", "景雅民宿", "臺中市和平區雪山路..."]
  ],
  "row_count_returned": 20
}
```

### 5. materialize_dataset
- **用途**：下載並匯出完整資料集
- **實作**：從 `dataset_rows` 組裝 CSV/JSON
- **參數**：`dataset_id`, `format`
- **回傳**：CSV 或 JSON 檔案

---

## 🔄 Sync Worker 流程

### 每日同步流程
```
1. 取得資料集目錄
   ↓
2. 比對新/更換/移除的資料集
   ↓
3. 對每個資料集：
   a. 從 data.gov.tw 下載原始檔案
   b. 偵測格式（CSV/JSON/XML/PDF）
   c. 正規化為統一的 JSONB 格式
   d. 分類到 19 領域之一（規則引擎）
   e. 存入資料庫
   ↓
4. 更新 sync_logs
```

### 資料格式處理（必須支援）
- **CSV**：處理全形數字、編碼問題（BIG5/UTF-8）
- **JSON**：處理多層嵌套、編碼問題
- **XML**：標籤萃取、屬性處理
- **PDF**：文字萃取（用 pdfminer 或 OCR）
- **GeoJSON**：轉換為標準格式

### 分類規則（19 領域）
```python
DOMAIN_RULES = {
    "realestate_land": ["不動產", "土地", "建物", "房屋", "地政"],
    "environment": ["PM2.5", "空氣品質", "水庫", "河川", "環境"],
    "health_food": ["醫療", "藥局", "健保", "食品", "衛生"],
    "transport": ["公車", "停車", "交通", "事故", "捷運"],
    # ... 其他 15 個領域
}
```

---

## 📦 Docker Compose 設定

```yaml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:16-3.4
    container_name: mcp-tw-postgres
    environment:
      POSTGRES_DB: tw_opendata
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme123}
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  mcp_server:
    build:
      context: ./mcp_server
      dockerfile: Dockerfile
    container_name: mcp-tw-server
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-changeme123}@postgres:5432/tw_opendata
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  sync_worker:
    build:
      context: ./sync
      dockerfile: Dockerfile
    container_name: mcp-tw-sync
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD:-changeme123}@postgres:5432/tw_opendata
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./sync/data:/app/data
    command: python main.py --schedule "0 3 * * *"
```

---

## 🔐 OpenClaw 對接設定

在 OpenClaw 的 `openclaw.json` 中新增：

```json
{
  "mcp": {
    "servers": {
      "tw-opendata-local": {
        "url": "http://localhost:8000/mcp/",
        "transport": "streamable-http"
      }
    }
  }
}
```

重啟後自動生效。

---

## ⏱️ 開發時程

| 階段 | 工作項目 | 預估時間 |
|------|----------|----------|
| Phase 1 | 環境架設（Docker + PostgreSQL + 初始化） | 1-2 天 |
| Phase 2 | Sync Worker（抓取 + 正規化 + 分類） | 3-5 天 |
| Phase 3 | MCP Server（5個工具實作） | 2-3 天 |
| Phase 4 | 對接 OpenClaw + 測試 | 1 天 |
| Phase 5 | 資料庫 Tuning（優化 50ms 查詢） | 1-2 天 |
| **Total** | | **~2 週** |

---

## 🚀 開始之前先確認

1. **PostgreSQL**：建議用 PostGIS 版本（支援地理資料）
2. **資料庫密碼**：使用 `.env` 檔案管理，不要 hardcode
3. **同步頻率**：建議每天凌晨 3 點（政府資料更新後）
4. **初始化資料**：第一次 sync 需要 6-12 小時下載全部資料

---

## 📝 給接手 AI 的指示

1. **閱讀此檔案**：完全理解專案目標和架構
2. **不要破壞現有系統**：只新增，不修改既有設定
3. **產生 Markdown**：把你的實作計畫寫成 Markdown 格式
4. **可測試的程式碼**：產生的程式碼必須是可執行、可測試的
5. **保持溝通**：有任何問題或最佳化建議，隨時提出

---

## ✅ 成功標準

- [ ] 52,960 筆資料集全部入庫
- [ ] `list_domains` 回傳正確的 19 個領域
- [ ] `search_datasets` 可以在 1 秒內搜尋
- [ ] `query_rows` 可以在 50ms 內回應（對單一資料集）
- [ ] 每日 sync 自動化
- [ ] OpenClaw 無縫對接
- [ ] 0 外部依賴（完全本地運行）
