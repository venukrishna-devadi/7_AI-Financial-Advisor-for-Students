"""
💸 TRANSACTION SCHEMA - Represents a single financial transaction
Core unit: every expense, income, or transfer is a Transaction.
"""

# from __future__ import annotations
# from datetime import datetime
# from datetime import date as date_type
# from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
# from typing import List, Dict, Optional, Literal, Any
# from enum import Enum


# # === LITERALS & ENUMS ===
# # Constrained vocabularies keep data consistent across agents/UI.
# PaymentMethod = Literal[
#     "cash", "credit_card", "debit_card", "venmo", "zelle", "paypal", "bank_transfer","other", "direct_deposit"
# ]
# Category = Literal[
#     "food", "groceries", "dining_out", "coffee",
#     "housing", "rent", "utilities", "internet", "phone",
#     "transport", "gas", "uber", "public_transit",
#     "entertainment", "streaming", "games", "movies",
#     "shopping", "clothing", "electronics", "amazon",
#     "education", "tuition", "books", "supplies",
#     "health", "medical", "gym", "pharmacy",
#     "personal_care", "haircut", "cosmetics",
#     "travel", "flights", "hotels",
#     "income", "salary", "gift", "refund",
#     "transfer", "savings", "investment",
#     "other","student_loan", "credit_card", "car_payment", "insurance"
# ]

# ConfidenceLevel = Literal["high", "medium", "low"]

# class TransactionType(str, Enum):
#     """Money direction ennum"""
#     EXPENSE = "expense"
#     INCOME = "income"
#     TRANSFER = "transfer"

# class Transaction(BaseModel):
#     """
#     💰 Single financial event.
#     Agents work in lists of these; graph stores them in state.
#     """
#     transaction_id: str = Field(
#         ..., min_length=5, max_length=60, description= "Unique id of the transaction"
#     )
#     student_id: str = Field(..., description="Owner of this transaction")
#     amount: float = Field(..., gt = 0, description="Absolute amount; sign from type")
#     transaction_type: TransactionType = Field(..., description="Expense/income/transfer")
#     date: date_type = Field(..., description= "Date it occured (not when we added it)")

#     description: str = Field(default= "",  max_length= 200, description= "Description of the transaction")
#     merchant: Optional[str] = Field(default= None, max_length=100)
#     category: Category = Field(default="other")
#     payment_method: PaymentMethod = Field(default="cash")

#     # source ttacking

#     source: Literal["manual", "pdf", "screenshot", "bank_api", "text"] = Field(
#         default= "manual", description="How we got this txn"
#     )
#     confidence: ConfidenceLevel = Field(default="high")
#     raw_data: Optional[Dict[str, Any]] = Field(default= None, description= "original payload")

#     # Recurring transactions
#     is_recurring: bool = Field(default= False)
#     recurring_frequency: Optional[Literal["weekly", "monthly", "biweekly", "yearly"]] = Field(default=None)

#     # Metadata
#     created_at: datetime = Field(default_factory= datetime.now)
#     notes: str= Field(default="", description="What is transaction about", max_length=200)
#     tags: list[str] = Field(default_factory= list)

#     is_subscription: bool = Field(default= False,
#                                   description="Subscription services auto-set recurring")

#     #### Validators
#     @field_validator("amount")
#     @classmethod
#     def validate_amount(cls, v: float) -> float:
#         """Reject absurb values and also catch OCR or other parsing junk"""
#         if v> 1_000_000:
#             raise ValueError("Please enter realistic values")
#         return v
    
#     @field_validator("merchant")
#     @classmethod
#     def validate_merchant(cls, v: Optional[str])-> Optional[str]:
#         """Normalize whitespaces and title-case merchant names"""
#         if v is None:
#             return v
#         return " ".join(v.strip().split()).title()
    
#     @field_validator("tags")
#     @classmethod
#     def validate_tags(cls, v: list[str])-> list[str]:
#         """Lowercase, strip entities, mantain order"""
#         seen = set()
#         cleaned: list[str] = []
#         for t in v:
#             t2 = t.strip().lower()
#             if t2 and t2 not in seen:
#                 cleaned.append(t2)
#                 seen.add(t2)
#         return cleaned
    
#     @field_validator("date")
#     @classmethod
#     def validate_date(cls, v: date_type) -> date_type:
#         """Warn if the transaction is not a future dated transaction"""
#         if v > date_type.today():
#             raise ValueError("Transaction date cannot be greater than today")
#         return v
    
#     @field_validator("recurring_frequency")
#     @classmethod
#     def validate_recurring_freq(cls, v: Optional[str], info: ValidationInfo):
#         "If frequency is set, ensure its is_recurring = True"
#         if v is not None and not info.data.get("is_recurring", False):
#             raise ValueError("recurring_frequency required is_recurring = True")
#         return v
    
#     @model_validator(mode="after")
#     def handle_subscription(self) -> "Transaction":
#         """If is_subscription=True, auto-set is_recurring and suggest frequency"""
#         if self.is_subscription:
#             self.is_recurring = True
#             if self.recurring_frequency is None:
#                 self.recurring_frequency = "monthly"
#         return self
    
#     @property
#     def signed_amount(self) -> float:
#         """ + for income, - for expense, 0 for transfer"""
#         if self.transaction_type == TransactionType.EXPENSE:
#             return -self.amount
#         if self.transaction_type == TransactionType.INCOME:
#             return self.amount
#         return 0.0
#     @property
#     def is_expense(self) -> bool:
#         return self.transaction_type == TransactionType.EXPENSE
#     @property
#     def month_key(self) -> str:
#         return self.date.strftime("%Y-%m")
#     @property
#     def css_class(self) -> str:
#         """Return CSS class for styling in UI"""
#         if self.is_expense:
#             return "expense-row"
#         if self.transaction_type == TransactionType.INCOME:
#             return "income-row"
#         return "transfer-row"
#     def short_description(self) -> str:
#         sign = "-" if self.is_expense else "+" if self.transaction_type == TransactionType.INCOME else "<->"
#         merchant = self.merchant or "Unknown"
#         return f"{sign}${self.amount:.2f} at {merchant} [{self.category}] on {self.date}"


from __future__ import annotations

from datetime import datetime
from datetime import date as date_type
from enum import Enum
from typing import Optional, Literal, Any, Dict

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo


# =========================================================
# LITERALS / ENUMS
# =========================================================

PaymentMethod = Literal[
    "cash",
    "credit_card",
    "debit_card",
    "venmo",
    "zelle",
    "paypal",
    "bank_transfer",
    "other",
    "direct_deposit",
]

Category = Literal[
    "food", "groceries", "dining_out", "coffee",
    "housing", "rent", "utilities", "internet", "phone",
    "transport", "gas", "uber", "public_transit",
    "entertainment", "streaming", "games", "movies",
    "shopping", "clothing", "electronics", "amazon",
    "education", "tuition", "books", "supplies",
    "health", "medical", "gym", "pharmacy",
    "personal_care", "haircut", "cosmetics",
    "travel", "flights", "hotels",
    "income", "salary", "gift", "refund",
    "transfer", "savings", "investment",
    "other",
    "student_loan", "credit_card", "car_payment", "insurance",
]

ConfidenceLevel = Literal["high", "medium", "low"]


class TransactionType(str, Enum):
    """Money direction enum."""
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


# =========================================================
# MODEL
# =========================================================

class Transaction(BaseModel):
    """
    Single financial event.
    """

    transaction_id: str = Field(
        ...,
        min_length=5,
        max_length=60,
        description="Unique id of the transaction",
    )
    student_id: str = Field(..., description="Owner of this transaction")
    amount: float = Field(..., gt=0, description="Absolute amount; sign comes from transaction_type")
    transaction_type: TransactionType = Field(..., description="Expense / income / transfer")
    date: date_type = Field(..., description="Date it occurred")

    description: str = Field(default="", max_length=200, description="Description of the transaction")
    merchant: Optional[str] = Field(default=None, max_length=100)
    category: Category = Field(default="other")
    payment_method: PaymentMethod = Field(default="cash")

    source: Literal["manual", "pdf", "screenshot", "bank_api", "text"] = Field(
        default="manual",
        description="How this transaction was captured",
    )
    confidence: ConfidenceLevel = Field(default="high")
    raw_data: Optional[Dict[str, Any]] = Field(default=None, description="Original payload")

    is_recurring: bool = Field(default=False)
    recurring_frequency: Optional[Literal["weekly", "monthly", "biweekly", "yearly"]] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    notes: str = Field(default="", max_length=200, description="Extra notes")
    tags: list[str] = Field(default_factory=list)

    is_subscription: bool = Field(
        default=False,
        description="If True, transaction is treated as recurring subscription",
    )

    # =====================================================
    # VALIDATORS
    # =====================================================

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v > 1_000_000:
            raise ValueError("Please enter realistic values")
        return v

    @field_validator("merchant")
    @classmethod
    def validate_merchant(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        cleaned = " ".join(v.strip().split())
        return cleaned.title() if cleaned else None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        seen = set()
        cleaned: list[str] = []
        for t in v:
            t2 = t.strip().lower()
            if t2 and t2 not in seen:
                cleaned.append(t2)
                seen.add(t2)
        return cleaned

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: date_type) -> date_type:
        if v > date_type.today():
            raise ValueError("Transaction date cannot be greater than today")
        return v

    @field_validator("recurring_frequency")
    @classmethod
    def validate_recurring_freq(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if v is not None and not info.data.get("is_recurring", False):
            raise ValueError("recurring_frequency requires is_recurring=True")
        return v

    @model_validator(mode="after")
    def handle_subscription(self) -> "Transaction":
        if self.is_subscription:
            self.is_recurring = True
            if self.recurring_frequency is None:
                self.recurring_frequency = "monthly"
        return self

    # =====================================================
    # HELPERS / PROPERTIES
    # =====================================================

    @property
    def signed_amount(self) -> float:
        """+ for income, - for expense, 0 for transfer."""
        if self.transaction_type == TransactionType.EXPENSE:
            return -self.amount
        if self.transaction_type == TransactionType.INCOME:
            return self.amount
        return 0.0

    @property
    def is_expense(self) -> bool:
        return self.transaction_type == TransactionType.EXPENSE

    @property
    def month_key(self) -> str:
        return self.date.strftime("%Y-%m")

    @property
    def css_class(self) -> str:
        if self.is_expense:
            return "expense-row"
        if self.transaction_type == TransactionType.INCOME:
            return "income-row"
        return "transfer-row"

    def short_description(self) -> str:
        sign = "-" if self.is_expense else "+" if self.transaction_type == TransactionType.INCOME else "<->"
        merchant = self.merchant or "Unknown"
        return f"{sign}${self.amount:.2f} at {merchant} [{self.category}] on {self.date}"