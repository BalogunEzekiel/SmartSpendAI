from database import get_all_expenses
from datetime import datetime
import calendar

def format_currency(value):
    """Format number with commas as thousands separator (for advice text only)."""
    return "{:,.2f}".format(value)

def smart_advice(total_income, total_expenses):
    """
    Provides AI financial advice based on:
    - Total income and total expenses
    - Spending per category
    Designed for irregular income and dynamic transactions.
    """

    if total_income == 0:
        return "<p>No income recorded yet. Log your income to get actionable advice.</p>"

    savings = total_income - total_expenses
    savings_ratio = savings / total_income

    advice_list = []

    # General savings advice
    if savings < 0:
        advice_list.append(
            "<p>⚠️ You are spending more than you earn! Reduce non-essential expenses immediately.</p>"
        )
    elif savings_ratio < 0.1:
        advice_list.append(
            "<p>⚠️ Your savings are very low. Aim to save at least 10% of your income.</p>"
        )
    elif savings_ratio > 0.3:
        advice_list.append(
            "<p>✅ Excellent! You are saving more than 30% of your income.</p>"
        )
    else:
        advice_list.append(
            "<p>Your spending is balanced. Continue tracking your finances.</p>"
        )

    # Analyze spending by category (ignore income rows)
    all_records = get_all_expenses()
    category_totals = {}

    for _, date, category, income_val, exp_amount in all_records:
        if exp_amount > 0:  # Only consider actual expenses
            category_totals[category] = category_totals.get(category, 0) + exp_amount

    if category_totals:
        advice_list.append("<ul>")  # Start bullet list
        for category, amount in category_totals.items():
            ratio = amount / total_income
            category_bold = f"<b>{category.capitalize()}</b>"

            if ratio > 0.4:
                advice_list.append(
                    f"<li>⚠️ High spending detected in {category_bold} ({format_currency(amount)}). Consider reducing this category.</li>"
                )
            elif ratio < 0.05:
                advice_list.append(
                    f"<li>Spending on {category_bold} is very low ({format_currency(amount)}). Ensure essential needs are covered.</li>"
                )
        advice_list.append("</ul>")  # End bullet list

    # Join all advice as HTML
    return "".join(advice_list)


def predict_month_end(total_income, total_expenses):
    """
    Predict estimated end-of-month savings based on current spending rate.
    Returns raw floats so app.py can format them safely.
    """

    today = datetime.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    current_day = today.day

    if current_day == 0:
        projected_expenses = total_expenses
        projected_savings = total_income - total_expenses
        status = "Not enough data yet"
    else:
        # Average daily spending
        avg_daily_spend = total_expenses / current_day
        projected_expenses = avg_daily_spend * days_in_month
        projected_savings = total_income - projected_expenses

        if projected_savings < 0:
            status = "⚠️ You may overspend before the end of the month."
        elif projected_savings < total_income * 0.2:
            status = "⚠️ Your savings may be low this month."
        else:
            status = "✅ You are on track for healthy savings."

    # Return floats (do NOT format here)
    return {
        "projected_expenses": projected_expenses,
        "projected_savings": projected_savings,
        "status": status
    }