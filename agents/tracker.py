"""
📈 TRACKER AGENT - Monitors actual spending against budget and goals

What Tracker does:
- Compares real transactions against the active budget
- Tells whether each category is on track / warning / over budget
- Computes overall budget health
- Tracks goal progress (if goals are supplied)
- Generates alerts + simple recommendations

Design principles:
- Pure tracking only (no DB writes, no UI, no side effects)
- JSON-friendly output for Streamlit / APIs / LangGraph state
- Explainable rule-based logic (easy to debug and improve)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, date
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget
from schemas.goal import Goal

# ------------------------------------------------------------
# Small helper models
# ------------------------------------------------------------

@dataclass
class TrackingAlert:
    """ Small alert obhect used internally, then converted to dict.
    
    severity:
    -info
    -warning
    -critical"""

    message: str
    severity: str = "info"
    category: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    def to_dict(self)-> Dict[str, Any]:
        """ COnver dataclass to clean JSON friendly dict.
        Ensure data is always a dictionary"""
        d = asdict(self)
        if d["data"] is None:
            d['data'] = {}
        return d
    
    # ------------------------------------------------------------
    # Tracker Agent
    # ------------------------------------------------------------

class TrackerAgent:
    """
    TrackerAgent = "Are we following the plan?"

    Inputs: 
    student
    transactions
    budget
    optional goals

    Outputs:
    overall budget status
    category by category tracking
    goal tracking
    alers
    recommendatations
    """

    def __init__(self, *, name: str = "Tracker Agent"):
        self.name = name

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def track_student(
            self,
            *,
            student: Student,
            transactions: List[Transaction],
            budget: Budget,
            goals: Optional[List[Goal]] = None,
            tracking_date: Optional[date] = None
    ) -> Dict[str, Any]:
        
        """
        Main entry point.

        Flow:
        1. Filter transactions to the budget window
        2. Track budget overall + by category
        3. Track Goals (if any)
        4. Generate alerts from the current status
        5. Generate recommendations
        """

        tracking_date = tracking_date or date.today()
        goals = goals or []

        budget_txns = self._filter_transactions_for_budget_period(transactions, budget)
        budget_report = self._track_budget(
            transactions = budget_txns,
            budget = budget,
            tracking_date = tracking_date
        )

        goal_report = self._track_goals(
            goals = goals,
            transactions = budget_txns,
            tracking_date = tracking_date
        )

        alerts = self._generate_alerts(
            budget_report = budget_report,
            goal_report = goal_report,
            tracking_date = tracking_date
        )

        recommendations = self._generate_recommendations(
            budget_report = budget_report,
            goal_report = goal_report
        )

        return {
            "student_id": student.student_id,
            "tracking_date": tracking_date.isoformat(),
            "budget_period": {
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat(),
                "name": budget.name,
                "period": budget.period.value
            },
            "budget_status": budget_report['overall'],
            "category_tracking": budget_report["categories"],
            "goal_tracking": goal_report,
            "alerts": [a.to_dict() for a in alerts],
            "recommendations": recommendations,
            "meta": {
                "transactions_considered": len(budget_txns),
                "goals_considered": len(goals)
            }
        }
    
    # --------------------------------------------------------
    # Basic helpers
    # --------------------------------------------------------

    def _is_expense(self, t: Transaction) -> bool:
        """True if a particular transaction is an expense"""
        return t.transaction_type == TransactionType.EXPENSE
    
    def _is_income(self, t: Transaction) -> bool:
        """True if a transactions is income"""
        return t.transaction_type == TransactionType.INCOME
    
    def _filter_transactions_for_budget_period(self,
                                               transactions: List[Transaction], 
                                               budget: Budget):
        """Keep only transactions inside the budget date window.
        
        Why:
        If a monthly budget covers March 1 to March 31, we should not compare Feb transactions
        against"""

        return [
            t for t in transactions
            if budget.start_date <= t.date <= budget.end_date
        ]
    
     # --------------------------------------------------------
    # Budget tracking
    # --------------------------------------------------------

    def _track_budget(
            self,
            *,
            transactions: List[Transaction],
            budget: Budget,
            tracking_date: date,
    ) -> Dict[str, Any]:
        """
        Track current budget health.
        
        Output contains:
        - overall budget summary
        - category by category status
        pacing information (Optional useful signal)
        
        Logic
        Only expenses transactions will be counted for budget usage
        For each budget category - 
        spent/ limit/ remaining/ present_used/ status
        overall budget:
        total_budget/ total_spent/ total_remaining/ present_used/ overall status
        """

        expense_txns = [t for t in transactions if self._is_expense(t)]

        # build per_category expense sums from transactions
        spent_by_category: Dict[str, float] = defaultdict(float)
        for t in expense_txns:
            spent_by_category[str(t.category)] += float(t.amount)

        # Track each budget category independently
        category_tracking: Dict[str, Dict[str, Any]] = {}
        total_limit = 0.0
        total_spent = 0.0

        for bc in budget.categories:
            category_name = str(bc.category)
            limit = float(bc.limit)
            spent = float(spent_by_category.get(category_name, 0.0))
            remaining = max(0.0, limit - spent)
            percent_used = (spent / limit * 100.0) if limit > 0 else 0.0

            # Category status rules
            # - over_budget if spent >= limit
            # - warning if spent >= alert threshold
            # - on track otherwise
            if spent >= limit:
                status = "over_budget"
            elif spent >= limit * float(budget.alert_threshold):
                status = "warning"
            else:
                status = "on_track"

            # add pacing info:
            # compare how much of month is elapsed vs how much of budget is used
            pace = self._calculate_budget_pace(
                start_date= budget.start_date,
                end_date = budget.end_date,
                tracking_date = tracking_date,
                percent_used = percent_used
            )

            category_tracking[category_name] = {
                "limit": round(limit, 2),
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "percent_used": round(percent_used, 1),
                "status": status,
                "pace": pace
            }

            total_limit += limit
            total_spent += spent
        
        total_remaining = max (0.0, total_limit - total_spent)
        overall_percent_used = (total_spent / total_limit * 100.0) if total_limit > 0 else 0.0

        # overall health rules
        over_count = sum(1 for c in category_tracking.values() if c["status"] == "over_budget")
        warning_count = sum(1 for c in category_tracking.values() if c["status"] == "warning")

        if over_count >=2 or overall_percent_used >= 100:
            overall_status = "critical"
        elif over_count >=1 or warning_count >=2 or overall_percent_used >= 85:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        ahead_count = sum(1 for c in category_tracking.values()
            if c.get("pace", {}).get("pace") == "ahead_of_spend"
        )
        if ahead_count >= 2 and overall_status == "healthy":
            overall_status = "warning"
        
        overall = {
            "total_budget": round(total_limit, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_remaining, 2),
            "percent_used": round(overall_percent_used, 1),
            "status": overall_status,
            "categories_over_budget": over_count,
            "categories_in_warning": warning_count,
            "pace": self._calculate_budget_pace(
                start_date = budget.start_date,
                end_date = budget.end_date,
                tracking_date = tracking_date,
                percent_used = overall_percent_used
            )
        }

        return {
            "overall": overall,
            "categories": category_tracking
        }
    
    def _calculate_budget_pace(
            self,
            *,
            start_date: date,
            end_date: date,
            tracking_date: date,
            percent_used: float
    ) -> Dict[str, Any]:
        
        """Compare budget usage with time elapsed.
        
        Example:
        - if 50% of the month is passed but 80% of the budget is gone -> ahead_of_spend
        - if 50% of the month has passed and 40% of the budget is used then - on track or under_pace"""

        total_days = max(1, (end_date - start_date).days +1)
        elapsed_days = min(max(1, (tracking_date - start_date).days +1), total_days)

        expected_used_percent = (elapsed_days / total_days ) * 100.0

        # pace classification:
        # - ahead of spend = using budget faster than time is passing
        # - under pace = using slower than time passing
        # - on track = reasonabily aligned

        delta = percent_used - expected_used_percent

        if delta >= 15:
            pace_status = "ahead_of_spend"
        elif delta <= -15:
            pace_status = "under_pace"
        else:
            pace_status = "on_track"
        
        return {
            "elapsed_days": elapsed_days,
            "total_days": total_days,
            "expected_used_percent_by_now": round(expected_used_percent, 1),
            "actual_used_percent": round(percent_used, 1),
            "pace": pace_status
        }
    
    def _inder_savings_from_transactions(
            self,
            transactions: List[Transaction],
            goal: Goal
    )-> float:
        """Try to detect savings contributions"""
        keywords = ["savings", "transfer to savings", "to savings"]
        savings_txns = [
            t for t in transactions
            if any(k in t.description.lower() for k in keywords) and self._is_expense(t)
        ]

        return sum(t.amount for t in savings_txns)
    
    # --------------------------------------------------------
    # Goal tracking
    # --------------------------------------------------------

    def _track_goals(self,
                     *,
                     goals: List[Goal],
                     transactions: List[Transaction],
                     tracking_date: date) -> List[Dict[str, Any]]:
        """
        
        Track goal progress.
        
        We keep it simple.
        - Use goal.current_amount directly as th source of truth.
        - compute progress %, remaining, status
        - estimate whether it is on pace for the target date"""

        reports: List[Dict[str, Any]] = []

        for goal in goals:
            progress = float(goal.progress_percent)
            remaining = float(goal.remaining_amount)
            status = goal.status.value if hasattr(goal.status, "value") else str(goal.status)

            report = {
                "goal_id": goal.goal_id,
                "name": goal.name,
                "category": goal.category.value if hasattr(goal.category, "value") else str(goal.category),
                "priority": goal.priority.value if hasattr(goal.priority, "value") else str(goal.priority),
                "target_amount": round(float(goal.target_amount), 2),
                "current_amount":round(float(goal.current_amount), 2),
                "remaining_amount": round(remaining, 2),
                "progress_percent": round(progress, 1),
                "status": status,
                "target_date": goal.target_date.isoformat() if goal.target_date else None,
                "recurring_type":goal.recurring_type.value if hasattr(goal.recurring_type, "value") else str(goal.recurring_type),
                "recurring_amount":round(float(goal.recurring_amount), 2) if goal.recurring_amount else None
            }

            if goal.target_date:
                report["pace"] = self._calculate_goal_pace(goal, tracking_date)
            
            reports.append(report)
        return reports
    
    def _calculate_goal_pace(self,
                             goal: Goal,
                             tracking_date: date) -> Dict[str, Any]:
        """
        Compare actual goal progress vs expected progress by this data.

        Example - 
        - Goal created on Jan 1, target date Apr 1 => total duration 90 days
        - today is halfway => expected progress around 50%
        - If actual progress is 20% => behind
        """

        start = goal.create_on
        end = goal.target_date or tracking_date

        total_days = max(1, (end - start).days)
        elapsed_days = min(max(0, (tracking_date - start).days), total_days)

        expected_progress = (elapsed_days / total_days) * 100.0
        actual_progress = float(goal.progress_percent)
        delta = actual_progress - expected_progress

        if delta >= 10:
            pace_status = "ahead"
        elif delta <= -10:
            pace_status = "behind"
        else:
            pace_status = "on_track"

        return {
            "expected_progress_percent_by_now": round(expected_progress, 1),
            "actual_progress_percent": round(actual_progress, 1),
            "status": pace_status
        }
    
    # --------------------------------------------------------
    # Alerts
    # --------------------------------------------------------

    def _generate_alerts(self,
                         *,
                         budget_report: Dict[str, Any],
                         goal_report: List[Dict[str, Any]],
                         tracking_date: date) -> List[TrackingAlert]:
        """
        Turn tracking numbers into readable alerts.

        Budget alerts:
         - category over budget
         - category in warning zone
         - category spending too fast for time elapsed
         - overall budget critical/ warning

        Goal Alerts -
        - goal behind pace
        - goal completed
        """
        alerts: List[TrackingAlert] = []

        overall = budget_report['overall']
        categories = budget_report['categories']

        # overall budget alers
        if overall["status"] == "critical":
            alerts.append(
                TrackingAlert(
                    message=f"Overall budget is critical: {overall['percent_used']}% used.",
                    severity= "critical",
                    data= overall
                )
            )
        elif overall['status'] == "warning":
            alerts.append(
                TrackingAlert(
                    message=f"Overall budget is in warning zone: {overall['percent_used']}% used.",
                    severity= "warning",
                    data= overall
                )
            )
        
        # category level alerts
        for cat, info in categories.items():
            if info['status'] == "over_budget":
                alerts.append(
                    TrackingAlert(
                        message=f"'{cat}' is over budget ({info['percent_used']}% used).",
                        severity="critical",
                        category=cat,
                        data=info
                    )
                )
            elif info['status'] == "warning":
                alerts.append(
                    TrackingAlert(
                        message=f"'{cat}' is nearing its limits. ({info['percent_used']}% used).",
                        severity="warning",
                        category=cat,
                        data=info
                    )
                )
            # pace alert: spending faster than time is passing
            overall_pace = overall.get("pace", {})
            if overall_pace.get("pace") == "ahead_of_spend" and overall["status"] != "over_budget":
                alerts.append(
                    TrackingAlert(
                        message="Overall budget is being spent faster than expected for this point in the cycle.",
                        severity="warning",
                        data=overall_pace
                    )
                )
        
        # Goal ALerts
        for goal in goal_report:
            goal_name = goal["name"]

            if goal["status"] == "completed":
                alerts.append(
                    TrackingAlert(
                        message=f"Goal Completed: {goal_name}",
                        severity="info",
                        data=goal
                    )
                )
            pace = goal.get("pace")
            if pace and pace.get("status") == "behind":
                alerts.append(
                    TrackingAlert(
                        message=f"Goal {goal_name} is behind schedule.",
                        severity="warning",
                        data=goal
                    )
                )
        
        return alerts[:20]
    
    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    def _generate_recommendations(
            self,
            *,
            budget_report: Dict[str, Any],
            goal_report: List[Dict[str, Any]]
    )-> List[str]:
        
        """
        Convert tracking state into simple next step suggestions.
        Recommendations are intentionally short and actionable
        """

        recommendations: List[str] = []

        overall = budget_report["overall"]
        categories = budget_report["categories"]

        # overall suggestions
        if overall["status"] == "critical":
            recommendations.append("Pause excess spending untill budget pressure drops.")
        elif overall["status"] == "warning":
            recommendations.append("Review this week's spending and trim at least one non-essential spending")

        # category-specific suggestion
        for cat, info in categories.items():
            if info["status"] == "over_budget":
                recommendations.append(f"Stop or sharply reduce spending in '{cat}' for the rest of the budget period.")
            elif info["status"] == "warning":
                recommendations.append(f"Be careful with '{cat}' — it is close to the budget limit.")
            elif info.get("pace", {}).get("status") == "ahead_of_spend":
                recommendations.append(f"Slow down spending in '{cat}' to avoid going over budget later this period.")

        # Goal specific suggestions
        for goal in goal_report:
            pace = goal.get("pace")
            if pace and pace.get("status") == "behind":
                recommendations.append(
                    f"Increase contributions to '{goal['name']}' or extend the timeline if needed."
                )
            elif goal["status"] == "completed":
                recommendations.append(
                    f"'{goal["name"]}' is completed. Consider setting a new financial goal."
                )
        
        # Deduplication while preserving the order
        deduped: List[str] = []
        seen = set()
        for r in recommendations:
            if r not in seen:
                deduped.append(r)
                seen.add(r)
        
        return deduped[:20]
    

def create_tracker()-> TrackerAgent:
    """Simple factory function used by tests or graph builder."""
    return TrackerAgent()


    



