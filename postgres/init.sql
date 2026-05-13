-- ============================================
-- Twinkle Hub 本地複製計畫 - 資料庫初始化
-- ============================================

-- 1. 資料集目錄表
CREATE TABLE IF NOT EXISTS datasets (
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
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. 已正規化的資料列
CREATE TABLE IF NOT EXISTS dataset_rows (
    id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(50) NOT NULL,
    row_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id) ON DELETE CASCADE
);

-- 3. 領域定義表（19領域）
CREATE TABLE IF NOT EXISTS domains (
    key VARCHAR(50) PRIMARY KEY,
    name_zh VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    role VARCHAR(20),
    scope TEXT,
    typical_questions TEXT[],
    anchor_examples TEXT[]
);

-- 4. 同步日誌表
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    sync_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),
    datasets_added INT DEFAULT 0,
    datasets_updated INT DEFAULT 0,
    datasets_removed INT DEFAULT 0,
    error_message TEXT
);

-- ============================================
-- 索引
-- ============================================

-- datasets 索引
CREATE INDEX IF NOT EXISTS idx_datasets_dataset_id ON datasets(dataset_id);
CREATE INDEX IF NOT EXISTS idx_datasets_primary_domain ON datasets(primary_domain);
CREATE INDEX IF NOT EXISTS idx_datasets_agency ON datasets(agency);
CREATE INDEX IF NOT EXISTS idx_datasets_update_freq ON datasets(update_freq);
CREATE INDEX IF NOT EXISTS idx_datasets_quality_tier ON datasets(quality_tier);
CREATE INDEX IF NOT EXISTS idx_datasets_last_sync ON datasets(last_sync);
CREATE INDEX IF NOT EXISTS idx_datasets_search_vector ON datasets USING GIN(search_vector);

-- dataset_rows 索引
CREATE INDEX IF NOT EXISTS idx_dataset_rows_dataset_id ON dataset_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_rows_row_data_gin ON dataset_rows USING GIN(row_data);

-- ============================================
-- 初始化 19 領域
-- ============================================

INSERT INTO domains (key, name_zh, name_en, role, scope, typical_questions, anchor_examples) VALUES
('realestate_land', '不動產與地政', 'Real Estate & Land', 'topical',
 '土地、建物、房屋、都市計畫、地價、建照使照、不動產交易、租金',
 ARRAY['某地段近一年實價中位數', '某學區內近期使用執照核發數', '都市更新案件清單'],
 ARRAY['臺南市不動產經紀業違規裁罰名單', '臺北市115年度使用執照摘要', '臺北市都市計畫委員會議紀錄']),

('economy_business', '經濟、產業、公司商業', 'Economy & Business', 'topical',
 '營業/公司/工廠登記、產業統計、進出口貿易、景氣/物價指數、金融市場、上市櫃公司、公平交易',
 ARRAY['某統編公司歷史登記變更', '本月某產業景氣燈號', '某產業上市公司營收'],
 ARRAY['上市公司公司治理之相關規程規則', '工程技術顧問公司登記按營業範圍技師科別查詢表', '全國營業(稅籍)登記(停業)資料集']),

('procurement_subsidy', '政府採購與補助', 'Procurement & Subsidy', 'topical',
 '招標/決標公告、補助案件、獎助、政府支出予個人',
 ARRAY['某廠商近五年得標金額', '某機關本月補助清單'],
 ARRAY['衛生福利部食品藥物管理署公務預算補助案件資料集', '國立臺灣圖書館視障/身心障礙研究優良學位論文歷年獎助名單', '桃園市原住民族學生清寒獎助金及優秀獎學金獎勵情形']),

('public_finance', '政府預決算與會計', 'Public Finance', 'topical',
 '中央/地方總預算、會計月報、附屬單位預算、債務、國庫、主計統計',
 ARRAY['某機關歷年預算趨勢', '中央政府公共債務餘額'],
 ARRAY['國庫券買賣斷成交行情資訊', '國庫券之發行、償還及未償還餘額表', '109年度教育部所屬機構作業基金附屬單位預算會計月報']),

('tax_revenue', '稅務與稅收', 'Tax & Revenue', 'topical',
 '綜合所得稅、營業稅、地價/房屋/牌照稅、稅捐稽徵、申報核定統計',
 ARRAY['某縣市本月稅收結構', '某稅目歷年實徵淨額'],
 ARRAY['地方檢察署執行違反稅捐稽徵法案件裁判確定人數(統計)', '各項稅捐實徵淨額與預算數及上年同期比較 -本月數', '新北巿各項稅捐實徵淨額與預算數及上年同期比較－累計數']),

('transport', '交通運輸、道路與停車', 'Transport', 'topical',
 '車禍事故、公車/客運/捷運/鐵路/航班、停車場、即時路況、油價、車籍、道路設施',
 ARRAY['某路口近一年事故數', '即時公車到站', '本市公有停車場剩餘車位'],
 ARRAY['新北市路邊收費停車場停車欠費查詢', '臺北市停車管理工程處公有收費停車場收入金額', '臺北市道路交通事故按月別']),

('public_safety', '治安、警消與災防', 'Public Safety', 'topical',
 '刑案、警政、消防/救護、火災/溺水/地震/風災、110/119',
 ARRAY['本市本月詐騙手法統計', '即時災害示警', '消防救護案件'],
 ARRAY['消防榮譽榜─每月績優人員', '110年臺南市緊急救護服務統計', '彰化縣消防緊急救護服務']),

('judicial_legal', '司法、法務、校正與裁罰', 'Judicial & Legal', 'topical',
 '法院判決、檢察偵查/起訴、校正/監所/受刑人、訴願、政府機關裁罰名單',
 ARRAY['某公司被金管會裁罰歷史', '某地檢偵查終結概況'],
 ARRAY['上市公司金管會證券期貨局裁罰案件專區', '臺灣南投地方檢察署偵查終結公告', '法制司訴願業務收結案統計']),

('health_food', '醫療、衛生、食品與藥物', 'Healthcare & Food', 'topical',
 '醫事機構、健保特約、藥局、藥品/食品許可、疫情、長照、母嬰親善、食安',
 ARRAY['住家附近健保藥局', '某藥品/醫材許可資訊', '近期傳染病通報'],
 ARRAY['健保特約醫事機構-區域醫院', '國際重要疫情資訊', '雲林縣長照資源C級單位']),

('environment', '環境、氣象、生態與水文', 'Environment', 'topical',
 '空品 AQI、河川水質、雨量、水庫、廢棄物回收、林班、生態保育、噪音、碳排',
 ARRAY['今日本區 AQI', '某河川水質歷史', '本市資源回收成果'],
 ARRAY['雲林縣應回收廢棄物回收處理業', '水庫每日營運狀況', '空氣品質指標(AQI)']),

('education_research', '教育與科研', 'Education & Research', 'topical',
 '各級學校、教師/學生統計、補習班、圖書館、科研計畫、專利、學位論文',
 ARRAY['某學區學校清單', '某學校歷年學生數', '某機構研究專利'],
 ARRAY['全國立案短期補習班基本資料', '專利案件數量統計', '全國各級學校統一編號資料集']),

('agriculture_fisheries', '农林漁牧', 'Agriculture & Fisheries', 'topical',
 '農產交易、畜牧場、漁港/漁船、農藥/肥料、農會、養殖、畜產統計',
 ARRAY['某果菜市場今日交易行情', '某縣畜牧場分布'],
 ARRAY['農藥廢容器回收方式', '畜牧場用藥監測資訊', '「金融卡-金融機構屬性」結構比統計(月報)']),

('labor_employment', '勞動與就業', 'Labor & Employment', 'topical',
 '違反勞動法令、薪資、職缺、職業訓練、勞退/勞保、職災',
 ARRAY['某雇主違反勞動法令紀錄', '某產業薪資中位數'],
 ARRAY['櫃買「勞工就業88指數」歷史收盤指數', '違反勞動法令事業單位-勞工退休金條例', '勞工體格及健康檢查認可醫療機構']),

('social_population', '社會福利、戶政、人口、選舉與公務人事', 'Social & Population', 'topical',
 '人口/戶籍/出生/死亡/結婚/離婚、低收入戶、身心障礙、原住民/新住民、選舉投票、公務人員事',
 ARRAY['某選區歷次得票結構', '某縣身心障礙人口', '本市本月人口變動'],
 ARRAY['地方檢察署辦理違反公職人員選舉罷免法案件偵查終結人數(統計)', '農民健康保險生效中身心障礙被保險人人數統計表', '臺北市低收入戶及補助按月別']),

('culture_tourism_sport', '文化、觀光與體育', 'Culture & Tourism', 'topical',
 '景點、博物館、古蹟、寺廟、活動行事曆、體育場館、運動賽事',
 ARRAY['本週某縣市活動', '某博物館館藏'],
 ARRAY['臺北市道路申請活動使用管制圖資', '雲林縣政府全球資訊網活動行事曆', '臺北市市政網站整合平台之熱門活動']),

('foreign_affairs', '外交、領事與兩岸', 'Foreign Affairs', 'topical',
 '外交部公告、領事/簽證/護照、駐外館處、兩岸貿易/政策/案件、僑務、國際合作、新南向、邦交國',
 ARRAY['某國家近年我國進出口金額', '近期外交部聲明 / 兩岸政策談話', '簽證 / 護照申辦規定', '駐外館處清單與聯絡資訊'],
 ARRAY['外交部全球資訊網-中文版-最新消息', '對中國大陸及香港出口－按主要貨品分', '兩岸貿易金額統計']),

('gov_publication', '政府公告與檔案', 'Government Publication', 'meta',
 '機關新聞稿、公報、最新消息、電子公布欄、公文範本、檔案目錄、施政方針、資訊公開申請、公共政策參與',
 ARRAY['本週某機關新聞稿', '行政院公報全文檢索', '某類公文 / 表單範本', '政府資訊公開申請統計'],
 ARRAY['全國政府機關電子公布欄公告資訊', '政府資料開放平臺「最新消息」刊登清單', '公共政策網路參與平台-提點子(行政院版本)']),

('geo_basemap', '地理底圖（橫向層）', 'Geographic Basemap', 'horizontal',
 '行政區界、村里界、門牌、坐標、路網、河系、土地利用',
 ARRAY['作為其他資料集的 join 來源；空間查詢'],
 ARRAY['環保餐廳環境即時通地圖資料', '新北市門牌位置數值資料', '臺中市114年GIS門牌號碼各月份版本']),

('utilities_telecom', '能源、水電瓦斯與電信（橫向層）', 'Utilities & Telecom', 'horizontal',
 '電力供需、加油站、自來水、瓦斯、再生能源、電信與寬頻、無線網路',
 ARRAY['即時電力負載', '某行政區自來水水質', '某地加油站清單'],
 ARRAY['自來水管承裝商狀態統計', '公司登記(依營業項目別)－加油站業', '臺北市自來水及天然氣供應按月別']),

('legislature', '立法院/國會', 'Legislature', 'topical',
 '立法院議案、法律提案、表決、公報、質詢、發言、IVOD 影音索引、立委個人資料、選區、會議記錄。',
 ARRAY['某委員第N屆提了哪些法案', '某黨團對 X 議案的表決傾向', '某議題在公報的歷次發言'],
 ARRAY['立法院議案', '立法院委員個人資料與選區', '立法院公報目錄']);

-- ============================================
-- 全文搜尋觸發器（自動更新 search_vector）
-- ============================================

CREATE OR REPLACE FUNCTION update_datasets_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('simple', COALESCE(NEW.name_zh, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.name_en, '')), 'A') ||
        setweight(to_tsvector('simple', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('simple', COALESCE(NEW.agency, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS datasets_search_vector_trigger ON datasets;
CREATE TRIGGER datasets_search_vector_trigger
    BEFORE INSERT OR UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_datasets_search_vector();

-- ============================================
-- 版本的 View（方便除錯）
-- ============================================

CREATE OR REPLACE VIEW domain_summary AS
SELECT 
    primary_domain,
    COUNT(*) as dataset_count,
    MAX(last_sync) as last_sync
FROM datasets
GROUP BY primary_domain;