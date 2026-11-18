
import os
import re
import json
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://www.tazkarti.com/#/matches"
MATCH_DATE = ["23 november 2026", "23 nov 2026", "23/11/2026", "2026-11-23"]

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

STATE_FILE = "state.txt"

def notify(message):
    response = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=20
    )
    response.raise_for_status()

def normalize(value):
    return re.sub(r"\s+", " ", value.lower()).strip()

def find_match_card(page):
    return page.evaluate("""() => {
        const nodes = [...document.querySelectorAll('body *')];
        const norm = s => (s || '').toLowerCase().replace(/\\\\s+/g, ' ').trim();

        const isAhly = s => s.includes('al ahly') || s.includes('الأهلي') || s.includes('الاهلي');
        const isPyramids = s => s.includes('pyramids') || s.includes('بيراميدز');
        const hasDate = s =>
            s.includes('23 november 2026') ||
            s.includes('23 nov 2026') ||
            s.includes('23/11/2026') ||
            s.includes('2026-11-23');

        let candidates = [];

        for (const el of nodes) {
            const t = norm(el.innerText);
            if (!t || t.length > 5000) continue;
            if (!isAhly(t) || !isPyramids(t) || !hasDate(t)) continue;

            candidates.push({
                length: t.length,
                text: el.innerText,
                html: el.outerHTML.slice(0, 12000)
            });
        }

        candidates.sort((a, b) => a.length - b.length);
        return candidates.length ? candidates[0] : null;
    }""")

def main():
    print("Ticket Hunter started", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(locale="en-US")

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(15000)

        card = find_match_card(page)

        print("Page title:", page.title(), flush=True)

        if not card:
            print(
                "Exact match card/date not identified. No alert sent.",
                flush=True
            )
            browser.close()
            return

        card_text = normalize(card["text"])
        print("Exact match card found:", flush=True)
        print(card["text"], flush=True)

        available_words = [
            "buy tickets", "book now", "get tickets",
            "purchase", "available", "احجز الآن",
            "شراء التذاكر", "احجز تذكرتك"
        ]

        unavailable_words = [
            "sold out", "not available", "unavailable",
            "coming soon", "نفدت", "غير متاح",
            "قريباً", "قريبا"
        ]

        available = any(x in card_text for x in available_words)
        unavailable = any(x in card_text for x in unavailable_words)

        browser.close()

    if available and not unavailable:
        status = "AVAILABLE"
    elif unavailable:
        status = "NOT_AVAILABLE"
    else:
        status = "UNKNOWN"

    print("Detected status:", status, flush=True)

    if status != "AVAILABLE":
        print("No booking-open alert sent.", flush=True)
        return

    fingerprint = hashlib.sha256(
        (status + card_text).encode("utf-8")
    ).hexdigest()

    old = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            old = f.read().strip()

    if fingerprint != old:
        notify(
            "🎟️ Ticket Hunter\\n"
            "تم رصد مؤشر فتح الحجز لمباراة الأهلي وبيراميدز "
            "يوم 23 نوفمبر 2026.\\n"
            "افتح تذكرتي وتأكد من الإتاحة وأكمل الحجز بنفسك:\\n"
            + URL
        )
        print("Telegram alert sent.", flush=True)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(fingerprint)

if __name__ == "__main__":
    main()
