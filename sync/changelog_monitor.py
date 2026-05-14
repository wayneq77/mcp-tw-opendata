"""
Changelog Monitor - 自動偵測 Twinkle Hub 官方更新並推播 Telegram 通知
動態解析網頁內容，精準提取每次更新的摘要。
"""
import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup


def send_telegram_message(token, chat_id, message):
    """使用 HTML 格式發送 Telegram 訊息，避免 Markdown 特殊字元干擾"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            print(f"Telegram API 回應異常: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")


def parse_changelog(html):
    """
    從 Changelog 頁面動態解析所有更新條目。
    回傳: (content_hash, date_entries, highlights)
    """
    soup = BeautifulSoup(html, 'html.parser')
    full_text = soup.get_text(separator=" ", strip=True)

    # 用整頁文字的 hash 來偵測任何變動
    content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()[:16]

    # 解析日期標題：抓 📌 開頭的文字
    date_entries = []
    for el in soup.find_all(string=re.compile(r"📌?\s*\d{4}-\d{2}-\d{2}")):
        text = el.strip()
        if text and len(text) > 8:
            date_entries.append(text[:120])

    # 解析 Highlights：從 <li> 元素中抓取以 ✓ 開頭的項目
    highlights = []
    for li in soup.find_all("li"):
        text = li.get_text(strip=True)
        if text.startswith("✓") and len(text) > 2:
            # 截短到 100 字避免訊息太長
            highlights.append(text[:100])

    return content_hash, date_entries, highlights


def check_changelog():
    print("正在檢查 Twinkle Hub 更新...")
    url = "https://hub.twinkleai.tw/changelog"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"無法讀取 Changelog: {e}")
        return

    content_hash, date_entries, highlights = parse_changelog(resp.text)

    # 讀取上次的 hash
    state_file = "/app/data/last_changelog_hash.txt"
    last_hash = ""
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            last_hash = f.read().strip()

    if content_hash == last_hash:
        print("目前為最新狀態，無需重複通知。")
        return

    print("💡 發現新的更新！")

    # 組裝通知訊息（使用 HTML 格式）
    msg_parts = ["🔔 <b>Twinkle Hub 官方更新通知</b>\n"]

    if date_entries:
        msg_parts.append("📌 <b>最新更新：</b>")
        for entry in date_entries[:3]:
            msg_parts.append(f"  • {entry}")

    if highlights:
        msg_parts.append("\n✨ <b>重點摘要：</b>")
        for h in highlights[:8]:
            msg_parts.append(f"  • {h}")

    msg_parts.append(f"\n🔗 完整內容：https://hub.twinkleai.tw/changelog")
    msg = "\n".join(msg_parts)

    # 發送 Telegram
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        send_telegram_message(token, chat_id, msg)
        print("✅ 已發送 Telegram 更新通知。")
    else:
        print("⚠️ 未設定 Telegram Token，僅於日誌顯示更新。")
        print(msg)

    # 儲存新的 hash
    with open(state_file, "w") as f:
        f.write(content_hash)


if __name__ == "__main__":
    check_changelog()
