
import os
import re
import hashlib
from playwright.sync_api import sync_playwright

URL = "https://www.tazkarti.com/#/matches"
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_alert(message):
    import requests
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    )
    response.raise_for_status()

def main():
    print("Ticket Hunter: starting page check", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.on("pageerror", lambda error: print(
            f"PAGE ERROR: {error}", flush=True
        ))

        response = page.goto(
            URL, wait_until="domcontentloaded", timeout=60000
        )
        page.wait_for_timeout(12000)

        try:
            page_text = re.sub(
                r"\s+", " ",
                page.locator("body").inner_text(timeout=15000)
            )
        except Exception as error:
            page_text = ""
            print(f"BODY READ ERROR: {error}", flush=True)

        print(f"HTTP status: {response.status if response else 'no response'}", flush=True)
        print(f"Page title: {page.title()}", flush=True)
        print(f"Visible text length: {len(page_text)}", flush=True)
        print(f"Visible text preview: {page_text[:700]}", flush=True)

        browser.close()

    text = page_text.lower()
    ahly = "al ahly" in text or "الأهلي" in text or "الاهلي" in text
    pyramids = "pyramids" in text or "بيراميدز" in text

    print(f"Ahly found: {ahly}; Pyramids found: {pyramids}", flush=True)

    if ahly and pyramids:
        digest = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
        old = ""

        if os.path.exists("state.txt"):
            with open("state.txt", encoding="utf-8") as f:
                old = f.read().strip()

        if digest != old:
            send_alert(
                "ظهرت أسماء الأهلي وبيراميدز في صفحة تذكرتي. "
                "هذا لا يؤكد توفر التذاكر؛ تحقق يدويًا:\n" + URL
            )
            print("Telegram alert sent.", flush=True)
        else:
            print("Both teams found; page text unchanged.", flush=True)

        with open("state.txt", "w", encoding="utf-8") as f:
            f.write(digest)
    else:
        print("لم تظهر بيانات الفريقين في النص المقروء.", flush=True)

if __name__ == "__main__":
    main()
