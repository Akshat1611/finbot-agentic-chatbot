"""
FinBot Logic Module
------------------
Cloud-safe, goal-aware agentic finance logic.
"""

import pandas as pd

# =====================================================
# Optional LLM (LLaMA 3 via Ollama) – Safe Import
# =====================================================
USE_LLM = False
llm = None

try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0)
    USE_LLM = True
except Exception:
    USE_LLM = False


# =====================================================
# Configuration
# =====================================================

CATEGORY_LIMITS = {
    "Food": 40,
    "Rent": 35,
    "Shopping": 15,
    "Entertainment": 10,
    "Travel": 10,
    "Utilities": 10
}

GOALS = {
    "Emergency Fund": {
        "months": 6,
        "description": "Financial safety net"
    },
    "Travel": {
        "months": 6,
        "description": "Trip or vacation"
    },
    "Gadget": {
        "months": 4,
        "description": "Laptop / phone purchase"
    },
    "Investment": {
        "months": 12,
        "description": "Long-term wealth building"
    }
}


# =====================================================
# Data Loading
# =====================================================
def load_expense_data(file):
    """
    Load CSV or Excel expense file.
    Required columns: Date, Category, Amount
    """
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        raise ValueError("Unsupported file type")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df.dropna(subset=["Category", "Amount"], inplace=True)

    return df


# =====================================================
# Budget Analysis Tool
# =====================================================
def analyze_budget(df, budget):
    total_spent = df["Amount"].sum()
    remaining = budget - total_spent

    breakdown = (
        df.groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    return {
        "budget": round(budget, 2),
        "total_spent": round(total_spent, 2),
        "remaining": round(remaining, 2),
        "category_breakdown": breakdown
    }


# =====================================================
# Recommendation Agent
# =====================================================
def generate_recommendations(analysis):
    budget = analysis["budget"]
    remaining = analysis["remaining"]
    breakdown = analysis["category_breakdown"]

    avoid = []
    okay = []
    actions = []

    for category, amount in breakdown.items():
        limit = CATEGORY_LIMITS.get(category, 20)
        percent = (amount / budget) * 100

        if percent > limit:
            avoid.append(
                f"{category}: ₹{amount} ({percent:.1f}% > {limit}%)"
            )
            reduce_by = amount - (limit / 100) * budget
            actions.append(
                f"Reduce {category} spending by approx ₹{int(reduce_by)}"
            )
        else:
            okay.append(
                f"{category}: ₹{amount} ({percent:.1f}%)"
            )

    goal_text = (
        f"Save ₹{remaining} this month"
        if remaining > 0
        else "Reduce discretionary spending to stay within budget"
    )

    return {
        "avoid": avoid,
        "okay": okay,
        "actions": actions,
        "goal": goal_text
    }


# =====================================================
# Goal Planning Agent
# =====================================================
def goal_planning_agent(analysis, goal_name, goal_amount):
    remaining = analysis["remaining"]
    breakdown = analysis["category_breakdown"]

    months = GOALS.get(goal_name, {}).get("months", 6)
    monthly_required = goal_amount / months

    feasible = remaining >= monthly_required
    plan = []

    if feasible:
        plan.append(
            f"Save ₹{int(monthly_required)} per month to achieve this goal."
        )
    else:
        shortfall = monthly_required - remaining
        plan.append(
            f"You need ₹{int(shortfall)} more per month to reach this goal."
        )

        for category in ["Shopping", "Entertainment", "Travel"]:
            if category in breakdown:
                plan.append(
                    f"Reduce {category} spending by ₹500–₹1000."
                )

    return {
        "goal": goal_name,
        "target_amount": goal_amount,
        "duration_months": months,
        "monthly_saving_required": int(monthly_required),
        "feasible": feasible,
        "plan": plan
    }


# =====================================================
# Explanation Generator (AI or Rule-based)
# =====================================================
def generate_explanation(summary, goal_plan=None):
    if USE_LLM and llm is not None:
        prompt = f"""
        Explain the following financial advice in simple language:

        Overspending areas: {summary['avoid']}
        Safe spending areas: {summary['okay']}
        Goal: {summary['goal']}
        Action steps: {summary['actions']}
        Goal plan: {goal_plan}
        """
        try:
            return llm.invoke(prompt).content
        except Exception:
            pass

    # Rule-based fallback
    explanation = (
        "Based on your expenses and budget, focus on reducing discretionary "
        "spending, prioritizing essential categories, and consistently saving "
        "towards your financial goals."
    )

    return explanation


# =====================================================
# MASTER AGENT FUNCTION
# =====================================================
def finbot_advanced(df, budget, goal_name=None, goal_amount=None):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    goal_plan = None
    if goal_name and goal_amount:
        goal_plan = goal_planning_agent(
            analysis, goal_name, goal_amount
        )

    explanation = generate_explanation(summary, goal_plan)

    return analysis, summary, goal_plan, explanation
