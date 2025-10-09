import streamlit as st
import requests
from playwright.sync_api import sync_playwright
import time

st.set_page_config(page_title="مدیریت دارایی", layout="wide")

# --- Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
BASE_URL = "https://api.baserow.io/api/database/rows/table/698482/"
HEADERS = {"Authorization": f"Token {BASEROW_TOKEN}"}

PRICE_FIELD = "field_5832628"
ASSETS_FIELD = "field_5832629"
TOTAL_FIELD = "field_5832630"

# --- Bonbast XPaths ---
XPATHS = {
    "eur": "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[3]/td[3]",
    "usd": "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[3]",
    "gold18k": "/html/body/div[2]/div[2]/div[1]/div[4]/div[1]/div/div/span",
    "coinemami": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[2]",
    "coinhalf": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[4]/td[2]",
    "coinquarter": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[5]/td[2]",
    "coin1g": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[6]/td[2]",
}

# --- تابع فرمت هزارگان ---
def format_thousands(num):
    try:
        return "{:,}".format(int(num)).replace(",", ".")
    except:
        return num

# --- گرفتن Priceها از Bonbast ---
def fetch_prices():
    prices = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.bonbast.com/")
        time.sleep(2)
        for symbol, xpath in XPATHS.items():
            try:
                el = page.locator(f"xpath={xpath}")
                prices[symbol] = el.inner_text().strip().replace(",", "")
            except:
                prices[symbol] = None
        browser.close()
    prices["cash"] = "0"
    return prices

# --- آپدیت Priceها در Baserow ---
def update_prices(prices):
    resp = requests.get(BASE_URL + "?user_field_names=true", headers=HEADERS)
    rows = resp.json().get("results", [])
    for row in rows:
        symbol = row.get("Symbol")
        row_id = row.get("id")
        if row_id and symbol in prices:
            data = {PRICE_FIELD: prices[symbol]}
            requests.patch(BASE_URL + f"{row_id}/", headers=HEADERS, json=data)

# --- گرفتن ردیف‌ها ---
def get_rows():
    resp = requests.get(BASE_URL + "?user_field_names=true", headers=HEADERS)
    return resp.json().get("results", [])

# --- آپدیت Assets و Total ---
def update_assets(symbol, value):
    rows = get_rows()
    for row in rows:
        if row["Symbol"] == symbol:
            price = row.get("Price", "0").replace(".", "")
            try:
                total = int(price) * int(value)
            except:
                total = 0
            data = {ASSETS_FIELD: str(value), TOTAL_FIELD: str(total)}
            requests.patch(BASE_URL + f"{row['id']}/", headers=HEADERS, json=data)
            break

# --- اجرای اولیه ---
prices = fetch_prices()
update_prices(prices)
rows = get_rows()

# --- بخش 1: قیمت های لحظه ای ---
st.header("💰 قیمت‌های لحظه‌ای")
price_table = []
for row in rows:
    if row["Symbol"] == "cash":
        continue
    price_table.append({
        "نام نماد": row["Name"],
        "قیمت": format_thousands(row.get("Price", "0"))
    })
st.table(price_table)

# --- بخش 2: ورود دارایی ها ---
with st.expander("📥 ورود دارایی‌ها", expanded=False):
    for row in rows:
        name = row["Name"]
        symbol = row["Symbol"]
        value = st.text_input(f"{name}:", row.get("Assets", ""), key=f"asset_{symbol}")
        if value.isdigit():
            update_assets(symbol, value)

# --- بخش 3: محاسبه دارایی ها ---
st.header("📊 محاسبه دارایی‌ها")
calc_table = []
total_sum = 0
for row in rows:
    assets = int(row.get("Assets", "0") or 0)
    total = int(row.get("Total Assets Prices", "0") or 0)
    calc_table.append({
        "نام نماد": row["Name"],
        "تعداد دارایی": assets,
        "مجموع دارایی": format_thousands(total)
    })
    total_sum += total
st.table(calc_table)
st.markdown(f"**جمع کل دارایی‌ها: {format_thousands(total_sum)}**")
