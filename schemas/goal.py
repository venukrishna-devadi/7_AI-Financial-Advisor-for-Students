"""
🎯 GOAL SCHEMA — Financial targets for a student.
Agents update current_amount; graph checks status; UI shows progress bar.
"""

from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Any, Dict
from enum import Enum
from decimal import Decimal


# === ENUMS ===
class GoalCategory(str, Enum):
    """Goal type bucket"""
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"
    MAJOR_PURCHASE= "major_purchase"
    EDUCATION = "education"
    INVESTMENT = "investment"
    TRAVEL = "travel"
    EVERYDAY = "everyday"
    CUSTOM = "custom"

class GoalPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    AMBITIOUS = "ambitious"

class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    BEHIND = "behind"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"

class RecurringType(str, Enum):
    ONE_TIME = "one_time"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    PER_PAYCHECK = "per_paycheck"

# === MAIN MODEL ===

class Goal(BaseModel):
    """Single financial goal.
    Agents update current amount, graph cehcks the status, ui shows progress bar"""

    goal_id: str = Field(..., min_length=5, max_length=60, description="Unique Identifier for this goal")
    student_id: str = Field(..., description= "owner of this goal")
    name: str = Field(..., min_length=3, max_length=100, description="Show description name")
    category: GoalCategory = Field(..., description="Type of financial goal")

    # target amount
    target_amount: float = Field(..., gt=0, description="total amount to reach")
    current_amount: float = Field(default=0.0, ge = 0, description="Amount saved so far")

    # timeline
    target_date: Optional[date] = Field(default=None, description= "deadline to hit the goal")
    create_on: date = Field(default_factory=date.today, description="Date goal was created")
    created_at: datetime = Field(default_factory= datetime.now, description="Full timestamp of creation date")

    # contribution plan
    recurring_type: RecurringType = Field(default=RecurringType.ONE_TIME,
                                          description="How often contributions are made")
    
    recurring_amount: Optional[float] = Field(default= None, gt = 0, description="Amount per contribution cycle (required if recurring)")

    # priority and status
    priority: GoalPriority = Field(default=GoalPriority.MEDIUM, description="how important this goal is")
    status: GoalStatus = Field(default = GoalStatus.NOT_STARTED, description= "Current goal status")

    # Metadata
    tags: List[str] = Field(default_factory=list, description= "Free-form labels")
    notes: str = Field(default="", max_length=500, description="Extra context or motivation")
    last_updated: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default= None, description="when goal was completed")

    # =============================
    # VALIDATORS
    # =============================

    @field_validator("target_amount")
    @classmethod
    def validate_target_amount(cls, v: float)-> float:
        """Reject unrealistic targets and round."""
        if v>100_000:
            raise ValueError("Target amount is unrealistic")
        return round(v, 2)
    
    @field_validator("current_amount")
    @classmethod
    def validate_current_amount(cls, v:float) -> float:
        """Round stored amount to cents"""
        return round(v, 2)
    
    @field_validator("target_date")
    @classmethod
    def validate_target_date(cls, v: Optional[date]) -> Optional[date]:
        """Disallow past deadlines, (so a goal isnt expired on day 1 itself)"""
        if v and  v< date.today():
            raise ValueError("target date cannot be in the past")
        return v
    
    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        """Lowercase and strip tags, remove empty strings, dedupe while preserving order"""
        return list(dict.fromkeys(t.strip().lower() for t in v if t.strip()))
    
    @model_validator(mode="after")
    def validate_recurring_amount(self) -> "Goal":
        """
        Enforce clean recurring behavior:
        - ONE_TIME => recurring_amount must be None
        - otherwise => recurring_amount required
        """
        if self.recurring_type == RecurringType.ONE_TIME:
            self.recurring_amount = None
            return self
        
        if self.recurring_amount is None:
            raise ValueError("recurring amount is required when recurring_type is not one_time")
        
        return self
    
    @model_validator(mode="after")
    def clamp_current_amount(self) -> "Goal":
        """Ensures current_amount never exceeds target_amount"""
        if self.current_amount > self.target_amount:
            self.current_amount = self.target_amount
        return self
    
    @model_validator(mode = "after")
    def compute_status(self) -> "Goal":
        """
        Auto derive status from progress and deadline.
        IMPORTANT - Respect ambondoned (manual terminal state)"""
        # respect manual terminal states
        if self.status in (GoalStatus.ABANDONED, ):
            return self
        
        if self.current_amount >= self.target_amount:
            self.status = GoalStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.now()
            return self
        
        # if time passes later, this can become expired
        if self.target_date and date.today() > self.target_date:
            self.status = GoalStatus.EXPIRED
            return self
        
        if self.current_amount == 0:
            self.status = GoalStatus.NOT_STARTED
        else:
            self.status = GoalStatus.IN_PROGRESS
        
        return self
    
    # =============================
    # COMPUTED PROPERTIES
    # =============================

    @property
    def is_completed(self) -> bool:
        """True if goal has been fully funded"""
        return self.current_amount >= self.target_amount
    
    @property
    def remaining_amount(self) -> float:
        """How much more needs to be saved"""
        return max(0.0, self.target_amount - self.current_amount)
    
    @property
    def progress_percent(self) -> float:
        """Percentage of target reached"""
        return(self.current_amount / self.target_amount * 100) if self.target_amount else 0.0
    
    @property
    def days_remaining(self) -> Optional[int]:
        """Days until deadline, or None if no deadline"""
        return (self.target_date - date.today()).days if self.target_date else None
    
    @property
    def recommended_monthly(self) -> Optional[float]:
        """Monthly savings needed to hit target on time.
        If no deadline, we dont force a monthly recommendation."""
        if not self.target_date or self.days_remaining in (None, 0):
            return None
        
        months = self.days_remaining / 30.44
        return round(self.remaining_amount / months, 2) if months > 0 else None
    
    @property
    def is_on_track(self) -> bool:
        """
        very rough check: if recurring_amount exists which is monthly, see if it meets recommeended.
        Later we will compute pace properly (expected_saved_by_total vs actual)
        """
        rec = self.recommended_monthly
        if rec is None:
            return True
        return (self.recurring_amount or 0) >= rec
    
    # =============================
    # METHODS
    # =============================

    def is_feasible(self, monthly_savings: float) -> bool:
        """Can the student hit this goal with the monthly savings"""
        rec = self.recommended_monthly
        if rec is None:
            return True
        return monthly_savings >= rec
    
    def add_contribution(self, amount: float) -> None:
        """Add a contribution towards the goal"""
        if amount <= 0:
            return ValueError("Please enter contribution amount which is greater than 0")
        
        self.current_amount = round(min(self.target_amount, self.current_amount + amount), 2)
        self.last_updated = datetime.now()

        # refresh status
        if self.is_completed:
            self.status = GoalStatus.COMPLETED
            self.completed_at= datetime.now()
        elif self.current_amount > 0 and self.status != GoalStatus.ABANDONED:
            self.status = GoalStatus.IN_PROGRESS

    def abandon(self, reason: str = "") -> None:
        """Mark goal as abandoned with an optional reason"""
        self.status = GoalStatus.ABANDONED
        if reason:
            self.notes = f"[Abandoned] {reason}"
        self.last_updated = datetime.now()

    def progress_bar(self, width: int = 20) -> str:
        """Visual ASCII progress bar."""
        filled = int(self.progress_percent / 100 * width)
        return f"[{'█' * filled}{'░' * (width - filled)}] {self.progress_percent:.1f}%"
    
    def summary(self) -> Dict[str, Any]:
        """Structured summary for agent use or UI display"""
        return{
            "goal_id": self.goal_id,
            "name": self.name,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "target": self.target_amount,
            "saved": self.current_amount,
            "remaining": self.remaining_amount,
            "progress": f"{self.progress_percent:.1f}%",
            "days_remaining": self.days_remaining,
            "recommended_monthly": self.recommended_monthly,
            "recurring": {
                "type": self.recurring_type.value,
                "amount": self.recurring_amount
            },
            "tags": self.tags,
            "notes": self.notes,
            "completed_at": str(self.completed_at) if self.completed_at else None
        }
    
    def __str__(self) -> str:
        icon = "✅" if self.is_completed else "🎯"
        return (
            f"{icon} {self.name}:"
            f"${self.current_amount:.0f}/${self.target_amount:.0f}"
            f"{self.progress_bar(15)} - {self.status.value}"
        )



    

    





