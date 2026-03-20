"""
🧪 TEST PLANNER DEBUG - Isolate planner.build_plan() outside the graph

Purpose
-------
This test helps debug why planner may be failing inside graph/builder.py.

It:
1. creates the same kind of student / transactions / goals / analysis used in graph tests
2. runs analyzer first
3. runs planner directly
4. prints full outputs
5. prints full traceback if planner crashes

Run
---
python -m agents.test_planner_debug
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import uuid
import traceback
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.analyzer import create_analyzer
from agents.planner import create_planner

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod


# =========================================================
# TEST DATA HELPERS
# =========================================================

def generate_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_test_student() -> Student:
    """
    Matches the structure used in your current project.
    """
    return Student(
        student_id="STU001",
        name="Alex Johnson",
        age=24,
        status="student",
        currency="USD",
        monthly_income=2800.0,
        income_frequency="monthly",
        risk_profile="moderate",
        preferred_categories=["groceries", "coffee", "dining_out", "transport", "streaming"],
        fixed_monthly_expenses={
            "rent": 1200.0,
            "utilities": 150.0,
            "internet": 60.0,
            "phone": 50.0,
        },
    )


def create_test_budget(student_id: str = "STU001") -> Budget:
    today = date.today()
    start_date = date(today.year, today.month, 1)

    if today.month == 12:
        end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    return Budget(
        budget_id=generate_id("bud"),
        student_id=student_id,
        name=f"Monthly Budget - {start_date.strftime('%B %Y')}",
        period=BudgetPeriod.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        categories=[
            BudgetCategory(category="groceries", limit=400.0),
            BudgetCategory(category="dining_out", limit=250.0),
            BudgetCategory(category="coffee", limit=80.0),
            BudgetCategory(category="shopping", limit=200.0),
            BudgetCategory(category="transport", limit=120.0),
            BudgetCategory(category="streaming", limit=40.0),
        ],
        savings_goal=400.0,
        alert_threshold=0.8,
        notes="Debug budget for planner test",
    )


def create_test_goals(student_id: str = "STU001") -> List[Goal]:
    today = date.today()

    return [
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="Emergency Fund",
            category=GoalCategory.EMERGENCY_FUND,
            target_amount=8000.0,
            current_amount=2500.0,
            target_date=today + timedelta(days=365),
            priority=GoalPriority.HIGH,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=200.0,
            notes="Build a stronger financial cushion",
        ),
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="New Laptop",
            category=GoalCategory.MAJOR_PURCHASE,
            target_amount=1800.0,
            current_amount=600.0,
            target_date=today + timedelta(days=180),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=100.0,
            notes="Upgrade before next semester",
        ),
    ]


def create_test_transactions(student_id: str = "STU001") -> List[Transaction]:
    today = date.today()

    return [
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=2800.0,
            transaction_type=TransactionType.INCOME,
            date=today - timedelta(days=8),
            description="PAYROLL DIRECT DEPOSIT",
            merchant="University Payroll",
            category="salary",
            payment_method="direct_deposit",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=95.50,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=2),
            description="Walmart groceries",
            merchant="Walmart",
            category="groceries",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=18.25,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=1),
            description="Starbucks coffee",
            merchant="Starbucks",
            category="coffee",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=42.10,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=6),
            description="Chipotle dinner",
            merchant="Chipotle",
            category="dining_out",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=15.99,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=10),
            description="Netflix subscription",
            merchant="Netflix",
            category="streaming",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=26.40,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=4),
            description="Uber trip",
            merchant="Uber",
            category="uber",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
        Transaction(
            transaction_id=generate_id("txn"),
            student_id=student_id,
            amount=120.00,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=12),
            description="Target household shopping",
            merchant="Target",
            category="shopping",
            payment_method="credit_card",
            source="manual",
            confidence="high",
            raw_data={},
            notes="",
            tags=[],
        ),
    ]


# =========================================================
# DEBUG HELPERS
# =========================================================

def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"🔎 {title}")
    print("=" * 80)


def safe_print_dict(d, title: str):
    print(f"\n📌 {title}")
    if not isinstance(d, dict):
        print(f"   Not a dict: {type(d)}")
        print(f"   Value: {d}")
        return

    for k, v in d.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            print(f"   {k}: {v}")
        elif isinstance(v, list):
            print(f"   {k}: list[{len(v)}]")
        elif isinstance(v, dict):
            print(f"   {k}: dict[{len(v)} keys]")
        else:
            print(f"   {k}: {type(v).__name__}")


# =========================================================
# MAIN DEBUG TEST
# =========================================================

def test_planner_direct():
    print_section("PLANNER DIRECT DEBUG TEST")

    student = create_test_student()
    budget = create_test_budget()
    goals = create_test_goals()
    transactions = create_test_transactions()

    analyzer = create_analyzer()
    planner = create_planner()

    print("\n✅ Input objects created")
    print(f"   student: {student.student_id}")
    print(f"   transactions: {len(transactions)}")
    print(f"   goals: {len(goals)}")
    print(f"   budget categories: {len(budget.categories)}")

    # -------------------------
    # Step 1: Run analyzer first
    # -------------------------
    print_section("RUN ANALYZER FIRST")

    try:
        analysis = analyzer.analyze_student(
            student=student,
            transactions=transactions,
            budget=budget,
            lookback_days=90,
        )
        print("✅ Analyzer succeeded")
        safe_print_dict(analysis, "Analysis top-level keys")
        safe_print_dict(analysis.get("summary", {}), "Analysis summary")
    except Exception as e:
        print("❌ Analyzer failed")
        traceback.print_exc()
        return

    # -------------------------
    # Step 2: Run planner
    # -------------------------
    print_section("RUN PLANNER DIRECTLY")

    try:
        plan = planner.build_plan(
            student=student,
            transactions=transactions,
            analysis=analysis,
            goals=goals,
        )
        print("✅ Planner succeeded")
        safe_print_dict(plan, "Plan top-level keys")

        if isinstance(plan, dict):
            safe_print_dict(plan.get("baseline", {}), "Plan baseline")
            safe_print_dict(plan.get("savings_plan", {}), "Plan savings_plan")

            action_plan = plan.get("action_plan", [])
            print(f"\n📌 action_plan count: {len(action_plan) if isinstance(action_plan, list) else 'not a list'}")

            suggested_goals = plan.get("suggested_goals", [])
            print(f"📌 suggested_goals count: {len(suggested_goals) if isinstance(suggested_goals, list) else 'not a list'}")

            warnings = plan.get("warnings", [])
            print(f"📌 warnings count: {len(warnings) if isinstance(warnings, list) else 'not a list'}")

    except Exception as e:
        print("❌ Planner failed with exception")
        print(f"\nException type: {type(e).__name__}")
        print(f"Exception message: {e}\n")
        traceback.print_exc()

        # Extra debug context
        print_section("DEBUG CONTEXT SNAPSHOT")
        print(f"student type: {type(student).__name__}")
        print(f"transactions type: {type(transactions).__name__}, count={len(transactions)}")
        print(f"analysis type: {type(analysis).__name__}")
        print(f"goals type: {type(goals).__name__}, count={len(goals)}")

        if isinstance(analysis, dict):
            print(f"analysis keys: {list(analysis.keys())}")
            print(f"summary keys: {list(analysis.get('summary', {}).keys()) if isinstance(analysis.get('summary'), dict) else 'summary not dict'}")


if __name__ == "__main__":
    test_planner_direct()