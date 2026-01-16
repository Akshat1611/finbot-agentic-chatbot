import streamlit as st
import pandas as pd

from finbot import (
    load_expense_data,
    finbot_advanced
)

# -------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="FinBot – Agentic Finance Assistant",
    layout="wide"
)

st.title("💰 FinBot – Agentic Finance Assistant")
st.write(
    "Upload your expense file, enter your budget, and get actionable "
    "financial insights with optional goal-based planning."
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

# Goal Mode Inputs
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

    try:
        df = load_expense_data(uploaded_file)

        analysis, summary, goal_plan, explanation = finbot_advanced(
            df=df,
            budget=budget,
            goal_name=None if goal_name == "None" else goal_name,
            goal_amount=goal_amount
        )

        # -------------------------------------------------
        # Display Budget Summary
        # -------------------------------------------------
        st.subheader("📊 Budget Summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("Budget (₹)", analysis["budget"])
        col2.metric("Total Spent (₹)", analysis["total_spent"])
        col3.metric("Remaining (₹)", analysis["remaining"])

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
        # Financial Goal (General)
        # -------------------------------------------------
        st.subheader("🎯 Monthly Financial Goal")
        st.info(summary["goal"])

        # -------------------------------------------------
        # Goal Mode Output
        # -------------------------------------------------
        if goal_plan:
            st.subheader("🎯 Goal-Based Planning")

            st.write(
                f"**Goal:** {goal_plan['goal']}  \n"
                f"**Target Amount:** ₹{goal_plan['target_amount']}  \n"
                f"**Duration:** {goal_plan['duration_months']} months  \n"
                f"**Monthly Saving Required:** ₹{goal_plan['monthly_saving_required']}"
            )

            if goal_plan["feasible"]:
                st.success("✅ This goal is achievable with your current budget.")
            else:
                st.error("⚠️ This goal requires spending adjustments.")

            for step in goal_plan["plan"]:
                st.warning(step)

        # -------------------------------------------------
        # AI / Rule-Based Explanation
        # -------------------------------------------------
        st.subheader("🧠 Explanation")
        st.write(explanation)

        # -------------------------------------------------
        # Raw Data (Optional View)
        # -------------------------------------------------
        with st.expander("📄 View Uploaded Expense Data"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.info(
        "👈 Please upload an expense file and enter your monthly budget "
        "to begin analysis."
    )
