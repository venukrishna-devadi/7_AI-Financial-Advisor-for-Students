from schemas.transaction import Transaction, TransactionType
from datetime import date

# print("Test 1: Vlid expenses \n")

# try:
#     t1 = Transaction(
#         transaction_id="txn_20240227_001",
#         student_id="007",
#         amount=10,
#         transaction_type= TransactionType.EXPENSE,
#         date=date(2026, 2, 27),
#         merchant="EXON",
#         category="gas",
#         payment_method="cash",
#         source="manual",
#         confidence="high",
#         tags=["Gas for car"]
#     )
#     print("Created:", t1)
#     print("Signed amount:", t1.signed_amount)
#     print("Short:", t1.short_description())
#     print("Tags normalized:", t1.tags)

# except Exception as e:
#     print("Failed:", e)


# print("\n=== Test 2: Future date (should fail) ===")

# try:
#     t1 = Transaction(
#         transaction_id="txn_20240227_001",
#         student_id="007",
#         amount=10,
#         transaction_type= TransactionType.EXPENSE,
#         date=date(2026, 3, 27),
#         merchant="EXON",
#         category="gas",
#         payment_method="cash",
#         source="manual",
#         confidence="high",
#         tags=["Gas for car"]
#     )
#     print("Created:", t1)
#     print("Signed amount:", t1.signed_amount)
#     print("Short:", t1.short_description())
#     print("Tags normalized:", t1.tags)

# except Exception as e:
#     print("Failed:", e)


# print("\n=== Test 3: Recurring flag logic (should fail) ===")
# try:
#     t3 = Transaction(
#         transaction_id="txn_recur_bad",
#         student_id="stu_001",
#         amount=1000,
#         transaction_type=TransactionType.INCOME,
#         date=date(2025, 8, 1),
#         is_recurring=False,
#         recurring_frequency="monthly"  # invalid without flag
#     )
#     print("Created:", t3)
# except Exception as e:
#     print("Failed transaction", e)

t2 = Transaction(
    transaction_id="txn_sub_001",
    student_id="007",
    amount=15.99,
    transaction_type=TransactionType.EXPENSE,
    date=date(2026, 2, 27),
    merchant="Netflix",
    category="streaming",
    is_subscription=True   # ← only set this
)
print("Is recurring:", t2.is_recurring)           # True ✅ (auto-set)
print("Frequency:", t2.recurring_frequency)