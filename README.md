# Expense Tracker

A local web app to track your expenses and monthly budgets.

## Setup (one time)

1. Make sure Python 3 is installed on your computer.
2. Open Terminal and navigate to this folder:
   ```
   cd /path/to/expense-tracker
   ```
3. Install the one dependency:
   ```
   pip3 install flask
   ```

## Running the app

```
python3 app.py
```

Then open your browser and go to: **http://127.0.0.1:5000**

Your data is stored locally in `expenses.db` (created automatically).

## Features

- **Dashboard** — monthly spending summary with progress bars vs. your budgets
- **Expenses** — add expenses by amount, category, date & description; delete any entry
- **Budgets** — set monthly spending limits per category; see color-coded warnings when you're close or over

## Categories

Food & Dining · Transport · Housing · Entertainment · Health · Shopping · Utilities · Other
