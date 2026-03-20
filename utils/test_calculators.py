"""
🧪 Test suite for financial calculators
"""

from utils.calculators import (
    to_monthly_amount,
    compound_future_value,
    monthly_payment_for_loan,
    months_to_payoff,
    rule_50_30_20,
    emergency_fund_months
)

def test_to_monthly_amount():
    """Test income frequency conversion"""
    assert to_monthly_amount(1000, "monthly") == 1000.0
    assert to_monthly_amount(200, "weekly") == round(200 * 52 / 12, 2)
    assert to_monthly_amount(500, "biweekly") == round(500 * 26 / 12, 2)
    print("✅ Income conversion works")

def test_compound_interest():
    """Test investment growth projections"""
    # $1000 at 7% for 10 years = $1967.15
    result = compound_future_value(1000, 0.07, 10, contributions_per_year=1)
    assert round(result, 2) == 1967.15
    print("✅ Compound interest works")

def test_loan_payment():
    """Test loan calculations"""
    # $10,000 loan at 5% for 3 years (36 months)
    payment = monthly_payment_for_loan(10000, 0.05, 36)
    assert round(payment, 2) == 299.71
    print("✅ Loan payment calculation works")

def test_emergency_fund():
    """Test emergency fund runway"""
    months = emergency_fund_months(6000, 2000)
    assert months == 3.0
    print("✅ Emergency fund calculation works")

def test_budget_rule():
    """Test 50/30/20 budget rule"""
    budget = rule_50_30_20(5000)
    assert budget["needs"] == 2500.0
    assert budget["wants"] == 1500.0
    assert budget["savings"] == 1000.0
    print("✅ Budget rule works")

if __name__ == "__main__":
    test_to_monthly_amount()
    test_compound_interest()
    test_loan_payment()
    test_emergency_fund()
    test_budget_rule()
    print("\n🎉 ALL CALCULATOR TESTS PASSED!")