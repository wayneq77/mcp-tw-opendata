"""地址工具 (5 tools)"""
import json, os, re

_DATA = os.path.join(os.path.dirname(__file__), "data")

def _load_districts():
    with open(os.path.join(_DATA, "districts.json"), encoding="utf-8") as f:
        return json.load(f)

# 舊名 → 新名
_LEGACY = {"台北市":"臺北市","台中市":"臺中市","台南市":"臺南市","台東縣":"臺東縣",
           "高雄縣":"高雄市","臺北縣":"新北市","台北縣":"新北市","桃園縣":"桃園市","台中縣":"臺中市","台南縣":"臺南市","高雄縣":"高雄市"}

def normalize_taiwan_address(address: str) -> dict:
    """正規化台灣地址：全形→半形、異體字統一、台→臺、舊縣升格"""
    a = address.strip()
    # 全形→半形
    a = a.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    a = a.replace('　', ' ')
    # 異體字
    a = a.replace('巿', '市').replace('区', '區').replace('号', '號').replace('路', '路')
    # 台→臺
    for old, new in [("台北", "臺北"), ("台中", "臺中"), ("台南", "臺南"), ("台東", "臺東")]:
        a = a.replace(old, new)
    # 舊縣升格
    for old, new in _LEGACY.items():
        a = a.replace(old, new)
    return {"original": address, "normalized": a}

def address_to_postal_code(address: str) -> dict:
    """從中文地址推 3 碼郵遞區號"""
    a = normalize_taiwan_address(address)["normalized"]
    districts = _load_districts()
    for county, info in districts.items():
        if county in a:
            for dist, code in info["districts"].items():
                if dist in a:
                    return {"address": address, "postal_code": code, "county": county, "district": dist}
            # 只匹配到縣市
            first_dist = list(info["districts"].keys())[0]
            return {"address": address, "county": county, "warning": "僅匹配到縣市，無法確定區", "postal_code": list(info["districts"].values())[0]}
    return {"address": address, "error": "無法從地址中辨識縣市"}

def address_zh_to_en(address: str) -> dict:
    """中文地址 → 英文（Hanyu Pinyin 慣例）"""
    a = normalize_taiwan_address(address)["normalized"]
    districts = _load_districts()
    county_en = {"臺北市":"Taipei City","新北市":"New Taipei City","桃園市":"Taoyuan City",
                 "臺中市":"Taichung City","臺南市":"Tainan City","高雄市":"Kaohsiung City",
                 "基隆市":"Keelung City","新竹市":"Hsinchu City","新竹縣":"Hsinchu County",
                 "苗栗縣":"Miaoli County","彰化縣":"Changhua County","南投縣":"Nantou County",
                 "雲林縣":"Yunlin County","嘉義市":"Chiayi City","嘉義縣":"Chiayi County",
                 "屏東縣":"Pingtung County","宜蘭縣":"Yilan County","花蓮縣":"Hualien County",
                 "臺東縣":"Taitung County","澎湖縣":"Penghu County","金門縣":"Kinmen County",
                 "連江縣":"Lienchiang County"}
    found_county = None
    found_district = None
    for county in districts:
        if county in a:
            found_county = county
            for dist in districts[county]["districts"]:
                if dist in a:
                    found_district = dist
                    break
            break
    parts = []
    # 提取路名等（保留中文）
    road_part = a
    if found_county:
        road_part = road_part.replace(found_county, "")
    if found_district:
        road_part = road_part.replace(found_district, "")
    road_part = road_part.strip()
    result = {"original": address}
    if road_part:
        result["street_remaining"] = road_part
    if found_district:
        result["district_zh"] = found_district
    if found_county:
        result["county_zh"] = found_county
        result["county_en"] = county_en.get(found_county, found_county)
    return result

def address_en_to_zh(address_en: str) -> dict:
    """英文地址 → 中文（有限版：縣市區做 reverse lookup）"""
    a = address_en.strip()
    en_to_zh = {"Taipei":"臺北市","New Taipei":"新北市","Taoyuan":"桃園市",
                "Taichung":"臺中市","Tainan":"臺南市","Kaohsiung":"高雄市",
                "Keelung":"基隆市","Hsinchu":"新竹","Miaoli":"苗栗縣",
                "Changhua":"彰化縣","Nantou":"南投縣","Yunlin":"雲林縣",
                "Chiayi":"嘉義","Pingtung":"屏東縣","Yilan":"宜蘭縣",
                "Hualien":"花蓮縣","Taitung":"臺東縣","Penghu":"澎湖縣",
                "Kinmen":"金門縣","Lienchiang":"連江縣"}
    # District name mapping (common ones)
    dist_en = {"Zhongzheng":"中正區","Datong":"大同區","Zhongshan":"中山區",
               "Songshan":"松山區","Daan":"大安區","Xinyi":"信義區",
               "Wanhua":"萬華區","Shilin":"士林區","Beitou":"北投區",
               "Neihu":"內湖區","Nangang":"南港區","Wenshan":"文山區",
               "Banqiao":"板橋區","Sanchong":"三重區","Zhonghe":"中和區",
               "Yonghe":"永和區","Tucheng":"土城區","Xindian":"新店區"}
    county_zh = None
    district_zh = None
    confidence = "low"
    for en, zh in en_to_zh.items():
        if en.lower() in a.lower():
            county_zh = zh
            confidence = "high"
            break
    for en, zh in dist_en.items():
        if en.lower() in a.lower().replace(" ", "").replace(".", ""):
            district_zh = zh
            confidence = "high" if county_zh else "medium"
            break
    # 保留路名英文
    street_en = re.sub(r'(,?\s*(City|County|District|Dist\.|Taiwan|ROC)\s*)', '', a, flags=re.I).strip().rstrip(',').strip()
    return {"address_en": address_en, "county_zh": county_zh, "district_zh": district_zh,
            "street_en": street_en, "confidence": confidence,
            "warning": "路名保留英文，英文音譯→中文為 1-to-N 對應，需人工確認" if confidence != "high" else None}

def align_legacy_county(name: str) -> dict:
    """舊縣名 → 現名"""
    n = name.strip()
    legacy_info = {
        "高雄縣": {"new": "高雄市", "year": 2010, "note": "2010年12月25日高雄縣市合併改制"},
        "臺北縣": {"new": "新北市", "year": 2010, "note": "2010年12月25日改制為新北市"},
        "台北縣": {"new": "新北市", "year": 2010, "note": "2010年12月25日改制為新北市"},
        "桃園縣": {"new": "桃園市", "year": 2014, "note": "2014年12月25日改制為直轄市"},
        "台中縣": {"new": "臺中市", "year": 2010, "note": "2010年12月25日臺中縣市合併改制"},
        "台中市": {"new": "臺中市", "year": 2010, "note": "正寫為「臺中市」"},
        "台南縣": {"new": "臺南市", "year": 2010, "note": "2010年12月25日臺南縣市合併改制"},
        "台南市": {"new": "臺南市", "year": 2010, "note": "正寫為「臺南市」"},
        "台北市": {"new": "臺北市", "year": None, "note": "正寫為「臺北市」"},
        "台東縣": {"new": "臺東縣", "year": None, "note": "正寫為「臺東縣」"},
    }
    if n in legacy_info:
        info = legacy_info[n]
        return {"input": n, "current_name": info["new"], "reform_year": info["year"], "note": info["note"]}
    return {"input": n, "current_name": n, "note": "非舊名或無需對齊"}
