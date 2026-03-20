"""
🧪 TEST ADVISOR AGENT - Test LLM-powered financial advice
Tests context building, LLM integration, validation, and fallback
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import json
import random
import uuid
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.advisor import create_advisor
from agents.analyzer import create_analyzer
from agents.planner import create_planner
from agents.tracker import create_tracker
from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod


# =========================================================
# TEST DATA GENERATORS
# =========================================================

def generate_id(prefix: str = "txn") -> str:
    """Generate a unique ID for test objects"""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def create_test_student() -> Student:
    """Create a test student with realistic profile"""
    return Student(
        student_id="STU001",
        name="Alex Johnson",
        email="alex.johnson@university.edu",
        university="State University",
        graduation_year=2026,
        monthly_income=2800.0,
        current_savings=4200.0,
        risk_profile="moderate"
    )


def create_test_transactions(scenario: str = "normal") -> List[Transaction]:
    """
    Create realistic test transactions for different scenarios:
    - "normal": balanced spending
    - "warning": some categories near limit
    - "critical": multiple categories over budget
    - "good_saver": high savings rate
    """
    transactions = []
    today = date.today()
    student_id = "STU001"
    
    # Fixed monthly expenses (always present)
    fixed_expenses = [
        ("RENT", 950.0, "housing"),
        ("ELECTRIC", 85.0, "utilities"),
        ("INTERNET", 70.0, "internet"),
        ("PHONE", 50.0, "phone"),
    ]
    
    # Add fixed expenses for last 3 months
    for months in range(3):
        for desc, amt, cat in fixed_expenses:
            transactions.append(Transaction(
                transaction_id=generate_id(),
                student_id=student_id,
                amount=amt,
                transaction_type=TransactionType.EXPENSE,
                date=today - timedelta(days=months*30 + 5),
                description=desc,
                merchant=desc.split()[0],
                category=cat,
                payment_method="credit_card",
                source="manual",
                confidence="high"
            ))
    
    # Variable expenses based on scenario
    if scenario == "normal":
        category_factors = {
            "groceries": (300, 400, 0.5),
            "dining_out": (150, 250, 0.4),
            "coffee": (40, 70, 0.5),
            "entertainment": (80, 150, 0.3),
            "shopping": (100, 200, 0.4),
            "transport": (80, 120, 0.5),
        }
    elif scenario == "warning":
        category_factors = {
            "groceries": (350, 450, 0.85),
            "dining_out": (200, 300, 0.9),
            "coffee": (60, 90, 0.8),
            "entertainment": (120, 180, 0.6),
            "shopping": (150, 250, 0.5),
            "transport": (90, 130, 0.7),
        }
    elif scenario == "critical":
        category_factors = {
            "groceries": (450, 550, 1.2),
            "dining_out": (300, 400, 1.1),
            "coffee": (80, 120, 1.0),
            "entertainment": (200, 300, 0.9),
            "shopping": (250, 350, 0.8),
            "transport": (120, 180, 1.1),
        }
    else:  # good_saver
        category_factors = {
            "groceries": (250, 350, 0.4),
            "dining_out": (100, 180, 0.3),
            "coffee": (30, 50, 0.3),
            "entertainment": (50, 100, 0.2),
            "shopping": (50, 120, 0.2),
            "transport": (60, 100, 0.4),
        }
    
    # Generate daily transactions for last 60 days
    for days_ago in range(60):
        tx_date = today - timedelta(days=days_ago)
        
        for cat, (min_amt, max_amt, factor) in category_factors.items():
            # Random frequency based on category
            freq = random.random()
            if (cat == "groceries" and freq < 0.2) or \
               (cat == "coffee" and freq < 0.3) or \
               (freq < 0.15):
                
                amount = round(random.uniform(min_amt/10, max_amt/10), 2)
                
                # Merchant mapping
                merchants = {
                    "groceries": ["Walmart", "Kroger", "Trader Joes", "Whole Foods"],
                    "dining_out": ["Chipotle", "Local Diner", "Pizza Place", "Sushi Spot"],
                    "coffee": ["Starbucks", "Dunkin", "Local Coffee Shop"],
                    "entertainment": ["AMC", "Netflix", "Spotify", "GameStop"],
                    "shopping": ["Amazon", "Target", "Mall Store", "Best Buy"],
                    "transport": ["Uber", "Lyft", "Gas Station", "Metro Pass"],
                }
                merchant_list = merchants.get(cat, ["Various"])
                merchant = random.choice(merchant_list)
                
                transactions.append(Transaction(
                    transaction_id=generate_id(),
                    student_id=student_id,
                    amount=amount,
                    transaction_type=TransactionType.EXPENSE,
                    date=tx_date,
                    description=f"{merchant} purchase",
                    merchant=merchant,
                    category=cat,
                    payment_method="credit_card",
                    source="manual",
                    confidence="high"
                ))
    
    # Add income transactions (paydays)
    for months in range(3):
        payday = today - timedelta(days=months*30 + 1)
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id=student_id,
            amount=2800.0,
            transaction_type=TransactionType.INCOME,
            date=payday,
            description="PAYROLL - University",
            merchant="University",
            category="salary",
            payment_method="direct_deposit",
            source="manual",
            confidence="high"
        ))
    
    # Add some refunds/credits occasionally
    if random.random() > 0.7:
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id=student_id,
            amount=random.uniform(20, 50),
            transaction_type=TransactionType.INCOME,
            date=today - timedelta(days=random.randint(5, 30)),
            description="Refund",
            merchant="Various",
            category="refund",
            payment_method="cash",
            source="manual",
            confidence="high"
        ))
    
    return transactions

def create_test_transactions_for_budget(
    budget: Budget,
    scenario: str = "on_track"
) -> List[Transaction]:
    """
    Create transactions ONLY for the current budget period with totals
    that reliably hit on_track / warning / critical for their category limit.
    """
    transactions: List[Transaction] = []
    today = date.today()
    student_id = budget.student_id

    # Helpers
    def add_tx(cat: str, amt: float):
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id=student_id,
            amount=amt,
            transaction_type=TransactionType.EXPENSE,
            date=today,
            description=f"{cat} spend",
            merchant=cat.title(),
            category=cat,
            payment_method="debit_card",
            source="manual",
            confidence="high",
        ))

    # Category targets as % of limit
    if scenario == "on_track":
        pct = 0.5
    elif scenario == "warning":
        pct = 0.85
    else: # critical
        pct = 1.15

    for bc in budget.categories:
        target = round(bc.limit * pct, 2)
        # split into 3 transactions so tracker’s date logic isn’t brittle
        chunk = round(target / 3, 2)
        for _ in range(3):
            add_tx(bc.category, chunk)

    # One income transaction so net_flow is realistic
    transactions.append(Transaction(
        transaction_id=generate_id(),
        student_id=student_id,
        amount=2800.0,
        transaction_type=TransactionType.INCOME,
        date=today,
        description="PAYROLL",
        merchant="University",
        category="salary",
        payment_method="direct_deposit",
        source="manual",
        confidence="high",
    ))

    return transactions


def create_test_goals(student_id: str = "STU001") -> List[Goal]:
    """Create test goals for advisor"""
    today = date.today()
    
    return [
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="Emergency Fund",
            category=GoalCategory.EMERGENCY_FUND,
            target_amount=10000.0,
            current_amount=4200.0,
            target_date=today + timedelta(days=365),
            priority=GoalPriority.HIGH,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=250.0,
            notes="Build 3-6 months of expenses"
        ),
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="Summer Internship Relocation",
            category=GoalCategory.TRAVEL,
            target_amount=2500.0,
            current_amount=800.0,
            target_date=today + timedelta(days=120),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=150.0,
            notes="Moving costs for summer internship"
        ),
        Goal(
            goal_id=generate_id("goal"),
            student_id=student_id,
            name="New Laptop",
            category=GoalCategory.MAJOR_PURCHASE,
            target_amount=1500.0,
            current_amount=300.0,
            target_date=today + timedelta(days=180),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=100.0,
            notes="Need for next semester"
        )
    ]


def create_test_budget(student_id: str = "STU001") -> Budget:
    """Create a test budget"""
    today = date.today()
    start_date = date(today.year, today.month, 1)
    
    if start_date.month == 12:
        end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
    
    categories = [
        BudgetCategory(category="groceries", limit=400.0),
        BudgetCategory(category="dining_out", limit=250.0),
        BudgetCategory(category="coffee", limit=80.0),
        BudgetCategory(category="entertainment", limit=150.0),
        BudgetCategory(category="shopping", limit=200.0),
        BudgetCategory(category="transport", limit=120.0),
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
        notes="Test budget for advisor"
    )


# =========================================================
# TEST FUNCTIONS
# =========================================================

def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)


def test_advisor_with_scenario(
    advisor,
    analyzer,
    planner,
    tracker,
    student,
    transactions,
    budget,
    goals,
    scenario_name: str
):
    """Test advisor with a specific scenario"""
    print_separator(f"SCENARIO: {scenario_name.upper()}")
    
    print(f"\n📊 Analyzing {len(transactions)} transactions...")
    
    # Run the agent pipeline
    analysis = analyzer.analyze_student(student, transactions, lookback_days=90)
    plan = planner.build_plan(
        student=student,
        transactions=transactions,
        analysis=analysis,
        goals=goals
    )
    tracking = tracker.track_student(
        student=student,
        transactions=transactions,
        budget=budget,
        goals=goals
    )
    #
    # print("\n[DEBUG TRACKER OUTPUT]")
    print(json.dumps(tracking.get("budget_status", {}), indent=2))
    
    print("\n🤖 Generating AI-powered advice...")
    #print("\n[DEBUG CATEGORY TRACKING]")
    for cat, info in tracking.get("category_tracking", {}).items():
        print(cat, "->", info.get("status"), "|", info.get("percent_used"), "|", info.get("pace", {}))
    
    # Get advice
    advice_result = advisor.advice_student(
        student=student,
        analysis=analysis,
        plan=plan,
        tracking_report=tracking,
        goals=goals
    )
    #print("\n[DEBUG TRACKER OUTPUT]")
    print(json.dumps(tracking.get("budget_status", {}), indent=2))

    #print("\n[DEBUG CATEGORY TRACKING]")
    for cat, info in tracking.get("category_tracking", {}).items():
        print(
            f"{cat}: status={info.get('status')}, "
            f"percent_used={info.get('percent_used')}, "
            f"pace={info.get('pace', {})}"
        )
    
    # Print results
    advice = advice_result["advice"]
    
    print(f"\n💡 OVERALL HEALTH: {advice['overall_financial_health'].upper()}")
    
    print("\n🎯 TOP PRIORITIES:")
    for i, p in enumerate(advice.get("top_priorities", []), 1):
        print(f"  {i}. {p}")
    
    print("\n⚡ IMMEDIATE ACTIONS:")
    for i, a in enumerate(advice.get("immediate_actions", []), 1):
        print(f"  {i}. {a}")
    
    print("\n📈 STRATEGIC ADVICE:")
    for a in advice.get("strategic_advice", []):
        print(f"  • {a}")
    
    print("\n📝 SUMMARY:")
    print(f"  {advice.get('advisor_summary', '')}")
    
    print("\n💬 ENCOURAGEMENT:")
    for e in advice.get("encouragement", []):
        print(f"  ✨ {e}")
    
    # Print metadata
    metadata = advice_result.get("metadata", {})
    if metadata.get("fallback"):
        print(f"\n⚠️ Using fallback advice (LLM unavailable)")
    else:
        print(f"\n📊 Tokens used (cumulative): {metadata.get('tokens_used_cumulative', 0)}")
        print(f"   Model: {metadata.get('model', 'unknown')}")
    
    return advice_result


def test_advisor_components():
    """Test individual advisor components"""
    print_separator("COMPONENT TESTS")
    
    advisor = create_advisor()
    student = create_test_student()
    transactions = create_test_transactions("normal")
    goals = create_test_goals()
    
    # Test 1: Context Building
    print("\n📦 Testing Context Building...")
    
    # Create minimal analysis, plan, tracking for context test
    analysis = {
        "summary": {
            "amount_spent": 2100.0,
            "amount_earned": 2800.0,
            "net_flow": 700.0,
            "top_categories": [
                {"category": "groceries", "amount": 400.0, "share_pct": 19.0},
                {"category": "dining_out", "amount": 300.0, "share_pct": 14.3}
            ]
        },
        "patterns": [
            {"name": "weekend_spending", "description": "Spends 40% more on weekends", "severity": "warning"},
            {"name": "category_concentration", "description": "60% on food", "severity": "warning"}
        ],
        "trends": [
            {"type": "decreasing", "description": "Spending down 15%", "severity": "positive"}
        ],
        "window_days": 90
    }
    
    plan = {
        "baseline": {
            "total_spend_est_monthly": 2100.0,
            "variable_spend_est_monthly": 700.0
        },
        "action_plan": [
            {"title": "Reduce dining out", "description": "Cut by $50/month", "priority": "high", "impact_monthly_usd": 50},
            {"title": "Increase savings", "description": "Auto-transfer $100", "priority": "medium", "impact_monthly_usd": 100}
        ]
    }
    
    tracking_report = {
        "budget_status": {
            "status": "warning",
            "percent_used": 75.0,
            "categories_over_budget": 1,
            "categories_in_warning": 2,
            "pace": {"status": "ahead_of_spend"}
        },
        "category_tracking": {
            "groceries": {"status": "warning", "percent_used": 85.0, "limit": 400, "spent": 340},
            "dining_out": {"status": "over_budget", "percent_used": 110.0, "limit": 250, "spent": 275},
            "coffee": {"status": "on_track", "percent_used": 60.0, "limit": 80, "spent": 48}
        }
    }
    
    context = advisor._build_context(
        student=student,
        analysis=analysis,
        plan=plan,
        tracking_report=tracking_report,
        goals=goals
    )
    
    print(f"   ✅ Context built with {len(json.dumps(context))} chars")
    print(f"   ✅ Contains {len(context.get('patterns', []))} patterns")
    print(f"   ✅ Contains {len(context.get('flexible_problem_categories', []))} flexible problem categories")
    print(f"   ✅ Contains {len(context.get('fixed_problem_categories', []))} fixed problem categories")
    print(f"   ✅ Contains {len(context.get('goals', []))} goals")


def test_validation():
    """Test the validation and normalization logic"""
    print_separator("VALIDATION TESTS")
    
    advisor = create_advisor()
    
    # Test 1: Missing keys
    print("\n🔍 Testing missing keys...")
    incomplete_advice = {
        "overall_financial_health": "warning"
    }
    validated = advisor._validate_llm_advice_structure(advice=incomplete_advice, default_health="warning")
    assert "top_priorities" in validated, "Missing top_priorities should be added"
    assert "immediate_actions" in validated, "Missing immediate_actions should be added"
    print("   ✅ Missing keys handled correctly")
    
    # Test 2: Invalid health status
    print("\n🔍 Testing invalid health status...")
    invalid_health = {"overall_financial_health": "super_healthy"}
    validated = advisor._validate_llm_advice_structure(advice=invalid_health, default_health="warning")
    assert validated["overall_financial_health"] == "warning", f"Expected warning, got {validated['overall_financial_health']}"
    print("   ✅ Invalid health corrected")
    
    # Test 3: String instead of list
    print("\n🔍 Testing string instead of list...")
    string_advice = {
        "overall_financial_health": "healthy",
        "top_priorities": "This is a string, not a list"
    }
    validated = advisor._validate_llm_advice_structure(advice=string_advice, default_health="healthy")
    assert isinstance(validated["top_priorities"], list), "String should be converted to list"
    print("   ✅ String fields normalized")
    
    # Test 4: List size limits
    print("\n🔍 Testing list size limits...")
    long_list = {
        "overall_financial_health": "healthy",
        "top_priorities": [f"Priority {i}" for i in range(10)],
        "immediate_actions": [f"Action {i}" for i in range(10)]
    }
    validated = advisor._validate_llm_advice_structure(advice=long_list, default_health="healthy")
    assert len(validated["top_priorities"]) <= 5, f"Too many priorities: {len(validated['top_priorities'])}"
    assert len(validated["immediate_actions"]) <= 3, f"Too many actions: {len(validated['immediate_actions'])}"
    print("   ✅ List sizes limited correctly")


def test_fallback():
    """Test fallback mechanism"""
    print_separator("FALLBACK TESTS")
    
    advisor = create_advisor()
    student = create_test_student()
    
    # Test fallback with different health categories
    for health in ["healthy", "warning", "critical", "unknown"]:
        fallback = advisor._fallback_response(
            student=student,
            health_category=health,
            error="LLM connection failed"
        )
        
        print(f"\n🔍 Fallback for {health}:")
        print(f"   ✅ Health: {fallback['advice']['overall_financial_health']}")
        print(f"   ✅ Priorities: {len(fallback['advice']['top_priorities'])}")
        print(f"   ✅ Actions: {len(fallback['advice']['immediate_actions'])}")
        print(f"   ✅ Metadata shows fallback: {fallback['metadata']['fallback']}")
        print(f"   ✅ Error preserved: {fallback['metadata']['error']}")


def test_health_detection():
    """Test health category detection"""
    print_separator("HEALTH DETECTION TESTS")
    
    advisor = create_advisor()
    
    # Test 1: Healthy from budget status
    tracking_healthy = {"budget_status": {"status": "healthy"}}
    health = advisor._detect_health_category(
        tracking_report=tracking_healthy,
        analysis={},
        plan={}
    )
    print(f"   ✅ Healthy detection: {health} (should be healthy)")
    
    # Test 2: Critical from patterns
    tracking_warning = {"budget_status": {"status": "warning"}}
    analysis_critical = {"patterns": [{"severity": "critical"}]}
    health = advisor._detect_health_category(
        tracking_report=tracking_warning,
        analysis=analysis_critical,
        plan={}
    )
    print(f"   ✅ Critical detection from patterns: {health} (should be critical)")
    
    # Test 3: Warning from budget
    tracking_warning = {"budget_status": {"status": "warning"}}
    health = advisor._detect_health_category(
        tracking_report=tracking_warning,
        analysis={},
        plan={}
    )
    print(f"   ✅ Warning detection: {health} (should be warning)")


def test_full_pipeline():
    """Test the complete advisor pipeline with real data"""
    print_separator("FULL PIPELINE TEST")
    
    # Initialize
    advisor = create_advisor()
    analyzer = create_analyzer()
    planner = create_planner()
    tracker = create_tracker()
    
    student = create_test_student()
    budget = create_test_budget()
    goals = create_test_goals()
    
    # Test different scenarios
    scenarios = [
        ("normal", "Balanced spending"),
        ("warning", "Nearing budget limits"),
        ("critical", "Over budget in multiple categories"),
        ("good_saver", "High savings rate")
    ]

    scenario_map = {
    "normal": "on_track",
    "warning": "warning",
    "critical": "critical",
    "good_saver": "on_track",
}
    
    for scenario_name, description in scenarios:
        print(f"\n📋 Testing: {description}")
        #transactions = create_test_transactions(scenario_name)
        
        result = test_advisor_with_scenario(
            advisor=advisor,
            analyzer=analyzer,
            planner=planner,
            tracker=tracker,
            student=student,
            transactions = create_test_transactions_for_budget(
                budget, scenario_map[scenario_name]),
            budget=budget,
            goals=goals,
            scenario_name=f"{scenario_name} - {description}"
        )
        
        # Verify structure
        advice = result["advice"]
        assert "overall_financial_health" in advice
        assert "top_priorities" in advice
        assert "immediate_actions" in advice
        assert "advisor_summary" in advice
        
        print(f"\n   ✅ Structure valid for {scenario_name}")
        
        # Small delay between scenarios to avoid rate limits
        import time
        time.sleep(1)


# =========================================================
# MAIN TEST RUNNER
# =========================================================

def run_all_tests():
    """Run all advisor tests"""
    print("=" * 80)
    print("🧪🧪🧪 ADVISOR AGENT COMPREHENSIVE TEST SUITE 🧪🧪🧪")
    print("=" * 80)
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Run component tests first
    test_advisor_components()
    test_validation()
    test_health_detection()
    test_fallback()
    
    # Run full pipeline test (commented out if you want to skip LLM calls)
    print("\n" + "=" * 80)
    print("🚀 Running full pipeline test (will call actual LLM)")
    print("=" * 80)
    test_full_pipeline()
    
    print("\n" + "=" * 80)
    print("✅ ALL ADVISOR TESTS COMPLETE")
    print("=" * 80)


def run_quick_tests():
    """Run only the fast, deterministic tests (no LLM calls)"""
    print("=" * 80)
    print("🧪 ADVISOR AGENT QUICK TESTS (No LLM)")
    print("=" * 80)
    
    test_advisor_components()
    test_validation()
    test_health_detection()
    test_fallback()
    
    print("\n" + "=" * 80)
    print("✅ QUICK TESTS COMPLETE")
    print("=" * 80)




if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_tests()
    else:
        run_all_tests()