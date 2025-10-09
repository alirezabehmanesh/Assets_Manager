import streamlit as st
import requests
import json

# --- تنظیمات Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
TABLE_ID = 698482
BASE_URL = "https://api.baserow.io/api/database/rows/table"

HEADERS = {
    "Authorization": f"Token {BASEROW_TOKEN}",
    "Content-Type": "application/json",
}

# --- دریافت ردیف‌ها از Baserow ---
@st.cache_data(show_spinner=False)
def get_rows():
    resp = requests.get(f"{BASE_URL}/{TABLE_ID}/?user_field_names=true", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["results"]

# --- آپدیت یک ردیف در Baserow ---
def update_row(row_id, field_data):
    url = f"{BASE_URL}/{TABLE_ID}/{row_id}/"
    resp = requests.patch(url, headers=HEADERS, data=json.dumps(field_data))
    if resp.status_code != 200:
        st.error(f"خطا در آپدیت {row_id}: {resp.text}")

# --- دریافت قیمت‌ها از Bonbast ---
def fetch_prices():
    url = "https://www.bonbast.com/json"
    try:
        resp = requests.post(url, data={})
        resp.raise_for_status()
        data = resp.json()
        prices = {
            "eur": float(data["EUR"]["Sell"].replace(",", "")),
            "usd": float(data["USD"]["Sell"].replace(",", "")),
            "gold18k": float(data["Gold"]["18K"]["Sell"].replace(",", "")),
            "coinemami": float(data["Coins"]["Emami"]["Sell"].replace(",", "")),
            "coinhalf": float(data["Coins"]["Half"]["Sell"].replace(",", "")),
            "coinquarter": float(data["Coins"]["Quarter"]["Sell"].replace(",", "")),
            "coin1g": float(data["Coins"]["1g"]["Sell"].replace(",", "")),
            "cash": 0
        }
        return prices
    except Exception as e:
        st.error(f"خطا در دریافت قیمت‌ها: {e}")
        return {}

# --- آپدیت Price ها در Baserow ---
def update_prices(prices):
    rows = get_rows()
    for row in rows:
        symbol = row["Symbol"]
        if symbol in prices:
            update_row(row["id"], {"Price": str(prices[symbol])})

# --- بخش Streamlit ---
st.set_page_config(page_title="مدیریت دارایی‌ها", layout="wide")
st.title("مدیریت دارایی‌ها")

# --- بخش 1: قیمت‌های لحظه‌ای ---
st.subheader("قیمت‌های لحظه‌ای")
prices = fetch_prices()
update_prices(prices)  # آپدیت Price ها در Baserow

rows = get_rows()
display_rows = [r for r in rows if r["Symbol"] != "cash"]

table_data = []
for r in display_rows:
    price = r.get("Price") or 0
    table_data.append([r["Name"], "{:,.0f}".format(float(price))])

st.table(table_data)

# --- بخش 2: ورود دارایی‌ها ---
with st.expander("ورود دارایی‌ها", expanded=False):
    for r in rows:
        name = r["Name"]
        symbol = r["Symbol"]
        current = r.get("Assets") or ""
        value = st.text_input(f"{name}:", current, key=symbol)
        if value.strip().isdigit():
            update_row(r["id"], {"Assets": value})
            # محاسبه Total Assets Prices
            price = float(r.get("Price") or 0)
            total = float(value) * price
            update_row(r["id"], {"Total Assets Prices": str(total)})

# --- بخش 3: محاسبه دارایی‌ها ---
st.subheader("محاسبه دارایی‌ها")
table_assets = []
total_assets = 0
for r in rows:
    name = r["Name"]
    assets = float(r.get("Assets") or 0)
    total = float(r.get("Total Assets Prices") or 0)
    table_assets.append([name, "{:,.0f}".format(assets), "{:,.0f}".format(total)])
    total_assets += total

st.table(table_assets)
st.write(f"**جمع کل دارایی‌ها:** {total_assets:,.0f}")
