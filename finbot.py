import pandas as pd

# -------------------------------------------------
# Optional LLM (Cloud-safe)
# -------------------------------------------------
USE_LLM = False
llm = None

try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0)
    USE_LLM = True
except Exception:
    USE_LLM = False


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
# Load Expense Data (Indian + Month Names)
# -------------------------------------------------
def load_expense_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        raise ValueError("Only CSV and Excel supported")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

    df.dropna(subset=["Date", "Category", "Amount"], inplace=True)

    df["Month"] = df["Date"].dt.strftime("%b %Y")

    return df


# -------------------------------------------------
# Monthly Helpers
# -------------------------------------------------
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
    months = sorted(df["Month"].unique())

    return avg_monthly, months_detected, months


def get_monthly_spending_trend(df):
    return (
        df.groupby("Month")["Amount"]
        .sum()
        .reset_index()
    )


# -------------------------------------------------
# Budget Analysis
# -------------------------------------------------
def analyze_budget(df, budget):
    avg_breakdown, months_count, months = get_monthly_summary(df)

    avg_spent = sum(avg_breakdown.values())
    remaining = budget - avg_spent

    return {
        "budget": round(budget, 2),
        "avg_monthly_spent": round(avg_spent, 2),
        "remaining": round(remaining, 2),
        "months_detected": months_count,
        "months": months,
        "category_breakdown": avg_breakdown
    }


# -------------------------------------------------
# Recommendation Agent
# -------------------------------------------------
def generate_recommendations(analysis):
    budget = analysis["budget"]
    remaining = analysis["remaining"]
    breakdown = analysis["category_breakdown"]

    avoid, okay, actions = [], [], []

    for category, amount in breakdown.items():
        limit = CATEGORY_LIMITS.get(category, 20)
        percent = (amount / budget) * 100

        if percent > limit:
            avoid.append(
                f"{category}: ₹{int(amount)} ({percent:.1f}% > {limit}%)"
            )
            reduce_by = amount - (limit / 100) * budget
            actions.append(
                f"Reduce {category} by approx ₹{int(reduce_by)} per month"
            )
        else:
            okay.append(
                f"{category}: ₹{int(amount)} ({percent:.1f}%)"
            )

    goal_text = (
        f"Save ₹{int(remaining)} per month"
        if remaining > 0
        else "Reduce discretionary spending to stay within budget"
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
    remaining = analysis["remaining"]

    feasible = remaining >= monthly_required
    plan = []

    if feasible:
        plan.append(
            f"Save ₹{int(monthly_required)} per month to reach this goal."
        )
    else:
        shortfall = monthly_required - remaining
        plan.append(
            f"You need ₹{int(shortfall)} more per month."
        )
        for cat in ["Shopping", "Entertainment", "Travel"]:
            if cat in analysis["category_breakdown"]:
                plan.append(
                    f"Reduce {cat} spending by ₹500–₹1000."
                )

    return {
        "goal": goal_name,
        "target_amount": goal_amount,
        "duration_months": months,
        "monthly_saving_required": int(monthly_required),
        "feasible": feasible,
        "plan": plan
    }


# -------------------------------------------------
# Multi-Step Planner Agent (NEW)
# -------------------------------------------------
def multi_step_planner(analysis, summary, goal_plan=None):
    steps = []
    step_no = 1

    for action in summary["actions"]:
        steps.append(f"Step {step_no}: {action}")
        step_no += 1

    if analysis["remaining"] > 0:
        steps.append(
            f"Step {step_no}: Allocate ₹{int(analysis['remaining'])} to savings"
        )
        step_no += 1

    if goal_plan:
        steps.append(
            f"Step {step_no}: Redirect savings towards '{goal_plan['goal']}'"
        )
        step_no += 1

    steps.append(
        f"Step {step_no}: Review expenses and progress next month"
    )

    return steps


# -------------------------------------------------
# Explanation Generator
# -------------------------------------------------
def generate_explanation(summary, goal_plan=None):
    if USE_LLM and llm:
        try:
            return llm.invoke(
                f"Explain this financial advice simply: {summary}, Goal: {goal_plan}"
            ).content
        except Exception:
            pass

    return (
        "Based on your average monthly spending, reduce overspending, "
        "prioritize essentials, and follow the step-by-step plan to "
        "achieve your financial goals."
    )


# -------------------------------------------------
# MASTER FUNCTION
# -------------------------------------------------
def finbot_advanced(df, budget, goal_name=None, goal_amount=None):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    goal_plan = None
    if goal_name and goal_amount:
        goal_plan = goal_planning_agent(analysis, goal_name, goal_amount)

    steps = multi_step_planner(analysis, summary, goal_plan)
    explanation = generate_explanation(summary, goal_plan)

    return analysis, summary, goal_plan, steps, explanation
