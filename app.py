import requests
from lxml import html
import streamlit as st

# --- تنظیمات Baserow ---
BASEROW_TOKEN = "dc2jtvdYze2paMsbTsTwPQhXNKQ7awQa"
TABLE_ID = 698482
FIELDS = {
    "Name": "field_5832624",
    "Symbol": "field_5832627",
    "Price": "field_5832628",
    "Assets": "field_5832629",
    "TotalAssetsPrices": "field_5832630",
}

HEADERS = {"Authorization": f"Token {BASEROW_TOKEN}"}

# --- XPaths سایت Bonbast ---
XPATHS = {
    "eur": "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[3]/td[3]/text()",
    "usd": "/html/body/div[2]/div[2]/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[3]/text()",
    "gold18k": "/html/body/div[2]/div[2]/div[1]/div[4]/div[1]/div/div/span/text()",
    "coinemami": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[3]/td[2]/text()",
    "coinhalf": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[4]/td[2]/text()",
    "coinquarter": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[5]/td[2]/text()",
    "coin1g": "/html/body/div[2]/div[2]/div[1]/div[3]/div[2]/table/tbody/tr[6]/td[2]/text()",
}

# --- استخراج قیمت‌ها ---
def fetch_prices():
    url = "https://www.bonbast.com/"
    r = requests.get(url)
    tree = html.fromstring(r.content)
    prices = {}
    for symbol, xpath in XPATHS.items():
        try:
            text = tree.xpath(xpath)[0].replace(",", "").strip()
            prices[symbol] = int(text)
        except Exception as e:
            st.warning(f"خطا در خواندن {symbol}: {e}")
            prices[symbol] = 0
    return prices

# --- دریافت ردیف‌ها ---
def get_rows():
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/?user_field_names=true"
    r = requests.get(url, headers=HEADERS).json()
    return r["results"]

# --- آپدیت Price ---
def update_price(row_id, value):
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/{row_id}/"
    data = {FIELDS["Price"]: str(value)}
    r = requests.patch(url, headers=HEADERS, json=data)
    return r.json()

# --- آپدیت Assets و TotalAssetsPrices ---
def update_assets(row_id, assets_value, price_value):
    total = assets_value * price_value
    data = {
        FIELDS["Assets"]: str(assets_value),
        FIELDS["TotalAssetsPrices"]: str(total)
    }
    url = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/{row_id}/"
    requests.patch(url, headers=HEADERS, json=data)

# --- قالب‌بندی هزارگان ---
def fmt(n):
    return f"{n:,}".replace(",", ".")

# --- اجرای استخراج قیمت و آپدیت Price ---
prices = fetch_prices()
rows = get_rows()
row_map = {row["Symbol"]: row for row in rows}

for symbol, price in prices.items():
    if symbol in row_map:
        update_price(row_map[symbol]["id"], price)

# --- Streamlit ---
st.title("مدیریت دارایی و قیمت‌ها")

# --- بخش 1: قیمت‌های لحظه‌ای ---
st.header("قیمت‌های لحظه‌ای")
price_table = []
for row in rows:
    if row["Symbol"] == "cash":
        continue
    symbol = row["Symbol"]
    name = row["Name"]
    price = prices.get(symbol, 0)
    price_table.append({"نام": name, "قیمت": fmt(price)})
st.table(price_table)

# --- بخش 2: ورود دارایی‌ها ---
st.header("ورود دارایی‌ها")
with st.expander("ورود دارایی‌ها", expanded=False):
    for row in rows:
        symbol = row["Symbol"]
        name = row["Name"]
        current_assets = row.get("Assets", "")
        value = st.text_input(f"{name}:", current_assets, key=symbol)
        if value.isdigit():
            update_assets(row["id"], int(value), prices.get(symbol, 0))

# --- بخش 3: محاسبه دارایی‌ها ---
st.header("محاسبه دارایی‌ها")
asset_table = []
total_sum = 0
for row in rows:
    name = row["Name"]
    assets = int(row.get("Assets") or 0)
    total = int(row.get("Total Assets Prices") or 0)
    total_sum += total
    asset_table.append({
        "نام": name,
        "تعداد دارایی": fmt(assets),
        "مجموع دارایی": fmt(total)
    })
st.table(asset_table)
st.write(f"**جمع کل دارایی‌ها: {fmt(total_sum)}**")
