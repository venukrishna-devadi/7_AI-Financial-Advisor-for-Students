from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from schemas.transaction import Category
from datetime import date, timedelta

# create a monthly budget
start = date.today()
end = start + timedelta(days=30)

categories = [
    BudgetCategory(category="gas", limit=100),
    BudgetCategory(category="groceries", limit=150),
    BudgetCategory(category="rent", limit=450)
]

budget = Budget(
    budget_id="032026",
    student_id="krishna",
    name="March 2026 Budget",
    period=BudgetPeriod.MONTHLY,
    start_date=start,
    end_date=end,
    is_active=True,
    savings_goals=150,
    categories=categories
)

print("✅ Budget created!")
print(budget)  # Uses __str__
print(f"Total limit: ${budget.total_limit}")
print(f"Status: {budget.status.value}")

# adding more expenses
budget.add_expense('gas', 10.50)
budget.add_expense('groceries', 20)
budget.add_expense('rent', 400)

print(f"\nAfter expenses: ${budget.total_spent} spent")
print(f"Rent status: {budget.category_status('rent')}")

# generate report
report = budget.spending_report()
print(f"\n📊 Report: {report['overall_percent']:.1f}% used")