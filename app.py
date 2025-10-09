import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ======================
# NocoDB Config
# ======================
NOCO_BASE_URL = "https://app.nocodb.com/api/v2/tables/mui5zdsmxpu4fnf/records"
NOCO_TOKEN = "5Fgbn8ql_OOPAnEaeeDuizUq7tHZHZLnkpPBlFkt"

HEADERS = {
    "xc-token": NOCO_TOKEN,
    "Content-Type": "application/json"
}

# ======================
# API URLs
# ======================
CURRENCY_API = "https://api.alanchand.com/?type=currencies&token=OHt1R0mKruA6tGysczCy"
GOLD_API = "https://api.alanchand.com/?type=golds&token=OHt1R0mKruA6tGysczCy"

# ======================
# Utility functions
# ======================
def format_number(x):
    try:
        return "{:,}".format(int(x)).replace(",", ".")
    except:
        return x

def fetch_api_data():
    currencies = requests.get(CURRENCY_API).json()
    golds = requests.get(GOLD_API).json()
    
    data = {}
    for sym in ["usd", "eur"]:
        data[sym] = {"name": currencies[sym]["name"], "price": str(currencies[sym]["sell"])}
    for sym in ["18ayar", "sekkeh", "nim", "rob", "sek"]:
        data[sym] = {"name": golds[sym]["name"], "price": str(golds[sym]["price"])}
    return data


# ======================
# CRUD operations (NocoDB)
# ======================
def get_all_records():
    response = requests.get(NOCO_BASE_URL, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("list", [])

def get_table_df():
    records = get_all_records()
    rows = []
    for r in records:
        rows.append({
            "id": r.get("Id"),
            "Timestamp": r.get("Timestamp", ""),
            "Symbol": r.get("Symbol", ""),
            "Name": r.get("Name", ""),
            "Price": r.get("Price", "0"),
            "Assets": r.get("Assets", "0"),
            "Total Assets Prices": r.get("Total Assets Prices", "0")
        })
    return pd.DataFrame(rows)


def update_nocodb_prices_only(api_data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = get_all_records()
    symbol_to_record = {r.get("Symbol"): r for r in records}

    for sym, info in api_data.items():
        if sym in symbol_to_record:
            record_id = symbol_to_record[sym]["Id"]
            payload = {
                "Price": info["price"],
                "Timestamp": now
            }
            requests.patch(f"{NOCO_BASE_URL}/{record_id}", headers=HEADERS, json=payload)
        else:
            payload = {
                "Timestamp": now,
                "Symbol": sym,
                "Name": info["name"],
                "Price": info["price"],
                "Assets": "0",
                "Total Assets Prices": "0"
            }
            requests.post(NOCO_BASE_URL, headers=HEADERS, json=payload)


def save_asset(record_id, assets, price):
    total = str(int(assets) * int(price))
    payload = {
        "Assets": str(assets),
        "Total Assets Prices": total
    }
    requests.patch(f"{NOCO_BASE_URL}/{record_id}", headers=HEADERS, json=payload)


# ======================
# Streamlit UI
# ======================
st.set_page_config(page_title="پنل دارایی", layout="wide")
st.title("💰 قیمت لحظه‌ای و دارایی‌ها")

# ======================
# Fetch & update API
# ======================
api_data = fetch_api_data()
update_nocodb_prices_only(api_data)

# ======================
# نمایش قیمت لحظه‌ای
# ======================
st.subheader("📈 قیمت لحظه‌ای")
price_data = {v['name']: format_number(v['price']) for v in api_data.values()}
df_price = pd.DataFrame(list(price_data.items()), columns=["نماد", "قیمت"])
st.table(df_price)

# ======================
# دریافت جدول NocoDB
# ======================
df = get_table_df()
df.set_index("Symbol", inplace=True)

# ======================
# mapping Symbol -> record_id برای آپدیت خودکار
# ======================
symbol_to_id = {r["Symbol"]: r["id"] for r in df.reset_index().to_dict("records") if r.get("id")}

# ======================
# بخش ورود دارایی با ذخیره خودکار
# ======================
st.subheader("💼 ورود دارایی")
with st.expander("✏️ ورود مقادیر دارایی"):
    for sym in df.index:
        key_name = f"assets_{sym}"
        if key_name not in st.session_state:
            try:
                st.session_state[key_name] = int(df.at[sym, 'Assets'])
            except:
                st.session_state[key_name] = 0
        
        assets_input = st.number_input(
            f"{df.at[sym, 'Name']}:",
            min_value=0,
            value=st.session_state[key_name],
            key=key_name
        )
        
        record_id = symbol_to_id.get(sym)
        if record_id:
            save_asset(record_id, assets_input, int(df.at[sym, 'Price']))

# ======================
# نمایش Total Assets Prices
# ======================
df = get_table_df()
df.set_index("Symbol", inplace=True)

st.subheader("💵 ارزش دارایی‌ها")
total_rows = []
for sym in df.index:
    total = int(df.at[sym, 'Assets']) * int(df.at[sym, 'Price'])
    total_rows.append({
        "نام": df.at[sym, 'Name'],
        "قیمت": format_number(df.at[sym, 'Price']),
        "دارایی": df.at[sym, 'Assets'],
        "مجموع": format_number(total)
    })

df_total = pd.DataFrame(total_rows)
st.table(df_total)

total_sum = sum([int(x.replace(".", "")) for x in df_total["مجموع"]])
st.markdown(f"**جمع کل دارایی: {format_number(total_sum)}**")
