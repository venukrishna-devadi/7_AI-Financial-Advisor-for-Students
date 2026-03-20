# utils/calculators.py
"""
🧮 CALCULATORS - Pure financial math helpers (no UI, no LLM, no LangGraph)

Rules for this file:
✅ Pure functions only (easy to test)
✅ No side effects (no prints, no file I/O)
✅ Reusable by agents, graph, and UI

All money values are assumed to be in the user's currency.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pow
from typing import List, Any, Dict, Literal, Optional, Tuple

IncomeFrequency = Literal["weekly", "biweekly", "monthly"]

# ---------------------------------------------------------------------
# 1) Income / Frequency normalization
# ---------------------------------------------------------------------

def to_monthly_amount(amount: float, frequency: IncomeFrequency) -> float:
    """
    Convert an income amount to a normalized monthly amount.

    Assumptions:
    - weekly  -> 52 weeks / 12 months
    - biweekly -> 26 pay periods / 12 months
    - monthly -> as-is
    """
    if amount < 0:
        raise ValueError("Amount should be greater than 0 and non negative")
    if frequency == "monthly":
        return round(amount, 2)
    if frequency == "biweekly":
        return round(amount * (26 / 12), 2)
    if frequency == "weekly":
        return round(amount * (52 / 12), 2)
    
    # should never happen due to literal
    raise ValueError(f"Unsupported frequency - {frequency}")

# ---------------------------------------------------------------------
# 2) Disposable income / savings rate
# ---------------------------------------------------------------------

def disposable_income(monthly_income: float, fixed_monthly_expenses: float) -> float:
    """Income left after fixed monthly expenses (never negative)"""
    if monthly_income < 0 or fixed_monthly_expenses < 0:
        raise ValueError("Inputs cannot be negative")
    return round(max(0.0, monthly_income - fixed_monthly_expenses), 2)

def savings_rate(monthly_income: float, monthly_savings: float)-> float:
    """savings rate as a percentage"""
    if monthly_income <=0:
        return 0.0
    if monthly_savings < 0:
        raise ValueError("No monthly savings and monthly savings cannot be negative")
    return round((monthly_savings / monthly_income)* 100, 2)

# ---------------------------------------------------------------------
# 3) Compound interest projection
# ---------------------------------------------------------------------

def compound_future_value(
    principal: float,
    annual_rate: float,
    years: float,
    contributions_per_year: int = 12,
    contribution_amount: float = 0.0,
) -> float:
    """
    Future value with contributions and compounding.

    - principal: starting amount (>=0)
    - annual_rate: decimal (e.g., 0.07 for 7%)
    - years: number of years (>=0)
    - contributions_per_year: typically 12 (monthly), 26 (biweekly), 52 (weekly)
    - contribution_amount: contribution each period (>=0)

    Uses standard future value formula for annuity + principal growth.
    """
    if annual_rate < -1.0:
        raise ValueError("annual_rate cannot be less than -100%")
    if annual_rate > 1.0:
        # Could be percentage (7%) or decimal (0.07)
        # This is a common source of bugs!
        pass  # Maybe warn or auto-convert?
    
    if principal < 0 or years < 0:
        raise ValueError("principal and years must be >= 0")
    if contribution_amount < 0:
        raise ValueError("contribution_amount must be >= 0")
    if contributions_per_year <= 0:
        raise ValueError("contributions_per_year must be > 0")
    if annual_rate < -0.999:
        raise ValueError("annual_rate is too low (invalid)")

    if years == 0:
        return round(principal, 2)

    r = annual_rate / contributions_per_year
    n = contributions_per_year * years

    # Principal growth
    principal_growth = principal * pow(1 + r, n)

    # Contributions future value (annuity)
    if annual_rate == 0:
        contrib_growth = contribution_amount * n
    else:
        contrib_growth = contribution_amount * ((pow(1 + r, n) - 1) / r)

    return round(principal_growth + contrib_growth, 2)

def compound_schedule_monthly(
    principal: float,
    annual_rate: float,
    months: int,
    monthly_contribution: float = 0.0
) -> Dict[str, float]:
    """
    Returns a lightweight schedule for UI:
    { "month_1": value, ..., "month_N": value }
    """
    if months < 0:
        raise ValueError("months must be >= 0")
    if principal < 0 or monthly_contribution < 0:
        raise ValueError("principal and monthly_contribution must be >= 0")

    schedule: Dict[str, float] = {}
    value = principal
    monthly_rate = annual_rate / 12

    for m in range(1, months + 1):
        value = value * (1 + monthly_rate) + monthly_contribution
        schedule[f"month_{m}"] = round(value, 2)

    return schedule


# ---------------------------------------------------------------------
# 4) Loan / Debt payoff calculators
# ---------------------------------------------------------------------

def monthly_payment_for_loan(principal: float, annual_rate: float, months: int) -> float:
    """
    Standard amortized loan monthly payment.

    annual_rate is decimal (e.g., 0.12 for 12% APR).
    """
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if months <= 0:
        raise ValueError("months must be > 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")

    r = annual_rate / 12
    if r == 0:
        return round(principal / months, 2)

    payment = principal * (r * pow(1 + r, months)) / (pow(1 + r, months) - 1)
    return round(payment, 2)


def months_to_payoff(principal: float, annual_rate: float, monthly_payment: float) -> Optional[int]:
    """
    Estimate months to pay off a loan if paying fixed monthly_payment.
    Returns None if payment is too low to ever pay off (interest overwhelms).
    """
    if principal <= 0:
        return 0
    if annual_rate < 0 or monthly_payment <= 0:
        raise ValueError("annual_rate must be >=0 and monthly_payment must be >0")

    r = annual_rate / 12
    balance = principal
    months = 0

    # If payment doesn't cover interest, it will never finish
    if r > 0 and monthly_payment <= balance * r:
        return None

    while balance > 0 and months < 10_000:  # safety cap
        interest = balance * r
        balance = balance + interest - monthly_payment
        months += 1

    return months


# ---------------------------------------------------------------------
# 5) Emergency fund runway
# ---------------------------------------------------------------------

def emergency_fund_months(emergency_fund: float, essential_monthly_expenses: float) -> float:
    """
    How many months the emergency fund lasts.
    """
    if emergency_fund < 0 or essential_monthly_expenses < 0:
        raise ValueError("Inputs cannot be negative")
    if essential_monthly_expenses == 0:
        return float("inf")
    return round(emergency_fund / essential_monthly_expenses, 2)


# ---------------------------------------------------------------------
# 6) Simple budget allocation helpers
# ---------------------------------------------------------------------

def rule_50_30_20(monthly_income: float) -> Dict[str, float]:
    """
    Classic budget rule:
    - needs: 50%
    - wants: 30%
    - savings: 20%
    """
    if monthly_income < 0:
        raise ValueError("monthly_income cannot be negative")
    return {
        "needs": round(monthly_income * 0.50, 2),
        "wants": round(monthly_income * 0.30, 2),
        "savings": round(monthly_income * 0.20, 2),
    }


def category_percent_allocation(monthly_income: float, allocation: Dict[str, float]) -> Dict[str, float]:
    """
    Convert a percent allocation into dollar amounts.

    allocation example:
      {"food": 0.15, "rent": 0.35, "savings": 0.20}

    Percent values must sum to <= 1.0 (100%).
    """
    if monthly_income < 0:
        raise ValueError("monthly_income cannot be negative")

    total = sum(allocation.values())
    if total > 1.0 + 1e-9:
        raise ValueError("Allocation percentages must sum to <= 1.0")

    return {k: round(monthly_income * v, 2) for k, v in allocation.items()}

def savings_goal_feasibility(
    target_amount: float,
    current_savings: float,
    monthly_savings: float,
    years: int,
    interest_rate: float = 0.02  # Conservative 2% savings account
) -> dict:
    """Can they reach their goal given current savings rate?"""
    future = compound_future_value(
        principal=current_savings,
        annual_rate=interest_rate,
        years=years,
        contribution_amount=monthly_savings * 12,  # yearly contributions
        contributions_per_year=1
    )
    return {
        "projected": future,
        "target": target_amount,
        "feasible": future >= target_amount,
        "gap": max(0, target_amount - future)
    }

def future_value_in_todays_money(
    future_amount: float, 
    inflation_rate: float, 
    years: int
) -> float:
    """Adjust future money to today's purchasing power"""
    return future_amount / ((1 + inflation_rate) ** years)