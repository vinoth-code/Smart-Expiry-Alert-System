import os
from datetime import date
from dotenv import load_dotenv
from db import get_items
from utils import days_until
from notifier import send_email

load_dotenv()
ALERT_DAYS = int(os.getenv("ALERT_DAYS", "3"))

def build_alerts():
    items = get_items(status="active")
    due = []
    today = date.today().isoformat()
    for it in items:
        d = days_until(it["expiry_date"])
        if d <= ALERT_DAYS:
            due.append((it, d))
    return due

def main():
    due = build_alerts()
    if not due:
        return
    lines = []
    for it, d in due:
        lines.append(f"- {it['name']} (expires {it['expiry_date']} | in {d} days)")
    body = "The following items are nearing expiry:\n\n" + "\n".join(lines)
    send_email("Smart Expiry Alert", body)

if __name__ == "__main__":
    main()
