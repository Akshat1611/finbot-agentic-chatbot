import pandas as pd

# -------------------------------------------------
# Configuration
# -------------------------------------------------
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
# Monthly Helpers
# -------------------------------------------------
def get_monthly_summary(df):
    monthly = df.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    avg_monthly = monthly.groupby("Category")["Amount"].mean().to_dict()
    months_detected = df["Month"].nunique()
    months = sorted(df["Month"].unique())

    return avg_monthly, months_detected, months

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
# Goal Planning Agent
# -------------------------------------------------
def goal_planning_agent(analysis, goal_name, goal_amount):
    months = GOALS.get(goal_name, 6)
    monthly_required = goal_amount / months
    current_saving = max(analysis["remaining"], 0)

    feasible = current_saving >= monthly_required

    return {
        "goal": goal_name,
        "target_amount": goal_amount,
        "duration_months": months,
        "monthly_saving_required": int(monthly_required),
        "current_saving": int(current_saving),
        "feasible": feasible
    }

# -------------------------------------------------
# MASTER FUNCTION (RETURNS 4 VALUES – MATCHES app.py)
# -------------------------------------------------
def finbot_advanced(df, budget, goal_name=None, goal_amount=None):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    goal_plan = None
    if goal_name and goal_amount:
        goal_plan = goal_planning_agent(
            analysis, goal_name, goal_amount
        )

    explanation = (
        "Insights are generated based on average monthly spending "
        "with goal-oriented financial planning."
    )

    return analysis, summary, goal_plan, explanation
