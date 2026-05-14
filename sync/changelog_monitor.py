"""
Changelog Monitor - 自動偵測 Twinkle Hub 官方更新並推播 Telegram 通知
以 <article> 為單位解析每筆更新，呈現中文內容，支援同一天多筆更新。
"""
import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup


def send_telegram_message(token, chat_id, message):
    """使用 HTML 格式發送 Telegram 訊息"""
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
    從 Changelog 頁面動態解析所有更新條目（以 <article> 為單位）。
    回傳: (content_hash, updates_list)
      updates_list: [{"date": "2026-05-14", "highlights": ["✓...","✓..."]}]
    """
    soup = BeautifulSoup(html, 'html.parser')
    full_text = soup.get_text(separator=" ", strip=True)
    content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()[:16]

    updates = []
    articles = soup.find_all("article")
    for art in articles:
        # 找日期
        date_match = art.find(string=re.compile(r"\d{4}-\d{2}-\d{2}"))
        date_str = ""
        if date_match:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", date_match)
            if m:
                date_str = m.group(1)

        # 找日期標題行（📌 開頭的完整行）
        title = ""
        pin_el = art.find(string=re.compile(r"📌"))
        if pin_el:
            title = pin_el.strip()[:120]

        # 找 Highlights（<li> 中以 ✓ 開頭的項目）
        highlights = []
        for li in art.find_all("li"):
            text = li.get_text(strip=True)
            if text.startswith("✓") and len(text) > 2:
                highlights.append(text[:100])

        if date_str or highlights:
            updates.append({
                "date": date_str,
                "title": title,
                "highlights": highlights
            })

    return content_hash, updates


def check_changelog():
    print("正在檢查 Twinkle Hub 更新...")
    # 不帶 /en/ 的 URL 會回傳中文版
    url = "https://hub.twinkleai.tw/changelog"

    try:
        resp = requests.get(url, timeout=15, headers={"Accept-Language": "zh-TW,zh;q=0.9"})
        resp.raise_for_status()
    except Exception as e:
        print(f"無法讀取 Changelog: {e}")
        return

    content_hash, updates = parse_changelog(resp.text)

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

    # 組裝通知訊息（按日期分組，顯示每筆更新的重點）
    msg_parts = ["🔔 <b>Twinkle Hub 官方更新通知</b>\n"]

    for upd in updates[:5]:  # 最多顯示 5 個更新區塊
        date = upd["date"] or "未知日期"
        title = upd["title"]

        if title:
            msg_parts.append(f"\n📌 <b>{title}</b>")
        else:
            msg_parts.append(f"\n📌 <b>{date}</b>")

        for h in upd["highlights"][:4]:  # 每區塊最多 4 條重點
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
