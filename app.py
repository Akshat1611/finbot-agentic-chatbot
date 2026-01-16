import streamlit as st
from finbot import load_expense_data, finbot_advanced

st.set_page_config(page_title="FinBot", layout="wide")
st.title("💰 FinBot – AI Finance Assistant")

uploaded_file = st.file_uploader(
    "Upload your expense file (CSV or Excel)",
    type=["csv", "xlsx"]
)

budget = st.number_input(
    "Enter your monthly budget (₹)",
    min_value=0,
    step=500
)

if uploaded_file and budget > 0:
    df = load_expense_data(uploaded_file)
    analysis, summary, explanation = finbot_advanced(df, budget)

    st.subheader("📊 Budget Summary")
    st.json(analysis)

    st.subheader("❌ Where NOT to Spend")
    for item in summary["avoid"]:
        st.error(item)

    st.subheader("✅ Safe Spending Areas")
    for item in summary["okay"]:
        st.success(item)

    st.subheader("🎯 Financial Goal")
    st.info(summary["goal"])

    st.subheader("📋 Action Plan")
    for act in summary["actions"]:
        st.warning(act)

    st.subheader("🧠 AI Explanation")
    st.write(explanation)

