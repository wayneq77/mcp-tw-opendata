"""時間工具 (3 tools)"""
from datetime import datetime
import pytz

def current_time_in(timezone: str = "Asia/Taipei") -> dict:
    """取指定時區的當前時間"""
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return {"timezone": timezone, "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"),
                "weekday": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][now.weekday()],
                "utc_offset": now.strftime("%z")}
    except pytz.UnknownTimeZoneError:
        return {"error": f"未知時區: {timezone}"}

def timezone_convert(datetime_str: str, from_tz: str, to_tz: str) -> dict:
    """時區轉換"""
    try:
        src = pytz.timezone(from_tz)
        dst = pytz.timezone(to_tz)
    except pytz.UnknownTimeZoneError as e:
        return {"error": f"未知時區: {e}"}
    try:
        dt = datetime.strptime(datetime_str.strip(), "%Y-%m-%d %H:%M:%S")
        dt_src = src.localize(dt)
        dt_dst = dt_src.astimezone(dst)
        return {"from": {"timezone": from_tz, "datetime": dt_src.strftime("%Y-%m-%d %H:%M:%S")},
                "to": {"timezone": to_tz, "datetime": dt_dst.strftime("%Y-%m-%d %H:%M:%S")}}
    except ValueError:
        return {"error": "日期格式錯誤，請用 YYYY-MM-DD HH:MM:SS"}

def duration_humanize(seconds: float, lang: str = "zh") -> dict:
    """秒數 → 人話"""
    s = abs(int(seconds))
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if lang == "zh":
        parts = []
        if d: parts.append(f"{d} 天")
        if h: parts.append(f"{h} 小時")
        if m: parts.append(f"{m} 分鐘")
        if s or not parts: parts.append(f"{s} 秒")
        return {"seconds": seconds, "humanized": " ".join(parts), "lang": "zh"}
    else:
        parts = []
        if d: parts.append(f"{d}d")
        if h: parts.append(f"{h}h")
        if m: parts.append(f"{m}m")
        if s or not parts: parts.append(f"{s}s")
        return {"seconds": seconds, "humanized": " ".join(parts), "lang": "en"}
