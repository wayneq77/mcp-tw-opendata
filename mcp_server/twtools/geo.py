"""行政區/縣市/捷運/郵遞區號查詢 (5 tools)"""
import json, os

_DATA = os.path.join(os.path.dirname(__file__), "data")

def _load(name):
    with open(os.path.join(_DATA, name), encoding="utf-8") as f:
        return json.load(f)

def list_districts_in_county(county: str) -> dict:
    """列出指定縣市下所有鄉鎮市區"""
    from .address import normalize_taiwan_address, _LEGACY
    c = county.strip()
    c = _LEGACY.get(c, c)
    for old, new in [("台北","臺北"),("台中","臺中"),("台南","臺南"),("台東","臺東")]:
        c = c.replace(old, new)
    districts = _load("districts.json")
    if c not in districts:
        # 嘗試模糊匹配
        for k in districts:
            if c in k or k in c:
                c = k
                break
    if c not in districts:
        return {"error": f"查無縣市: {county}", "available": list(districts.keys())}
    info = districts[c]
    result = []
    for dist, code in info["districts"].items():
        result.append({"name": dist, "postal_code": code})
    return {"county": c, "county_code": info.get("code"), "districts": result, "count": len(result)}

def lookup_administrative_district(name: str = None, postal_code: str = None, county: str = None) -> dict:
    """三向行政區 lookup"""
    if not name and not postal_code:
        return {"error": "必須至少給 name 或 postal_code 一項"}
    districts = _load("districts.json")
    results = []
    for cty, info in districts.items():
        if county and county not in cty and cty not in county:
            continue
        for dist, code in info["districts"].items():
            match = False
            if postal_code and code == postal_code.strip()[:3]:
                match = True
            if name and name.strip() in dist:
                match = True
            if match:
                results.append({"county": cty, "district": dist, "postal_code": code, "county_code": info.get("code")})
    return {"results": results, "count": len(results)}

def lookup_county_basic_info(county: str) -> dict:
    """查詢縣市基本資料"""
    from .address import _LEGACY
    c = county.strip()
    c = _LEGACY.get(c, c)
    for old, new in [("台北","臺北"),("台中","臺中"),("台南","臺南"),("台東","臺東")]:
        c = c.replace(old, new)
    info_map = {
        "臺北市":{"population":"~2,560,000","area_km2":271.8,"capital":"中正區","iso":"TW-TPE","area_code":"02"},
        "新北市":{"population":"~4,030,000","area_km2":2052.6,"capital":"板橋區","iso":"TW-NWT","area_code":"02"},
        "桃園市":{"population":"~2,290,000","area_km2":1220.9,"capital":"桃園區","iso":"TW-TAO","area_code":"03"},
        "臺中市":{"population":"~2,820,000","area_km2":2214.9,"capital":"西屯區","iso":"TW-TXG","area_code":"04"},
        "臺南市":{"population":"~1,870,000","area_km2":2191.6,"capital":"安平區","iso":"TW-TNN","area_code":"06"},
        "高雄市":{"population":"~2,740,000","area_km2":2951.8,"capital":"苓雅區","iso":"TW-KHH","area_code":"07"},
        "基隆市":{"population":"~364,000","area_km2":132.8,"capital":"中正區","iso":"TW-KEE","area_code":"02"},
        "新竹市":{"population":"~453,000","area_km2":104.2,"capital":"北區","iso":"TW-HSZ","area_code":"03"},
        "新竹縣":{"population":"~574,000","area_km2":1427.6,"capital":"竹北市","iso":"TW-HSQ","area_code":"03"},
        "苗栗縣":{"population":"~541,000","area_km2":1820.3,"capital":"苗栗市","iso":"TW-MIA","area_code":"037"},
        "彰化縣":{"population":"~1,260,000","area_km2":1074.4,"capital":"彰化市","iso":"TW-CHA","area_code":"04"},
        "南投縣":{"population":"~493,000","area_km2":4106.4,"capital":"南投市","iso":"TW-NAN","area_code":"049"},
        "雲林縣":{"population":"~677,000","area_km2":1290.8,"capital":"斗六市","iso":"TW-YUN","area_code":"05"},
        "嘉義市":{"population":"~266,000","area_km2":60.0,"capital":"東區","iso":"TW-CYI","area_code":"05"},
        "嘉義縣":{"population":"~502,000","area_km2":1903.6,"capital":"太保市","iso":"TW-CYQ","area_code":"05"},
        "屏東縣":{"population":"~817,000","area_km2":2775.6,"capital":"屏東市","iso":"TW-PIF","area_code":"08"},
        "宜蘭縣":{"population":"~454,000","area_km2":2143.6,"capital":"宜蘭市","iso":"TW-ILA","area_code":"03"},
        "花蓮縣":{"population":"~326,000","area_km2":4628.6,"capital":"花蓮市","iso":"TW-HUA","area_code":"03"},
        "臺東縣":{"population":"~217,000","area_km2":3515.3,"capital":"臺東市","iso":"TW-TTT","area_code":"089"},
        "澎湖縣":{"population":"~106,000","area_km2":126.9,"capital":"馬公市","iso":"TW-PEN","area_code":"06"},
        "金門縣":{"population":"~140,000","area_km2":151.7,"capital":"金城鎮","iso":"TW-KIN","area_code":"082"},
        "連江縣":{"population":"~13,000","area_km2":28.8,"capital":"南竿鄉","iso":"TW-LIE","area_code":"0836"},
    }
    if c in info_map:
        return {"county": c, **info_map[c]}
    return {"error": f"查無: {county}", "available": list(info_map.keys())}

def lookup_mrt_line(station: str) -> dict:
    """以站名查捷運路線"""
    s = station.strip()
    mrt = _load("mrt_lines.json")
    results = []
    for system, lines in mrt.items():
        for line, stations in lines.items():
            for st in stations:
                if s in st or st in s:
                    results.append({"system": system, "line": line, "station": st,
                                    "station_index": stations.index(st) + 1, "total_stations": len(stations)})
    return {"query": station, "results": results, "count": len(results)}

def lookup_bank_code(query: str) -> dict:
    """查銀行代碼"""
    q = query.strip()
    banks = _load("banks.json")
    results = []
    for b in banks:
        if q in b["code"] or q in b["name"] or q in b["short"]:
            results.append(b)
    return {"query": q, "results": results, "count": len(results)}
