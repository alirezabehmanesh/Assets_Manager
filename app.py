# app.py
import streamlit as st
from playwright.sync_api import sync_playwright
import requests
import time

# --- تنظیمات Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
TABLE_ID = 698482
FIELDS = {
    "Name": "field_5832624",
    "Symbol": "field_5832627",
    "Price": "field_5832628",
    "Assets": "field_5832629",
    "Total Assets Prices": "field_5832630"
}

# --- تابع گرفتن ردیف‌ها از Baserow ---
def get_rows():
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/?user_field_names=true"
    headers = {"Authorization": f"Token {BASEROW_TOKEN}"}
    res = requests.get(url, headers=headers).json()
    return res["results"]

# --- تابع آپدیت قیمت ---
def update_price(row_id, price):
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/{row_id}/"
    headers = {"Authorization": f"Token {BASEROW_TOKEN}"}
    data = {"Price": str(price)}
    res = requests.patch(url, headers=headers, json=data)
    return res.json()

# --- گرفتن قیمت‌ها از Bonbast با Playwright ---
def fetch_prices():
    prices = {}
    xpaths = {
        "eur": '/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[3]/td[3]',
        "usd": '/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[3]',
        "gold18k": '/html/body/div[2]/div[2]/div[1]/div[4]/div[1]/div/div/span',
        "coinemami": '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[2]',
        "coinhalf": '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[4]/td[2]',
        "coinquarter": '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[5]/td[2]',
        "coin1g": '/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[6]/td[2]'
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.bonbast.com/", timeout=60000)
        time.sleep(2)  # اجازه بده JS لود بشه

        for symbol, xp in xpaths.items():
            el = page.query_selector(f"xpath={xp}")
            if el:
                prices[symbol] = el.inner_text().replace(",", "").strip()
            else:
                st.error(f"خطا در خواندن {symbol}")
        browser.close()
    return prices

# --- آپدیت ردیف‌ها در Baserow ---
def update_baserow_prices(prices):
    rows = get_rows()
    for row in rows:
        symbol = row["Symbol"]
        if symbol in prices:
            update_price(row["id"], prices[symbol])
            st.success(f"{symbol} آپدیت شد به {prices[symbol]}")

# --- Streamlit ---
st.title("مدیریت دارایی و قیمت‌ها")

st.header("قیمت‌های لحظه‌ای")
prices = fetch_prices()
update_baserow_prices(prices)

rows = get_rows()
for row in rows:
    if row["Name"] != "موجودی نقد":
        st.write(f"{row['Name']}: {int(float(row['Price'])):,}")

st.header("ورود دارایی‌ها (Click to show/hide)")
with st.expander("نمایش/پنهان کردن دارایی‌ها"):
    for row in rows:
        value = st.text_input(f"{row['Name']}:", row.get("Assets", ""), key=row["Symbol"])
        if value.isdigit():
            # آپدیت Assets و محاسبه Total Assets Prices
            total = int(float(value)) * int(float(row.get("Price") or 0))
            url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/{row['id']}/"
            headers = {"Authorization": f"Token {BASEROW_TOKEN}"}
            data = {"Assets": value, "Total Assets Prices": str(total)}
            requests.patch(url, headers=headers, json=data)

st.header("محاسبه دارایی‌ها")
total_sum = 0
for row in rows:
    assets = int(float(row.get("Assets") or 0))
    total_price = int(float(row.get("Total Assets Prices") or 0))
    total_sum += total_price
    st.write(f"{row['Name']}: تعداد={assets:,} مجموع={total_price:,}")
st.write(f"جمع کل دارایی‌ها: {total_sum:,}")
