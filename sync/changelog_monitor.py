"""
Changelog Monitor - 自動偵測 Twinkle Hub 官方更新並推播 Telegram 通知
會動態解析網頁內容，精準提取每次更新的摘要，而非使用寫死的關鍵字。
"""
import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            print(f"Telegram API 回應異常: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"Telegram 推播失敗: {e}")


def parse_changelog(html):
    """
    從 Changelog 頁面動態解析所有更新條目。
    回傳: (content_hash, entries_list)
      - content_hash: 整頁內容的 SHA256，用來判斷是否有新變動
      - entries_list: 每筆更新的摘要字串清單
    """
    soup = BeautifulSoup(html, 'html.parser')
    full_text = soup.get_text(separator="\n", strip=True)

    # 用整頁文字的 hash 來偵測任何變動（比寫死關鍵字精確得多）
    content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()[:16]

    # 解析更新條目：抓取所有日期行（格式 📌 2026-05-14 ...）
    entries = []
    for line in full_text.split("\n"):
        line = line.strip()
        # 匹配日期開頭的更新標題行
        if re.match(r"^📌?\s*\d{4}-\d{2}-\d{2}", line):
            entries.append(line)

    # 同時抓取 Highlights 區塊中的重點
    highlights = []
    for line in full_text.split("\n"):
        line = line.strip()
        if line.startswith("- ✓") or line.startswith("✓"):
            highlights.append(line[:80])  # 截短避免訊息太長

    return content_hash, entries, highlights


def check_changelog():
    print("正在檢查 Twinkle Hub 更新...")
    url = "https://hub.twinkleai.tw/changelog"

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"無法讀取 Changelog: {e}")
        return

    content_hash, entries, highlights = parse_changelog(resp.text)

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

    # 組裝通知訊息（動態內容）
    msg_parts = ["🔔 *Twinkle Hub 官方更新通知*\n"]

    if entries:
        msg_parts.append("📌 *最新更新：*")
        for entry in entries[:3]:  # 最多顯示 3 條最新
            msg_parts.append(f"  {entry}")

    if highlights:
        msg_parts.append("\n✨ *重點摘要：*")
        for h in highlights[:6]:  # 最多顯示 6 條重點
            msg_parts.append(f"  {h}")

    msg_parts.append("\n🔗 完整內容：https://hub.twinkleai.tw/changelog")
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
