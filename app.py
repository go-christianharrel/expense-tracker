from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")

CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Housing",
    "Entertainment",
    "Health",
    "Shopping",
    "Utilities",
    "Other",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            monthly_limit REAL NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


# ── Expenses API ───────────────────────────────────────────────────────────────

@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    month = request.args.get("month")  # YYYY-MM
    conn = get_db()
    if month:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date LIKE ? ORDER BY date DESC",
            (f"{month}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses ORDER BY date DESC LIMIT 200"
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.json
    if not data or not data.get("amount") or not data.get("category"):
        return jsonify({"error": "amount and category are required"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (
            float(data["amount"]),
            data["category"],
            data.get("description", ""),
            data.get("date", datetime.today().strftime("%Y-%m-%d")),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": expense_id})


# ── Budgets API ────────────────────────────────────────────────────────────────

@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    conn = get_db()
    rows = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/budgets", methods=["POST"])
def set_budget():
    data = request.json
    if not data or not data.get("category") or data.get("monthly_limit") is None:
        return jsonify({"error": "category and monthly_limit are required"}), 400

    conn = get_db()
    conn.execute(
        """INSERT INTO budgets (category, monthly_limit)
           VALUES (?, ?)
           ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit""",
        (data["category"], float(data["monthly_limit"])),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM budgets WHERE category = ?", (data["category"],)
    ).fetchone()
    conn.close()
    return jsonify(dict(row)), 200


@app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    conn = get_db()
    conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": budget_id})


# ── Summary API ────────────────────────────────────────────────────────────────

@app.route("/api/summary", methods=["GET"])
def get_summary():
    month = request.args.get("month", datetime.today().strftime("%Y-%m"))
    conn = get_db()

    spending = conn.execute(
        """SELECT category, SUM(amount) as total
           FROM expenses
           WHERE date LIKE ?
           GROUP BY category""",
        (f"{month}%",),
    ).fetchall()

    budgets = conn.execute("SELECT * FROM budgets").fetchall()
    conn.close()

    spending_map = {r["category"]: r["total"] for r in spending}
    budget_map = {r["category"]: r["monthly_limit"] for r in budgets}

    all_cats = set(spending_map.keys()) | set(budget_map.keys())
    result = []
    for cat in sorted(all_cats):
        result.append({
            "category": cat,
            "spent": spending_map.get(cat, 0),
            "budget": budget_map.get(cat),
        })

    total_spent = sum(spending_map.values()) if spending_map else 0
    return jsonify({"month": month, "total_spent": total_spent, "categories": result})


if __name__ == "__main__":
    init_db()
    print("\n  Expense Tracker running at http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
