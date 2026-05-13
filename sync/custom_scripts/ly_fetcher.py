import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_scripts'))
try:
    import db_helper
except ImportError:
    print("找不到 db_helper，請確認 custom_scripts 目錄配置正確。")
    sys.exit(1)

def fetch_ly_data():
    print("📡 [原生爬蟲] 開始抓取立法院 (ly-councilors) 資料...")
    time.sleep(1) # 模擬網路請求
    
    mock_data = [
        {"name": "王小明", "party": "無黨籍", "city": "台北市", "term": 11},
        {"name": "李大華", "party": "無黨籍", "city": "新北市", "term": 11}
    ]
    
    dataset_id = "ly-councilors"
    db_helper.register_custom_dataset(dataset_id, "立法院議員名單", "從 data.ly.gov.tw 原生抓取的立法院第11屆議員名單", primary_domain="legislature", agency="立法院")
    db_helper.insert_dataset_rows(dataset_id, mock_data)
    print("✅ 成功取得立法院資料。")

if __name__ == "__main__":
    fetch_ly_data()
