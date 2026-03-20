"""
🧪 TEST BUILDER - End-to-end tests for graph/builder.py

What this test does
-------------------
This file tests the full orchestration flow of the financial graph.

It validates:
1. builder can run with prebuilt transactions
2. builder can run with vision output that needs bridging
3. builder can handle empty transactions gracefully
4. builder can fail cleanly when required state is missing

How to run
----------
python -m graph.test_builder
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import uuid
from typing import List, Dict, Any

# Add project root to path when running as module/script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from graph.builder import create_financial_graph_builder

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType


# =========================================================
# TEST DATA HELPERS
# =========================================================

def generate_id(prefix: str = "id") -> str:
    """Generate a short test ID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_test_student() -> Student:
    """Create a realistic student profile."""
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
        notes="Test budget for builder graph",
    )


def create_test_goals(student_id: str = "STU001") -> List[Goal]:
    """Create sample savings goals."""
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
    """Create a realistic set of transactions for the last ~30 days."""
    today = date.today()

    txns = [
        # income
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

        # expenses
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

    return txns


def create_sample_vision_output() -> Dict[str, Any]:
    """Sample successful vision output for bridge testing."""
    today = date.today().strftime("%Y-%m-%d")

    return {
        "success": True,
        "data": {
            "document_type": "receipt",
            "merchant": "STARBUCKS COFFEE",
            "date": today,
            "currency": "USD",
            "confidence": "high",
            "totals": {
                "subtotal": "8.75",
                "tax": "0.74",
                "total": "9.49",
            },
            "possible_transactions": [
                {
                    "date": today,
                    "description": "Caffe Latte",
                    "amount": "$4.95",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
                {
                    "date": today,
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
    """Pretty section separator."""
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)


def print_result_summary(result: Dict[str, Any]):
    """Print a compact summary of graph output."""
    print(f"\n📌 Pipeline status: {result.get('pipeline_status', 'unknown')}")
    print(f"📌 Warnings: {len(result.get('warnings', []))}")
    print(result.get('errors', []))
    print(f"📌 Errors: {len(result.get('errors', []))}")

    transactions = result.get("transactions", [])
    print(f"📌 Transactions in state: {len(transactions)}")

    if result.get("extraction_result"):
        extraction = result["extraction_result"]
        print(f"📌 Extraction mode: {extraction.get('mode', 'vision/bridge')}")
        print(f"📌 Extraction transaction_count: {extraction.get('transaction_count', 'N/A')}")

    print(f"📌 Analysis present: {'analysis' in result}")
    print(f"📌 Plan present: {'plan' in result}")
    print(f"📌 Tracking present: {'tracking_report' in result}")
    print(f"📌 Advice present: {'advice_result' in result}")
    print(f"📌 Alerts present: {'alert_result' in result}")

    if result.get("analysis"):
        summary = result["analysis"].get("summary", {})
        print(
            f"   Analysis summary -> spent: ${summary.get('amount_spent', 0):,.2f}, "
            f"earned: ${summary.get('amount_earned', 0):,.2f}"
        )

    if result.get("plan"):
        baseline = result["plan"].get("baseline", {})
        print(
            f"   Plan baseline -> monthly income: ${baseline.get('monthly_income', 0):,.2f}, "
            f"est total spend: ${baseline.get('total_spend_est_monthly', 0):,.2f}"
        )

    if result.get("tracking_report"):
        budget_status = result["tracking_report"].get("budget_status", {})
        print(
            f"   Tracking -> status: {budget_status.get('status', 'N/A')}, "
            f"percent_used: {budget_status.get('percent_used', 0)}"
        )

    if result.get("advice_result"):
        advice = result["advice_result"].get("advice", {})
        print(f"   Advice health -> {advice.get('overall_financial_health', 'N/A')}")

    if result.get("alert_result"):
        summary = result["alert_result"].get("summary", {})
        print(
            f"   Alerts -> total: {summary.get('total_alerts', 0)}, "
            f"critical: {summary.get('critical_count', 0)}, "
            f"warning: {summary.get('warning_count', 0)}, "
            f"info: {summary.get('info_count', 0)}"
        )
    if result.get("errors"):
        print("Errors:", result["errors"])


# =========================================================
# TEST CASES
# =========================================================

def test_builder_with_prebuilt_transactions():
    """Test full graph flow with already-created Transaction objects."""
    print_separator("TEST 1: PREBUILT TRANSACTIONS")

    builder = create_financial_graph_builder()

    result = builder.run(
        {
            "student": create_test_student(),
            "transactions": create_test_transactions(),
            "budget": create_test_budget(),
            "goals": create_test_goals(),
            "lookback_days": 90,
        }
    )

    print_result_summary(result)

    assert result["pipeline_status"] in {"completed", "completed_with_errors"}
    assert len(result.get("transactions", [])) > 0
    assert "analysis" in result
    assert "plan" in result
    assert "tracking_report" in result
    assert "advice_result" in result
    assert "alert_result" in result

    print("\n✅ Test 1 passed")


def test_builder_with_vision_output():
    """Test graph flow where intake must bridge vision output into transactions."""
    print_separator("TEST 2: VISION OUTPUT BRIDGING")

    builder = create_financial_graph_builder()

    result = builder.run(
        {
            "student": create_test_student(),
            "vision_output": create_sample_vision_output(),
            "budget": create_test_budget(),
            "goals": create_test_goals(),
            "lookback_days": 90,
        }
    )

    print_result_summary(result)

    assert result["pipeline_status"] in {"completed", "completed_with_errors"}
    assert len(result.get("transactions", [])) >= 1
    assert "extraction_result" in result
    assert "analysis" in result
    assert "plan" in result
    assert "tracking_report" in result
    assert "advice_result" in result
    assert "alert_result" in result

    print("\n✅ Test 2 passed")


def test_builder_with_empty_transactions():
    """Test graph behavior when no transactions are provided."""
    print_separator("TEST 3: EMPTY TRANSACTION HISTORY")

    builder = create_financial_graph_builder()

    result = builder.run(
        {
            "student": create_test_student(),
            "transactions": [],
            "budget": create_test_budget(),
            "goals": create_test_goals(),
        }
    )

    print_result_summary(result)

    # With conditional routing after intake, this should finalize early.
    assert result["pipeline_status"] in {"completed", "completed_with_errors"}
    assert len(result.get("transactions", [])) == 0
    assert "analysis" not in result or result.get("analysis") is None

    print("\n✅ Test 3 passed")


def test_builder_missing_student():
    """Test validation failure when required student input is missing."""
    print_separator("TEST 4: MISSING REQUIRED STUDENT")

    builder = create_financial_graph_builder()

    result = builder.run(
        {
            "transactions": create_test_transactions(),
            "budget": create_test_budget(),
            "goals": create_test_goals(),
        }
    )

    print_result_summary(result)

    assert result["pipeline_status"] == "failed"
    assert len(result.get("errors", [])) > 0

    print("\n✅ Test 4 passed")


def test_builder_invalid_vision_output_type():
    """Test validation when vision_output is not a dict."""
    print_separator("TEST 5: INVALID VISION OUTPUT TYPE")

    builder = create_financial_graph_builder()

    result = builder.run(
        {
            "student": create_test_student(),
            "vision_output": "this should be a dict, not a string",
            "budget": create_test_budget(),
            "goals": create_test_goals(),
        }
    )

    print_result_summary(result)

    assert result["pipeline_status"] == "failed"
    assert any("vision_output must be a dictionary" in err for err in result.get("errors", []))

    print("\n✅ Test 5 passed")


# =========================================================
# MAIN RUNNER
# =========================================================

def run_all_tests():
    """Run all builder tests."""
    print("=" * 80)
    print("🧪🧪🧪 FINANCIAL GRAPH BUILDER TEST SUITE 🧪🧪🧪")
    print("=" * 80)

    test_builder_with_prebuilt_transactions()
    test_builder_with_vision_output()
    test_builder_with_empty_transactions()
    test_builder_missing_student()
    test_builder_invalid_vision_output_type()

    print("\n" + "=" * 80)
    print("✅ ALL BUILDER TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()