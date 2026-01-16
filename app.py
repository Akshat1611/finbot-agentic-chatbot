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
if goal_name != "None":
    goal_amount = st.sidebar.number_input(
        "Goal Amount (₹)",
        min_value=1000,
        step=1000
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
        goal_amount=goal_amount
    )

    # -------------------------------------------------
    # Month Detection Info
    # -------------------------------------------------
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

    # =================================================
    # 📊 VISUAL ANALYTICS (2 GRAPHS PER ROW)
    # =================================================
    st.subheader("📊 Spending Insights")

    # ---------- ROW 1 (2 graphs) ----------
    col1, col2 = st.columns(2)

    # 🥧 Pie Chart – Spending Distribution
    with col1:
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(
            analysis["category_breakdown"].values(),
            labels=analysis["category_breakdown"].keys(),
            autopct="%1.0f%%",
            startangle=90
        )
        ax1.set_title("Spending Distribution", fontsize=10)
        ax1.axis("equal")
        st.pyplot(fig1)

    # 📉 Bar Chart – Actual vs Recommended
    with col2:
        fig2, ax2 = plt.subplots(figsize=(4.5, 3))

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

        ax2.bar(x - width/2, actual, width, label="Actual")
        ax2.bar(x + width/2, recommended, width, label="Recommended")

        ax2.set_xticks(x)
        ax2.set_xticklabels(categories, rotation=30, ha="right", fontsize=8)
        ax2.set_ylabel("Amount (₹)")
        ax2.set_title("Actual vs Recommended", fontsize=10)
        ax2.legend(fontsize=8)

        st.pyplot(fig2)

    # ---------- ROW 2 (1 centered graph) ----------
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.markdown("### 📈 Monthly Spending Trend")

        monthly_spend = get_monthly_spending_trend(df)

        fig3, ax3 = plt.subplots(figsize=(5, 3))
        ax3.plot(
            monthly_spend["Month"],
            monthly_spend["Amount"],
            marker="o"
        )
        ax3.set_xlabel("Month")
        ax3.set_ylabel("Total Spend (₹)")
        ax3.grid(True)

        st.pyplot(fig3)

    # =================================================
    # RECOMMENDATIONS
    # =================================================
    st.subheader("❌ Where NOT to Spend")
    if summary["avoid"]:
        for item in summary["avoid"]:
            st.error(item)
    else:
        st.success("No major overspending detected.")

    st.subheader("✅ Safe Spending Areas")
    for item in summary["okay"]:
        st.success(item)

    st.subheader("📋 Action Plan")
    for act in summary["actions"]:
        st.warning(act)

    st.subheader("🎯 Monthly Saving Goal")
    st.info(summary["goal"])

    # =================================================
    # GOAL MODE
    # =================================================
    if goal_plan:
        st.subheader("🎯 Goal Planning")

        st.write(
            f"**Goal:** {goal_plan['goal']}  \n"
            f"**Target Amount:** ₹{goal_plan['target_amount']}  \n"
            f"**Duration:** {goal_plan['duration_months']} months  \n"
            f"**Monthly Required:** ₹{goal_plan['monthly_saving_required']}"
        )

        progress = max(analysis["remaining"], 0) / goal_plan["target_amount"]
        st.progress(min(progress, 1.0))

        if goal_plan["feasible"]:
            st.success("✅ Goal is achievable with current spending.")
        else:
            st.error("⚠️ Goal requires spending adjustments.")

        for step in goal_plan["plan"]:
            st.warning(step)

    # =================================================
    # EXPLANATION
    # =================================================
    st.subheader("🧠 Explanation")
    st.write(explanation)

    with st.expander("📄 View Uploaded Data"):
        st.dataframe(df)

else:
    st.info("👈 Upload an expense file and enter a budget to begin.")
