# Smart Expiry Alert System (MVP)

This is a minimal, working starter for a Smart Expiry Alert System using **OCR** and **alerts**.
It lets you upload a product label image, auto-extract an expiry date, store items in SQLite, and send email alerts for items expiring soon.

## 1) Prerequisites
- Python 3.10+
- Tesseract OCR installed
  - Windows: Install from https://github.com/UB-Mannheim/tesseract/wiki
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
- (Optional) Git

## 2) Setup
```bash
cd smart-expiry-alert
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- If on Windows, set `TESSERACT_CMD` to your `tesseract.exe` path.
- Fill SMTP settings (or use a test SMTP server). For Gmail, create an **App Password**.

## 3) Run the app
```bash
streamlit run app.py
```

## 4) Daily alerts (email)
- Run once to test:
  ```bash
  python check_and_notify.py
  ```
- Schedule daily:
  - **Windows Task Scheduler**: Run `python check_and_notify.py` every morning.
  - **Linux/macOS (cron)**: `0 9 * * * /path/to/python /path/to/smart-expiry-alert/check_and_notify.py`

## 5) Optional ML risk model
- Add your usage history to `data/history.csv` (see header in `model.py`).
- Train:
  ```bash
  python model.py --train data/history.csv
  ```

## Project layout
```
smart-expiry-alert/
├─ app.py                # Streamlit UI
├─ ocr.py                # OCR and date extraction
├─ db.py                 # SQLite operations
├─ utils.py              # Helpers (date parsing, etc.)
├─ notifier.py           # Email sender
├─ check_and_notify.py   # Daily alert job
├─ model.py              # (optional) ML risk scoring
├─ requirements.txt
├─ .env.example
└─ data/
   ├─ expiry.db
   └─ images/
```
