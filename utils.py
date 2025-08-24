from datetime import datetime, date
import dateparser

def parse_date_any(text):
    # Attempts to parse many date formats and returns ISO date string (YYYY-MM-DD)
    if not text:
        return None
    dt = dateparser.parse(text, settings={
        'PREFER_DAY_OF_MONTH': 'first',
        'DATE_ORDER': 'DMY',
        'RETURN_AS_TIMEZONE_AWARE': False,
    })
    if not dt:
        return None
    return dt.date().isoformat()

def days_until(iso_date_str):
    try:
        target = datetime.fromisoformat(iso_date_str).date()
    except ValueError:
        target = datetime.strptime(iso_date_str, "%Y-%m-%d").date()
    today = date.today()
    return (target - today).days

def is_future_or_today(iso_date_str):
    try:
        d = datetime.fromisoformat(iso_date_str).date()
    except ValueError:
        d = datetime.strptime(iso_date_str, "%Y-%m-%d").date()
    return d >= date.today()
