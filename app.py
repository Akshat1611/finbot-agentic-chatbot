import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from finbot import (
    load_expense_data,
    finbot_advanced,
    get_monthly_spending_trend
)

st.set_page_config(page_title="FinBot", layout="wide")
st.title("💰 FinBot – Agentic Finance Assistant")

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Expense File", type=["csv", "xlsx"]
)
budget = st.sidebar.number_input("Monthly Budget (₹)", min_value=0)

goal_name = st.sidebar.selectbox(
    "Goal (Optional)",
    ["None", "Emergency Fund", "Travel", "Gadget", "Investment"]
)

goal_amount = None
if goal_name != "None":
    goal_amount = st.sidebar.number_input(
        "Goal Amount (₹)", min_value=1000
    )

# -------------------------------------------------
# Main Logic
# -------------------------------------------------
if uploaded_file and budget > 0:
    df = load_expense_data(uploaded_file)

    # 🔴 EXACTLY 5 VALUES EXPECTED
    analysis, summary, goal_plan, steps, explanation = finbot_advanced(
        df,
        budget,
        None if goal_name == "None" else goal_name,
        goal_amount
    )

    st.info(
        f"Months detected: {analysis['months_detected']} "
        f"({', '.join(analysis['months'])})"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", analysis["budget"])
    c2.metric("Avg Spend", int(analysis["avg_monthly_spent"]))
    c3.metric("Remaining", int(analysis["remaining"]))

    # -------------------------------------------------
    # Graphs (2 per row)
    # -------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(
            analysis["category_breakdown"].values(),
            labels=analysis["category_breakdown"].keys(),
            autopct="%1.0f%%"
        )
        st.pyplot(fig1)

    with col2:
        cats = list(analysis["category_breakdown"].keys())
        actual = list(analysis["category_breakdown"].values())
        x = np.arange(len(cats))

        fig2, ax2 = plt.subplots(figsize=(4.5, 3))
        ax2.bar(x, actual)
        ax2.set_xticks(x)
        ax2.set_xticklabels(cats, rotation=30)
        st.pyplot(fig2)

    st.subheader("📈 Monthly Trend")
    trend = get_monthly_spending_trend(df)
    fig3, ax3 = plt.subplots(figsize=(5, 3))
    ax3.plot(trend["Month"], trend["Amount"], marker="o")
    st.pyplot(fig3)

    # -------------------------------------------------
    # Multi-Step Planner
    # -------------------------------------------------
    st.subheader("🪜 Multi-Step Plan")
    for step in steps:
        st.info(step)

    st.subheader("🧠 Explanation")
    st.write(explanation)

else:
    st.info("Upload file and enter budget to start.")
