import streamlit as st
import matplotlib.pyplot as plt

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
st.write(
    "Upload your expense data, enter a monthly budget, and receive "
    "goal-based financial insights with visual analytics."
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
# Main App Logic
# -------------------------------------------------
if uploaded_file and budget > 0:
    df = load_expense_data(uploaded_file)

    analysis, summary, goal_plan, explanation = finbot_advanced(
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
    # Pie Chart
    # -------------------------------------------------
    st.subheader("📊 Spending Distribution (Avg Monthly)")

    fig1, ax1 = plt.subplots(4,4)
    ax1.pie(
        analysis["category_breakdown"].values(),
        labels=analysis["category_breakdown"].keys(),
        autopct="%1.1f%%",
        startangle=90
    )
    ax1.axis("equal")
    st.pyplot(fig1)

    # -------------------------------------------------
    # Bar Chart
    # -------------------------------------------------
    st.subheader("📉 Spending vs Recommended Limits")

    LIMITS = {
        "Food": 40, "Rent": 35, "Shopping": 15,
        "Entertainment": 10, "Travel": 10, "Utilities": 10
    }

    cats, actual, limits = [], [], []
    for cat, amt in analysis["category_breakdown"].items():
        cats.append(cat)
        actual.append(amt)
        limits.append((LIMITS.get(cat, 20) / 100) * analysis["budget"])

    fig2, ax2 = plt.subplots(5,3)
    ax2.bar(cats, actual, label="Actual")
    ax2.bar(cats, limits, alpha=0.6, label="Recommended")
    ax2.set_ylabel("Amount (₹)")
    ax2.legend()
    st.pyplot(fig2)

    # -------------------------------------------------
    # Month-wise Trend Graph
    # -------------------------------------------------
    st.subheader("📈 Month-wise Spending Trend")

    monthly_spend = get_monthly_spending_trend(df)

    fig3, ax3 = plt.subplots(5,3)
    ax3.plot(
        monthly_spend["Month"],
        monthly_spend["Amount"],
        marker="o"
    )
    ax3.set_xlabel("Month")
    ax3.set_ylabel("Total Spending (₹)")
    ax3.grid(True)
    st.pyplot(fig3)

    # -------------------------------------------------
    # Recommendations
    # -------------------------------------------------
    st.subheader("❌ Where NOT to Spend")
    for item in summary["avoid"]:
        st.error(item)

    st.subheader("✅ Safe Spending Areas")
    for item in summary["okay"]:
        st.success(item)

    st.subheader("📋 Action Plan")
    for act in summary["actions"]:
        st.warning(act)

    st.subheader("🎯 Monthly Saving Goal")
    st.info(summary["goal"])

    # -------------------------------------------------
    # Goal Mode
    # -------------------------------------------------
    if goal_plan:
        st.subheader("🎯 Goal Planning")

        st.write(
            f"**Goal:** {goal_plan['goal']}  \n"
            f"**Target:** ₹{goal_plan['target_amount']}  \n"
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

    # -------------------------------------------------
    # Explanation
    # -------------------------------------------------
    st.subheader("🧠 Explanation")
    st.write(explanation)

    with st.expander("📄 View Uploaded Data"):
        st.dataframe(df)

else:
    st.info("👈 Upload an expense file and enter a budget to begin.")

