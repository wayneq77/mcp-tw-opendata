"""文字工具 (3 tools): 簡繁轉換、國字大寫"""

def simplified_to_traditional(text: str, variant: str = "zh-tw") -> dict:
    """簡體 → 繁體"""
    try:
        import opencc
        config = {"zh-tw": "s2twp", "zh-hk": "s2hk", "zh-hant": "s2t"}.get(variant, "s2twp")
        cc = opencc.OpenCC(config + ".json")
        return {"original": text, "converted": cc.convert(text), "variant": variant}
    except ImportError:
        return {"error": "需要 opencc-python-reimplemented 套件"}

def traditional_to_simplified(text: str) -> dict:
    """繁體 → 簡體"""
    try:
        import opencc
        cc = opencc.OpenCC("tw2sp.json")
        return {"original": text, "converted": cc.convert(text)}
    except ImportError:
        return {"error": "需要 opencc-python-reimplemented 套件"}

def format_chinese_numerals(number: str, direction: str = "arabic_to_chinese") -> dict:
    """阿拉伯 ↔ 國字大寫"""
    zh_digits = "零壹貳參肆伍陸柒捌玖"
    zh_units = ["", "拾", "佰", "仟"]
    zh_big = ["", "萬", "億", "兆"]

    if direction == "arabic_to_chinese":
        try:
            n = int(str(number).replace(",", ""))
        except ValueError:
            return {"error": f"無法解析數字: {number}"}
        if n == 0:
            return {"arabic": "0", "chinese": "零"}
        result = ""
        group_idx = 0
        while n > 0:
            group = n % 10000
            n //= 10000
            group_str = ""
            for i in range(4):
                d = group % 10
                group //= 10
                if d > 0:
                    group_str = zh_digits[d] + zh_units[i] + group_str
                elif group_str and not group_str.startswith("零"):
                    group_str = "零" + group_str
            if group_str:
                result = group_str + zh_big[group_idx] + result
            group_idx += 1
        result = result.rstrip("零")
        return {"arabic": str(number), "chinese": result}
    elif direction == "chinese_to_arabic":
        text = str(number)
        mapping = {c: str(i) for i, c in enumerate("零壹貳參肆伍陸柒捌玖")}
        mapping.update({c: str(i) for i, c in enumerate("〇一二三四五六七八九")})
        result = ""
        for c in text:
            if c in mapping:
                result += mapping[c]
        if result:
            return {"chinese": text, "arabic": int(result)}
        return {"error": f"無法解析: {number}"}
    return {"error": f"direction 應為 arabic_to_chinese 或 chinese_to_arabic"}
