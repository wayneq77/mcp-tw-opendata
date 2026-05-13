"""身分證/統編/車牌/電話驗證工具 (7 tools)"""
import re, random

# 身分證加權表
_ID_MAP = {'A':10,'B':11,'C':12,'D':13,'E':14,'F':15,'G':16,'H':17,'I':34,'J':18,
           'K':19,'L':20,'M':21,'N':22,'O':35,'P':23,'Q':24,'R':25,'S':26,'T':27,
           'U':28,'V':29,'W':32,'X':30,'Y':31,'Z':33}
_CITY_MAP = {'A':'臺北市','B':'臺中市','C':'基隆市','D':'臺南市','E':'高雄市','F':'新北市',
             'G':'宜蘭縣','H':'桃園市','I':'嘉義市','J':'新竹縣','K':'苗栗縣','L':'臺中縣',
             'M':'南投縣','N':'彰化縣','O':'新竹市','P':'雲林縣','Q':'嘉義縣','R':'臺南縣',
             'S':'高雄縣','T':'屏東縣','U':'花蓮縣','V':'臺東縣','W':'金門縣','X':'澎湖縣',
             'Y':'陽明山','Z':'連江縣'}

def validate_taiwan_id_number(id_number: str) -> dict:
    """驗證中華民國身分證字號（純算法，無 PII lookup）"""
    id_number = id_number.strip().upper()
    if not re.match(r'^[A-Z]\d{9}$', id_number):
        return {"valid": False, "reason": "格式錯誤：應為 1 字母 + 9 數字"}
    letter = id_number[0]
    n = _ID_MAP.get(letter)
    if n is None:
        return {"valid": False, "reason": f"無效首字母: {letter}"}
    d1, d2 = n // 10, n % 10
    digits = [int(c) for c in id_number[1:]]
    sex_digit = digits[0]
    weights = [1, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    total = d1 * 1 + d2 * 9 + sum(d * w for d, w in zip(digits, weights))
    valid = total % 10 == 0
    return {
        "valid": valid, "id_number": id_number,
        "sex": "男" if sex_digit == 1 else ("女" if sex_digit == 2 else "未知"),
        "registered_city": _CITY_MAP.get(letter, "未知"),
        "reason": None if valid else "checksum 不正確"
    }

def validate_tax_id_number(tax_id: str, rule: str = "post-2023") -> dict:
    """驗證 8 位統一編號"""
    tax_id = tax_id.strip()
    if not re.match(r'^\d{8}$', tax_id):
        return {"valid": False, "reason": "格式錯誤：應為 8 位數字"}
    weights = [1, 2, 1, 2, 1, 2, 4, 1]
    total = 0
    for i, w in enumerate(weights):
        p = int(tax_id[i]) * w
        total += p // 10 + p % 10
    mod = 5 if rule == "post-2023" else 10
    valid = total % mod == 0
    return {"valid": valid, "tax_id": tax_id, "rule": rule,
            "reason": None if valid else f"checksum 不正確 (mod {mod})"}

def generate_test_taiwan_id(sex: str = None, city_letter: str = None, seed: int = None) -> dict:
    """產生通過 checksum 的測試用身分證字號"""
    rng = random.Random(seed)
    letter = (city_letter or rng.choice(list(_ID_MAP.keys()))).upper()
    sex_d = 1 if sex == "male" else (2 if sex == "female" else rng.choice([1, 2]))
    digits = [sex_d] + [rng.randint(0, 9) for _ in range(7)]
    n = _ID_MAP[letter]
    d1, d2 = n // 10, n % 10
    weights = [1, 9, 8, 7, 6, 5, 4, 3, 2]
    total = d1 + d2 * 9 + sum(d * w for d, w in zip(digits, weights))
    check = (10 - total % 10) % 10
    digits.append(check)
    return {"id_number": letter + "".join(str(d) for d in digits), "test_only": True}

def generate_test_tax_id(rule: str = "post-2023", seed: int = None) -> dict:
    """產生通過 checksum 的測試用統一編號"""
    rng = random.Random(seed)
    weights = [1, 2, 1, 2, 1, 2, 4, 1]
    mod = 5 if rule == "post-2023" else 10
    for _ in range(10000):
        digits = [rng.randint(0, 9) for _ in range(8)]
        total = sum((d * w // 10 + d * w % 10) for d, w in zip(digits, weights))
        if total % mod == 0:
            return {"tax_id": "".join(str(d) for d in digits), "rule": rule, "test_only": True}
    return {"error": "無法在合理次數內產生"}

def validate_license_plate(plate: str) -> dict:
    """驗證台灣車牌格式"""
    plate = plate.strip().upper().replace("-", "").replace(" ", "")
    patterns = [
        (r'^[A-Z]{3}\d{4}$', "自用小客車(新式)"),
        (r'^[A-Z]{2}\d{4}$', "自用小客車(舊式)"),
        (r'^\d{4}[A-Z]{2}$', "自用小客車(舊式)"),
        (r'^[A-Z]{2}\d{3}$', "機車(舊式)"),
        (r'^[A-Z]{3}\d{3}$', "機車(新式)"),
        (r'^\d{3}[A-Z]{3}$', "機車(新式)"),
        (r'^[A-Z]\d{2}\d{3}$', "機車"),
    ]
    for pat, vtype in patterns:
        if re.match(pat, plate):
            return {"valid": True, "plate": plate, "vehicle_type": vtype}
    return {"valid": False, "plate": plate, "reason": "不符合已知車牌格式"}

def validate_phone(phone: str) -> dict:
    """驗證台灣電話格式"""
    clean = re.sub(r'[\s\-\(\)]', '', phone.strip())
    clean = re.sub(r'^\+886', '0', clean)
    if re.match(r'^09\d{8}$', clean):
        return {"valid": True, "type": "行動電話", "normalized": clean}
    if re.match(r'^0[2-8]\d{7,8}$', clean):
        return {"valid": True, "type": "市話", "normalized": clean,
                "area_code": re.match(r'^(0\d)', clean).group(1)}
    if re.match(r'^0800\d{6}$', clean):
        return {"valid": True, "type": "免付費", "normalized": clean}
    return {"valid": False, "reason": "不符合台灣電話格式"}

def validate_postal_code(postal_code: str) -> dict:
    """驗證郵遞區號"""
    import json, os
    code = postal_code.strip()[:3]
    if not re.match(r'^\d{3}', code):
        return {"valid": False, "reason": "格式錯誤"}
    data_path = os.path.join(os.path.dirname(__file__), "data", "districts.json")
    with open(data_path, encoding="utf-8") as f:
        districts = json.load(f)
    for county, info in districts.items():
        for dist, pc in info["districts"].items():
            if pc == code:
                return {"valid": True, "postal_code": code, "county": county, "district": dist}
    return {"valid": False, "postal_code": code, "reason": "查無對應行政區"}
