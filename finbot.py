import pandas as pd

# -----------------------------------------
# Optional LLM (Safe for Cloud)
# -----------------------------------------
USE_LLM = False
llm = None

try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0)
    USE_LLM = True
except Exception:
    USE_LLM = False


# -----------------------------------------
# Configuration
# -----------------------------------------
CATEGORY_LIMITS = {
    "Food": 40,
    "Rent": 35,
    "Shopping": 15,
    "Entertainment": 10,
    "Travel": 10,
    "Utilities": 10
}

GOALS = {
    "Emergency Fund": 6,
    "Travel": 6,
    "Gadget": 4,
    "Investment": 12
}


# -----------------------------------------
# Load Expense Data (Indian Dates Supported)
# -----------------------------------------
def load_expense_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        raise ValueError("Only CSV and Excel supported")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    # Indian + month-name date parsing
    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

    df.dropna(subset=["Date", "Category", "Amount"], inplace=True)

    # Month in readable format (Jan 2026)
    df["Month"] = df["Date"].dt.strftime("%b %Y")

    return df


# -----------------------------------------
# Monthly Summary (Multi-month Support)
# -----------------------------------------
def get_monthly_summary(df):
    monthly = (
        df.groupby(["Month", "Category"])["Amount"]
        .sum()
        .reset_index()
    )

    avg_monthly = (
        monthly.groupby("Category")["Amount"]
        .mean()
        .to_dict()
    )

    months_detected = df["Month"].nunique()
    month_list = sorted(df["Month"].unique())

    return avg_monthly, months_detected, month_list


# -----------------------------------------
# Budget Analysis
# -----------------------------------------
def analyze_budget(df, budget):
    avg_breakdown, months_count, months = get_monthly_summary(df)

    avg_monthly_spent = sum(avg_breakdown.values())
    remaining = budget - avg_monthly_spent

    return {
        "budget": round(budget, 2),
        "avg_monthly_spent": round(avg_monthly_spent, 2),
        "remaining": round(remaining, 2),
        "months_detected": months_count,
        "months": months,
        "category_breakdown": avg_breakdown
    }


# -----------------------------------------
# Recommendation Agent
# -----------------------------------------
def generate_recommendations(analysis):
    budget = analysis["budget"]
    remaining = analysis["remaining"]
    breakdown = analysis["category_breakdown"]

    avoid, okay, actions = [], [], []

    for category, amount in breakdown.items():
        limit = CATEGORY_LIMITS.get(category, 20)
        percent = (amount / budget) * 100

        if percent > limit:
            avoid.append(f"{category}: ₹{int(amount)} ({percent:.1f}% > {limit}%)")
            reduce_by = amount - (limit / 100) * budget
            actions.append(f"Reduce {category} by approx ₹{int(reduce_by)} per month")
        else:
            okay.append(f"{category}: ₹{int(amount)} ({percent:.1f}%)")

    goal_text = (
        f"Save ₹{int(remaining)} per month"
        if remaining > 0
        else "Reduce discretionary expenses to stay within budget"
    )

    return {
        "avoid": avoid,
        "okay": okay,
        "actions": actions,
        "goal": goal_text
    }


# -----------------------------------------
# Goal Planning Agent
# -----------------------------------------
def goal_planning_agent(analysis, goal_name, goal_amount):
    months = GOALS.get(goal_name, 6)
    monthly_required = goal_amount / months
    remaining = analysis["remaining"]

    feasible = remaining >= monthly_required
    plan = []

    if feasible:
        plan.append(f"Save ₹{int(monthly_required)} per month to reach this goal.")
    else:
        shortfall = monthly_required - remaining
        plan.append(f"Need ₹{int(shortfall)} more per month to reach this goal.")
        for cat in ["Shopping", "Entertainment", "Travel"]:
            if cat in analysis["category_breakdown"]:
                plan.append(f"Reduce {cat} spending by ₹500–₹1000.")

    return {
        "goal": goal_name,
        "target_amount": goal_amount,
        "duration_months": months,
        "monthly_saving_required": int(monthly_required),
        "feasible": feasible,
        "plan": plan
    }


# -----------------------------------------
# Explanation Generator
# -----------------------------------------
def generate_explanation(summary, goal_plan=None):
    if USE_LLM and llm:
        try:
            return llm.invoke(
                f"Explain this financial advice simply: {summary}, Goal: {goal_plan}"
            ).content
        except Exception:
            pass

    return (
        "Based on your average monthly spending, reduce overspending categories, "
        "prioritize essentials, and save consistently to achieve your financial goals."
    )


# -----------------------------------------
# MASTER FUNCTION
# -----------------------------------------
def finbot_advanced(df, budget, goal_name=None, goal_amount=None):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    goal_plan = None
    if goal_name and goal_amount:
        goal_plan = goal_planning_agent(analysis, goal_name, goal_amount)

    explanation = generate_explanation(summary, goal_plan)

    return analysis, summary, goal_plan, explanation
