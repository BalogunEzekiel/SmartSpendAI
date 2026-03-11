import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "smartspend.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Users table with plan type
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        plan TEXT DEFAULT 'Basic'  -- default plan is 'basic'
    )
    """)

    # Combined transactions table (expenses only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        exp_amount REAL DEFAULT 0
    )
    """)

    # Income table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        income REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


# ---------------- User Functions ---------------- #

def register_user(name, email, password, plan='Basic'):
    """Register a new user with hashed password."""
    hashed_pw = generate_password_hash(password)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (name, email, password, plan)
        VALUES (?, ?, ?, ?)
        """, (name, email, hashed_pw, plan))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # email already exists
    finally:
        conn.close()


def verify_user(email, password):
    """Verify login credentials. Returns user dict or None."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password, plan FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row[3], password):
        return {"id": row[0], "name": row[1], "email": row[2], "plan": row[4]}
    return None


def get_user_plan(user_id):
    """Return the plan type of a user by ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT plan FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def update_user_plan(user_id, plan):
    """Upgrade or change a user's plan."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))
    conn.commit()
    conn.close()


# ---------------- Transactions Functions ---------------- #

# Insert an expense record
def insert_expense(date, category, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (date, category, exp_amount)
    VALUES (?, ?, ?)
    """, (date, category, amount))
    conn.commit()
    conn.close()

# Insert an income record
def insert_income(date, category, amount):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO income (date, category, income)
    VALUES (?, ?, ?)
    """, (date, category, amount))
    conn.commit()
    conn.close()


# Get all transactions and income as unified table
def get_all_expenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all expenses
    cursor.execute("SELECT id, date, category, 0 as income, exp_amount FROM transactions")
    expenses = cursor.fetchall()

    # Fetch all incomes
    cursor.execute("SELECT id, date, category, income, 0 as exp_amount FROM income")
    incomes = cursor.fetchall()

    # Combine and sort by date
    all_records = expenses + incomes
    all_records.sort(key=lambda x: x[1], reverse=True)  # sort by date descending

    conn.close()
    return all_records


# Total expenses this month
def get_total_expenses_current_month():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.today()
    month = f"{today.month:02d}"
    year = str(today.year)
    cursor.execute("""
    SELECT SUM(exp_amount) FROM transactions
    WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
    """, (month, year))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return float(total)


# Total income this month
def get_total_income_current_month():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    today = datetime.today()
    month = f"{today.month:02d}"
    year = str(today.year)
    cursor.execute("""
    SELECT SUM(income) FROM income
    WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
    """, (month, year))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return float(total)