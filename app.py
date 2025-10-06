import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pyairtable import Table

# ======================
# Airtable config
# ======================
AIRTABLE_API_KEY = "patRr6OVKGHn2Zyin.f779b21d2982f5d752d8f596220d3c55653851fe3b5d0e17e58813d3bec04474"
BASE_ID = "appBh5G9yDkiqBAkd"
TABLE_NAME = "tblVEZtxVsSXgOREF"

table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)

# ======================
# API URLs
# ======================
CURRENCY_API = "https://api.alanchand.com/?type=currencies&token=OHt1R0mKruA6tGysczCy"
GOLD_API = "https://api.alanchand.com/?type=golds&token=OHt1R0mKruA6tGysczCy"

# ======================
# Utility functions
# ======================
def format_number(x):
    return "{:,}".format(int(x)).replace(",", ".")

def fetch_api_data():
    currencies = requests.get(CURRENCY_API).json()
    golds = requests.get(GOLD_API).json()
    
    data = {}
    for sym in ["usd", "eur"]:
        data[sym] = {"name": currencies[sym]["name"], "price": str(currencies[sym]["sell"])}
    for sym in ["18ayar", "sekkeh", "nim", "rob", "sek"]:
        data[sym] = {"name": golds[sym]["name"], "price": str(golds[sym]["price"])}
    return data

def update_airtable_prices_only(api_data):
    """ آپدیت قیمت‌ها و timestamp رکوردهای موجود بدون پاک کردن ستون Assets """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = table.all()
    symbol_to_record = {r['fields'].get("Symbol"): r for r in records}

    for sym, info in api_data.items():
        if sym in symbol_to_record:
            # آپدیت Price و Timestamp فقط
            table.update(symbol_to_record[sym]['id'], {
                "Price": info["price"],
                "Timestamp": now
            })
        else:
            # رکورد جدید بساز اگر وجود ندارد
            table.create({
                "Timestamp": now,
                "Symbol": sym,
                "Name": info["name"],
                "Price": info["price"],
                "Assets": "0",
                "Total Assets Prices": "0"
            })

def get_table_df():
    records = table.all()
    rows = []
    for r in records:
        f = r['fields']
        rows.append({
            "id": r['id'],
            "Timestamp": f.get("Timestamp",""),
            "Symbol": f.get("Symbol",""),
            "Name": f.get("Name",""),
            "Price": f.get("Price","0"),
            "Assets": f.get("Assets","0"),
            "Total Assets Prices": f.get("Total Assets Prices","0")
        })
    df = pd.DataFrame(rows)
    return df

def save_asset(record_id, assets, price):
    total = str(int(assets) * int(price))
    table.update(record_id, {
        "Assets": str(assets),
        "Total Assets Prices": total
    })

# ======================
# Streamlit UI
# ======================
st.set_page_config(page_title="پنل دارایی", layout="wide")
st.title("💰 قیمت لحظه‌ای و دارایی‌ها")

# ======================
# Fetch & update API
# ======================
api_data = fetch_api_data()
update_airtable_prices_only(api_data)

# ======================
# نمایش قیمت لحظه‌ای
# ======================
st.subheader("📈 قیمت لحظه‌ای")
price_data = {v['name']: format_number(v['price']) for v in api_data.values()}
df_price = pd.DataFrame(list(price_data.items()), columns=["نماد", "قیمت"])
st.table(df_price)

# ======================
# دریافت جدول Airtable
# ======================
df = get_table_df()
df.set_index("Symbol", inplace=True)

# ======================
# mapping Symbol -> record_id برای آپدیت خودکار
# ======================
symbol_to_id = {r['fields'].get("Symbol"): r['id'] for r in table.all()}

# ======================
# بخش ورود دارایی با ذخیره خودکار
# ======================
st.subheader("💼 ورود دارایی")
with st.expander("✏️ ورود مقادیر دارایی"):
    for sym in df.index:
        key_name = f"assets_{sym}"
        if key_name not in st.session_state:
            st.session_state[key_name] = int(df.at[sym,'Assets'])
        
        # فقط خواندن مقدار از session_state
        assets_input = st.number_input(
            f"{df.at[sym,'Name']}:",
            min_value=0,
            value=st.session_state[key_name],
            key=key_name
        )
        
        # آپدیت Airtable فقط
        record_id = symbol_to_id.get(sym)
        if record_id is not None:
            save_asset(record_id, assets_input, int(df.at[sym,'Price']))

# ======================
# نمایش Total Assets Prices
# ======================
df = get_table_df()
df.set_index("Symbol", inplace=True)

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

# جمع کل
total_sum = sum([int(x.replace(".","")) for x in df_total["مجموع"]])
st.markdown(f"**جمع کل دارایی: {format_number(total_sum)}**")
