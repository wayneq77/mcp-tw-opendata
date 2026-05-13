"""日曆/時間工具 (7 tools): 民國年、農曆、節氣、假日、生肖"""
import json, os, re
from datetime import datetime, date

_DATA = os.path.join(os.path.dirname(__file__), "data")

def roc_year_to_western(date_str: str) -> dict:
    """民國年 → 西元年"""
    s = date_str.strip()
    # "114" → 2025
    m = re.match(r'^(\d{1,3})$', s)
    if m:
        roc = int(m.group(1))
        return {"roc_year": roc, "western_year": roc + 1911}
    # "114-05-04" or "114/05/04"
    m = re.match(r'^(\d{1,3})[/\-.](\d{1,2})[/\-.](\d{1,2})$', s)
    if m:
        roc, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        wy = roc + 1911
        return {"roc_date": s, "western_date": f"{wy}-{mon:02d}-{day:02d}", "western_year": wy}
    # "114年5月4日"
    m = re.match(r'^(\d{1,3})年(\d{1,2})月(\d{1,2})日$', s)
    if m:
        roc, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        wy = roc + 1911
        return {"roc_date": s, "western_date": f"{wy}年{mon}月{day}日", "western_year": wy}
    # "1140504"
    m = re.match(r'^(\d{3})(\d{2})(\d{2})$', s)
    if m:
        roc, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        wy = roc + 1911
        return {"roc_date": s, "western_date": f"{wy}-{mon:02d}-{day:02d}", "western_year": wy}
    return {"error": f"無法解析: {s}"}

def western_year_to_roc(date_str: str) -> dict:
    """西元年 → 民國年"""
    s = date_str.strip()
    m = re.match(r'^(\d{4})$', s)
    if m:
        wy = int(m.group(1))
        return {"western_year": wy, "roc_year": wy - 1911}
    m = re.match(r'^(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})$', s)
    if m:
        wy, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        roc = wy - 1911
        return {"western_date": s, "roc_date": f"{roc}-{mon:02d}-{day:02d}", "roc_year": roc}
    m = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日$', s)
    if m:
        wy, mon, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        roc = wy - 1911
        return {"western_date": s, "roc_date": f"{roc}年{mon}月{day}日", "roc_year": roc}
    return {"error": f"無法解析: {s}"}

def lookup_holidays(year: int) -> dict:
    """列出指定西元年所有國定假日"""
    with open(os.path.join(_DATA, "holidays.json"), encoding="utf-8") as f:
        data = json.load(f)
    yr = str(year)
    holidays = data.get(yr, [])
    makeup = data.get("补班", {}).get(yr, [])
    if not holidays:
        return {"year": year, "error": f"無 {year} 年假日資料（內建 2024-2026）"}
    return {"year": year, "holidays": holidays, "makeup_workdays": makeup, "count": len(holidays)}

def is_taiwan_business_day(date_str: str) -> dict:
    """判定是否為台灣公務上班日"""
    try:
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return {"error": "日期格式錯誤，請用 YYYY-MM-DD"}
    with open(os.path.join(_DATA, "holidays.json"), encoding="utf-8") as f:
        data = json.load(f)
    yr = str(d.year)
    holidays_list = [h["date"] for h in data.get(yr, [])]
    makeup_list = data.get("补班", {}).get(yr, [])
    ds = d.isoformat()
    if ds in makeup_list:
        return {"date": ds, "is_business_day": True, "reason": "補班日"}
    if ds in holidays_list:
        name = next((h["name"] for h in data.get(yr, []) if h["date"] == ds), "假日")
        return {"date": ds, "is_business_day": False, "reason": name}
    if d.weekday() >= 5:
        return {"date": ds, "is_business_day": False, "reason": "週末"}
    return {"date": ds, "is_business_day": True, "reason": "一般工作日"}

def lookup_zodiac(year: int) -> dict:
    """西元年 → 生肖"""
    animals = ["鼠","牛","虎","兔","龍","蛇","馬","羊","猴","雞","狗","豬"]
    idx = (year - 4) % 12
    return {"year": year, "zodiac": animals[idx], "zodiac_en": ["Rat","Ox","Tiger","Rabbit","Dragon","Snake","Horse","Goat","Monkey","Rooster","Dog","Pig"][idx]}

def lookup_24_solar_terms(year: int) -> dict:
    """列出指定年 24 節氣（簡化版，用公式近似）"""
    if year < 1900 or year > 2100:
        return {"error": "僅支援 1900-2100 年"}
    terms = ["小寒","大寒","立春","雨水","驚蟄","春分","清明","穀雨",
             "立夏","小滿","芒種","夏至","小暑","大暑","立秋","處暑",
             "白露","秋分","寒露","霜降","立冬","小雪","大雪","冬至"]
    # Simplified approximation based on average dates
    base_days = [5,20,4,19,6,21,5,20,6,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22]
    base_months = [1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12]
    result = []
    for i in range(24):
        result.append({"name": terms[i], "approx_date": f"{year}-{base_months[i]:02d}-{base_days[i]:02d}"})
    return {"year": year, "terms": result, "note": "日期為近似值，實際以天文觀測為準"}

def solar_to_lunar(date_str: str) -> dict:
    """國曆 → 農曆（簡化版）"""
    try:
        from lunardate import LunarDate
        d = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        ld = LunarDate.fromSolarDate(d.year, d.month, d.day)
        return {"solar_date": date_str, "lunar_year": ld.year, "lunar_month": ld.month,
                "lunar_day": ld.day, "is_leap_month": ld.isLeapMonth}
    except ImportError:
        return {"error": "需要 lunardate 套件", "solar_date": date_str}
    except Exception as e:
        return {"error": str(e)}

def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool = False) -> dict:
    """農曆 → 國曆"""
    try:
        from lunardate import LunarDate
        ld = LunarDate(lunar_year, lunar_month, lunar_day, is_leap)
        sd = ld.toSolarDate()
        return {"lunar": f"{lunar_year}-{lunar_month:02d}-{lunar_day:02d}",
                "solar_date": sd.isoformat(), "is_leap_month": is_leap}
    except ImportError:
        return {"error": "需要 lunardate 套件"}
    except Exception as e:
        return {"error": str(e)}
