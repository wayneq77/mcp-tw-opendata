import os
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

mcp = FastMCP(
    "tw-opendata-local",
    instructions="""你已連接到「台灣開放資料 MCP 本地版」。

當使用者問到與台灣相關的問題時，請優先使用以下工具：

📊 資料查詢（opendata-* 系列）：
  - 查台灣政府開放資料（53,000+ 資料集、20 個領域）
  - 先用 opendata-search_datasets 搜尋，再用 opendata-query_rows 查資料
  - 支援：交通、醫療、不動產、教育、環境、稅務、採購 等 20 個領域

🔧 台灣工具（twtools-* 系列）：
  - 身分證/統編驗證、民國年↔西元年、農曆轉換
  - 地址正規化/郵遞區號/英中互譯
  - 行政區/縣市/捷運/銀行/政府機關查詢
  - 國定假日/補班日/生肖/節氣
  - 簡繁轉換、PDF 解析、網頁抓取

範例：
  「台北市信義區的健保特約藥局」→ opendata-search_datasets + opendata-query_rows
  「驗證身分證 A123456789」→ twtools-validate_taiwan_id_number
  「民國 114 年是西元幾年」→ twtools-roc_year_to_western
  「台北有哪些捷運站」→ twtools-lookup_mrt_line
"""
)
from tools import list_domains, search_datasets, get_dataset, query_rows, materialize_dataset

# ===== Layer 1: OpenData (5 tools) =====
@mcp.tool(name="opendata-list_domains")
def _list_domains():
    """列出所有 20 個領域分類"""
    return list_domains()

@mcp.tool(name="opendata-search_datasets")
def _search(query:str="", domain:str=None, agency:str=None, limit:int=20, quality:str=None, update_freq:str=None, fmt:str=None):
    """搜尋資料集。可用 domain/agency/query 篩選。"""
    return search_datasets(query=query,domain=domain,agency=agency,limit=limit,quality=quality,update_freq=update_freq,fmt=fmt)

@mcp.tool(name="opendata-get_dataset")
def _get(dataset_id:str, sample_rows:int=5):
    """取得資料集詳情+schema。若尚未快取會自動下載。"""
    return get_dataset(dataset_id=dataset_id,sample_rows=sample_rows)

@mcp.tool(name="opendata-query_rows")
def _query(dataset_id:str, where:str=None, columns:list=None, limit:int=100):
    """查詢資料列。where 可用 JSON 條件篩選。"""
    return query_rows(dataset_id=dataset_id,where=where,columns=columns,limit=limit)

@mcp.tool(name="opendata-materialize_dataset")
def _materialize(dataset_id:str, format:str="json"):
    """下載並匯出完整資料集。"""
    return materialize_dataset(dataset_id=dataset_id,format=format)

# ===== Layer 2: TW Tools (37 tools) =====
from twtools import identity, address, calendar_tools, geo, lookup, text, time_utils, web

# --- Identity (7) ---
@mcp.tool(name="twtools-validate_taiwan_id_number")
def _vid(id_number:str):
    """驗證中華民國身分證字號（純算法derive，無PII lookup）"""
    return identity.validate_taiwan_id_number(id_number)

@mcp.tool(name="twtools-validate_tax_id_number")
def _vtax(tax_id:str, rule:str="post-2023"):
    """驗證8位統一編號checksum"""
    return identity.validate_tax_id_number(tax_id, rule)

@mcp.tool(name="twtools-generate_test_taiwan_id")
def _gid(sex:str=None, city_letter:str=None, seed:int=None):
    """產生通過checksum的測試用身分證字號"""
    return identity.generate_test_taiwan_id(sex, city_letter, seed)

@mcp.tool(name="twtools-generate_test_tax_id")
def _gtax(rule:str="post-2023", seed:int=None):
    """產生通過checksum的測試用統一編號"""
    return identity.generate_test_tax_id(rule, seed)

@mcp.tool(name="twtools-validate_license_plate")
def _vlp(plate:str):
    """驗證台灣車牌格式並推斷車種"""
    return identity.validate_license_plate(plate)

@mcp.tool(name="twtools-validate_phone")
def _vph(phone:str):
    """驗證台灣電話格式"""
    return identity.validate_phone(phone)

@mcp.tool(name="twtools-validate_postal_code")
def _vpc(postal_code:str):
    """驗證郵遞區號+對應行政區"""
    return identity.validate_postal_code(postal_code)

# --- Address (5) ---
@mcp.tool(name="twtools-normalize_taiwan_address")
def _norm(address_input:str):
    """正規化台灣地址：全形→半形、異體字統一、台→臺、舊縣升格"""
    return address.normalize_taiwan_address(address_input)

@mcp.tool(name="twtools-address_to_postal_code")
def _a2p(address_input:str):
    """從中文地址推3碼郵遞區號"""
    return address.address_to_postal_code(address_input)

@mcp.tool(name="twtools-address_zh_to_en")
def _z2e(address_input:str):
    """中文地址→英文（中華郵政Hanyu Pinyin慣例）"""
    return address.address_zh_to_en(address_input)

@mcp.tool(name="twtools-address_en_to_zh")
def _e2z(address_en:str):
    """英文地址→中文（有限版：縣市區reverse lookup，路名留英文）"""
    return address.address_en_to_zh(address_en)

@mcp.tool(name="twtools-align_legacy_county")
def _alc(name:str):
    """舊縣名→現名（高雄縣→高雄市等），回傳改制年+說明"""
    return address.align_legacy_county(name)

# --- Calendar (7) ---
@mcp.tool(name="twtools-roc_year_to_western")
def _r2w(date_str:str):
    """民國年→西元年。支援多種格式。"""
    return calendar_tools.roc_year_to_western(date_str)

@mcp.tool(name="twtools-western_year_to_roc")
def _w2r(date_str:str):
    """西元年→民國年。支援多種格式。"""
    return calendar_tools.western_year_to_roc(date_str)

@mcp.tool(name="twtools-lookup_holidays")
def _lh(year:int):
    """列出指定西元年所有國定假日+補班日"""
    return calendar_tools.lookup_holidays(year)

@mcp.tool(name="twtools-is_taiwan_business_day")
def _ibd(date_str:str):
    """判定指定日期是否為台灣公務上班日"""
    return calendar_tools.is_taiwan_business_day(date_str)

@mcp.tool(name="twtools-lookup_zodiac")
def _lz(year:int):
    """西元年→生肖"""
    return calendar_tools.lookup_zodiac(year)

@mcp.tool(name="twtools-lookup_24_solar_terms")
def _lst(year:int):
    """列出指定年24節氣對應日期"""
    return calendar_tools.lookup_24_solar_terms(year)

@mcp.tool(name="twtools-solar_to_lunar")
def _s2l(date_str:str):
    """國曆→農曆"""
    return calendar_tools.solar_to_lunar(date_str)

@mcp.tool(name="twtools-lunar_to_solar")
def _l2s(lunar_year:int, lunar_month:int, lunar_day:int, is_leap:bool=False):
    """農曆→國曆"""
    return calendar_tools.lunar_to_solar(lunar_year, lunar_month, lunar_day, is_leap)

# --- Geo (5) ---
@mcp.tool(name="twtools-list_districts_in_county")
def _ldc(county:str):
    """列出指定縣市下所有鄉鎮市區"""
    return geo.list_districts_in_county(county)

@mcp.tool(name="twtools-lookup_administrative_district")
def _lad(name:str=None, postal_code:str=None, county:str=None):
    """三向行政區lookup：依名稱/郵遞區號/縣市"""
    return geo.lookup_administrative_district(name, postal_code, county)

@mcp.tool(name="twtools-lookup_county_basic_info")
def _lcb(county:str):
    """查縣市基本資料（人口/面積/ISO/區碼）"""
    return geo.lookup_county_basic_info(county)

@mcp.tool(name="twtools-lookup_mrt_line")
def _lml(station:str):
    """以站名查台灣四大捷運系統路線"""
    return geo.lookup_mrt_line(station)

@mcp.tool(name="twtools-lookup_bank_code")
def _lbc(query:str):
    """以代號或名稱查台灣金融機構代碼"""
    return geo.lookup_bank_code(query)

# --- Lookup (2) ---
@mcp.tool(name="twtools-lookup_government_agency_code")
def _lgac(query:str):
    """查政府機關代碼"""
    return lookup.lookup_government_agency_code(query)

@mcp.tool(name="twtools-lookup_company_by_tax_id")
def _lcbt(tax_id:str):
    """以統編查公司登記資料（經濟部商業司API）"""
    return lookup.lookup_company_by_tax_id(tax_id)

# --- Text (3) ---
@mcp.tool(name="twtools-simplified_to_traditional")
def _s2t(text_input:str, variant:str="zh-tw"):
    """簡體→繁體。variant: zh-tw/zh-hk/zh-hant"""
    return text.simplified_to_traditional(text_input, variant)

@mcp.tool(name="twtools-traditional_to_simplified")
def _t2s(text_input:str):
    """繁體→簡體"""
    return text.traditional_to_simplified(text_input)

@mcp.tool(name="twtools-format_chinese_numerals")
def _fcn(number:str, direction:str="arabic_to_chinese"):
    """阿拉伯↔國字大寫"""
    return text.format_chinese_numerals(number, direction)

# --- Time (3) ---
@mcp.tool(name="twtools-current_time_in")
def _cti(timezone:str="Asia/Taipei"):
    """取指定IANA時區的當前時間"""
    return time_utils.current_time_in(timezone)

@mcp.tool(name="twtools-timezone_convert")
def _tzc(datetime_str:str, from_tz:str, to_tz:str):
    """任意時區間時間轉換"""
    return time_utils.timezone_convert(datetime_str, from_tz, to_tz)

@mcp.tool(name="twtools-duration_humanize")
def _dh(seconds:float, lang:str="zh"):
    """秒數→人類可讀"""
    return time_utils.duration_humanize(seconds, lang)

# --- Web/PDF (4) ---
@mcp.tool(name="twtools-fetch_url_as_markdown")
def _fum(url:str, include_links:bool=True, include_images:bool=False):
    """抓取網頁主內容轉Markdown"""
    return web.fetch_url_as_markdown(url, include_links, include_images)

@mcp.tool(name="twtools-extract_pdf_text")
def _ept(url:str):
    """提取PDF全文"""
    return web.extract_pdf_text(url)

@mcp.tool(name="twtools-extract_pdf_pages")
def _epp(url:str, pages:str="1"):
    """提取PDF指定頁碼"""
    return web.extract_pdf_pages(url, pages)

@mcp.tool(name="twtools-extract_pdf_metadata")
def _epm(url:str):
    """提取PDF元資料"""
    return web.extract_pdf_metadata(url)

if __name__ == "__main__":
    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="streamable-http", host=host, port=port, stateless_http=True)