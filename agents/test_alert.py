"""
🧪 TEST ALERT AGENT - Cleaned and aligned test suite for AlertAgent

What this test file covers
--------------------------
1. Healthy / calm scenario
2. Warning budget scenario
3. Critical budget scenario
4. Pace-only scenario
5. Savings-related alerts
6. Goal-related alerts
7. Pattern-related alerts
8. Stress / structural alerts
9. Utility tests:
   - deduplication
   - sorting
   - overall alert level

Important note
--------------
This test file is aligned to the current AlertAgent behavior:
- overall alert levels are: info, warning, critical
- "healthy" is NOT an alert level
- the healthy scenario is intentionally built to avoid warning/critical signals
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.alert import create_alert_agent
from schemas.student import Student
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType


# =========================================================
# TEST DATA BUILDERS
# =========================================================

def create_test_student(
    *,
    monthly_income: float = 2800.0,
    current_savings: float = 6000.0,
    fixed_expenses: float = 1500.0,
) -> Student:
    """
    Create a test student aligned with the current Student schema.
    """
    student = Student(
        student_id="STU001",
        name="Alex Johnson",
        monthly_income=monthly_income,
        current_savings=current_savings,
        risk_profile="moderate",
        fixed_monthly_expenses={"rent": fixed_expenses},
    )
    return student


def create_test_goals(mode: str = "mixed") -> List[Goal]:
    """
    Build test goals.

    mode:
    - "none"   -> no goals
    - "healthy"-> all goals on track
    - "mixed"  -> one behind / one okay / one almost complete
    """
    today = date.today()

    if mode == "none":
        return []

    if mode == "healthy":
        return [
            Goal(
                goal_id="goal_001",
                student_id="STU001",
                name="Emergency Fund",
                category=GoalCategory.EMERGENCY_FUND,
                target_amount=10000.0,
                current_amount=5500.0,
                target_date=today + timedelta(days=240),
                priority=GoalPriority.HIGH,
                recurring_type=RecurringType.MONTHLY,
                recurring_amount=250.0,
            ),
            Goal(
                goal_id="goal_002",
                student_id="STU001",
                name="Laptop Upgrade",
                category=GoalCategory.MAJOR_PURCHASE,
                target_amount=1500.0,
                current_amount=900.0,
                target_date=today + timedelta(days=180),
                priority=GoalPriority.MEDIUM,
                recurring_type=RecurringType.MONTHLY,
                recurring_amount=100.0,
            ),
        ]

    # default = mixed
    return [
        Goal(
            goal_id="goal_001",
            student_id="STU001",
            name="Emergency Fund",
            category=GoalCategory.EMERGENCY_FUND,
            target_amount=10000.0,
            current_amount=5000.0,
            target_date=today + timedelta(days=180),
            priority=GoalPriority.HIGH,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=200.0,
        ),
        Goal(
            goal_id="goal_002",
            student_id="STU001",
            name="Summer Trip",
            category=GoalCategory.TRAVEL,
            target_amount=2000.0,
            current_amount=500.0,
            target_date=today + timedelta(days=45),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=100.0,
        ),
        Goal(
            goal_id="goal_003",
            student_id="STU001",
            name="New Laptop",
            category=GoalCategory.MAJOR_PURCHASE,
            target_amount=1500.0,
            current_amount=1400.0,
            target_date=today + timedelta(days=5),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=100.0,
        ),
        # completed goal; let model compute completed from amount
        Goal(
            goal_id="goal_004",
            student_id="STU001",
            name="Textbooks",
            category=GoalCategory.EDUCATION,
            target_amount=500.0,
            current_amount=500.0,
            target_date=today + timedelta(days=30),
            priority=GoalPriority.MEDIUM,
            recurring_type=RecurringType.ONE_TIME,
            recurring_amount=None,
        ),
    ]


def create_mock_analysis(
    *,
    amount_earned: float = 8400.0,
    amount_spent: float = 6300.0,
    patterns: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Create analyzer-like output.
    """
    if patterns is None:
        patterns = [
            {
                "name": "weekend_spending",
                "description": "Spends 40% more on weekends",
                "severity": "warning",
            },
            {
                "name": "category_concentration",
                "description": "60% of spending on food",
                "severity": "warning",
                "data": {"category": "food", "pct": 60},
            },
            {
                "name": "subscriptions",
                "description": "Detected 4 subscription services",
                "severity": "info",
                "data": {
                    "subscriptions": [
                        {"merchant": "netflix"},
                        {"merchant": "spotify"},
                        {"merchant": "hulu"},
                        {"merchant": "amazon prime"},
                    ]
                },
            },
        ]

    return {
        "summary": {
            "amount_earned": amount_earned,
            "amount_spent": amount_spent,
            "net_flow": amount_earned - amount_spent,
        },
        "patterns": patterns,
        "trends": [],
    }


def create_healthy_analysis() -> Dict[str, Any]:
    """
    Truly healthy analysis:
    - no warning patterns
    - maybe only info-level subscription review
    """
    return create_mock_analysis(
        amount_earned=8400.0,
        amount_spent=6000.0,
        patterns=[
            {
                "name": "subscriptions",
                "description": "Detected 2 subscription services",
                "severity": "info",
                "data": {
                    "subscriptions": [
                        {"merchant": "netflix"},
                        {"merchant": "spotify"},
                    ]
                },
            }
        ],
    )


def create_mock_plan(
    *,
    monthly_income: float = 2800.0,
    fixed_monthly_expenses: float = 1500.0,
    variable_spend_est_monthly: float = 700.0,
    total_spend_est_monthly: float = 2200.0,
    disposable_income: float = 600.0,
) -> Dict[str, Any]:
    """
    Create planner-like output.
    """
    return {
        "baseline": {
            "monthly_income": monthly_income,
            "fixed_monthly_expenses": fixed_monthly_expenses,
            "variable_spend_est_monthly": variable_spend_est_monthly,
            "total_spend_est_monthly": total_spend_est_monthly,
            "disposable_est_monthly": disposable_income,
        }
    }


def create_mock_tracking(
    scenario: str = "healthy",
    *,
    with_goal_tracking: bool = False,
) -> Dict[str, Any]:
    """
    Create tracker-like output.

    Scenarios:
    - healthy
    - warning
    - critical
    - pace
    - mixed
    """
    today = date.today()
    start_date = date(today.year, today.month, 1)
    elapsed_days = (today - start_date).days + 1
    total_days = 30
    expected_used = (elapsed_days / total_days) * 100

    if scenario == "healthy":
        budget_status = {
            "status": "healthy",
            "percent_used": 45.0,
            "total_budget": 1350.0,
            "total_spent": 607.5,
            "categories_over_budget": 0,
            "categories_in_warning": 0,
            "pace": {
                "elapsed_days": elapsed_days,
                "total_days": total_days,
                "expected_used_percent_by_now": expected_used,
                "actual_used_percent": 45.0,
                "pace": "on_track",
            },
        }
        category_tracking = {
            "groceries": {
                "status": "on_track",
                "percent_used": 45.0,
                "limit": 400,
                "spent": 180,
                "pace": {"pace": "on_track"},
            },
            "dining_out": {
                "status": "on_track",
                "percent_used": 40.0,
                "limit": 250,
                "spent": 100,
                "pace": {"pace": "on_track"},
            },
            "coffee": {
                "status": "on_track",
                "percent_used": 50.0,
                "limit": 80,
                "spent": 40,
                "pace": {"pace": "on_track"},
            },
            "entertainment": {
                "status": "on_track",
                "percent_used": 30.0,
                "limit": 150,
                "spent": 45,
                "pace": {"pace": "under_pace"},
            },
        }

    elif scenario == "warning":
        budget_status = {
            "status": "warning",
            "percent_used": 85.0,
            "total_budget": 1350.0,
            "total_spent": 1147.5,
            "categories_over_budget": 0,
            "categories_in_warning": 2,
            "pace": {
                "elapsed_days": elapsed_days,
                "total_days": total_days,
                "expected_used_percent_by_now": expected_used,
                "actual_used_percent": 85.0,
                "pace": "ahead_of_spend",
            },
        }
        category_tracking = {
            "groceries": {
                "status": "warning",
                "percent_used": 85.0,
                "limit": 400,
                "spent": 340,
                "pace": {"pace": "ahead_of_spend"},
            },
            "dining_out": {
                "status": "warning",
                "percent_used": 90.0,
                "limit": 250,
                "spent": 225,
                "pace": {"pace": "ahead_of_spend"},
            },
            "coffee": {
                "status": "on_track",
                "percent_used": 60.0,
                "limit": 80,
                "spent": 48,
                "pace": {"pace": "on_track"},
            },
            "entertainment": {
                "status": "on_track",
                "percent_used": 40.0,
                "limit": 150,
                "spent": 60,
                "pace": {"pace": "under_pace"},
            },
        }

    elif scenario == "critical":
        budget_status = {
            "status": "critical",
            "percent_used": 115.0,
            "total_budget": 1350.0,
            "total_spent": 1552.5,
            "categories_over_budget": 2,
            "categories_in_warning": 1,
            "pace": {
                "elapsed_days": elapsed_days,
                "total_days": total_days,
                "expected_used_percent_by_now": expected_used,
                "actual_used_percent": 115.0,
                "pace": "ahead_of_spend",
            },
        }
        category_tracking = {
            "groceries": {
                "status": "over_budget",
                "percent_used": 120.0,
                "limit": 400,
                "spent": 480,
                "pace": {"pace": "ahead_of_spend"},
            },
            "dining_out": {
                "status": "over_budget",
                "percent_used": 110.0,
                "limit": 250,
                "spent": 275,
                "pace": {"pace": "ahead_of_spend"},
            },
            "coffee": {
                "status": "warning",
                "percent_used": 90.0,
                "limit": 80,
                "spent": 72,
                "pace": {"pace": "ahead_of_spend"},
            },
            "entertainment": {
                "status": "on_track",
                "percent_used": 45.0,
                "limit": 150,
                "spent": 67.5,
                "pace": {"pace": "on_track"},
            },
        }

    elif scenario == "pace":
        budget_status = {
            "status": "healthy",
            "percent_used": 70.0,
            "total_budget": 1350.0,
            "total_spent": 945.0,
            "categories_over_budget": 0,
            "categories_in_warning": 0,
            "pace": {
                "elapsed_days": elapsed_days,
                "total_days": total_days,
                "expected_used_percent_by_now": expected_used,
                "actual_used_percent": 70.0,
                "pace": "ahead_of_spend",
            },
        }
        category_tracking = {
            "groceries": {
                "status": "on_track",
                "percent_used": 80.0,
                "limit": 400,
                "spent": 320,
                "pace": {"pace": "ahead_of_spend"},
            },
            "dining_out": {
                "status": "on_track",
                "percent_used": 75.0,
                "limit": 250,
                "spent": 187.5,
                "pace": {"pace": "ahead_of_spend"},
            },
            "coffee": {
                "status": "on_track",
                "percent_used": 70.0,
                "limit": 80,
                "spent": 56.0,
                "pace": {"pace": "ahead_of_spend"},
            },
            "entertainment": {
                "status": "on_track",
                "percent_used": 65.0,
                "limit": 150,
                "spent": 97.5,
                "pace": {"pace": "ahead_of_spend"},
            },
        }

    else:  # mixed
        budget_status = {
            "status": "warning",
            "percent_used": 88.0,
            "total_budget": 1350.0,
            "total_spent": 1188.0,
            "categories_over_budget": 1,
            "categories_in_warning": 2,
            "pace": {
                "elapsed_days": elapsed_days,
                "total_days": total_days,
                "expected_used_percent_by_now": expected_used,
                "actual_used_percent": 88.0,
                "pace": "ahead_of_spend",
            },
        }
        category_tracking = {
            "groceries": {
                "status": "over_budget",
                "percent_used": 105.0,
                "limit": 400,
                "spent": 420.0,
                "pace": {"pace": "ahead_of_spend"},
            },
            "dining_out": {
                "status": "warning",
                "percent_used": 92.0,
                "limit": 250,
                "spent": 230.0,
                "pace": {"pace": "ahead_of_spend"},
            },
            "coffee": {
                "status": "warning",
                "percent_used": 88.0,
                "limit": 80,
                "spent": 70.4,
                "pace": {"pace": "ahead_of_spend"},
            },
            "entertainment": {
                "status": "on_track",
                "percent_used": 60.0,
                "limit": 150,
                "spent": 90.0,
                "pace": {"pace": "on_track"},
            },
        }

    goal_tracking = []
    if with_goal_tracking:
        goal_tracking = [
            {
                "name": "Emergency Fund",
                "progress_percent": 50.0,
                "target_amount": 10000.0,
                "current_amount": 5000.0,
                "pace": {"status": "on_track"},
            },
            {
                "name": "Summer Trip",
                "progress_percent": 25.0,
                "target_amount": 2000.0,
                "current_amount": 500.0,
                "pace": {"status": "behind"},
            },
        ]

    return {
        "budget_status": budget_status,
        "category_tracking": category_tracking,
        "goal_tracking": goal_tracking,
    }


# =========================================================
# PRINT HELPERS
# =========================================================

def print_alerts(alert_result: Dict[str, Any], title: str):
    """
    Pretty-print alerts for quick visual inspection.
    """
    print(f"\n{'=' * 70}")
    print(f"🚨 {title}")
    print(f"{'=' * 70}")
    print(f"Overall Level: {alert_result['overall_alert_level'].upper()}")
    print(f"Summary: {alert_result['summary']}")

    alerts = alert_result.get("alerts", [])
    if not alerts:
        print("\n✅ No alerts")
        return

    print(f"\n📋 Alerts ({len(alerts)} total):")
    for i, alert in enumerate(alerts, 1):
        severity_emoji = "🔴" if alert["severity"] == "critical" else "🟡" if alert["severity"] == "warning" else "ℹ️"
        print(f"\n{i}. {severity_emoji} [{alert['severity'].upper()}] {alert['title']}")
        print(f"   📝 {alert['message']}")
        print(f"   💡 {alert['recommended_action']}")
        print(f"   📌 Type: {alert['type']} | Source: {alert['source']}")
        if alert.get("category"):
            print(f"   🏷️ Category: {alert['category']}")
        if alert.get("goal_name"):
            print(f"   🎯 Goal: {alert['goal_name']}")


# =========================================================
# TESTS
# =========================================================

def test_healthy_scenario():
    """
    Truly healthy scenario:
    - healthy tracker output
    - healthy goals
    - only info-level analysis pattern
    - solid emergency cushion
    """
    print("\n🧪 TEST: Healthy Scenario")

    alert_agent = create_alert_agent()
    student = create_test_student(
        monthly_income=2800.0,
        current_savings=6000.0,
        fixed_expenses=1500.0,
    )

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_healthy_analysis(),
        plan=create_mock_plan(
            monthly_income=2800.0,
            fixed_monthly_expenses=1500.0,
            total_spend_est_monthly=2200.0,
            disposable_income=600.0,
        ),
        tracking_report=create_mock_tracking("healthy"),
        goals=create_test_goals("healthy"),
    )

    print_alerts(result, "HEALTHY SCENARIO")

    assert result["overall_alert_level"] == "info"
    assert result["summary"]["critical_count"] == 0
    assert result["summary"]["warning_count"] == 0
    assert result["summary"]["info_count"] >= 1


def test_warning_scenario():
    """
    Warning scenario should produce warning-level alerts.
    """
    print("\n🧪 TEST: Warning Scenario")

    alert_agent = create_alert_agent()
    student = create_test_student()
    goals = create_test_goals("mixed")

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_mock_analysis(),
        plan=create_mock_plan(),
        tracking_report=create_mock_tracking("warning"),
        goals=goals,
    )

    print_alerts(result, "WARNING SCENARIO")

    assert result["overall_alert_level"] in ["warning", "critical"]
    assert result["summary"]["warning_count"] > 0

    alert_types = [a["type"] for a in result["alerts"]]
    assert "overall_budget_warning" in alert_types
    assert "category_near_limit" in alert_types


def test_critical_scenario():
    """
    Critical scenario should produce critical alerts.
    """
    print("\n🧪 TEST: Critical Scenario")

    alert_agent = create_alert_agent()
    student = create_test_student()
    goals = create_test_goals("mixed")

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_mock_analysis(),
        plan=create_mock_plan(),
        tracking_report=create_mock_tracking("critical"),
        goals=goals,
    )

    print_alerts(result, "CRITICAL SCENARIO")

    assert result["overall_alert_level"] == "critical"
    assert result["summary"]["critical_count"] > 0

    alert_types = [a["type"] for a in result["alerts"]]
    assert "overall_budget_critical" in alert_types
    assert "category_over_budget" in alert_types


def test_pace_scenario():
    """
    Pace scenario should create pace-related alerts even if budget is not yet over.
    """
    print("\n🧪 TEST: Pace Scenario")

    alert_agent = create_alert_agent()
    student = create_test_student()
    goals = create_test_goals("healthy")

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_healthy_analysis(),
        plan=create_mock_plan(),
        tracking_report=create_mock_tracking("pace"),
        goals=goals,
    )

    print_alerts(result, "PACE SCENARIO")

    pace_alerts = [a for a in result["alerts"] if "pace" in a["type"]]
    assert len(pace_alerts) > 0
    assert result["overall_alert_level"] in ["warning", "info"]


def test_savings_alerts():
    """
    Savings alerts:
    - negative cashflow
    - low emergency cushion
    """
    print("\n🧪 TEST: Savings Alerts")

    alert_agent = create_alert_agent()

    student = create_test_student(
        monthly_income=2800.0,
        current_savings=500.0,   # weak cushion
        fixed_expenses=2000.0,   # high fixed expenses
    )

    analysis = create_mock_analysis(
        amount_earned=8400.0,
        amount_spent=9000.0,     # spending > income
        patterns=[],
    )

    result = alert_agent.generate_alerts(
        student=student,
        analysis=analysis,
        plan=create_mock_plan(
            monthly_income=2800.0,
            fixed_monthly_expenses=2000.0,
            total_spend_est_monthly=3000.0,
            disposable_income=100.0,
        ),
        tracking_report=create_mock_tracking("healthy"),
        goals=[],
    )

    print_alerts(result, "SAVINGS ALERTS")

    alert_types = [a["type"] for a in result["alerts"]]
    assert any(t in alert_types for t in [
        "low_savings_rate",
        "negative_cashflow",
        "very_low_emergency_cushion",
        "low_emergency_cushion",
    ])


def test_goal_alerts():
    """
    Goal alerts should detect behind / deadline risk.
    """
    print("\n🧪 TEST: Goal Alerts")

    alert_agent = create_alert_agent()
    student = create_test_student()
    goals = create_test_goals("mixed")

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_healthy_analysis(),
        plan=create_mock_plan(),
        tracking_report=create_mock_tracking("healthy", with_goal_tracking=True),
        goals=goals,
    )

    print_alerts(result, "GOAL ALERTS")

    goal_alerts = [
        a for a in result["alerts"]
        if a["type"] in {"goal_behind_schedule", "goal_deadline_warning", "goal_at_risk"}
    ]
    assert len(goal_alerts) > 0


def test_pattern_alerts():
    """
    Analyzer pattern alerts should appear when warnings/critical patterns exist.
    """
    print("\n🧪 TEST: Pattern Alerts")

    alert_agent = create_alert_agent()
    student = create_test_student()

    analysis = create_mock_analysis(
        patterns=[
            {
                "name": "category_concentration",
                "description": "80% of spending on food",
                "severity": "critical",
                "data": {"category": "food", "pct": 80},
            },
            {
                "name": "subscriptions",
                "description": "Detected 6 subscription services",
                "severity": "info",
                "data": {"subscriptions": [{"merchant": f"service_{i}"} for i in range(6)]},
            },
        ]
    )

    result = alert_agent.generate_alerts(
        student=student,
        analysis=analysis,
        plan=create_mock_plan(),
        tracking_report=create_mock_tracking("healthy"),
        goals=[],
    )

    print_alerts(result, "PATTERN ALERTS")

    pattern_alerts = [a for a in result["alerts"] if a["source"] == "analyzer"]
    assert len(pattern_alerts) > 0
    assert any(a["severity"] == "critical" for a in pattern_alerts)


def test_stress_alerts():
    """
    Structural stress alerts:
    - planned spend above income
    - tiny monthly buffer
    - escalating budget pressure
    """
    print("\n🧪 TEST: Stress Alerts")

    alert_agent = create_alert_agent()

    student = create_test_student(
        monthly_income=2500.0,
        current_savings=800.0,
        fixed_expenses=2400.0,
    )

    plan = create_mock_plan(
        monthly_income=2500.0,
        fixed_monthly_expenses=2400.0,
        total_spend_est_monthly=2600.0,
        disposable_income=50.0,
    )

    tracking = create_mock_tracking("warning")

    result = alert_agent.generate_alerts(
        student=student,
        analysis=create_mock_analysis(patterns=[]),
        plan=plan,
        tracking_report=tracking,
        goals=[],
    )

    print_alerts(result, "STRESS ALERTS")

    stress_alerts = [
        a for a in result["alerts"]
        if a["type"] in {"monthly_plan_under_stress", "low_monthly_buffer", "budget_stress_escalating"}
    ]
    assert len(stress_alerts) > 0


def test_deduplication():
    """
    Deduplication should collapse exact duplicates.
    Since severity is part of the current alert ID key in alert.py,
    higher severity creates a different ID. So we only test exact duplicates here.
    """
    print("\n🧪 TEST: Deduplication")

    alert_agent = create_alert_agent()

    alert1 = alert_agent._make_alert(
        alert_type="test_alert",
        severity="warning",
        title="Test Alert",
        message="This is a test",
        recommended_action="Test action",
        source="tracker",
        category="groceries",
    )

    alert2 = alert_agent._make_alert(
        alert_type="test_alert",
        severity="warning",
        title="Test Alert",
        message="This is a test",
        recommended_action="Test action",
        source="tracker",
        category="groceries",
    )

    alert3 = alert_agent._make_alert(
        alert_type="test_alert",
        severity="critical",
        title="Test Alert",
        message="This is a test",
        recommended_action="Test action",
        source="tracker",
        category="groceries",
    )

    assert alert1.id == alert2.id
    assert alert1.id != alert3.id

    deduped = alert_agent._deduplicate_alerts([alert1, alert2])
    assert len(deduped) == 1
    assert deduped[0].severity == "warning"

    print("✅ Deduplication works correctly for exact duplicates")


def test_sorting():
    """
    Alerts should sort by severity descending, then title.
    """
    print("\n🧪 TEST: Alert Sorting")

    alert_agent = create_alert_agent()

    alerts = [
        alert_agent._make_alert(
            alert_type="type_c",
            severity="info",
            title="C Alert",
            message="Test",
            recommended_action="Test",
            source="tracker",
        ),
        alert_agent._make_alert(
            alert_type="type_a",
            severity="critical",
            title="A Alert",
            message="Test",
            recommended_action="Test",
            source="tracker",
        ),
        alert_agent._make_alert(
            alert_type="type_b",
            severity="warning",
            title="B Alert",
            message="Test",
            recommended_action="Test",
            source="tracker",
        ),
    ]

    sorted_alerts = alert_agent._sort_alerts(alerts)

    assert sorted_alerts[0].severity == "critical"
    assert sorted_alerts[1].severity == "warning"
    assert sorted_alerts[2].severity == "info"

    print("✅ Sorting works correctly")


def test_overall_level():
    """
    Overall alert level should reflect highest severity present.
    """
    print("\n🧪 TEST: Overall Alert Level")

    alert_agent = create_alert_agent()

    alerts_critical = [
        alert_agent._make_alert(
            alert_type="test",
            severity="critical",
            title="Test",
            message="Test",
            recommended_action="Test",
            source="tracker",
        )
    ]
    assert alert_agent._get_overall_alert_level(alerts_critical) == "critical"

    alerts_warning = [
        alert_agent._make_alert(
            alert_type="test",
            severity="warning",
            title="Test",
            message="Test",
            recommended_action="Test",
            source="tracker",
        )
    ]
    assert alert_agent._get_overall_alert_level(alerts_warning) == "warning"

    alerts_info = [
        alert_agent._make_alert(
            alert_type="test",
            severity="info",
            title="Test",
            message="Test",
            recommended_action="Test",
            source="tracker",
        )
    ]
    assert alert_agent._get_overall_alert_level(alerts_info) == "info"

    assert alert_agent._get_overall_alert_level([]) == "info"

    print("✅ Overall level calculation works correctly")


# =========================================================
# MAIN RUNNER
# =========================================================

def run_all_tests():
    """
    Run the full alert-agent test suite.
    """
    print("=" * 80)
    print("🧪🧪🧪 ALERT AGENT COMPREHENSIVE TEST SUITE 🧪🧪🧪")
    print("=" * 80)

    test_healthy_scenario()
    test_warning_scenario()
    test_critical_scenario()
    test_pace_scenario()
    test_savings_alerts()
    test_goal_alerts()
    test_pattern_alerts()
    test_stress_alerts()

    test_deduplication()
    test_sorting()
    test_overall_level()

    print("\n" + "=" * 80)
    print("✅ ALL ALERT AGENT TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()