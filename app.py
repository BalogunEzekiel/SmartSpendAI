from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import (
    init_db, insert_expense, insert_income,
    get_all_expenses, get_total_income_current_month,
    get_total_expenses_current_month,
    register_user, verify_user, get_user_plan
)
from model import smart_advice, predict_month_end
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "smartspend_secret_key"

# Initialize database
init_db()

# ----------------- HOME ----------------- #
@app.route('/')
def home():
    """Homepage for all users, with personalized greeting if logged in."""
    user_name = session.get('user_name')
    user_plan = session.get('user_plan', 'Basic')
    return render_template("index.html", user_name=user_name, user_plan=user_plan)

# ----------------- REGISTER ----------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        success = register_user(name, email, password)
        if success:
            return redirect(url_for('login'))
        else:
            return render_template("register.html", error="Email already exists.")

    return render_template("register.html")

# ----------------- LOGIN ----------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        user = verify_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_plan'] = user['plan']
            # Redirect to homepage with personalized greeting
            return redirect(url_for('home'))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ----------------- LOGOUT ----------------- #
@app.route('/logout')
def logout():
    """Log out the current user and redirect to homepage."""
    session.clear()
    return redirect(url_for('home'))

# ----------------- PREDICT ----------------- #
@app.route('/predict', methods=['POST'])
def predict():
    entry_date = request.form.get('entry_date', '').strip()
    if not entry_date:
        entry_date = datetime.today().strftime('%Y-%m-%d')

    # Income
    monthly_income = request.form.get('monthly_income', '').strip()
    daily_income = request.form.get('daily_income', '').strip()
    if monthly_income:
        try:
            insert_income(entry_date, "monthly", float(monthly_income))
        except ValueError:
            pass
    if daily_income:
        try:
            insert_income(entry_date, "daily", float(daily_income))
        except ValueError:
            pass

    # Expenses (dynamic)
    for key in request.form:
        if key.startswith('category_'):
            index = key.split('_')[1]
            category = request.form.get(f'category_{index}', '').strip()
            amount = request.form.get(f'amount_{index}', '').strip()
            if category and amount:
                try:
                    insert_expense(entry_date, category, float(amount))
                except ValueError:
                    pass

    total_income = get_total_income_current_month()
    total_expenses = get_total_expenses_current_month()
    savings = total_income - total_expenses
    advice = smart_advice(total_income, total_expenses)
    forecast = predict_month_end(total_income, total_expenses)
    projected_expense = forecast["projected_expenses"]
    projected_savings = forecast["projected_savings"]

    # Pass user info for personalized greeting
    user_name = session.get('user_name')
    user_plan = session.get('user_plan', 'Basic')

    return render_template(
        "index.html",
        user_name=user_name,
        user_plan=user_plan,
        prediction=advice,
        total="{:,.0f}".format(total_expenses),
        savings="{:,.0f}".format(savings),
        projected_expense="{:,.0f}".format(projected_expense),
        projected_savings="{:,.0f}".format(projected_savings)
    )

# ----------------- DASHBOARD ----------------- #
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    data = get_all_expenses()
    total_income = get_total_income_current_month()
    total_expenses = get_total_expenses_current_month()
    savings = total_income - total_expenses

    total_income_str = "{:,.0f}".format(total_income)
    total_expenses_str = "{:,.0f}".format(total_expenses)
    savings_str = "{:,.0f}".format(savings)

    # Category totals
    category_totals = defaultdict(float)
    for row in data:
        if len(row) == 5:
            _, _, category, _, exp_amount = row
            if exp_amount and exp_amount > 0:
                category_totals[category] += float(exp_amount)

    # Optionally display upgrade message
    user_plan = session.get('user_plan', 'Basic')
    show_upgrade_msg = user_plan == 'Basic'

    return render_template(
        "dashboard.html",
        data=data,
        total_income=total_income_str,
        total_expenses=total_expenses_str,
        savings=savings_str,
        category_totals=dict(category_totals),
        show_upgrade_msg=show_upgrade_msg
    )

# ----------------- CATEGORY DATA ----------------- #
@app.route('/category_data')
def category_data():
    data = get_all_expenses()
    totals = defaultdict(float)
    for row in data:
        if len(row) == 5:
            _, _, category, _, amount = row
        else:
            _, _, category, amount = row
        totals[category] += float(amount)
    return jsonify({
        "categories": list(totals.keys()),
        "amounts": list(totals.values())
    })

if __name__ == "__main__":
    app.run(debug=True)