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
st.caption(
    "Agentic personal finance assistant with goal-based planning "
    "and compact visual analytics."
)

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

st.sidebar.subheader("🎯 Goal Mode (Optional)")

goal_name = st.sidebar.selectbox(
    "Select Financial Goal",
    ["None", "Emergency Fund", "Travel", "Gadget", "Investment"]
)

goal_amount = None
goal_months = None

if goal_name != "None":
    goal_amount = st.sidebar.number_input(
        "Goal Amount (₹)",
        min_value=1000,
        step=1000
    )

    goal_months = st.sidebar.number_input(
        "Target Duration (Months)",
        min_value=1,
        max_value=60,
        value=6
    )

    st.sidebar.caption(
        f"Saving ₹{int(goal_amount / goal_months)} per month"
    )

# -------------------------------------------------
# Main Logic
# -------------------------------------------------
if uploaded_file and budget > 0:

    df = load_expense_data(uploaded_file)

    analysis, summary, goal_plan, explanation = finbot_advanced(
        df=df,
        budget=budget,
        goal_name=None if goal_name == "None" else goal_name,
        goal_amount=goal_amount,
        goal_months=goal_months
    )

    st.info(
        f"📅 Detected {analysis['months_detected']} month(s): "
        f"{', '.join(analysis['months'])}"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Monthly Budget (₹)", analysis["budget"])
    c2.metric("Avg Monthly Spend (₹)", analysis["avg_monthly_spent"])
    c3.metric("Remaining (₹)", analysis["remaining"])

    # -------------------------------------------------
    # Charts
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
        ax1.axis("equal")
        st.pyplot(fig1)

    with col2:
        categories = list(analysis["category_breakdown"].keys())
        actual = list(analysis["category_breakdown"].values())

        LIMITS = {
            "Food": 40, "Rent": 35, "Shopping": 15,
            "Entertainment": 10, "Travel": 10, "Utilities": 10
        }

        recommended = [
            (LIMITS.get(cat, 20) / 100) * analysis["budget"]
            for cat in categories
        ]

        x = np.arange(len(categories))
        width = 0.35

        fig2, ax2 = plt.subplots(figsize=(4.5, 3))
        ax2.bar(x - width/2, actual, width, label="Actual")
        ax2.bar(x + width/2, recommended, width, label="Recommended")
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=30, ha="right")
        ax2.legend()
        st.pyplot(fig2)

    # -------------------------------------------------
    # Goal Mode
    # -------------------------------------------------
    if goal_plan:
        st.subheader("🎯 Goal Planning")

        st.write(
            f"""
            **Goal:** {goal_plan['goal']}  
            **Target Amount:** ₹{goal_plan['target_amount']}  
            **Duration:** {goal_plan['duration_months']} months  
            **Required / Month:** ₹{goal_plan['monthly_saving_required']}
            """
        )

        progress = max(analysis["remaining"], 0) / goal_plan["target_amount"]
        st.progress(min(progress, 1.0))

        if goal_plan["feasible"]:
            st.success("✅ Goal is achievable.")
        else:
            st.warning("⚠️ Increase duration or reduce expenses.")

        for step in goal_plan["plan"]:
            st.warning(step)

    st.subheader("🧠 Explanation")
    st.write(explanation)

    with st.expander("📄 View Uploaded Data"):
        st.dataframe(df)

else:
    st.info("👈 Upload an expense file and enter a budget to begin.")
