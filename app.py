import streamlit as st
import matplotlib.pyplot as plt

from finbot import (
    load_expense_data,
    finbot_advanced
)

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="FinBot – Agentic Finance Assistant",
    layout="wide"
)

st.title("💰 FinBot – Agentic Finance Assistant")
st.write(
    "Upload your expense file, enter your monthly budget, and receive "
    "actionable financial insights with goal-based planning."
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

# Goal Mode
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
# Main Processing
# -------------------------------------------------
if uploaded_file and budget > 0:

    try:
        df = load_expense_data(uploaded_file)

        analysis, summary, goal_plan, explanation = finbot_advanced(
            df=df,
            budget=budget,
            goal_name=None if goal_name == "None" else goal_name,
            goal_amount=goal_amount
        )

        # -------------------------------------------------
        # Budget Summary
        # -------------------------------------------------
        st.subheader("📊 Budget Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Monthly Budget (₹)", analysis["budget"])
        c2.metric("Total Spent (₹)", analysis["total_spent"])
        c3.metric("Remaining (₹)", analysis["remaining"])

        # -------------------------------------------------
        # Spending Distribution (Pie Chart)
        # -------------------------------------------------
        st.subheader("📊 Spending Distribution")

        fig1, ax1 = plt.subplots()
        ax1.pie(
            analysis["category_breakdown"].values(),
            labels=analysis["category_breakdown"].keys(),
            autopct="%1.1f%%",
            startangle=90
        )
        ax1.axis("equal")
        st.pyplot(fig1)

        # -------------------------------------------------
        # Spending vs Recommended Limit (Bar Chart)
        # -------------------------------------------------
        st.subheader("📉 Spending vs Recommended Limits")

        CATEGORY_LIMITS = {
            "Food": 40,
            "Rent": 35,
            "Shopping": 15,
            "Entertainment": 10,
            "Travel": 10,
            "Utilities": 10
        }

        categories = []
        actual = []
        limits = []

        for category, amount in analysis["category_breakdown"].items():
            limit_pct = CATEGORY_LIMITS.get(category, 20)
            categories.append(category)
            actual.append(amount)
            limits.append((limit_pct / 100) * analysis["budget"])

        fig2, ax2 = plt.subplots()
        ax2.bar(categories, actual, label="Actual Spending")
        ax2.bar(categories, limits, alpha=0.6, label="Recommended Limit")
        ax2.set_ylabel("Amount (₹)")
        ax2.legend()
        st.pyplot(fig2)

        # -------------------------------------------------
        # Overspending Areas
        # -------------------------------------------------
        st.subheader("❌ Where NOT to Spend")

        if summary["avoid"]:
            for item in summary["avoid"]:
                st.error(item)
        else:
            st.success("No major overspending detected.")

        # -------------------------------------------------
        # Safe Spending Areas
        # -------------------------------------------------
        st.subheader("✅ Safe Spending Areas")

        if summary["okay"]:
            for item in summary["okay"]:
                st.success(item)
        else:
            st.info("No safe categories identified.")

        # -------------------------------------------------
        # Action Plan
        # -------------------------------------------------
        st.subheader("📋 Recommended Action Plan")

        if summary["actions"]:
            for action in summary["actions"]:
                st.warning(action)
        else:
            st.success("No immediate action required.")

        # -------------------------------------------------
        # Monthly Financial Goal
        # -------------------------------------------------
        st.subheader("🎯 Monthly Financial Goal")
        st.info(summary["goal"])

        # -------------------------------------------------
        # Goal Mode Output + Progress
        # -------------------------------------------------
        if goal_plan:
            st.subheader("🎯 Goal-Based Planning")

            st.write(
                f"**Goal:** {goal_plan['goal']}  \n"
                f"**Target Amount:** ₹{goal_plan['target_amount']}  \n"
                f"**Duration:** {goal_plan['duration_months']} months  \n"
                f"**Monthly Saving Required:** ₹{goal_plan['monthly_saving_required']}"
            )

            # Progress bar
            st.subheader("📈 Goal Progress")

            current_saving = max(analysis["remaining"], 0)
            progress = min(current_saving / goal_plan["target_amount"], 1.0)

            st.progress(progress)

            st.write(
                f"Saved this month: ₹{current_saving} / ₹{goal_plan['target_amount']} "
                f"({int(progress * 100)}%)"
            )

            if goal_plan["feasible"]:
                st.success("✅ You are on track to achieve this goal.")
            else:
                st.error("⚠️ You need spending adjustments to achieve this goal.")

            for step in goal_plan["plan"]:
                st.warning(step)

        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------
        st.subheader("🧠 Explanation")
        st.write(explanation)

        # -------------------------------------------------
        # Raw Data
        # -------------------------------------------------
        with st.expander("📄 View Uploaded Expense Data"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error processing data: {e}")

else:
    st.info(
        "👈 Upload an expense file and enter your monthly budget to begin."
    )

