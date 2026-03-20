"""
🧪 TEST PLANNER AGENT - End-to-end planner validation

What this test does:
1) Creates realistic synthetic student + transactions
2) Runs AnalyzerAgent first
3) Feeds analyzer output into PlannerAgent
4) Prints the final planning result in a readable way

Run:
    python -m agents.test_planner
"""

from __future__ import annotations

from datetime import date, timedelta
import random
import uuid
from typing import List

from agents.analyzer import create_analyzer
from agents.planner import create_planner
from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def generate_id() -> str:
    """Generate a short random ID for test objects."""
    return str(uuid.uuid4())[:8]


def create_test_student() -> Student:
    """
    Create a test student using the Student schema fields
    you shared earlier.
    """
    return Student(
        student_id="STU001",
        name="Test Student",
        age=22,
        status="student",
        currency="USD",
        monthly_income=2000.0,
        income_frequency="monthly",
        risk_profile="moderate",
        preferred_categories=["groceries", "coffee", "streaming", "amazon"],
        fixed_monthly_expenses={
            "rent": 700.0,
            "phone": 60.0,
            "internet": 40.0,
            "insurance": 100.0,
        },
    )


def create_test_transactions() -> List[Transaction]:
    """
    Create ~90 days of realistic transactions.

    Mix includes:
    - frequent coffee
    - weekly groceries
    - monthly subscriptions
    - monthly payroll
    - occasional weekend entertainment
    """
    random.seed(42)  # Make test repeatable
    transactions: List[Transaction] = []
    today = date.today()

    # 1) Daily-ish coffee
    for i in range(90):
        if random.random() > 0.72:
            continue
        transactions.append(
            Transaction(
                transaction_id=generate_id(),
                student_id="STU001",
                amount=4.50,
                transaction_type=TransactionType.EXPENSE,
                date=today - timedelta(days=i),
                description="Starbucks coffee",
                merchant="Starbucks",
                category="coffee",
                payment_method="credit_card",
                source="manual",
                confidence="high",
            )
        )

    # 2) Weekly groceries
    for i in range(0, 90, 7):
        transactions.append(
            Transaction(
                transaction_id=generate_id(),
                student_id="STU001",
                amount=round(random.uniform(45, 65), 2),
                transaction_type=TransactionType.EXPENSE,
                date=today - timedelta(days=i),
                description="Weekly groceries",
                merchant="Walmart",
                category="groceries",
                payment_method="debit_card",
                source="manual",
                confidence="high",
            )
        )

    # 3) Monthly subscriptions
    for months in range(3):
        for service, amount, category in [
            ("Netflix", 15.99, "streaming"),
            ("Spotify", 9.99, "streaming"),
            ("Amazon Prime", 14.99, "amazon"),
        ]:
            transactions.append(
                Transaction(
                    transaction_id=generate_id(),
                    student_id="STU001",
                    amount=amount,
                    transaction_type=TransactionType.EXPENSE,
                    date=today - timedelta(days=(months * 30) + random.randint(1, 4)),
                    description=service,
                    merchant=service,
                    category=category,
                    payment_method="credit_card",
                    source="manual",
                    confidence="high",
                    is_subscription=True,
                )
            )

    # 4) Monthly income
    for months in range(3):
        transactions.append(
            Transaction(
                transaction_id=generate_id(),
                student_id="STU001",
                amount=2000.0,
                transaction_type=TransactionType.INCOME,
                date=today - timedelta(days=(months * 30) + 5),
                description="Payroll direct deposit",
                merchant="Employer",
                category="salary",
                payment_method="bank_transfer",
                source="pdf",
                confidence="high",
            )
        )

    # 5) Weekend entertainment spikes
    for i in range(8):
        # Create weekend dates
        d = today - timedelta(days=(i * 10 + 1))
        # Shift to Saturday if needed
        while d.weekday() != 5:
            d = d - timedelta(days=1)

        transactions.append(
            Transaction(
                transaction_id=generate_id(),
                student_id="STU001",
                amount=round(random.uniform(35, 90), 2),
                transaction_type=TransactionType.EXPENSE,
                date=d,
                description="Weekend entertainment",
                merchant="AMC Theatres",
                category="movies",
                payment_method="credit_card",
                source="manual",
                confidence="high",
            )
        )

    return transactions


def create_test_budget() -> Budget:
    """
    Optional existing budget to compare against planner output.
    """
    start = date.today().replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    return Budget(
        budget_id="BUD001",
        student_id="STU001",
        name="Existing Monthly Budget",
        period=BudgetPeriod.MONTHLY,
        start_date=start,
        end_date=end,
        categories=[
            BudgetCategory(category="groceries", limit=500),
            BudgetCategory(category="coffee", limit=100),
            BudgetCategory(category="streaming", limit=40),
            BudgetCategory(category="amazon", limit=60),
            BudgetCategory(category="movies", limit=80),
        ],
        savings_goals=150,
        alert_threshold=0.8,
        notes="Manually created test budget",
    )


def create_test_goal() -> Goal:
    """
    Optional existing goal. Planner should usually avoid creating
    extra default goals if one already exists.
    """
    return Goal(
        goal_id="GOAL001",
        student_id="STU001",
        name="Emergency Fund",
        category=GoalCategory.EMERGENCY_FUND,
        target_amount=1000,
        current_amount=250,
        recurring_type=RecurringType.MONTHLY,
        recurring_amount=100,
        priority=GoalPriority.HIGH,
        notes="Test goal",
    )


# ------------------------------------------------------------
# Pretty printers
# ------------------------------------------------------------

def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def print_subheader(title: str):
    print("\n" + "-" * 50)
    print(f"📌 {title}")
    print("-" * 50)


def print_baseline(plan: dict):
    baseline = plan["baseline"]
    print_subheader("BASELINE")
    print(f"Monthly income:              ${baseline['monthly_income']:,.2f}")
    print(f"Fixed monthly expenses:     ${baseline['fixed_monthly_expenses']:,.2f}")
    print(f"Variable est. monthly:      ${baseline['variable_spend_est_monthly']:,.2f}")
    print(f"Total est. monthly spend:   ${baseline['total_spend_est_monthly']:,.2f}")
    print(f"Disposable est. monthly:    ${baseline['disposable_est_monthly']:,.2f}")
    print(f"Window days used:           {baseline['window_days_used']}")


def print_budget(plan: dict):
    print_subheader("RECOMMENDED BUDGET")

    budget = plan.get("recommended_budget")
    rationale = plan.get("budget_rationale", {})

    if not budget:
        print("No budget recommended.")
        return

    print(f"Budget name:   {budget['name']}")
    print(f"Period:        {budget['period']}")
    print(f"Date range:    {budget['start_date']} to {budget['end_date']}")
    print(f"Alert level:   {budget['alert_threshold'] * 100:.0f}%")
    print()

    total_limit = 0.0
    for cat in budget["categories"]:
        print(f"  • {cat['category']:<15}  limit = ${cat['limit']:>7.2f}")
        total_limit += cat["limit"]

    print(f"\nTotal variable budget limit: ${total_limit:,.2f}")

    if rationale:
        print("\nRationale:")
        for k, v in rationale.items():
            if k == "nudges" and isinstance(v, list):
                print("  nudges:")
                for item in v:
                    print(f"    - {item}")
            else:
                print(f"  {k}: {v}")


def print_savings(plan: dict):
    print_subheader("SAVINGS PLAN")
    s = plan["recommended_savings"]
    print(f"Target monthly savings:  ${s['target_monthly_savings']:,.2f}")
    print(f"Strategy:                {s['strategy']}")
    print(f"Rationale:               {s['rationale']}")


def print_goals(plan: dict):
    print_subheader("SUGGESTED GOALS")
    goals = plan.get("suggested_goals", [])
    if not goals:
        print("No new goals suggested.")
        return

    for g in goals:
        print(f"  • {g['name']}")
        print(f"      target_amount:   ${g['target_amount']:,.2f}")
        print(f"      recurring_type:  {g['recurring_type']}")
        print(f"      recurring_amount:{g.get('recurring_amount')}")
        print(f"      priority:        {g['priority']}")
        print(f"      notes:           {g['notes']}")


def print_actions(plan: dict):
    print_subheader("ACTION PLAN")
    actions = plan.get("action_plan", [])
    if not actions:
        print("No actions generated.")
        return

    for idx, a in enumerate(actions, start=1):
        print(f"{idx}. [{a['priority'].upper()}] {a['title']}")
        print(f"   {a['description']}")
        print(f"   Impact/month: ${a['impact_monthly_usd']:,.2f} | Confidence: {a['confidence']}")
        if a.get("tags"):
            print(f"   Tags: {', '.join(a['tags'])}")
        print()


def print_projections(plan: dict):
    print_subheader("PROJECTIONS")
    p = plan.get("projections", {})
    print(f"Estimated monthly improvement:  ${p.get('estimated_monthly_improvement', 0):,.2f}")
    print(f"Estimated 3-month improvement:  ${p.get('estimated_3_month_improvement', 0):,.2f}")
    print(f"Estimated 6-month improvement:  ${p.get('estimated_6_month_improvement', 0):,.2f}")
    print(f"Note: {p.get('note', '')}")


def print_warnings(plan: dict):
    print_subheader("WARNINGS")
    warnings = plan.get("warnings", [])
    if not warnings:
        print("No warnings.")
        return
    for w in warnings:
        print(f"  ⚠️ {w}")


# ------------------------------------------------------------
# Test Scenarios
# ------------------------------------------------------------

def test_planner_basic():
    """
    Standard end-to-end flow:
    analyzer -> planner
    """
    print_header("TEST 1: BASIC PLANNER FLOW")

    student = create_test_student()
    transactions = create_test_transactions()

    analyzer = create_analyzer()
    planner = create_planner()

    analysis = analyzer.analyze_student(student, transactions, lookback_days=90)
    plan = planner.build_plan(
        student=student,
        transactions=transactions,
        analysis=analysis,
        existing_budget=None,
        goals=[],
        lookback_days=60,
    )

    print(f"\nTransactions analyzed: {len(transactions)}")
    print_baseline(plan)
    print_savings(plan)
    print_budget(plan)
    print_goals(plan)
    print_actions(plan)
    print_projections(plan)
    print_warnings(plan)


def test_planner_with_existing_budget():
    """
    Planner with an existing budget supplied.
    """
    print_header("TEST 2: WITH EXISTING BUDGET")

    student = create_test_student()
    transactions = create_test_transactions()
    existing_budget = create_test_budget()

    analyzer = create_analyzer()
    planner = create_planner()

    analysis = analyzer.analyze_student(student, transactions, budget=existing_budget, lookback_days=90)
    plan = planner.build_plan(
        student=student,
        transactions=transactions,
        analysis=analysis,
        existing_budget=existing_budget,
        goals=[],
        lookback_days=60,
    )

    print_baseline(plan)
    print_savings(plan)
    print_budget(plan)
    print_actions(plan)
    print_projections(plan)


def test_planner_with_existing_goal():
    """
    If a goal already exists, planner should usually not create
    a new default emergency fund suggestion.
    """
    print_header("TEST 3: WITH EXISTING GOAL")

    student = create_test_student()
    transactions = create_test_transactions()
    existing_goal = create_test_goal()

    analyzer = create_analyzer()
    planner = create_planner()

    analysis = analyzer.analyze_student(student, transactions, lookback_days=90)
    plan = planner.build_plan(
        student=student,
        transactions=transactions,
        analysis=analysis,
        existing_budget=None,
        goals=[existing_goal],
        lookback_days=60,
    )

    print_savings(plan)
    print_goals(plan)
    print_actions(plan)


def test_planner_low_income_stress():
    """
    Stress scenario:
    - Lower income
    - Same expenses
    This tests warnings and planning under pressure.
    """
    print_header("TEST 4: LOW INCOME / STRESS CASE")

    student = create_test_student()
    student.monthly_income = 950.0  # lower than fixed expenses in this case

    transactions = create_test_transactions()

    analyzer = create_analyzer()
    planner = create_planner()

    analysis = analyzer.analyze_student(student, transactions, lookback_days=90)
    plan = planner.build_plan(
        student=student,
        transactions=transactions,
        analysis=analysis,
        existing_budget=None,
        goals=[],
        lookback_days=60,
    )

    print_baseline(plan)
    print_savings(plan)
    print_actions(plan)
    print_warnings(plan)
    print_projections(plan)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":
    test_planner_basic()
    test_planner_with_existing_budget()
    test_planner_with_existing_goal()
    test_planner_low_income_stress()

    print("\n" + "=" * 70)
    print("✅ PLANNER TESTS COMPLETE")
    print("=" * 70)