"""
🧪 TEST ANALYZER AGENT - Comprehensive tests
"""

from agents.analyzer import create_analyzer, SpendingPattern
from schemas.transaction import Transaction, TransactionType
from schemas.student import Student
from schemas.budget import Budget, BudgetCategory, BudgetPeriod
from datetime import date, timedelta
import random
import uuid
random.seed(42)
def generate_id():
    return str(uuid.uuid4())[:8]

def create_test_student():
    return Student(
        student_id="STU001",
        name="Test Student",
        email="test@uni.edu",
        university="Test University",
        graduation_year=2026,
        monthly_income=2000,
        current_savings=3000,
        risk_profile="moderate"
    )

def create_test_transactions():
    """Create 90 days of realistic transactions"""
    transactions = []
    today = date.today()
    
    # Daily coffee (expense)
    for i in range(90):
        # Skip some days to make it realistic
        if random.random() > 0.7:
            continue
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id="STU001",
            amount=4.50,
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=i),
            description="Starbucks",
            merchant="Starbucks",
            category="coffee",
            payment_method="credit_card",
            source="manual",
            confidence="high"
        ))
    
    # Weekly groceries
    for i in range(0, 90, 7):
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id="STU001",
            amount=random.uniform(45, 65),
            transaction_type=TransactionType.EXPENSE,
            date=today - timedelta(days=i),
            description="WEEKLY GROCERIES",
            merchant="Walmart",
            category="groceries",
            payment_method="debit_card",
            source="manual",
            confidence="high"
        ))
    
    # Monthly subscriptions
    for months in range(3):
        for service, amount in [("NETFLIX", 15.99), ("SPOTIFY", 9.99), ("AMAZON PRIME", 14.99)]:
            transactions.append(Transaction(
                transaction_id=generate_id(),
                student_id="STU001",
                amount=amount,
                transaction_type=TransactionType.EXPENSE,
                date=today - timedelta(days=months*30 + random.randint(1, 5)),
                description=service,
                merchant=service,
                category="streaming" if "NETFLIX" in service else "amazon",
                payment_method="credit_card",
                source="manual",
                confidence="high"
            ))
    
    # Monthly income (payday)
    for months in range(3):
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id="STU001",
            amount=2000,
            transaction_type=TransactionType.INCOME,
            date=today - timedelta(days=months*30 + 5),
            description="PAYROLL DIRECT DEPOSIT",
            merchant="Employer",
            category="salary",
            payment_method="direct_deposit",
            source="pdf",
            confidence="high"
        ))
    
    return transactions

def test_analyzer():
    print("=" * 70)
    print("🧪 TESTING ANALYZER AGENT")
    print("=" * 70)
    
    analyzer = create_analyzer()
    student = create_test_student()
    transactions = create_test_transactions()
    
    print(f"\n📊 Analyzing {len(transactions)} transactions...")
    
    # Test with full analysis
    results = analyzer.analyze_student(student, transactions, lookback_days=90)
    
    print(f"\n📈 SUMMARY")
    print("-" * 40)
    print(f"   Total spent: ${results['summary']['amount_spent']:,.2f}")
    print(f"   Total earned: ${results['summary']['amount_earned']:,.2f}")
    print(f"   Net flow: ${results['summary']['net_flow']:,.2f}")
    print(f"   Avg daily spend: ${results['summary']['avg_daily_spend_30d']:.2f}")
    
    print(f"\n🔍 TOP CATEGORIES")
    print("-" * 40)
    for cat in results['summary']['top_categories']:
        print(f"   • {cat['category']}: ${cat['amount']:,.2f} ({cat['share_pct']}%)")
    
    print(f"\n🔄 PATTERNS FOUND: {len(results['patterns'])}")
    print("-" * 40)
    for pattern in results['patterns']:
        emoji = "🔴" if pattern['severity'] == "critical" else "🟡" if pattern['severity'] == "warning" else "🟢"
        print(f"   {emoji} {pattern['description']}")
        if pattern.get('data'):
            for k, v in pattern['data'].items():
                print(f"      {k}: {v}")
    
    print(f"\n📈 TRENDS: {len(results['trends'])}")
    print("-" * 40)
    for trend in results['trends']:
        print(f"   • {trend['description']}")
    
    print(f"\n🚨 ANOMALIES: {len(results['anomalies'])}")
    print("-" * 40)
    for anomaly in results['anomalies'][:3]:  # Show first 3
        print(f"   • {anomaly['date']}: ${anomaly['amount']} ({anomaly['description']})")
    
    print(f"\n💡 ADVICE: {len(results['advice'])}")
    print("-" * 40)
    for advice in results['advice']:
        print(f"   • {advice}")

def test_pattern_detection():
    """Test specific pattern detection methods"""
    print("\n" + "=" * 70)
    print("🧪 TESTING PATTERN DETECTION")
    print("=" * 70)
    
    analyzer = create_analyzer()
    
    # Test weekend spending
    transactions = []
    base_date = date.today()
    
    # Add weekend transactions (higher amounts)
    for i in range(10):
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id="STU001",
            amount=100.0,
            transaction_type=TransactionType.EXPENSE,
            date=base_date - timedelta(days=i*7 + (5 if i%2 else 6)),  # Weekends
            description="Weekend fun",
            merchant="Various",
            category="entertainment",
            payment_method="credit_card",
            source="bank_api",
            confidence="high"
        ))
    
    # Add weekday transactions (lower amounts)
    for i in range(10):
        transactions.append(Transaction(
            transaction_id=generate_id(),
            student_id="STU001",
            amount=30.0,
            transaction_type=TransactionType.EXPENSE,
            date=base_date - timedelta(days=i*7 + 2),  # Weekdays
            description="Weekday necessities",
            merchant="Various",
            category="food",
            payment_method="debit_card",
            source="manual",
            confidence="high"
        ))
    
    pattern = analyzer._weekend_spend(transactions)
    print(f"\n📅 Weekend spending test:")
    print(f"   Pattern detected: {pattern is not None}")
    if pattern:
        print(f"   {pattern.description}")
        print(f"   Data: {pattern.data}")

if __name__ == "__main__":
    test_analyzer()
    test_pattern_detection()