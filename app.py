import streamlit as st
import requests

# ------------------ تنظیمات Baserow ------------------
BASEROW_API_TOKEN = "توکن_خودت_اینجا_بذار"
BASE_ID = "appBh5G9yDkiqBAkd"  # بیس تو
TABLE_ID = "tblVEZtxVsSXgOREF"  # تیبل تو
BASEROW_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}/"

HEADERS = {
    "Authorization": f"Token {BASEROW_API_TOKEN}",
    "Content-Type": "application/json"
}

# ------------------ تابع گرفتن قیمت‌ها از Bonbast ------------------
def fetch_prices():
    url = "https://www.bonbast.com/json"
    try:
        response = requests.post(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = {
            "eur": int(data["eur1"]),
            "usd": int(data["usd1"]),
            "gold18k": int(data["gol18"]),
            "coinemami": int(data["emami1"]),
            "coinhalf": int(data["azadi1_2"]),
            "coinquarter": int(data["azadi1_4"]),
            "coin1g": int(data["azadi1g"]),
        }
        return prices
    except Exception as e:
        st.error(f"خطا در دریافت قیمت‌ها: {e}")
        return {}

# ------------------ توابع ارتباط با Baserow ------------------
def get_rows():
    r = requests.get(BASEROW_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()["results"]

def update_row(row_id, data):
    url = f"{BASEROW_URL}{row_id}/"
    r = requests.patch(url, headers=HEADERS, json=data)
    r.raise_for_status()

def update_prices_in_baserow(prices):
    rows = get_rows()
    for row in rows:
        name = row["Name"].lower()
        if name in prices:
            update_row(row["id"], {"Price": prices[name]})

# ------------------ اجرای اصلی ------------------
st.set_page_config(page_title="مدیریت دارایی‌ها", layout="wide")

st.title("💰 مدیریت دارایی‌ها")

# === بخش ۱: قیمت‌های لحظه‌ای ===
st.subheader("📊 قیمت‌های لحظه‌ای")
prices = fetch_prices()
if prices:
    update_prices_in_baserow(prices)

rows = get_rows()

data_display = []
for row in rows:
    if row["Name"].lower() != "naghd":  # موجودی نقدی رو نشون نده
        data_display.append({
            "نماد": row["Name"],
            "قیمت": f"{int(row['Price']):,}".replace(",", ".")
        })

st.table(data_display)

# === بخش ۲: ورود دارایی‌ها ===
st.subheader("🧮 ورود دارایی‌ها")
with st.expander("نمایش / ویرایش دارایی‌ها"):
    for row in rows:
        asset_val = st.text_input(
            f"{row['Name']} :", value=str(row.get("Assets", "")), key=row["id"]
        )
        if asset_val.strip():
            try:
                asset_int = int(asset_val)
                total_val = asset_int * int(row.get("Price", 0))
                update_row(row["id"], {
                    "Assets": asset_int,
                    "Total Assets Prices": total_val
                })
            except ValueError:
                st.warning(f"مقدار '{asset_val}' برای {row['Name']} معتبر نیست.")

# === بخش ۳: محاسبه دارایی‌ها ===
st.subheader("📈 محاسبه دارایی‌ها")
rows = get_rows()
summary_data = []
total_sum = 0
for row in rows:
    total_val = int(row.get("Total Assets Prices", 0))
    total_sum += total_val
    summary_data.append({
        "نماد": row["Name"],
        "تعداد": f"{int(row.get('Assets', 0)):,}".replace(",", "."),
        "مجموع ارزش": f"{total_val:,}".replace(",", ".")
    })

st.table(summary_data)
st.markdown(f"### 💵 جمع کل دارایی‌ها: {total_sum:,}".replace(",", "."))

st.caption("آخرین به‌روزرسانی قیمت‌ها به صورت خودکار از Bonbast انجام شد ✅")
