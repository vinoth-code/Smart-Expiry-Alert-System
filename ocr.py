# ocr.py
import os
import re
import cv2
import pytesseract
from dotenv import load_dotenv
from utils import parse_date_any

load_dotenv()
TESSERACT_CMD = os.getenv("TESSERACT_CMD") or ""
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# -------------------------------
# Regex patterns (supports: 12/07/2025, 2025-07-12, 12 July 2025,
# July 12, 2025, MAR 2026, 03/2026, 2026/03)
# -------------------------------
MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december)"
DATE_REGEXPS = [
   
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",         # 12/07/2025
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",           # 2025-07-12
    r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b",     # 12 July 2025
    r"\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}\b",   # July 12, 2025
    r"\b[A-Za-z]{3,9}\s*\d{2,4}\b",               # MAR2026, MARCH2026 ✅
    r"\b\d{1,2}[/-]\d{4}\b",                      # 03/2026 ✅
    r"\b\d{4}[/-]\d{1,2}\b",                      # 2026/03 ✅
    r"\b\d{6,8}\b",                               # 032026 or 230326 ✅
]

# Words that indicate the number is an EXPIRY
EXPIRY_KEYS = [
    "exp", "expiry", "expires", "expdate", "use by", "use before",
    "best before", "bestbefore", "bb", "bbd", "bb date", "expiry date"
]
# Words that indicate MANUFACTURE/PACKED (to be de-prioritized/ignored)
MFG_KEYS = ["mfg", "mfd", "pkd", "packed on", "packed", "manufacture", "manufactured", "prod", "production"]

def preprocess_for_ocr(img_bgr):
    """Basic denoise + threshold for better OCR."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thr = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    return thr

def run_ocr(image_path: str) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    proc = preprocess_for_ocr(img)
    # --psm 6: Assume a block of text
    text = pytesseract.image_to_string(proc, config="--psm 6")
    return text

def _has_any(s: str, keys: list[str]) -> bool:
    s = s.lower()
    return any(k in s for k in keys)

def extract_best_expiry(text: str):
    """
    Scan line-by-line, score each found date using nearby context.
    Priority:
      - dates on/near lines with EXPIRY keywords
      - far from MFG/PKD keywords
    We also filter implausible years.
    """
    lines = [ln.strip() for ln in text.splitlines()]
    candidates = []  # (iso_date, score, idx, raw_match)

    for i, line in enumerate(lines):
        # context window: current line ± 1 line
        context_lines = lines[max(0, i-1): min(len(lines), i+2)]
        context = " ".join(context_lines)
        for rx in DATE_REGEXPS:
            for m in re.findall(rx, line, flags=re.IGNORECASE):
                iso = parse_date_any(m)
                if not iso:
                    continue

                # Year sanity check (2000..2050)
                year = int(iso[:4])
                if year < 2000 or year > 2050:
                    continue

                score = 0
                # strong boost if expiry keywords on this or nearby lines
                if _has_any(context, EXPIRY_KEYS):
                    score += 5
                # penalty if manufacture/packed words are nearby
                if _has_any(context, MFG_KEYS):
                    score -= 4

                # slight bonus if month is textual (e.g., "MAR 2026")
                if re.search(MONTH, m, re.IGNORECASE):
                    score += 1

                # Prefer future dates (today-or-future is inherently higher value in app logic)
                # Here we simply add a tiny bias to larger (later) ISO dates by scoring later years
                score += (year - 2000) * 0.01

                candidates.append((iso, score, i, m))

    if not candidates:
        return None

    # 1) Prefer highest score
    candidates.sort(key=lambda t: (t[1], t[0]))  # by score, then by date (latest)
    best_iso, _, _, _ = candidates[-1]
    return best_iso

def extract_expiry_from_image(image_path: str):
    """
    Public API used by app.py
    Returns: (best_expiry_iso_date or None, raw_ocr_text)
    """
    text = run_ocr(image_path)

    # First pass with scoring
    best = extract_best_expiry(text)
    if best:
        return best, text

    # Fallback (very rare): try a loose search on full text
    flat = " ".join(text.splitlines())
    for rx in DATE_REGEXPS:
        m = re.search(rx, flat, re.IGNORECASE)
        if m:
            iso = parse_date_any(m.group(0))
            if iso:
                return iso, text

    return None, text
