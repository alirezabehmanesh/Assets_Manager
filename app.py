import streamlit as st
import requests

# --- تنظیمات Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
TABLE_ID = 698482
BASE_URL = "https://api.baserow.io/api/database/rows/table"

HEADERS = {"Authorization": f"Token {BASEROW_TOKEN}"}

# --- تابع دریافت داده‌های Baserow ---
def get_baserow_rows():
    url = f"{BASE_URL}/{TABLE_ID}/?user_field_names=true"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["results"]

# --- تابع آپدیت Price ---
def update_price(symbol, price):
    rows = get_baserow_rows()
    row_id = next((r["id"] for r in rows if r["Symbol"] == symbol), None)
    if row_id:
        url = f"{BASE_URL}/{TABLE_ID}/{row_id}/"
        data = {"Price": str(price)}
        requests.patch(url, headers=HEADERS, json=data)

# --- تابع آپدیت Assets و Total Assets Prices ---
def update_assets(symbol, asset_value):
    rows = get_baserow_rows()
    row = next((r for r in rows if r["Symbol"] == symbol), None)
    if row:
        price = float(row.get("Price") or 0)
        total = price * float(asset_value)
        url = f"{BASE_URL}/{TABLE_ID}/{row['id']}/"
        data = {"Assets": str(asset_value), "Total Assets Prices": str(total)}
        requests.patch(url, headers=HEADERS, json=data)

# --- دریافت قیمت‌ها از Bonbast ---
def fetch_prices():
    url = "https://www.bonbast.com/json"
    payload = {}
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    
    prices = {}
    # استخراج قیمت‌ها از JSON بر اساس کلیدها
    prices["eur"] = data["usd"]["euro"]  # مثال
    prices["usd"] = data["usd"]["dollar"]
    prices["gold18k"] = data["gold"]["gold18"]
    prices["coinemami"] = data["coins"]["emami"]
    prices["coinhalf"] = data["coins"]["half"]
    prices["coinquarter"] = data["coins"]["quarter"]
    prices["coin1g"] = data["coins"]["onegram"]
    prices["cash"] = 0
    return prices

# --- آپدیت قیمت‌ها در Baserow ---
prices = fetch_prices()
for symbol, price in prices.items():
    update_price(symbol, price)

# --- بخش 1: قیمت‌های لحظه‌ای ---
st.header("💹 قیمت‌های لحظه‌ای")
rows = get_baserow_rows()
table_data = []
for r in rows:
    if r["Symbol"] != "cash":
        name = r["Name"]
        price = r.get("Price") or 0
        price_fmt = f"{int(float(price)):,}".replace(",", ".")
        table_data.append({"نام نماد": name, "قیمت": price_fmt})
st.table(table_data)

# --- بخش 2: ورود دارایی‌ها ---
st.header("📥 ورود دارایی‌ها")
with st.expander("ورود دارایی‌ها", expanded=False):
    for r in rows:
        name = r["Name"]
        symbol = r["Symbol"]
        current_asset = r.get("Assets") or ""
        value = st.text_input(f"{name}:", value=current_asset, key=symbol)
        if value.isdigit():
            update_assets(symbol, value)

# --- بخش 3: محاسبه دارایی‌ها ---
st.header("🧮 محاسبه دارایی‌ها")
calc_data = []
total_all = 0
rows = get_baserow_rows()
for r in rows:
    name = r["Name"]
    asset = float(r.get("Assets") or 0)
    total = float(r.get("Total Assets Prices") or 0)
    calc_data.append({"نام نماد": name, "تعداد دارایی": asset, "مجموع دارایی": total})
    total_all += total
st.table(calc_data)
st.write(f"**جمع کل دارایی‌ها:** {int(total_all):,}".replace(",", "."))
