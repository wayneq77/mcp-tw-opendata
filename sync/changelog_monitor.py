import os
import requests
from bs4 import BeautifulSoup

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")

def check_changelog():
    print("正在檢查 Twinkle Hub 更新...")
    url = "https://hub.twinkleai.tw/changelog"
    
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"無法讀取 Changelog: {e}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # 簡單擷取最新的更新內容 (以 pcc-tender 和 ly-councilors 為例，實作上可針對特定 DOM)
    text = soup.get_text()
    
    # 找尋關鍵字作為更新識別 (這裡可以根據真實網頁結構更精確擷取)
    new_features = []
    if "pcc-tender" in text:
        new_features.append("- `pcc-tender`: 政府採購招標公告 (162,189 筆)")
    if "ly-councilors" in text:
        new_features.append("- `ly-councilors` / `ly-votes`: 立法院與議員資料")
        
    if not new_features:
        print("沒有偵測到重大資料集更新。")
        return
        
    update_hash = str(hash("".join(new_features)))
    
    state_file = "/app/data/last_changelog_hash.txt"
    last_hash = ""
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last_hash = f.read().strip()
            
    if update_hash != last_hash:
        print("💡 發現新的更新！")
        msg = "🔔 **Twinkle Hub 本地同步服務通知**\n\n官方已釋出新資料集：\n" + "\n".join(new_features) + "\n\n系統將嘗試透過原生爬蟲自動抓取這些特規資料集！"
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            send_telegram_message(token, chat_id, msg)
            print("✅ 已發送 Telegram 更新通知。")
        else:
            print("⚠️ 未設定 Telegram Token，僅於日誌顯示更新。")
            
        with open(state_file, "w") as f:
            f.write(update_hash)
    else:
        print("目前為最新狀態，無需重複通知。")

if __name__ == "__main__":
    check_changelog()
