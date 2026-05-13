"""
Domain Classifier - 19領域自動分類器
使用規則引擎對資料集進行分類
"""

# 19領域的關鍵字規則
DOMAIN_KEYWORDS = {
    "realestate_land": [
        "不動產", "土地", "建物", "房屋", "地政", "地價", "建照", "使照",
        "不動產交易", "租金", "實價", "都市計畫", "城鄉", "測量", "地籍"
    ],
    "economy_business": [
        "公司", "商業", "登記", "營業", "工廠", "產業", "貿易", "進出口",
        "景氣", "物價", "金融市場", "上市", "櫃買", "公平交易", "統一編號"
    ],
    "procurement_subsidy": [
        "採購", "招標", "決標", "補助", "獎助", "政府支出", "標案", "投標"
    ],
    "public_finance": [
        "預算", "決算", "會計", "債務", "國庫", "主計", "財務", "歲入", "歲出"
    ],
    "tax_revenue": [
        "稅務", "稅收", "所得稅", "營業稅", "地價稅", "房屋稅", "牌照稅",
        "稅捐", "稽徵", "繳稅"
    ],
    "transport": [
        "交通", "運輸", "公車", "客運", "捷運", "鐵路", "航班", "停車",
        "事故", "路況", "油價", "車籍", "道路"
    ],
    "public_safety": [
        "治安", "警政", "消防", "救護", "災害", "地震", "颱風", "溺水",
        "110", "119", "警局", "刑事"
    ],
    "judicial_legal": [
        "司法", "法院", "判決", "檢察", "法務", "裁罰", "訴願", "監所",
        "受刑人", "起訴"
    ],
    "health_food": [
        "醫療", "衛生", "食品", "藥物", "健保", "藥局", "醫事機構", "疫情",
        "長照", "食安", "病房", "中醫", "西醫"
    ],
    "environment": [
        "環境", "氣象", "生態", "水文", "空品", "AQI", "PM2.5", "河川",
        "水庫", "廢棄物", "回收", "空氣", "水質", "生態"
    ],
    "education_research": [
        "教育", "學校", "學生", "教師", "補習班", "圖書館", "科研", "專利",
        "學位", "論文", "招生", "录取"
    ],
    "agriculture_fisheries": [
        "農業", "漁業", "畜牧", "農產", "漁港", "漁船", "農藥", "肥料",
        "農會", "養殖", "畜產", "水果", "蔬菜"
    ],
    "labor_employment": [
        "勞動", "就業", "薪資", "職缺", "職業訓練", "勞保", "勞退", "職災",
        "違反勞動", "雇用"
    ],
    "social_population": [
        "社會福利", "人口", "戶政", "出生", "死亡", "結婚", "離婚", "低收入",
        "身心障礙", "原住民", "新住民", "選舉", "投票"
    ],
    "culture_tourism_sport": [
        "文化", "觀光", "旅遊", "景點", "博物館", "古蹟", "寺廟", "活動",
        "體育", "運動", "賽事", "民宿", "公園"
    ],
    "foreign_affairs": [
        "外交", "兩岸", "領事", "簽證", "護照", "外交部", "僑務", "邦交",
        "新南向", "駐外"
    ],
    "gov_publication": [
        "政府公告", "公報", "新聞稿", "公文", "檔案", "資訊公開", "政策",
        "法規", "函釋"
    ],
    "geo_basemap": [
        "地理", "座標", "圖資", "GIS", "經緯度", "村里", "行政區", "門牌",
        "路網", "河川"
    ],
    "utilities_telecom": [
        "能源", "電力", "水電", "瓦斯", "加油站", "自來水", "電信", "寬頻",
        "再生能源", "天然氣"
    ],
    "legislature": [
        "立法院", "國會", "立委", "議案", "法案", "提案", "表決", "公報",
        "質詢", "IVOD", "議事", "黨團", "委員會", "選區", "議員"
    ]
}

def classify(text: str) -> str:
    """
    根據文字內容分類到 19 領域之一
    
    Args:
        text: 資料集的名稱或描述
        
    Returns:
        分類的 domain key
    """
    if not text:
        return "gov_publication"  # 預設分類
    
    text = text.lower()
    scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword.lower() in text:
                score += 1
        if score > 0:
            scores[domain] = score
    
    if not scores:
        return "gov_publication"  # 預設分類
    
    # 回傳最高分的 domain
    return max(scores, key=scores.get)

def get_domain_priority(domain: str) -> int:
    """取得領域的優先度（用於排序）"""
    # 主要領域優先於橫向領域
    primary_domains = [
        "realestate_land", "economy_business", "procurement_subsidy",
        "public_finance", "tax_revenue", "transport", "public_safety",
        "judicial_legal", "health_food", "environment", "education_research",
        "agriculture_fisheries", "labor_employment", "social_population",
        "culture_tourism_sport", "foreign_affairs", "gov_publication"
    ]
    
    if domain in primary_domains:
        return primary_domains.index(domain)
    
    # 橫向領域排在後面
    horizontal = ["geo_basemap", "utilities_telecom"]
    if domain in horizontal:
        return len(primary_domains) + horizontal.index(domain)
    
    return 999