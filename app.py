import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

from finbot import (
    load_expense_data,
    finbot_advanced,
    get_monthly_spending_trend,
    ai_chat_response
)

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="FinBot – AI Finance Chatbot",
    layout="wide"
)

st.title("💰 FinBot – AI Finance Chatbot")
st.caption("Agentic finance assistant with AI-powered conversation")

# -------------------------------------------------
# Sidebar Inputs
# -------------------------------------------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Expense File", type=["csv", "xlsx"]
)

budget = st.sidebar.number_input(
    "Monthly Budget (₹)", min_value=0, step=500
)

goal_name = st.sidebar.selectbox(
    "Financial Goal",
    ["None", "Emergency Fund", "Travel", "Gadget", "Investment"]
)

goal_amount = None
goal_months = None

if goal_name != "None":
    goal_amount = st.sidebar.number_input(
        "Goal Amount (₹)", min_value=1000, step=1000
    )

    goal_months = st.sidebar.number_input(
        "Target Duration (Months)", min_value=1, max_value=60, value=6
    )

# -------------------------------------------------
# Main Logic
# -------------------------------------------------
if uploaded_file and budget > 0:
    df = load_expense_data(uploaded_file)

    analysis, summary, goal_plan, explanation = finbot_advanced(
        df,
        budget,
        None if goal_name == "None" else goal_name,
        goal_amount,
        goal_months
    )

    st.info(
        f"📅 Months detected: {analysis['months_detected']} "
        f"({', '.join(analysis['months'])})"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Budget", int(analysis["budget"]))
    c2.metric("Avg Spend", int(analysis["avg_monthly_spent"]))
    c3.metric("Remaining", int(analysis["remaining"]))

    # -------------------------------------------------
    # Charts
    # -------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(
            analysis["category_breakdown"].values(),
            labels=analysis["category_breakdown"].keys(),
            autopct="%1.0f%%"
        )
        ax1.set_title("Spending Distribution")
        st.pyplot(fig1)

    with col2:
        cats = list(analysis["category_breakdown"].keys())
        vals = list(analysis["category_breakdown"].values())
        x = np.arange(len(cats))

        fig2, ax2 = plt.subplots(figsize=(4.5, 3))
        ax2.bar(x, vals)
        ax2.set_xticks(x)
        ax2.set_xticklabels(cats, rotation=30)
        ax2.set_title("Avg Monthly Spend")
        st.pyplot(fig2)

    trend = get_monthly_spending_trend(df)
    fig3, ax3 = plt.subplots(figsize=(5, 3))
    ax3.plot(trend["Month"], trend["Amount"], marker="o")
    ax3.set_title("Monthly Spending Trend")
    st.pyplot(fig3)

    # -------------------------------------------------
    # Goal Planning
    # -------------------------------------------------
    if goal_plan:
        st.subheader("🎯 Goal Planning Summary")

        st.write(
            f"""
            **Goal:** {goal_plan['goal']}  
            **Target Amount:** ₹{goal_plan['target_amount']}  
            **Duration:** {goal_plan['duration_months']} months  
            **Required / Month:** ₹{goal_plan['monthly_saving_required']}  
            **Current Saving Capacity:** ₹{goal_plan['current_saving']}
            """
        )

        progress = min(
            goal_plan["current_saving"] / goal_plan["target_amount"], 1.0
        )

        st.progress(progress)

        if goal_plan["feasible"]:
            st.success("✅ Goal is achievable.")
        else:
            st.warning("⚠️ Increase duration or reduce expenses.")

    # -------------------------------------------------
    # Chatbot
    # -------------------------------------------------
    st.subheader("💬 Chat with FinBot")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask FinBot about your finances...")

    if user_input:
        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        reply = ai_chat_response(
            user_input,
            analysis,
            summary,
            goal_plan
        )

        st.session_state.chat_history.append(
            {"role": "assistant", "content": reply}
        )

        with st.chat_message("assistant"):
            st.markdown(reply)

else:
    st.info("👈 Upload a file and enter budget to begin.")
