import streamlit as st
import requests

# --- تنظیمات Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
TABLE_ID = 698482
API_BASE = "https://api.baserow.io/api/database/rows/table"

HEADERS = {"Authorization": f"Token {BASEROW_TOKEN}"}

# --- XPaths حذف شد، از JSON مستقیم استفاده می‌کنیم ---
BONBAST_JSON_URL = "https://www.bonbast.com/json"

# --- بخش 1: قیمت های لحظه ای ---
def fetch_prices():
    try:
        resp = requests.post(BONBAST_JSON_URL)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.error(f"خطا در گرفتن قیمت‌ها: {e}")
        return {}

    # Map JSON keys to symbols
    prices = {}
    prices["eur"] = data.get("EUR", 0)
    prices["usd"] = data.get("USD", 0)
    prices["gold18k"] = data.get("Gold_18", 0)
    prices["coinemami"] = data.get("Emami", 0)
    prices["coinhalf"] = data.get("Half", 0)
    prices["coinquarter"] = data.get("Quarter", 0)
    prices["coin1g"] = data.get("One_gram", 0)
    prices["cash"] = 0
    return prices

def get_rows():
    url = f"{API_BASE}/{TABLE_ID}/?user_field_names=true"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["results"]

def update_row(row_id, fields):
    url = f"{API_BASE}/{TABLE_ID}/{row_id}/"
    requests.patch(url, headers=HEADERS, json=fields)

def update_prices(prices):
    rows = get_rows()
    for row in rows:
        symbol = row["Symbol"]
        if symbol in prices:
            update_row(row["id"], {"Price": str(prices[symbol])})

def update_assets(symbol, value):
    rows = get_rows()
    for row in rows:
        if row["Symbol"] == symbol:
            price = float(row.get("Price", 0))
            assets_val = float(value)
            update_row(row["id"], {
                "Assets": value,
                "Total Assets Prices": str(price * assets_val)
            })
            break

# --- آپدیت قیمت‌ها ---
prices = fetch_prices()
if prices:
    update_prices(prices)

rows = get_rows()

st.title("📊 مدیریت دارایی‌ها")

# --- بخش 1 ---
st.header("قیمت های لحظه ای")
price_table = []
for row in rows:
    if row["Symbol"] != "cash":
        price = float(row.get("Price", 0))
        price_table.append([row["Name"], f"{price:,.0f}"])
st.table(price_table)

# --- بخش 2 ---
st.header("ورود دارایی‌ها")
with st.expander("ثبت دارایی‌ها"):
    for row in rows:
        name = row["Name"]
        symbol = row["Symbol"]
        val = row.get("Assets", "")
        value = st.text_input(f"{name}:", val, key=f"asset_{symbol}")
        if value and value.replace(".","").isdigit():
            update_assets(symbol, value)

# --- بخش 3 ---
st.header("محاسبه دارایی ها")
asset_table = []
total_sum = 0
for row in rows:
    name = row["Name"]
    assets = float(row.get("Assets") or 0)
    total = float(row.get("Total Assets Prices") or 0)
    asset_table.append([name, f"{assets:,.0f}", f"{total:,.0f}"])
    total_sum += total
st.table(asset_table)
st.write(f"**جمع کل دارایی‌ها:** {total_sum:,.0f}")
