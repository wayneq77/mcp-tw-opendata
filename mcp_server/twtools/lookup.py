"""查詢工具 (3 tools): 政府機關、公司查統編"""
import json, os

_DATA = os.path.join(os.path.dirname(__file__), "data")

def lookup_government_agency_code(query: str) -> dict:
    """查政府機關代碼"""
    q = query.strip()
    with open(os.path.join(_DATA, "gov_agencies.json"), encoding="utf-8") as f:
        agencies = json.load(f)
    results = []
    for a in agencies:
        if q in a["code"] or q in a["name"]:
            results.append(a)
    return {"query": q, "results": results, "count": len(results)}

def lookup_company_by_tax_id(tax_id: str) -> dict:
    """以統編查公司（經濟部商業司 API）"""
    import requests
    tid = tax_id.strip()
    if len(tid) != 8 or not tid.isdigit():
        return {"error": "統編應為 8 位數字"}
    try:
        url = f"https://data.gcis.nat.gov.tw/od/data/api/5F64D864-61CB-4D0D-8AD9-492047CC1EA6?$format=json&$filter=Business_Accounting_NO eq {tid}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                d = data[0]
                return {"tax_id": tid, "company_name": d.get("Company_Name"),
                        "status": d.get("Company_Status_Desc"), "capital": d.get("Capital_Stock_Amount"),
                        "address": d.get("Company_Location"), "responsible_person": d.get("Responsible_Name")}
            return {"tax_id": tid, "error": "查無此統編"}
        return {"tax_id": tid, "error": f"API 回應 {resp.status_code}"}
    except Exception as e:
        return {"tax_id": tid, "error": f"查詢失敗: {str(e)}"}
