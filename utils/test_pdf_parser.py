"""
🧪 Test PDF parser with various bank statement formats
"""

from utils.pdf_parser import (
    parse_bank_text_to_transactions,
    detect_bank_format,
    calculate_confidence,
    deduplicate_transactions
)
from datetime import date

def test_chase_format():
    """Test Chase bank statement format"""
    print("\n🏦 TEST: Chase Format")
    print("=" * 50)
    
    sample = """
    CHASE CREDIT CARD STATEMENT
    Account: 1234
    Date        Description                 Amount
    03/01/2026  STARBUCKS #12345            4.50
    03/02/2026  AMAZON.COM*KINDLE           29.99
    03/03/2026  PAYMENT THANK YOU           -500.00
    03/04/2026  NETFLIX.COM                  15.99
    """
    
    format_name = detect_bank_format(sample)
    print(f"Detected format: {format_name}")
    
    result = parse_bank_text_to_transactions(sample, student_id="STU001")
    
    print(f"\n📊 Results:")
    print(f"   Transactions: {len(result.transactions)}")
    print(f"   Skipped: {len(result.skipped_lines)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   LLM Calls: {result.llm_calls}")
    
    for tx in result.transactions:
        print(f"\n   ✅ {tx.date}: ${tx.amount:.2f}")
        print(f"      {tx.description[:30]}...")
        print(f"      Category: {tx.category}")
        print(f"      Type: {tx.transaction_type.value}")

def test_boa_format():
    """Test Bank of America format"""
    print("\n🏦 TEST: Bank of America Format")
    print("=" * 50)
    
    sample = """
    Bank of America
    Account Ending: 1234
    03/01/2026   POS Debit   Walmart          $45.67
    03/02/2026   Online Trsf  Rent            $1200.00
    03/03/2026   Deposit      Payroll         $2000.00
    03/04/2026   ATM Withdrawal               $60.00
    """
    
    result = parse_bank_text_to_transactions(sample, student_id="STU001")
    
    print(f"\n📊 Results:")
    print(f"   Transactions: {len(result.transactions)}")
    for tx in result.transactions:
        print(f"\n   ✅ {tx.date}: ${tx.amount:.2f}")
        print(f"      {tx.description[:30]}...")
        print(f"      Category: {tx.category}")

def test_negative_amounts():
    """Test handling of negative amounts"""
    print("\n🏦 TEST: Negative Amounts")
    print("=" * 50)
    
    sample = """
    03/01/2026  Amazon.com         (29.99)  # Parentheses
    03/02/2026  Refund             15.00    # Positive
    03/03/2026  CHECK CARD -45.67           # Negative sign
    """
    
    result = parse_bank_text_to_transactions(sample, student_id="STU001")
    
    for tx in result.transactions:
        print(f"\n   {tx.date}: ${tx.amount:.2f} ({tx.transaction_type.value})")

def test_deduplication():
    """Test transaction deduplication"""
    print("\n🏦 TEST: Deduplication")
    print("=" * 50)
    
    from schemas.transaction import Transaction, TransactionType
    from datetime import date
    
    # Create duplicate transactions
    tx1 = Transaction(
        transaction_id="taxn1",
        student_id="STU001",
        amount=45.67,
        transaction_type=TransactionType.EXPENSE,
        date=date(2026, 3, 1),
        description="Walmart",
        merchant="Walmart",
        category="groceries",
        payment_method="debit_card",
        source="pdf",
        confidence="high"
    )
    
    tx2 = Transaction(
        transaction_id="taxn2",  # Different ID
        student_id="STU001",
        amount=45.67,
        transaction_type=TransactionType.EXPENSE,
        date=date(2026, 3, 1),
        description="WAL-MART",
        merchant="Walmart",
        category="groceries",
        payment_method="debit_card",
        source="pdf",
        confidence="high"
    )
    
    duplicates = [tx1, tx2]
    print(f"Before dedup: {len(duplicates)} transactions")
    
    unique = deduplicate_transactions(duplicates)
    print(f"After dedup: {len(unique)} transactions")

def test_confidence_calculation():
    """Test confidence scoring"""
    print("\n🏦 TEST: Confidence Scoring")
    print("=" * 50)
    
    test_cases = [
        ("rules", "high", "low", "high"),
        ("llm_fallback", "low", "high", "high"),
        ("llm_fallback", "low", "medium", "medium"),
        ("rules", "low", "low", "low"),
    ]
    
    for parser, cat_conf, llm_conf, expected in test_cases:
        result = calculate_confidence(parser, cat_conf, llm_conf)
        print(f"   {parser:12} {cat_conf:6} + {llm_conf:6} → {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"

def test_edge_cases():
    """Test edge cases"""
    print("\n🏦 TEST: Edge Cases")
    print("=" * 50)
    
    # Empty input
    result = parse_bank_text_to_transactions("", student_id="STU001")
    print(f"   Empty input: {len(result.errors)} errors")
    
    # Gibberish
    result = parse_bank_text_to_transactions("asdf asdf asdf", student_id="STU001")
    print(f"   Gibberish: {len(result.skipped_lines)} skipped")
    
    # Mixed content
    sample = """
    This is a header line
    03/01/2026  Starbucks  4.50
    This is a footer
    03/02/2026  Amazon  29.99
    """
    result = parse_bank_text_to_transactions(sample, student_id="STU001")
    print(f"   Mixed content: {len(result.transactions)} transactions, {len(result.skipped_lines)} skipped")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTING PDF PARSER")
    print("=" * 60)
    
    test_chase_format()
    test_boa_format()
    test_negative_amounts()
    test_deduplication()
    test_confidence_calculation()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)