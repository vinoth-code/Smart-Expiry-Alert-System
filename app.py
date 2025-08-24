import os
from datetime import date
import uuid
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from db import init_db, add_item, get_items, mark_consumed, delete_item, update_status
from ocr import extract_expiry_from_image
from utils import days_until, is_future_or_today
from model import predict

load_dotenv()
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMG_DIR = os.path.join(DATA_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

st.set_page_config(page_title="Smart Expiry Alert", page_icon="🧃", layout="wide")
st.title("🧃 Smart Expiry Alert System")

# Initialize DB
init_db()

with st.sidebar:
    st.header("Add Item")
    uploaded = st.file_uploader("Upload label image", type=["jpg", "jpeg", "png"])
    auto_date = None
    raw_text = ""

    img_path = None
    if uploaded:
        # Save image
        img_name = f"{uuid.uuid4().hex}.png"
        img_path = os.path.join(IMG_DIR, img_name)
        with open(img_path, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Running OCR..."):
            try:
                auto_date, raw_text = extract_expiry_from_image(img_path)
            except Exception as e:
                st.error(f"OCR failed: {e}")
                img_path = None

        if auto_date:
            st.success(f"Detected expiry: {auto_date}")
        else:
            st.warning("Could not detect expiry date automatically. Please enter manually.")

    name = st.text_input("Product name", value="")
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)

    # Date input
    today = date.today()
    if auto_date:
        try:
            y, m, d = map(int, auto_date.split("-"))
            default_date = date(y, m, d)
        except:
            default_date = today
    else:
        default_date = today
    user_date = st.date_input("Expiry date", value=default_date)

    if st.button("Add to Inventory", use_container_width=True):
        if not name:
            st.error("Please enter a product name.")
        else:
            iso_date = user_date.isoformat()
            if not is_future_or_today(iso_date):
                st.error("Expiry date must be today or in the future.")
            else:
                # simple feature set for risk prediction
                features = {
                    "name": name,
                    "category": "unknown",
                    "days_to_expiry": days_until(iso_date),
                    "quantity": int(quantity),
                    "previously_wasted_rate": 0.2
                }
                risk_score = predict(features)
                add_item(name=name, expiry_date=iso_date, quantity=int(quantity),
                         image_path=img_path if uploaded else None, risk_score=risk_score)
                st.success("Item added!")
                st.rerun()

st.subheader("📦 Your Inventory")
items = get_items()
if not items:
    st.info("No items yet. Add some from the sidebar.")
else:
    # compute derived columns
    rows = []
    for it in items:
        dleft = days_until(it["expiry_date"])
        status = it["status"]
        if dleft < 0 and status == "active":
            status = "expired"
            update_status(it["id"], "expired")
        rows.append({
            "ID": it["id"],
            "Name": it["name"][:50],
            "Expiry": it["expiry_date"],
            "Days Left": dleft,
            "Qty": it["quantity"],
            "Risk": round(float(it["risk_score"]), 2),
            "Status": status
        })
    df = pd.DataFrame(rows).sort_values(by=["Status", "Days Left"])

    def color_row(row):
        if row["Status"] == "expired" or row["Days Left"] <= 0:
            return ["background-color: #ffcccc"] * len(row)
        elif row["Days Left"] <= 3:
            return ["background-color: #fff3cd"] * len(row)
        else:
            return [""] * len(row)

    st.dataframe(df.style.apply(color_row, axis=1), use_container_width=True, height=420)

    st.markdown("### Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        id_consume = st.number_input("ID to mark consumed", min_value=0, step=1, value=0, key="consume_id")
        if st.button("Mark Consumed", key="consume_btn"):
            if id_consume > 0:
                mark_consumed(int(id_consume))
                st.success("Marked as consumed.")
                st.rerun()

    with col2:
        id_delete = st.number_input("ID to delete", min_value=0, step=1, value=0, key="delete_id")
        if st.button("Delete Item", key="delete_btn"):
            if id_delete > 0:
                delete_item(int(id_delete))
                st.success("Item deleted.")
                st.rerun()


with st.expander("🔎 OCR Raw Text (last upload)"):
    try:
        st.text(raw_text or "")
    except NameError:
        st.text("")
