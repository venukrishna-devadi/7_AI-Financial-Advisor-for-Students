"""
🧪 TEST FINANCIAL RUNNER - End-to-end tests for runners/financial_runner.py

What this test validates
------------------------
1. run_from_transactions() works with full pipeline
2. run_from_vision() works with vision-bridged intake
3. add_transaction_and_rerun() appends history correctly
4. add_vision_and_rerun() merges extracted transactions correctly
5. quick_health_check() returns compact summary
6. run_safe() never crashes and always returns dict
7. timeout wrapper returns clean failure shape

Run
---
python -m runners.test_financial_runner
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import uuid
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from runners.financial_runner import create_financial_runner

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType


# =========================================================
# TEST DATA HELPERS
# =========================================================

def generate_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_test_student() -> Student:
    """Create a realistic student profile for runner tests."""
    return Student(
        student_id="STU001",
        name="Alex Johnson",
        age=24,
        status="student",
        currency="USD",
        monthly_income=2800.0,
        income_frequency="monthly",
        risk_profile="moderate",
        preferred_categories=["groceries", "coffee", "dining_out", "shopping", "transport", "streaming"],
        fixed_monthly_expenses={
            "rent": 1200.0,
            "utilities": 150.0,
            "internet": 60.0,
            "phone": 50.0,
        },
    )


def create_test_budget(student_id: str = "STU001") -> Budget:
    """Create a current-month budget."""
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
        notes="Runner test budget",
    )


def create_test_goals(student_id: str = "STU001") -> List[Goal]:
    """Create sample goals."""
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
            notes="Build a stronger emergency cushion",
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
            notes="Upgrade for next semester",
        ),
    ]


def create_test_transactions(student_id: str = "STU001") -> List[Transaction]:
    """Create a reasonable transaction history."""
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


def create_manual_transaction(student_id: str = "STU001") -> Transaction:
    """Create one extra manual transaction for add-and-rerun tests."""
    return Transaction(
        transaction_id=generate_id("txn"),
        student_id=student_id,
        amount=12.75,
        transaction_type=TransactionType.EXPENSE,
        date=date.today(),
        description="Local Cafe coffee",
        merchant="Local Cafe",
        category="coffee",
        payment_method="debit_card",
        source="manual",
        confidence="high",
        raw_data={},
        notes="added manually",
        tags=[],
    )


def create_sample_vision_output() -> Dict[str, Any]:
    """Sample successful vision output for bridge testing."""
    today_str = date.today().strftime("%Y-%m-%d")

    return {
        "success": True,
        "data": {
            "document_type": "receipt",
            "merchant": "STARBUCKS COFFEE",
            "date": today_str,
            "currency": "USD",
            "confidence": "high",
            "totals": {
                "subtotal": "8.75",
                "tax": "0.74",
                "total": "9.49",
            },
            "possible_transactions": [
                {
                    "date": today_str,
                    "description": "Caffe Latte",
                    "amount": "$4.95",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
                {
                    "date": today_str,
                    "description": "Blueberry Muffin",
                    "amount": "$4.54",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
            ],
        },
    }


# =========================================================
# PRINT HELPERS
# =========================================================

def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)


def print_runner_result(result):
    """Pretty print a FinancialRunnerResult."""
    print(f"\n📌 Success: {result.success}")
    print(f"📌 Pipeline status: {result.pipeline_status}")
    print(f"📌 Partial results: {result.has_partial_results}")
    print(f"📌 Student ID: {result.student_id}")
    print(f"📌 Transactions: {len(result.transactions)}")
    print(f"📌 Warnings: {len(result.warnings)}")
    print(f"📌 Errors: {len(result.errors)}")
    print(f"📌 Overall health: {result.overall_health}")
    print(f"📌 Budget health: {result.budget_health}")
    print(f"📌 Budget used: {result.budget_percent_used}")
    print(f"📌 Alerts: total={result.alert_total}, critical={result.alert_critical}, warning={result.alert_warning}")
    print(f"📌 Top priorities: {len(result.top_priorities)}")
    print(f"📌 Immediate actions: {len(result.immediate_actions)}")
    print(f"📌 Execution time: {result.execution_time_seconds}")

    extraction_mode = result.extraction_result.get("mode")
    if extraction_mode:
        print(f"📌 Extraction mode: {extraction_mode}")

    if result.errors:
        print(f"📌 Error details: {result.errors}")


# =========================================================
# TESTS
# =========================================================

def test_run_from_transactions():
    print_separator("TEST 1: RUN FROM TRANSACTIONS")

    runner = create_financial_runner()
    result = runner.run_from_transactions(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
        lookback_days=90,
    )

    print_runner_result(result)

    assert result.success is True
    assert result.pipeline_status in {"completed", "completed_with_errors"}
    assert len(result.transactions) == 7
    assert isinstance(result.analysis, dict)
    assert isinstance(result.plan, dict)
    assert isinstance(result.tracking_report, dict)
    assert isinstance(result.advice_result, dict)
    assert isinstance(result.alert_result, dict)

    print("\n✅ Test 1 passed")


def test_run_from_vision():
    print_separator("TEST 2: RUN FROM VISION OUTPUT")

    runner = create_financial_runner()
    result = runner.run_from_vision(
        student=create_test_student(),
        vision_output=create_sample_vision_output(),
        budget=create_test_budget(),
        goals=create_test_goals(),
        lookback_days=90,
    )

    print_runner_result(result)
    print("extraction_result =", result.extraction_result)

    assert result.success is True
    assert result.pipeline_status in {"completed", "completed_with_errors"}
    assert len(result.transactions) >= 1
    assert result.extraction_result.get("mode") == "vision/bridge"

    print("\n✅ Test 2 passed")


def test_add_transaction_and_rerun():
    print_separator("TEST 3: ADD TRANSACTION AND RERUN")

    runner = create_financial_runner()
    existing = create_test_transactions()
    new_txn = create_manual_transaction()

    result = runner.add_transaction_and_rerun(
        student=create_test_student(),
        existing_transactions=existing,
        new_transaction=new_txn,
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    print_runner_result(result)

    assert result.success is True
    assert len(result.transactions) == len(existing) + 1

    print("\n✅ Test 3 passed")


def test_add_vision_and_rerun():
    print_separator("TEST 4: ADD VISION AND RERUN")

    runner = create_financial_runner()
    existing = create_test_transactions()
    vision_output = create_sample_vision_output()

    result = runner.add_vision_and_rerun(
        student=create_test_student(),
        existing_transactions=existing,
        vision_output=vision_output,
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    print_runner_result(result)

    assert result.success is True
    assert len(result.transactions) >= len(existing) + 1

    print("\n✅ Test 4 passed")


def test_quick_health_check():
    print_separator("TEST 5: QUICK HEALTH CHECK")

    runner = create_financial_runner()
    summary = runner.quick_health_check(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    print("\n📌 Quick summary:")
    for k, v in summary.items():
        print(f"   {k}: {v}")

    assert isinstance(summary, dict)
    assert "success" in summary
    assert "overall_health" in summary
    assert "alert_summary" in summary
    assert "top_priorities" in summary

    print("\n✅ Test 5 passed")


def test_run_safe_success():
    print_separator("TEST 6: RUN SAFE SUCCESS CASE")

    runner = create_financial_runner()
    result_dict = runner.run_safe(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    print("\n📌 run_safe result keys:")
    print(list(result_dict.keys()))

    assert isinstance(result_dict, dict)
    assert "success" in result_dict
    assert "pipeline_status" in result_dict
    assert "result" in result_dict

    print("\n✅ Test 6 passed")


def test_run_safe_invalid_input():
    print_separator("TEST 7: RUN SAFE INVALID INPUT CASE")

    runner = create_financial_runner()

    # Intentionally wrong type for vision_output
    result_dict = runner.run_safe(
        student=create_test_student(),
        vision_output="not a dict",  # invalid on purpose
    )

    print("\n📌 run_safe invalid result:")
    for k in ["success", "pipeline_status", "errors"]:
        print(f"   {k}: {result_dict.get(k)}")

    assert isinstance(result_dict, dict)
    assert result_dict["success"] is False
    assert result_dict["pipeline_status"] == "failed"
    assert len(result_dict["errors"]) > 0

    print("\n✅ Test 7 passed")


def test_timeout_path():
    print_separator("TEST 8: TIMEOUT PATH")

    runner = create_financial_runner()

    # Extremely tiny timeout to exercise timeout wrapper.
    result = runner.run(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
        timeout_seconds=0,
    )

    print_runner_result(result)

    assert result.success is False
    assert result.pipeline_status == "failed"
    assert len(result.errors) > 0

    print("\n✅ Test 8 passed")


def test_result_to_dict():
    print_separator("TEST 9: RESULT TO_DICT SHAPE")

    runner = create_financial_runner()
    result = runner.run_from_transactions(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    payload = result.to_dict()

    print("\n📌 to_dict top-level keys:")
    print(list(payload.keys()))

    assert isinstance(payload, dict)
    assert "success" in payload
    assert "result" in payload
    assert "transactions" in payload["result"]
    assert isinstance(payload["result"]["transactions"], list)

    print("\n✅ Test 9 passed")


def test_runner_stats():
    print_separator("TEST 10: RUNNER STATS")

    runner = create_financial_runner()

    _ = runner.run_from_transactions(
        student=create_test_student(),
        transactions=create_test_transactions(),
        budget=create_test_budget(),
        goals=create_test_goals(),
    )

    stats = runner.get_stats()

    print("\n📌 Runner stats:")
    for k, v in stats.items():
        print(f"   {k}: {v}")

    assert isinstance(stats, dict)
    assert stats["call_count"] >= 1
    assert stats["builder_initialized"] is True

    print("\n✅ Test 10 passed")


# =========================================================
# MAIN
# =========================================================

def run_all_tests():
    print("=" * 80)
    print("🧪🧪🧪 FINANCIAL RUNNER TEST SUITE 🧪🧪🧪")
    print("=" * 80)

    test_run_from_transactions()
    test_run_from_vision()
    test_add_transaction_and_rerun()
    test_add_vision_and_rerun()
    test_quick_health_check()
    test_run_safe_success()
    test_run_safe_invalid_input()
    test_timeout_path()
    test_result_to_dict()
    test_runner_stats()

    print("\n" + "=" * 80)
    print("✅ ALL FINANCIAL RUNNER TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()