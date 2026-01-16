import pandas as pd

# -------------------------------
# OPTIONAL LLM (Safe Import)
# -------------------------------
USE_LLM = False
llm = None

try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3", temperature=0)
    USE_LLM = True
except Exception:
    USE_LLM = False


# -------------------------------
# Budget Rules (Configurable)
# -------------------------------
CATEGORY_LIMITS = {
    "Food": 40,
    "Rent": 35,
    "Shopping": 15,
    "Entertainment": 10,
    "Travel": 10,
    "Utilities": 10
}


# -------------------------------
# Load Expense Data
# -------------------------------
def load_expense_data(file):
    """
    Load expense data from CSV or Excel.
    Required columns: Date, Category, Amount
    """
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        raise ValueError("Only CSV and Excel files are supported")

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df.dropna(subset=["Category", "Amount"], inplace=True)

    return df


# -------------------------------
# Budget Analysis Tool
# -------------------------------
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
        "budget": budget,
        "total_spent": round(total_spent, 2),
        "remaining": round(remaining, 2),
        "category_breakdown": breakdown
    }


# -------------------------------
# Recommendation Agent
# -------------------------------
def generate_recommendations(analysis):
    budget = analysis["budget"]
    breakdown = analysis["category_breakdown"]
    remaining = analysis["remaining"]

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

    # Goal logic
    if remaining > 0:
        goal = f"Save ₹{remaining} this month"
    else:
        goal = "Cut discretionary expenses to return within budget"

    return {
        "avoid": avoid,
        "okay": okay,
        "actions": actions,
        "goal": goal
    }


# -------------------------------
# Explanation Generator
# -------------------------------
def generate_explanation(summary):
    """
    Uses LLM if available, otherwise falls back to rule-based explanation.
    """
    if USE_LLM and llm is not None:
        prompt = f"""
        Explain the following financial advice in simple, friendly language:

        Overspending areas: {summary['avoid']}
        Safe spending areas: {summary['okay']}
        Goal: {summary['goal']}
        Action steps: {summary['actions']}
        """
        try:
            return llm.invoke(prompt).content
        except Exception:
            pass

    # Rule-based fallback (Cloud-safe)
    explanation = (
        "Based on your expenses and budget, you should reduce spending "
        "in high discretionary categories and focus on saving the remaining amount. "
        "Prioritize essentials and avoid unnecessary purchases."
    )

    return explanation


# -------------------------------
# MASTER AGENT FUNCTION
# -------------------------------
def finbot_advanced(df, budget):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)
    explanation = generate_explanation(summary)

    return analysis, summary, explanation
