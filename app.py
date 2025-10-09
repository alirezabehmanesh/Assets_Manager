import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ======================
# تنظیمات NocoDB
# ======================
NOCO_URL = "https://app.nocodb.com/api/v2/tables/mui5zdsmxpu4fnf/records"
NOCO_TOKEN = "5Fgbn8ql_OOPAnEaeeDuizUq7tHZHZLnkpPBlFkt"
HEADERS = {"xc-token": NOCO_TOKEN, "Content-Type": "application/json"}

# ======================
# API طلا و ارز
# ======================
API_URL = "https://brsapi.ir/Api/Market/Gold_Currency.php?key=BfDYYWKtijTbhNUkYARjPhvkME9q2xyw"

# ======================
# مپ بین نام‌ها و symbolهای مورد نظر
# ======================
ASSET_MAP = {
    "usd": "USD",
    "eur": "EUR",
    "18ayar": "IR_GOLD_18K",
    "24ayar": "IR_GOLD_24K",
    "abshodeh": "IR_GOLD_MELTED",
    "sekkeh": "IR_COIN_EMAMI",
    "nim": "IR_COIN_HALF",
    "rob": "IR_COIN_QUARTER",
    "gerami": "IR_COIN_1G"
}

# ======================
# توابع کاربردی
# ======================
def format_number(x):
    try:
        return "{:,}".format(int(x)).replace(",", ".")
    except:
        return x

def fetch_api_data():
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()

    all_items = data.get("currency", []) + data.get("gold", [])
    result = {}
    for key, api_symbol in ASSET_MAP.items():
        item = next((x for x in all_items if x["symbol"] == api_symbol), None)
        if item:
            result[key] = {
                "name": item["name"],
                "price": str(item["price"])
            }
    return result

def get_noco_records():
    res = requests.get(NOCO_URL, headers=HEADERS)
    res.raise_for_status()
    return res.json().get("list", [])

def update_or_create_record(symbol, name, price):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = get_noco_records()
    existing = next((r for r in records if r["Symbol"] == symbol), None)

    if existing:
        record_id = existing["Id"]
        requests.patch(f"{NOCO_URL}/{record_id}", headers=HEADERS, json={
            "Price": price,
            "Timestamp": now
        })
    else:
        requests.post(NOCO_URL, headers=HEADERS, json={
            "Timestamp": now,
            "Symbol": symbol,
            "Name": name,
            "Price": price,
            "Assets": "0",
            "Total Assets Prices": "0"
        })

def update_prices(api_data):
    for sym, info in api_data.items():
        update_or_create_record(sym, info["name"], info["price"])

def update_assets(record_id, assets, price):
    total = str(int(assets) * int(price))
    requests.patch(f"{NOCO_URL}/{record_id}", headers=HEADERS, json={
        "Assets": str(assets),
        "Total Assets Prices": total
    })

# ======================
# Streamlit UI
# ======================
st.set_page_config(page_title="پنل دارایی", layout="wide")
st.title("💰 قیمت لحظه‌ای و دارایی‌ها (NocoDB Version)")

# ======================
# به‌روزرسانی داده‌ها
# ======================
api_data = fetch_api_data()
update_prices(api_data)

# ======================
# نمایش قیمت‌ها
# ======================
st.subheader("📈 قیمت لحظه‌ای")
price_data = {v['name']: format_number(v['price']) for v in api_data.values()}
df_price = pd.DataFrame(list(price_data.items()), columns=["نماد", "قیمت"])
st.table(df_price)

# ======================
# جدول NocoDB
# ======================
records = get_noco_records()
df = pd.DataFrame(records)
if df.empty:
    st.warning("جدولی خالی است.")
else:
    df.set_index("Symbol", inplace=True)

    # ======================
    # ویرایش دارایی‌ها
    # ======================
    st.subheader("💼 ورود دارایی")
    with st.expander("✏️ ورود مقادیر دارایی"):
        for sym in df.index:
            key_name = f"assets_{sym}"
            assets_val = int(df.at[sym, "Assets"]) if df.at[sym, "Assets"] else 0

            assets_input = st.number_input(
                f"{df.at[sym,'Name']}:",
                min_value=0,
                value=assets_val,
                key=key_name
            )

            record_id = df.at[sym, "Id"]
            update_assets(record_id, assets_input, int(df.at[sym, "Price"]))

    # ======================
    # نمایش ارزش کل دارایی‌ها
    # ======================
    st.subheader("💵 ارزش دارایی‌ها")
    total_rows = []
    for sym in df.index:
        total = int(df.at[sym,'Assets']) * int(df.at[sym,'Price'])
        total_rows.append({
            "نام": df.at[sym,'Name'],
            "قیمت": format_number(df.at[sym,'Price']),
            "دارایی": df.at[sym,'Assets'],
            "مجموع": format_number(total)
        })

    df_total = pd.DataFrame(total_rows)
    st.table(df_total)

    total_sum = sum([int(x.replace(".","")) for x in df_total["مجموع"]])
    st.markdown(f"**جمع کل دارایی: {format_number(total_sum)}**")
