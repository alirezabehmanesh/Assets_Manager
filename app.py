import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# تنظیمات صفحه
st.set_page_config(page_title="مدیریت دارایی‌ها", layout="wide")

API_URL = "https://brsapi.ir/Api/Market/Gold_Currency.php?key=BfDYYWKtijTbhNUkYARjPhvkME9q2xyw"

# ---------------------------------------------------------------------
# دریافت داده از API
# ---------------------------------------------------------------------
def fetch_api_data():
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"خطا در دریافت اطلاعات از API: {e}")
        return None

# ---------------------------------------------------------------------
# تبدیل داده‌ها به DataFrame
# ---------------------------------------------------------------------
def parse_data(data):
    if not data:
        return pd.DataFrame()

    all_items = []

    # بخش ارزها
    for item in data.get("currency", []):
        all_items.append({
            "نوع": "ارز",
            "نام": item["name"],
            "نماد": item["symbol"],
            "قیمت": float(item["price"]),
            "واحد": item["unit"]
        })

    # بخش طلا و سکه
    for item in data.get("gold", []):
        all_items.append({
            "نوع": "طلا/سکه",
            "نام": item["name"],
            "نماد": item["symbol"],
            "قیمت": float(item["price"]),
            "واحد": item["unit"]
        })

    df = pd.DataFrame(all_items)

    # فقط نمادهای مورد نیاز
    target_symbols = [
        "USD", "EUR", "IR_GOLD_18K", "IR_GOLD_24K", "IR_GOLD_MELTED",
        "IR_COIN_EMAMI", "IR_COIN_HALF", "IR_COIN_QUARTER", "IR_COIN_1G"
    ]

    df = df[df["نماد"].isin(target_symbols)]

    df["order"] = df["نماد"].apply(lambda s: target_symbols.index(s))
    df = df.sort_values("order").drop(columns=["order"]).reset_index(drop=True)

    return df

# ---------------------------------------------------------------------
# رابط کاربری
# ---------------------------------------------------------------------
st.title("💰 مدیریت و نمایش دارایی‌ها")

# دریافت داده از API
api_data = fetch_api_data()

if api_data:
    df = parse_data(api_data)

    if not df.empty:
        st.subheader("📊 نرخ لحظه‌ای ارز و طلا")
        st.dataframe(df[["نام", "نماد", "قیمت", "واحد"]], use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------------------------
        # ورود مقدار دارایی‌ها توسط کاربر (فقط برای دارایی‌های واقعی)
        # ---------------------------------------------------------------------
        st.subheader("🧮 وارد کردن مقادیر دارایی‌ها")

        asset_values = {}
        total_value = 0

        for _, row in df.iterrows():
            amount = st.number_input(
                f"{row['نام']} ({row['نماد']}) — قیمت فعلی: {row['قیمت']:,} {row['واحد']}",
                min_value=0.0,
                value=0.0,
                step=1.0,
                key=row["نماد"]
            )
            asset_values[row["نماد"]] = amount * row["قیمت"]
            total_value += asset_values[row["نماد"]]

        # ---------------------------------------------------------------------
        # نمایش مجموع نهایی
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📈 ارزش کل دارایی‌ها")
        st.success(f"💰 مجموع دارایی‌ها: {total_value:,.0f} تومان")

        st.caption(f"آخرین بروزرسانی از API: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("هیچ داده‌ای برای نمایش وجود ندارد.")
else:
    st.error("اتصال به API برقرار نشد.")

