"""
📋 STUDENT SCHEMA - Core data model for a student
This file defines what a "Student" means in our system
"""

from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field, field_validator
from typing import List, Tuple, Optional, Literal, Dict, Any

IncomeFrequency = Literal["weekly", "biweekly", "monthly"]
RiskProfile = Literal["conservative", "moderate", "aggressive"]
StudentStatus = Literal["student", "employed", "unemployed"]

class Student(BaseModel):
    """
    🎓 Student model for the Financial Advisor project.
    This is a CONTRACT file—every agent and UI component imports it.
    """
    # ===== IDENTITY =====
    # Unique ID allows multiple students in storage; name is for display.

    student_id: str = Field(..., min_length=3, max_length=64,
                            description="Unique id for the student")
    
    name: str = Field(..., min_length=2, max_length=80, description="Full Name")
    age: Optional[int] = Field(default= None, ge= 13, le= 70, description="Age if provided")
    status: StudentStatus = Field(default="student", description="Life status")

    currency: str = Field(default="USD", min_length=3, max_length=5, description="3 Letter Currency identifeier code")
    monthly_income: float = Field(
        default= 0.0, ge= 0.0,
        description="Normalized Monthly income other (convert other frequencies to this format)"
    )
    current_savings: float = Field(
        default=0.0, ge=0.0,
        description="Current savings balance available for emergency fund / goals"
    )
    income_frequency: IncomeFrequency = Field(
        default= "monthly", description= "Original pay frequency for UI reference"
    )

    # Risk profile can guide agent suggestions (e.g., savings vs spending).
    risk_profile: RiskProfile = Field(default="moderate")

    # ===== PREFERENCES & CONSTRAINTS =====
    # Categories the student cares about (normalized to lowercase, unique).
    preferred_categories: List[str] = Field(default_factory=list)
    # Recurring bills: rent, phone, insurance. Keys are labels; values are monthly amounts.
    fixed_monthly_expenses: Dict[str, float] =Field(
        default_factory=dict,
        description="Recurring Monthly Expenses"
    )

    # ===== METADATA =====
    created_on: date = Field(
        default_factory= date.today, description="Profile creation date"
    )

     # -----------------------------
    # Validators — clean/protect data on creation
    # -----------------------------
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str)->str:
        """Ensure Currency is a 3 letter code (e.g: USD)"""
        v=v.upper().strip()
        if len(v)!= 3 or not v.isalpha():
            raise ValueError("currency must be a 3- Letter code (e.g : USD)")
        return v
    
    @field_validator("preferred_categories")
    @classmethod
    def normalize_categories(cls, v:List[str])-> List[str]:
        """Lowercase, strip, and deduplicate categories while preserving order."""
        seen = set()
        cleaned: List[str] = []
        for item in v:
            item2 = item.strip().lower()
            if item2 and item2 not in seen:
                cleaned.append(item2)
                seen.add(item2)
        return cleaned
    
    @field_validator("fixed_monthly_expenses")
    @classmethod
    def validate_fixed_expenses(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Garuntee no negative expense amounts."""
        for k, amnt in v.items():
            if amnt < 0:
                raise ValueError(f"Entered amount fixed_monthly_expenses ['{k}'] cannot be negative")
        return v
    
     # -----------------------------
    # Helper methods — pure calculations agents/UI can reuse
    # -----------------------------

    def total_fixed_expenses(self) -> float:
        """Sum of all the monthly recurring expenses"""
        return (float(sum(self.fixed_monthly_expenses.values())))
    
    def estimated_disposable_income(self) -> float:
        """Income remaining after fixed bills (never negative)."""
        return float(max(0.0, self.monthly_income - self.total_fixed_expenses()))

    def disposable_income_status(self) -> str:
        """Return a readable status about disposable income."""
        disposable = self.estimated_disposable_income()
        if disposable == 0.0:
            if self.total_fixed_expenses() > self.monthly_income:
                return "⚠️ Fixed expenses exceed income—no disposable funds left"
            return "ℹ️ No disposable income (expenses = income)"
        return f"✅ Disposable income available: {disposable:.2f} {self.currency}"
