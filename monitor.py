import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://www.tazkarti.com/"
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_alert(message):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    ).raise_for_status()

def main():
    response = requests.get(
        URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    page_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    current_hash = hashlib.sha256(page_text.encode()).hexdigest()

    old_hash = ""
    if os.path.exists("state.txt"):
        with open("state.txt", encoding="utf-8") as f:
            old_hash = f.read().strip()

    if not old_hash:
        send_alert("Ticket Hunter بدأ المراقبة. دي رسالة تشغيل أولية فقط.")
    elif current_hash != old_hash:
        send_alert(
            "صفحة تذكرتي اتغيرت. افحص تذاكر الأهلي وبيراميدز يدويًا:\n" + URL
        )

    with open("state.txt", "w", encoding="utf-8") as f:
        f.write(current_hash)

if __name__ == "__main__":
    main()
