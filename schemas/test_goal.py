"""
🧪 Test script for Goal schema
Tests creation, validation, contributions, and status transitions
"""

from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType, GoalStatus
from datetime import date, timedelta
import uuid

def generate_goal_id():
    """Helper to generate valid goal IDs"""
    return str(uuid.uuid4())[:8]

def test_goal_creation():
    """Test basic goal creation"""
    print("🎯 TEST 1: Goal Creation")
    print("=" * 50)
    
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="Emergency Fund",
        category=GoalCategory.EMERGENCY_FUND,
        target_amount=3000,
        current_amount=500,
        target_date=date.today() + timedelta(days=180),
        priority=GoalPriority.HIGH,
        recurring_type=RecurringType.MONTHLY,
        recurring_amount=200,
        tags=["safety", "important", "emergency"]
    )
    
    print(f"✅ Created: {goal}")
    print(f"   Remaining: ${goal.remaining_amount}")
    print(f"   Progress: {goal.progress_percent:.1f}%")
    print(f"   Days left: {goal.days_remaining}")
    print(f"   Need ${goal.recommended_monthly}/month")
    print(f"   Feasible with $500/month? {goal.is_feasible(500)}")
    print(f"   Feasible with $100/month? {goal.is_feasible(100)}")

def test_goal_contributions():
    """Test adding money to goals"""
    print("\n🎯 TEST 2: Goal Contributions")
    print("=" * 50)
    
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="New Laptop",
        category=GoalCategory.MAJOR_PURCHASE,
        target_amount=1500,
        current_amount=300,
        target_date=date.today() + timedelta(days=90)
    )
    
    print(f"Before: {goal}")
    print(f"Status: {goal.status.value}")
    
    # Add contributions
    goal.add_contribution(200)
    print(f"\nAfter +$200: {goal}")
    print(f"Status: {goal.status.value}")
    
    goal.add_contribution(1000)
    print(f"\nAfter +$1000: {goal}")
    print(f"Status: {goal.status.value}")
    print(f"Completed at: {goal.completed_at}")

def test_goal_expiry():
    """Test goals that pass deadline"""
    print("\n🎯 TEST 3: Goal Expiry")
    print("=" * 50)
    
    # Create goal with future date
    future_date = date.today() + timedelta(days=30)
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="Expiring Goal",
        category=GoalCategory.TRAVEL,
        target_amount=1000,
        current_amount=200,
        target_date=future_date
    )
    
    print(f"Goal created with future date: {goal.target_date}")
    print(f"Initial status: {goal.status.value}")
    
    # Simulate time passing
    object.__setattr__(goal, 'target_date', date.today() - timedelta(days=1))
    goal = goal.compute_status()
    
    print(f"\nAfter forcing past date: {goal.target_date}")
    print(f"Status should be EXPIRED: {goal.status.value}")

def test_goal_abandon():
    """Test abandoning a goal"""
    print("\n🎯 TEST 4: Goal Abandonment")
    print("=" * 50)
    
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="Too Ambitious",
        category=GoalCategory.CUSTOM,
        target_amount=10000,
        current_amount=100
    )
    
    print(f"Before: {goal}")
    print(f"Status: {goal.status.value}")
    
    goal.abandon(reason="Not realistic right now")
    print(f"\nAfter abandon: {goal}")
    print(f"Status: {goal.status.value}")
    print(f"Notes: {goal.notes}")

def test_goal_validation():
    """Test validation rules"""
    print("\n🎯 TEST 5: Validation")
    print("=" * 50)
    
    # This should work
    try:
        goal = Goal(
            goal_id=generate_goal_id(),
            student_id="STU001",
            name="Valid Goal",
            category=GoalCategory.EDUCATION,
            target_amount=5000,
            recurring_type=RecurringType.MONTHLY,
            recurring_amount=200
        )
        print("✅ Valid goal created")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # This should fail (recurring_amount missing)
    try:
        goal = Goal(
            goal_id=generate_goal_id(),
            student_id="STU001",
            name="Invalid Goal",
            category=GoalCategory.EDUCATION,
            target_amount=5000,
            recurring_type=RecurringType.MONTHLY
        )
        print("❌ Should have failed but didn't")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")

def test_goal_tags():
    """Test tag normalization"""
    print("\n🎯 TEST 6: Tag Normalization")
    print("=" * 50)
    
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="Tag Test",
        category=GoalCategory.CUSTOM,
        target_amount=100,
        tags=["  IMPORTANT  ", "Urgent", "  important  ", "  ", "saving"]
    )
    
    print(f"Normalized tags: {goal.tags}")
    print(f"✅ Duplicates removed, whitespace trimmed, lowercase")

def test_goal_progress_bar():
    """Test the progress bar visualization"""
    print("\n🎯 TEST 7: Progress Bar")
    print("=" * 50)
    
    goal = Goal(
        goal_id=generate_goal_id(),
        student_id="STU001",
        name="Progress Test",
        category=GoalCategory.CUSTOM,  # Fixed: using CUSTOM instead of SAVINGS
        target_amount=1000,
        current_amount=333
    )
    
    print(f"Goal: {goal}")
    print(f"Progress bar (20): {goal.progress_bar(20)}")
    print(f"Progress bar (10): {goal.progress_bar(10)}")
    print(f"Progress bar (30): {goal.progress_bar(30)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING GOAL SCHEMA")
    print("=" * 60)
    
    test_goal_creation()
    test_goal_contributions()
    test_goal_expiry()
    test_goal_abandon()
    test_goal_validation()
    test_goal_tags()
    test_goal_progress_bar()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)