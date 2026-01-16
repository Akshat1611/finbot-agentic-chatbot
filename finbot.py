import pandas as pd
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3", temperature=0)

CATEGORY_LIMITS = {
    "Food": 40,
    "Rent": 35,
    "Shopping": 15,
    "Entertainment": 10,
    "Travel": 10
}

def load_expense_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

def analyze_budget(df, budget):
    total_spent = df["Amount"].sum()
    remaining = budget - total_spent

    breakdown = (
        df.groupby("Category")["Amount"]
        .sum()
        .to_dict()
    )

    return {
        "budget": budget,
        "total_spent": total_spent,
        "remaining": remaining,
        "category_breakdown": breakdown
    }

def generate_recommendations(analysis):
    budget = analysis["budget"]
    breakdown = analysis["category_breakdown"]

    avoid, okay, actions = [], [], []

    for category, amount in breakdown.items():
        limit = CATEGORY_LIMITS.get(category, 20)
        percent = (amount / budget) * 100

        if percent > limit:
            avoid.append(f"{category}: ₹{amount} ({percent:.1f}%)")
            actions.append(
                f"Reduce {category} by ₹{int(amount - (limit/100)*budget)}"
            )
        else:
            okay.append(f"{category}: ₹{amount} ({percent:.1f}%)")

    goal = (
        f"Save ₹{analysis['remaining']} this month"
        if analysis["remaining"] > 0
        else "Reduce discretionary expenses"
    )

    return {
        "avoid": avoid,
        "okay": okay,
        "actions": actions,
        "goal": goal
    }

def finbot_advanced(df, budget):
    analysis = analyze_budget(df, budget)
    summary = generate_recommendations(analysis)

    explanation = llm.invoke(
        f"Explain this finance advice simply: {summary}"
    ).content

    return analysis, summary, explanation
