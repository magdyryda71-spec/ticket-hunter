
import os
import re
import hashlib
from playwright.sync_api import sync_playwright

URL = "https://www.tazkarti.com/#/matches"
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_alert(message):
    import requests
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    ).raise_for_status()

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(12000)
        page_text = re.sub(r"\s+", " ", page.locator("body").inner_text())
        browser.close()

    text = page_text.lower()

    ahly = "al ahly" in text or "الأهلي" in text or "الاهلي" in text
    pyramids = "pyramids" in text or "بيراميدز" in text

    if ahly and pyramids:
        digest = hashlib.sha256(page_text.encode()).hexdigest()
        old = ""
        if os.path.exists("state.txt"):
            old = open("state.txt", encoding="utf-8").read().strip()

        if digest != old:
            send_alert(
                "Ticket Hunter: ظهرت بيانات الأهلي وبيراميدز في صفحة مباريات تذكرتي. "
                "تحقق من حالة التذاكر يدويًا:\n" + URL
            )

        with open("state.txt", "w", encoding="utf-8") as f:
            f.write(digest)

    else:
        print("لم تظهر بيانات الفريقين في الصفحة حتى الآن.")

if __name__ == "__main__":
    main()
