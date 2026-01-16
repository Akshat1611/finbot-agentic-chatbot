import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from finbot import (
    load_expense_data,
    finbot_advanced,
    get_monthly_spending_trend
)

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="FinBot – Agentic Finance Assistant",
    layout="wide"
)

st.title("💰 FinBot – Agentic Finance Assistant")
st.caption("Agentic finance chatbot with goal-based planning and execution")

# -------------------------------------------------
# Sidebar Inputs
# -------------------------------------------------
st.sidebar.header("📥 Inputs")

uploaded_file = st.sidebar.file_uploader(
    "Upload Expense File (CSV / Excel)",
    type=["csv", "xlsx"]
)

budget = st.sidebar.number_input(
    "Monthly Budget (₹)",
    min_value=0,
    step=500
)

st.sidebar.subheader("🎯 Goal Mode")

goal_name = st.sidebar.selectbox(
    "Select Financial Goal",
    ["None", "Emergency Fund", "Travel", "Gadget", "Investment"]
)

goal_amount = None
if goal_name != "None":
    goal_amount = st.sidebar.number_input(
        "Goal Amount (₹)",
        min_value=1000,
        step=1000
    )

# -------------------------------------------------
# Main App Logic
# -------------------------------------------------
if uploaded_file and budget > 0:

    df = load_expense_data(uploaded_file)

    analysis, summary, goal_plan, steps, explanation = finbot_advanced(
        df,
        budget,
        None if goal_name == "None" else goal_name,
        goal_amount
    )

    st.info(
        f"📅 Detected {analysis['months_detected']} month(s): "
        f"{', '.join(analysis['months'])}. "
        "Analysis is based on average monthly spending."
    )

    # -------------------------------------------------
    # Budget Summary
    # -------------------------------------------------
    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Budget (₹)", analysis["budget"])
    c2.metric("Avg Monthly Spend (₹)", analysis["avg_monthly_spent"])
    c3.metric("Remaining (₹)", analysis["remaining"])

    # -------------------------------------------------
    # Visuals (2 per row)
    # -------------------------------------------------
    st.subheader("📊 Spending Insights")

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(
            analysis["category_breakdown"].values(),
            labels=analysis["category_breakdown"].keys(),
            autopct="%1.0f%%",
            startangle=90
        )
        ax1.set_title("Distribution")
        ax1.axis("equal")
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots(figsize=(4.5, 3))

        cats = list(analysis["category_breakdown"].keys())
        actual = list(analysis["category_breakdown"].values())

        LIMITS = {
            "Food": 40, "Rent": 35, "Shopping": 15,
            "Entertainment": 10, "Travel": 10, "Utilities": 10
        }

        recommended = [
            (LIMITS.get(cat, 20) / 100) * analysis["budget"]
            for cat in cats
        ]

        x = np.arange(len(cats))
        width = 0.35

        ax2.bar(x - width/2, actual, width, label="Actual")
        ax2.bar(x + width/2, recommended, width, label="Recommended")

        ax2.set_xticks(x)
        ax2.set_xticklabels(cats, rotation=30, ha="right", fontsize=8)
        ax2.set_title("Actual vs Recommended")
        ax2.legend(fontsize=8)

        st.pyplot(fig2)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        fig3, ax3 = plt.subplots(figsize=(5, 3))
        monthly_spend = get_monthly_spending_trend(df)
        ax3.plot(
            monthly_spend["Month"],
            monthly_spend["Amount"],
            marker="o"
        )
        ax3.set_title("Monthly Spending Trend")
        ax3.grid(True)
        st.pyplot(fig3)

    # -------------------------------------------------
    # Recommendations
    # -------------------------------------------------
    st.subheader("❌ Where NOT to Spend")
    for item in summary["avoid"]:
        st.error(item)

    st.subheader("📋 Multi-Step Financial Plan")
    for step in steps:
        st.info(step)

    st.subheader("🎯 Monthly Saving Goal")
    st.info(summary["goal"])

    # -------------------------------------------------
    # Goal Mode
    # -------------------------------------------------
    if goal_plan:
        st.subheader("🎯 Goal Planning")

        progress = max(analysis["remaining"], 0) / goal_plan["target_amount"]
        st.progress(min(progress, 1.0))

        for p in goal_plan["plan"]:
            st.warning(p)

    st.subheader("🧠 Explanation")
    st.write(explanation)

else:
    st.info("👈 Upload an expense file and enter budget to begin.")
