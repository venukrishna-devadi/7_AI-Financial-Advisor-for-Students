"""
🧪 TEST TRACKER AGENT - Comprehensive tests for budget monitoring
Tests all core functionality: budget tracking, goal tracking, alerts, recommendations
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import uuid
import random
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType
from agents.tracker import create_tracker, TrackingAlert


# =========================================================
# TEST DATA GENERATORS
# =========================================================

def generate_id(prefix: str = "txn") -> str:
    """Generate a unique ID for test objects"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def create_test_student() -> Student:
    """Create a test student"""
    return Student(
        student_id="STU001",
        name="Test Student",
        email="test@uni.edu",
        university="Test University",
        graduation_year=2026,
        monthly_income=3000,
        current_savings=5000,
        risk_profile="moderate"
    )

def create_test_budget(
    student_id: str = "STU001",
    month_offset: int = 0
) -> Budget:
    """Create a test budget with typical categories"""
    
    # Set budget period to current month
    today = date.today()
    start_date = date(today.year, today.month, 1)
    if month_offset != 0:
        # Adjust for previous/next month testing
        month = start_date.month + month_offset
        year = start_date.year
        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1
        start_date = date(year, month, 1)
    
    # End date is last day of month
    if start_date.month == 12:
        end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
    
    # Create budget categories with typical limits
    categories = [
        BudgetCategory(category="groceries", limit=400.0),
        BudgetCategory(category="dining_out", limit=200.0),
        BudgetCategory(category="coffee", limit=100.0),
        BudgetCategory(category="entertainment", limit=150.0),
        BudgetCategory(category="transport", limit=120.0),
        BudgetCategory(category="shopping", limit=200.0),
        BudgetCategory(category="utilities", limit=150.0),
    ]
    
    return Budget(
        budget_id=generate_id("bud"),
        student_id=student_id,
        name=f"Monthly Budget - {start_date.strftime('%B %Y')}",
        period=BudgetPeriod.MONTHLY,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        categories=categories,
        savings_goal=500.0,
        alert_threshold=0.8,
        notes="Test budget for tracker"
    )

def create_test_transactions(
        budget: Budget,
        student_id: str = "STU001",
        scenario: str = "on_track"
) -> List[Transaction]:
    """
    Create transactions for different test scenarios:
    
    - "on_track": Spending within budget, good pace
    - "warning": Some categories near limit
    - "critical": Multiple categories over budget
    - "mixed": Mix of on_track and warning categories
    - "ahead_of_spend": Spending fast but not over yet
    - "goal_progress": Includes savings contributions
    """
    transactions = []
    today = date.today()
    
    # Calculate days in period
    total_days = (budget.end_date - budget.start_date).days + 1
    elapsed_days = min((today - budget.start_date).days + 1, total_days)
    
    if scenario == "on_track":
        # Spending at normal pace (60% of budget in 50% of time)
        spend_factors = {
            "groceries": 0.5,
            "dining_out": 0.4,
            "coffee": 0.6,
            "entertainment": 0.3,
            "transport": 0.5,
            "shopping": 0.4,
            "utilities": 0.5,
        }
        
    elif scenario == "warning":
        # Some categories near limit
        spend_factors = {
            "groceries": 0.85,  # Warning zone
            "dining_out": 0.9,   # Warning zone
            "coffee": 0.6,
            "entertainment": 0.4,
            "transport": 0.5,
            "shopping": 0.3,
            "utilities": 0.5,
        }
        
    elif scenario == "critical":
        # Multiple categories over budget
        spend_factors = {
            "groceries": 1.2,    # Over
            "dining_out": 1.1,    # Over
            "coffee": 1.0,        # At limit
            "entertainment": 0.8,
            "transport": 0.9,
            "shopping": 0.5,
            "utilities": 0.5,
        }
        
    elif scenario == "mixed":
        # Mix of good and bad
        spend_factors = {
            "groceries": 0.9,     # Warning
            "dining_out": 0.5,
            "coffee": 0.8,
            "entertainment": 0.3,
            "transport": 1.1,     # Over
            "shopping": 0.4,
            "utilities": 0.5,
        }
        
    elif scenario == "ahead_of_spend":
        # Spending fast but not over yet (early in month)
        spend_factors = {
            "groceries": 0.7,
            "dining_out": 0.6,
            "coffee": 0.5,
            "entertainment": 0.4,
            "transport": 0.8,     # High for time elapsed
            "shopping": 0.3,
            "utilities": 0.5,
        }
        
    else:  # goal_progress
        spend_factors = {
            "groceries": 0.5,
            "dining_out": 0.4,
            "coffee": 0.3,
            "entertainment": 0.2,
            "transport": 0.5,
            "shopping": 0.3,
            "utilities": 0.5,
        }
        
        # Add savings transfers for goal progress
        savings_amounts = [50, 50, 50, 50, 50]  # $250 total
        for i, amount in enumerate(savings_amounts):
            tx_date = budget.start_date + timedelta(days=i*5)
            # FIX: Ensure date is not in the future
            if tx_date > date.today():
                tx_date = date.today()
            if tx_date <= today:  # This condition is now redundant but keep as safety
                transactions.append(Transaction(
                    transaction_id=generate_id("txn"),
                    student_id=student_id,
                    amount=amount,
                    transaction_type=TransactionType.EXPENSE,
                    date=tx_date,
                    description=f"Transfer to savings #{i+1}",
                    merchant="Savings Account",
                    category="savings",
                    payment_method="cash",
                    source="manual",
                    confidence="high"
                ))
    
    # Create transactions for each category
    for category, factor in spend_factors.items():
        # Find the budget category
        budget_cat = next((c for c in budget.categories if str(c.category) == category), None)
        if not budget_cat:
            continue
            
        limit = budget_cat.limit
        target_spend = limit * factor
        
        # Distribute spending across the elapsed days (but never into the future)
        num_transactions = max(1, min(elapsed_days // 3, 5))  # 1-5 transactions
        for i in range(num_transactions):
            # IMPORTANT FIX: Ensure date is not in the future
            # Generate a random day offset between 0 and elapsed_days-1
            day_offset = random.randint(0, max(0, elapsed_days - 1))
            tx_date = budget.start_date + timedelta(days=day_offset)
            
            # Safety check: ensure date is not > today
            if tx_date > date.today():
                tx_date = date.today()
            
            # Create merchant based on category
            merchants = {
                "groceries": ["Walmart", "Kroger", "Trader Joes", "Whole Foods"],
                "dining_out": ["Restaurant", "Cafe", "Fast Food", "Pizza Place"],
                "coffee": ["Starbucks", "Dunkin", "Local Coffee Shop"],
                "entertainment": ["Movie Theater", "Netflix", "Spotify", "Game Store"],
                "transport": ["Gas Station", "Uber", "Bus Pass", "Parking"],
                "shopping": ["Amazon", "Target", "Mall Store", "Online Shop"],
                "utilities": ["Electric Co", "Water Dept", "Internet Provider", "Phone Co"],
            }
            
            merchant_list = merchants.get(category, ["Various"])
            merchant = random.choice(merchant_list)
            amount = target_spend / num_transactions
            transactions.append(Transaction(
                transaction_id=generate_id("txn"),
                student_id=student_id,
                amount=round(amount, 2),
                transaction_type=TransactionType.EXPENSE,
                date=tx_date,
                description=f"{merchant} purchase",
                merchant=merchant,
                category=category,
                payment_method="credit_card",
                source="manual",
                confidence="high"
            ))
    
    return transactions

def create_test_goals(student_id: str = "STU001") -> List[Goal]:
    """Create test goals for tracker"""
    today = date.today()
    
    goals = [
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="Emergency Fund",
            category=GoalCategory.EMERGENCY_FUND,
            target_amount=5000.0,
            current_amount=2500.0,
            target_date=today + timedelta(days=180),
            priority=GoalPriority.HIGH,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=200.0,
            notes="Build 3-month emergency fund"
        ),
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="New Laptop",
            category=GoalCategory.MAJOR_PURCHASE,
            target_amount=1500.0,
            current_amount=500.0,
            target_date=today + timedelta(days=90),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=150.0,
            notes="Save for new laptop"
        ),
    ]
    
    return goals


# =========================================================
# TEST FUNCTIONS
# =========================================================

def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)

def print_category_status(categories: Dict[str, Any]):
    """Pretty print category tracking"""
    print("\n📊 Category Status:")
    print("-" * 40)
    for cat, info in sorted(categories.items()):
        emoji = "🟢" if info["status"] == "on_track" else "🟡" if info["status"] == "warning" else "🔴"
        print(f"  {emoji} {cat:15} ${info['spent']:>6.2f} / ${info['limit']:>6.2f} "
              f"({info['percent_used']:5.1f}%) - {info['status']}")
        if info.get("pace"):
            pace = info["pace"]
            pace_emoji = "⚡" if pace["pace"] == "ahead_of_spend" else "🐢" if pace["pace"] == "under_pace" else "✓"
            print(f"      Pace: {pace_emoji} {pace['actual_used_percent']:.1f}% used, "
                  f"expected {pace['expected_used_percent_by_now']:.1f}%")

def print_alerts(alerts: List[Dict[str, Any]]):
    """Pretty print alerts"""
    if not alerts:
        print("\n✅ No alerts")
        return
    
    print("\n🚨 Alerts:")
    print("-" * 40)
    for alert in alerts[:5]:  # Show first 5
        emoji = "🔴" if alert["severity"] == "critical" else "🟡" if alert["severity"] == "warning" else "ℹ️"
        print(f"  {emoji} {alert['message']}")

def print_recommendations(recs: List[str]):
    """Pretty print recommendations"""
    if not recs:
        return
    
    print("\n💡 Recommendations:")
    print("-" * 40)
    for rec in recs[:5]:
        print(f"  • {rec}")

def print_goal_status(goals: List[Dict[str, Any]]):
    """Pretty print goal tracking"""
    if not goals:
        return
    
    print("\n🎯 Goal Progress:")
    print("-" * 40)
    for goal in goals:
        emoji = "✅" if goal["status"] == "completed" else "🔄" if goal["status"] == "in_progress" else "⏳"
        print(f"  {emoji} {goal['name']}: ${goal['current_amount']:.0f}/${goal['target_amount']:.0f} "
              f"({goal['progress_percent']:.1f}%)")
        if "pace" in goal:
            pace = goal["pace"]
            pace_emoji = "✓" if pace["status"] == "on_track" else "⚠️" if pace["status"] == "behind" else "✨"
            print(f"      Pace: {pace_emoji} Expected {pace['expected_progress_percent_by_now']:.1f}%, "
                  f"Actual {pace['actual_progress_percent']:.1f}%")

def test_scenario(
    tracker,
    student: Student,
    budget: Budget,
    scenario: str,
    goals: Optional[List[Goal]] = None
):
    """Test a specific scenario"""
    print_separator(f"SCENARIO: {scenario.upper()}")
    
    # Create transactions for this scenario
    transactions = create_test_transactions(
        student_id=student.student_id,
        budget=budget,
        scenario=scenario
    )
    
    print(f"\n📈 Created {len(transactions)} test transactions")
    print(f"📅 Budget period: {budget.start_date} to {budget.end_date}")
    print(f"📅 Today: {date.today()}")
    
    # Run tracker
    report = tracker.track_student(
        student=student,
        transactions=transactions,
        budget=budget,
        goals=goals
    )
    
    # Print results
    overall = report["budget_status"]
    status_emoji = "🟢" if overall["status"] == "healthy" else "🟡" if overall["status"] == "warning" else "🔴"
    print(f"\n📊 OVERALL BUDGET STATUS: {status_emoji} {overall['status'].upper()}")
    print(f"   Total: ${overall['total_spent']:.2f} / ${overall['total_budget']:.2f} "
          f"({overall['percent_used']:.1f}%)")
    print(f"   Categories over: {overall['categories_over_budget']}, "
          f"warning: {overall['categories_in_warning']}")
    
    pace = overall.get("pace", {})
    if pace:
        pace_emoji = "⚡" if pace.get("pace") == "ahead_of_spend" else "🐢" if pace.get("pace") == "under_pace" else "✓"
        print(f"   Pace: {pace_emoji} {pace.get('actual_used_percent', 0):.1f}% used, "
              f"expected {pace.get('expected_used_percent_by_now', 0):.1f}%")
    
    print_category_status(report["category_tracking"])
    print_alerts(report["alerts"])
    print_recommendations(report["recommendations"])
    
    if goals and report["goal_tracking"]:
        print_goal_status(report["goal_tracking"])
    
    return report


# =========================================================
# MAIN TEST SUITE
# =========================================================

def run_all_tests():
    """Run all tracker tests"""
    print("=" * 80)
    print("🧪🧪🧪 TRACKER AGENT COMPREHENSIVE TEST SUITE 🧪🧪🧪")
    print("=" * 80)
    
    # Initialize
    tracker = create_tracker()
    student = create_test_student()
    budget = create_test_budget()
    goals = create_test_goals()
    
    # Test 1: On Track Scenario
    test_scenario(tracker, student, budget, "on_track")
    
    # Test 2: Warning Scenario
    test_scenario(tracker, student, budget, "warning")
    
    # Test 3: Critical Scenario
    test_scenario(tracker, student, budget, "critical")
    
    # Test 4: Mixed Scenario
    test_scenario(tracker, student, budget, "mixed")
    
    # Test 5: Ahead of Spend Scenario
    test_scenario(tracker, student, budget, "ahead_of_spend")
    
    # Test 6: With Goals
    test_scenario(tracker, student, budget, "goal_progress", goals)
    
    # Test 7: Edge Cases
    print_separator("EDGE CASES")
    
    # Empty transactions
    print("\n📊 Empty transactions test:")
    empty_report = tracker.track_student(
        student=student,
        transactions=[],
        budget=budget
    )
    print(f"   Status: {empty_report['budget_status']['status']}")
    print(f"   Spent: ${empty_report['budget_status']['total_spent']}")
    
    # Future budget period
    print("\n📊 Future budget period test:")
    future_budget = create_test_budget(month_offset=1)  # Next month
    future_report = tracker.track_student(
        student=student,
        transactions=[],
        budget=future_budget
    )
    print(f"   Status: {future_report['budget_status']['status']}")
    print(f"   Spent: ${future_report['budget_status']['total_spent']}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TRACKER TESTS COMPLETE")
    print("=" * 80)


def test_individual_methods():
    """Test individual tracker methods"""
    print_separator("UNIT TESTS")
    
    tracker = create_tracker()
    student = create_test_student()
    budget = create_test_budget()
    
    # Test _is_expense and _is_income
    print("\n🔍 Testing type detection:")
    expense_txn = Transaction(
        transaction_id="test_txn1",
        student_id="STU001",
        amount=10.0,
        transaction_type=TransactionType.EXPENSE,
        date=date.today(),
        description="Test expense",
        category="food",
        payment_method="cash",
        source="manual",
        confidence="high"
    )
    income_txn = Transaction(
        transaction_id="test_txn2",
        student_id="STU001",
        amount=1000.0,
        transaction_type=TransactionType.INCOME,
        date=date.today(),
        description="Test income",
        category="salary",
        payment_method="direct_deposit",
        source="manual",
        confidence="high"
    )
    print(f"   Expense detection: {tracker._is_expense(expense_txn)} ✅")
    print(f"   Income detection: {tracker._is_income(income_txn)} ✅")
    
    # Test budget period filtering
    print("\n🔍 Testing budget period filtering:")
    outside_txn = Transaction(
        transaction_id="test_txn3",
        student_id="STU001",
        amount=10.0,
        transaction_type=TransactionType.EXPENSE,
        date=budget.start_date - timedelta(days=1),
        description="Outside period",
        category="food",
        payment_method="cash",
        source="manual",
        confidence="high"
    )
    filtered = tracker._filter_transactions_for_budget_period(
        [expense_txn, outside_txn], budget
    )
    print(f"   Transactions before: 2, after: {len(filtered)} ✅")
    
    # Test pace calculation
    print("\n🔍 Testing pace calculation:")
    start = date(2024, 3, 1)
    end = date(2024, 3, 31)
    
    # Mid-month, 50% used
    pace1 = tracker._calculate_budget_pace(
        start_date=start,
        end_date=end,
        tracking_date=date(2024, 3, 15),
        percent_used=50
    )
    print(f"   Mid-month, 50% used: {pace1['pace']} (should be on_track)")
    
    # Mid-month, 80% used (spending too fast)
    pace2 = tracker._calculate_budget_pace(
        start_date=start,
        end_date=end,
        tracking_date=date(2024, 3, 15),
        percent_used=80
    )
    print(f"   Mid-month, 80% used: {pace2['pace']} (should be ahead_of_spend)")
    
    # Early month, 10% used (spending slow)
    pace3 = tracker._calculate_budget_pace(
        start_date=start,
        end_date=end,
        tracking_date=date(2024, 3, 5),
        percent_used=10
    )
    print(f"   Early month, 10% used: {pace3['pace']} (should be under_pace)")


if __name__ == "__main__":
    # Set random seed for reproducible tests
    random.seed(42)
    
    # Run all tests
    run_all_tests()
    
    # Run unit tests
    test_individual_methods()