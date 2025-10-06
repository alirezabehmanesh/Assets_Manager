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
    return "{:,}".format(x).replace(",", ".")

def fetch_api_data():
    currencies = requests.get(CURRENCY_API).json()
    golds = requests.get(GOLD_API).json()
    
    data = {}
    for sym in ["usd", "eur"]:
        data[sym] = {"name": currencies[sym]["name"], "price": currencies[sym]["sell"]}
    for sym in ["18ayar", "sekkeh", "nim", "rob", "sek"]:
        data[sym] = {"name": golds[sym]["name"], "price": golds[sym]["price"]}
    return data

def update_airtable(api_data):
    all_records = table.all()
    for rec in all_records:
        if rec['fields'].get("timestamp"):
            table.delete(rec['id'])
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for sym, info in api_data.items():
        table.create({
            "timestamp": now,
            "symbol": sym,
            "name": info["name"],
            "price": info["price"]
        })

def get_table_df():
    records = table.all()
    rows = []
    for r in records:
        f = r['fields']
        rows.append({
            "id": r['id'],
            "timestamp": f.get("timestamp",""),
            "symbol": f.get("symbol",""),
            "name": f.get("name",""),
            "price": f.get("price",0),
            "assets": f.get("assets",0),
            "total_assets_prices": f.get("total assets prices",0)
        })
    df = pd.DataFrame(rows)
    return df

def save_assets_bulk(df, assets_dict):
    for sym, assets in assets_dict.items():
        record_id = df.at[sym,'id']
        price = df.at[sym,'price']
        total = assets * price
        table.update(record_id, {
            "assets": assets,
            "total assets prices": total
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
update_airtable(api_data)

# ======================
# نمایش قیمت لحظه‌ای
# ======================
st.subheader("📈 قیمت لحظه‌ای")
price_data = {v['name']: format_number(v['price']) for k,v in api_data.items()}
df_price = pd.DataFrame(list(price_data.items()), columns=["نماد", "قیمت"])
st.table(df_price)

# ======================
# دریافت جدول Airtable
# ======================
df = get_table_df()
df.set_index("symbol", inplace=True)

# ======================
# بخش ورود دارایی با یک دکمه ثبت
# ======================
st.subheader("💼 ورود دارایی")
assets_inputs = {}
with st.expander("✏️ ورود مقادیر دارایی"):
    for sym in df.index:
        assets_inputs[sym] = st.number_input(f"{df.at[sym,'name']}:", min_value=0, value=int(df.at[sym,'assets']))

    if st.button("💾 ثبت مقادیر"):
        save_assets_bulk(df, assets_inputs)
        st.success("مقادیر با موفقیت ثبت شدند!")
        st.experimental_rerun()

# ======================
# نمایش total assets prices
# ======================
st.subheader("💵 ارزش دارایی‌ها")
df = get_table_df()
df.set_index("symbol", inplace=True)

total_rows = []
for sym in df.index:
    total = df.at[sym,'assets'] * df.at[sym,'price']
    total_rows.append({
        "نام": df.at[sym,'name'],
        "قیمت": format_number(df.at[sym,'price']),
        "دارایی": df.at[sym,'assets'],
        "مجموع": format_number(total)
    })

df_total = pd.DataFrame(total_rows)
st.table(df_total)

# جمع کل
total_sum = df_total["مجموع"].apply(lambda x: int(x.replace(".",""))).sum()
st.markdown(f"**جمع کل دارایی: {format_number(total_sum)}**")
