# schemas/budget.py
"""
🧾 BUDGET SCHEMA — Spending plan for a student over a period.
"""

from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal, Dict, Any
from enum import Enum
from schemas.transaction import Category

# ===== ENUMS ========
class BudgetPeriod(str, Enum):
    """How often the budget resets"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    SEMESTER = "semester"
    CUSTOM = "custom"

class BudgetStatus(str, Enum):
    """Current status of the budget"""
    ON_TRACK = "on_track"
    WARNING = "warning"
    EXCEEDED = "exceeded"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class RolloverRule(str, Enum):
    """What happens to the unused budget at period end"""
    EXPIRE = "expire"
    SAVINGS = "savings"
    ROLLOVER = "rollover"

# === BUDGET CATEGORY (Sub-model) ===
class BudgetCategory(BaseModel):
    """
    📊 Budget for a single spending category
    Example: Food budget with $500 limit, $350 spent so far
    """
    category: Category
    limit: float = Field(...,  gt=0, description="Maximum allowed for this category")
    spent: float = Field(default= 0.0, ge=0, description= "Amount spent on the particular category so far.")

    # optional sub limits
    sub_limits: Dict[str, Any] = Field(default_factory= dict)
    sub_spent: Dict[str, Any] = Field(default_factory= dict)

    rollover_rule: RolloverRule = Field(default=RolloverRule.SAVINGS)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: float)-> float:
        """Ensure limit is realistic"""
        if v > 100_000:
            raise ValueError("Limit must be realistic and not too high")
        return v
    
    @property
    def remaining(self)-> float:
        """How much money left to spend"""
        return max(0, self.limit - self.spent)
    
    @property
    def percent_used(self)-> float:
        """Percentage of budget used"""
        return (self.spent / self.limit * 100) if self.limit > 0 else 0
    
    @property
    def is_over_budget(self) -> bool:
        """check if exceeded"""
        return self.spent > self.limit
    
    @property
    def status(self) -> BudgetStatus:
        """Get status for this category"""
        if self.spent == 0:
            return BudgetStatus.ON_TRACK
        percent = self.percent_used
        if percent >= 100:
            return BudgetStatus.EXCEEDED
        if percent >= 80:
            return BudgetStatus.WARNING
        return BudgetStatus.ON_TRACK
    
    def add_expense(self, amount: float, sub_category: Optional[str] = None)->None:
        """Add a new expense to this category"""
        self.spent+= amount
        if sub_category and sub_category in self.sub_limits:
            self.sub_spent[sub_category] = self.sub_spent.get(sub_category, 0) + amount

    def reset(self) -> None:
        """Reset spent amounts for new period"""
        self.spent = 0.0
        self.sub_spent = {}

# === MAIN BUDGET MODEL ===
class Budget(BaseModel):
    """💰 Complete budget for a student
    Contains multiple categories and tracks overall spending"""

    # ===== IDENTITY =====

    budget_id: str = Field(..., min_length=5, max_length=60, description="Unique identifer for this budget")
    student_id: str = Field(..., min_length=1, max_length=60, description="Student who owns this budget")
    name: str = Field(..., min_length=2, max_length=100, description="Name of the Budget (Monthly rent, groceries, gas)")

    # ===== TIME PERIOD =====
    period: BudgetPeriod = Field(default=BudgetPeriod.MONTHLY,description="How often the budget resets")
    start_date: date = Field(..., description="When the budget period begins")
    end_date: date = Field(..., description="When the budget period ends")
    is_active: bool = Field(default=True, description="Whether this is the current budget or not")

    # ===== BUDGET CATEGORIES =====
    categories: List[BudgetCategory] = Field(..., min_length=1, description="All spending categories in this budget.")

    # ===== SAVINGS GOALS =====
    savings_goals:Optional[float] = Field(description="Target amount to save in the period.",
                                          default= None, gt= 0)
    
    saved_so_far: float = Field(description="The amount saved in this period.",
                                default=0.0, ge=0)
    

    # ===== ALERTS & NOTIFICATIONS =====
    alert_threshold: float = Field(
        default=0.8, ge=0, le=1.0, description="Alert when the budget is almost 80% used"
    )

    # ===== METADATA =====
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    notes: str = Field(default = "", max_length=1000)

    ## ===== VALIDATION =====
    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v:date, info) -> date:
        """Ensure the end date is after the start date"""
        if "start_date" in info.data and v <= info.data['start_date']:
            raise ValueError("end_date must be after the start date")
        return v
    
    @field_validator("alert_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Ensure threshold is between 0 and 1"""
        if not 0<= v <= 1:
            raise ValueError("alert_threshold must be between 0 and 1")
        return v
    
    @model_validator(mode="after")
    def validate_categories(self)-> Budget:
        """Ensure categories dont have duplicates"""
        seen = set()
        for cat in self.categories:
            if cat.category in seen:
                raise ValueError(f"Duplicate categories noticed : {cat.category}")
            seen.add(cat.category)
        return self
    
    
    # ===== PROPERTIES =====
    @property
    def total_limit(self)-> float:
        """Sum of all the category limits"""
        return sum(cat.limit for cat in self.categories)
    
    @property
    def total_spent(self)-> float:
        """Sum of all the category spending"""
        return sum(cat.spent for cat in self.categories)
    
    @property
    def total_remaining(self)-> float:
        """Total left to spend"""
        return max(0, self.total_limit- self.total_spent)
    
    @property
    def percent_used(self) -> float:
        """Overall percentage of the amount used"""
        return (self.total_spent / self.total_limit * 100) if self.total_limit > 0 else 0
    
    @property
    def days_remaining(self) -> float:
        """Days left in this budget period"""
        return (self.end_date - date.today()).days
    
    @property
    def status(self) -> BudgetStatus:
        """Overall status of the budget"""
        if not self.is_active:
            return BudgetStatus.ARCHIVED
        if date.today() > self.end_date:
            return BudgetStatus.COMPLETED
        if self.percent_used >= 100:
            return BudgetStatus.EXCEEDED
        if self.percent_used >= self.alert_threshold*100:
            return BudgetStatus.WARNING
        return BudgetStatus.ON_TRACK
    
    # ===== CATEGORY MANAGEMENT =====
    def get_category(self, category: Category) -> Optional[BudgetCategory]:
        """Get a specific category by name"""
        for cat in self.categories:
            if cat.category == category:
                return cat
        return None
    
    def add_expense(self, category: Category, amount: float, sub_category: Optional[str] =  None)-> bool:
        """
        Add an expense to a category
        Returns True if added, False if category not found
        """
        cat = self.get_category(category)
        if not cat:
            return False
        
        cat.add_expense(amount, sub_category)
        self.last_updated = datetime.now()
        return True
    
    def category_status(self, category: Category)-> Dict[str, Any]:
        """Get detailed status for a category"""
        cat = self.get_category(category)
        if not cat:
            return {"error": "No Category Found"}
        return {
            "limit": cat.limit,
            "spent": cat.spent,
            "remaining": cat.remaining,
            "percent":cat.percent_used,
            "status": cat.status,
            "is_over_budget":cat.is_over_budget
        }
    
    # ===== SAVINGS TRACKING =====

    def add_to_savings(self, amount: float)-> None:
        "Add money to svings goal"
        self.saved_so_far += amount
        self.last_updated = datetime.now()

    @property
    def savings_progress(self)-> float:
        "percentage of savings goal achieved"
        if not self.savings_goals:
            return 0
        return (self.saved_so_far / self.savings_goals * 100) 
    
    @property
    def savings_remaining(self)-> Optional[float]:
        """Amount left to reach savings goal"""
        if not self.savings_goals:
            return None
        return max(0, self.savings_goals - self.saved_so_far)
    
    # ===== BUDGET ACTIONS =====
    def reset_for_new_period(self)-> None:
        """Reset spent amounts for next budget period"""
        for cat in self.categories:
            cat.reset()
        self.saved_so_far = 0.0
        self.last_updated = datetime.now()
    
    def archive(self)-> None:
        """Mark budget as archived(old)"""
        self.is_active = False
        self.last_updated = datetime.now()

    # ===== REPORTING =====
    def spending_report(self) -> Dict[str, Any]:
        """Generate spending report for this budget"""
        categories_report = []
        for cat in self.categories:
            categories_report.append(
                {"category": cat.category,
                "limit":cat.limit,
                "spent":cat.spent,
                "remaining": cat.remaining,
                "percent": cat.percent_used,
                "status": cat.status.value}
            )

        return{
            "budget_name": self.name,
            "period": self.period.value,
            "date_range": f"{self.start_date} to {self.end_date}",
            "days_remaining": self.days_remaining,
            "total_limit": self.total_limit,
            "total_spent": self.total_spent,
            "total_remaining": self.total_remaining,
            "overall_percent":self.percent_used,
            "status": self.status.value,
            "categories": categories_report,
            "savings": {
                "goal":self.savings_goals,
                "saved":self.saved_so_far,
                "progress": self.savings_progress,
                "remaining": self.savings_remaining
            } if self.savings_goals else None
        }
    
    def __str__(self)-> str:
        """Friendly string representing"""
        return f"$ {self.name}: ${self.total_spent:.0f}/${self.total_limit:.0f} ({self.percent_used:.0f}%) - {self.status.value}"



