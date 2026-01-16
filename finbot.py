import pandas as pd

# -------------------------------------------------
# AI SETUP (LLaMA 3 via Ollama)
# -------------------------------------------------
USE_LLM = False
llm = None

try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0.3)
    USE_LLM = True
except Exception as e:
    print("LLM INIT ERROR:", e)
    USE_LLM = False

# -------------------------------------------------
# Load Expense Data
# -------------------------------------------------
def load_expense_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        raise ValueError("Only CSV and Excel supported")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

    df.dropna(subset=["Date", "Category", "Amount"], inplace=True)
    df["Month"] = df["Date"].dt.strftime("%b %Y")

    return df

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def get_monthly_summary(df):
    monthly = df.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    avg_monthly = monthly.groupby("Category")["Amount"].mean().to_dict()
    return avg_monthly, df["Month"].nunique(), sorted(df["Month"].unique())

def get_monthly_spending_trend(df):
    return df.groupby("Month")["Amount"].sum().reset_index()

# -------------------------------------------------
# Budget Analysis
# -------------------------------------------------
def analyze_budget(df, budget):
    avg_breakdown, months_count, months = get_monthly_summary(df)
    avg_spent = sum(avg_breakdown.values())
    remaining = budget - avg_spent

    return {
        "budget": budget,
        "avg_monthly_spent": avg_spent,
        "remaining": remaining,
        "months_detected": months_count,
        "months": months,
        "category_breakdown": avg_breakdown
    }

# -------------------------------------------------
# Recommendation Agent
# -------------------------------------------------
def generate_recommendations(analysis):
    CATEGORY_LIMITS = {
        "Food": 40,
        "Rent": 35,
        "Shopping": 15,
        "Entertainment": 10,
        "Travel": 10,
        "Utilities": 10
    }

    avoid, okay, actions = [], [], []

    for cat, amt in analysis["category_breakdown"].items():
        limit = CATEGORY_LIMITS.get(cat, 20)
        percent = (amt / analysis["budget"]) * 100

        if percent > limit:
            avoid.append(f"{cat}: ₹{int(amt)} ({percent:.1f}% > {limit}%)")
            actions.append(f"Reduce {cat} spending")
        else:
            okay.append(f"{cat}: ₹{int(amt)} ({percent:.1f}%)")

    goal_text = (
        f"Save ₹{int(max(analysis['remaining'], 0))} per month"
        if analysis["remaining"] > 0
        else "Reduce expenses to start saving"
    )

    return {
        "avoid": avoid,
        "okay": okay,
        "actions": actions,
        "goal": goal_text
    }

# -------------------------------------------------
# Goal Planning Agent (USER DEFINED MONTHS)
# -------------------------------------------------
def goal_planning_agent(analysis, goal_name, goal_amount, goal_months):
    monthly_required = goal_amount / goal_months
    current_saving = max(analysis["remaining"], 0)

    feasible = current_saving >= monthly_required

    return {
        "goal": goal_name,
        "target_amount": goal_amount,
        "duration_months": goal_months,
        "monthly_saving_required": int(monthly_required),
        "current_saving": int(current_saving),
        "feasible": feasible
    }

# -------------------------------------------------
# CONTEXT BUILDER (IMPORTANT)
# -------------------------------------------------
def build_financial_context(analysis, summary, goal_plan):
    context = f"""
    USER FINANCIAL SUMMARY:

    Monthly Budget: ₹{analysis['budget']}
    Average Monthly Spend: ₹{analysis['avg_monthly_spent']}
    Remaining Amount: ₹{analysis['remaining']}

    Spending Breakdown:
    """

    for cat, amt in analysis["category_breakdown"].items():
        context += f"- {cat}: ₹{int(amt)}\n"

    if summary["avoid"]:
        context += "\nOverspending Areas:\n"
        for a in summary["avoid"]:
            context += f"- {a}\n"
    else:
        context += "\nNo major overspending detected.\n"

    if goal_plan:
        context += f"""
        GOAL DETAILS:
        Goal: {goal_plan['goal']}
        Target Amount: ₹{goal_plan['target_amount']}
        Duration: {goal_plan['duration_months']} months
        Monthly Required Saving: ₹{goal_plan['monthly_saving_required']}
        """

    return context

# -------------------------------------------------
# AI CHAT RESPONSE (WITH CONTEXT)
# -------------------------------------------------
def ai_chat_response(user_input, analysis, summary, goal_plan):
    context = build_financial_context(analysis, summary, goal_plan)

    fallback = (
        f"Your monthly budget is ₹{analysis['budget']}. "
        f"You spend ₹{int(analysis['avg_monthly_spent'])} on average."
    )

    if not USE_LLM or llm is None:
        return fallback

    prompt = f"""
    You are FinBot, a helpful personal finance AI.

    {context}

    USER QUESTION:
    {user_input}

    Answer clearly using the user's actual financial data.
    """

    try:
        return llm.invoke(prompt).content
    except Exception as e:
        print("AI CHAT ERROR:", e)
        return fallback

# -------------------------------------------------
# MASTER FUNCTION
# -------------------------------------------------
def finbot_advanced(
    df,
    budget,
    goal_name=None,
    goal_amount=None,
    goal_months=None
):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    goal_plan = None
    if goal_name and goal_amount and goal_months:
        goal_plan = goal_planning_agent(
            analysis,
            goal_name,
            goal_amount,
            goal_months
        )

    explanation = (
        "Insights are generated using agent-based financial analysis."
    )

    return analysis, summary, goal_plan, explanation
