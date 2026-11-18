
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
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=20
    )
    response.raise_for_status()


def main():
    print("=== TICKET HUNTER STARTED ===", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.on(
            "pageerror",
            lambda error: print(f"PAGE ERROR: {error}", flush=True)
        )

        response = page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(15000)

        try:
            page_text = re.sub(
                r"\s+",
                " ",
                page.locator("body").inner_text(timeout=20000)
            )
        except Exception as error:
            page_text = ""
            print(f"READ ERROR: {error}", flush=True)

        print(
            f"HTTP STATUS: {response.status if response else 'NO RESPONSE'}",
            flush=True
        )

        print(f"PAGE TITLE: {page.title()}", flush=True)
        print(f"TEXT LENGTH: {len(page_text)}", flush=True)

        print("=== FULL PAGE TEXT ===", flush=True)
        print(page_text, flush=True)
        print("=== END PAGE TEXT ===", flush=True)

        browser.close()

    text = page_text.lower()

    ahly = (
        "al ahly" in text
        or "الأهلي" in text
        or "الاهلي" in text
    )

    pyramids = (
        "pyramids" in text
        or "بيراميدز" in text
    )

    print(f"AHLY FOUND: {ahly}", flush=True)
    print(f"PYRAMIDS FOUND: {pyramids}", flush=True)

    if not page_text:
        print("ERROR: NO PAGE TEXT READ", flush=True)
        return

    if ahly and pyramids:
        print(
            "Both team names appear on the page. "
            "This does NOT confirm a match or ticket availability.",
            flush=True
        )
    else:
        print(
            "One or both team names were not found.",
            flush=True
        )

    print("=== CHECK FINISHED ===", flush=True)


if __name__ == "__main__":
    main()
