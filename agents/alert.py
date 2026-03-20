"""
🚨 ALERT AGENT - Central urgency engine for financial monitoring

Why this agent exists
---------------------
Tracker tells us:
- what the current budget status is
- which categories are on track / warning / over budget
- whether goal progress is healthy or behind

Analyzer tells us:
- what patterns exist
- what anomalies or risky trends are happening

Planner tells us:
- what strategy the student should follow

AlertAgent's job:
- convert those signals into prioritized, student-friendly alerts
- assign severity
- deduplicate overlapping alerts
- return a clean, structured alert payload for UI / runner / advisor

Design principle
----------------
This agent is intentionally RULE-BASED, not LLM-based.

Why?
- alerts should be deterministic
- alerts should be explainable
- alerts should be easy to test
- alerts should not randomly change wording or severity
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, asdict
import hashlib

from schemas.student import Student
from schemas.goal import Goal


# ---------------------------------------------------------
# Type aliases
# ---------------------------------------------------------

AlertSeverity = Literal["info", "warning", "critical"]
AlertSource = Literal["tracker", "analyzer", "planner", "goal", "system"]


# ---------------------------------------------------------
# Small models
# ---------------------------------------------------------

@dataclass
class FinancialAlert:
    """
    Represents one alert item in the system.
    """
    id: str
    type: str
    severity: AlertSeverity
    title: str
    message: str
    recommended_action: str
    source: AlertSource
    category: Optional[str] = None
    goal_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["metadata"] is None:
            data["metadata"] = {}
        return data


# ---------------------------------------------------------
# Alert Agent
# ---------------------------------------------------------

class AlertAgent:
    """
    AlertAgent scans the student's financial state and raises
    structured alerts for urgent or noteworthy situations.

    Inputs usually come from:
    - Analyzer
    - Planner
    - Tracker
    - Goals
    """

    def __init__(self, name: str = "Alert Agent"):
        self.name = name

        # Used to sort alerts consistently
        self.severity_rank = {
            "info": 1,
            "warning": 2,
            "critical": 3,
        }

        # Category groups can help us build better alert messages later
        self.fixed_expense_categories = {
            "housing", "rent", "utilities", "internet", "phone", "tuition", "insurance"
        }
        self.flexible_expense_categories = {
            "food", "groceries", "dining_out", "coffee",
            "entertainment", "streaming", "games", "movies",
            "shopping", "clothing", "electronics", "amazon",
            "transport", "gas", "uber", "public_transit",
            "personal_care", "travel"
        }

    # -----------------------------------------------------
    # Public entrypoint
    # -----------------------------------------------------

    def generate_alerts(
        self,
        *,
        student: Student,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
        tracking_report: Dict[str, Any],
        goals: Optional[List[Goal]] = None,
    ) -> Dict[str, Any]:
        """
        Main alert generation function.

        Inputs
        ------
        student:
            Student profile

        analysis:
            Output from Analyzer agent

        plan:
            Output from Planner agent

        tracking_report:
            Output from Tracker agent

        goals:
            Optional list of goals

        Returns
        -------
        Structured alert payload:
        {
            "student_id": ...,
            "alert_date": ...,
            "overall_alert_level": ...,
            "alerts": [...],
            "summary": {...}
        }
        """
        goals = goals or []

        alerts: List[FinancialAlert] = []

        # Collect alerts from each detector
        alerts.extend(self._budget_alerts(tracking_report))
        alerts.extend(self._pace_alerts(tracking_report))
        alerts.extend(self._goal_alerts(goals, tracking_report))
        alerts.extend(self._savings_alerts(student, analysis, plan))
        alerts.extend(self._pattern_alerts(analysis))
        alerts.extend(self._stress_alerts(student, analysis, plan, tracking_report))

        # Clean up duplicates and sort by severity
        alerts = self._deduplicate_alerts(alerts)
        alerts = self._sort_alerts(alerts)

        overall_alert_level = self._get_overall_alert_level(alerts)
        summary = self._build_summary(alerts)

        return {
            "student_id": student.student_id,
            "alert_date": date.today().isoformat(),
            "overall_alert_level": overall_alert_level,
            "alerts": [a.to_dict() for a in alerts],
            "summary": summary,
        }

    # -----------------------------------------------------
    # Budget alerts
    # -----------------------------------------------------

    def _budget_alerts(self, tracking_report: Dict[str, Any]) -> List[FinancialAlert]:
        """
        Build alerts from current budget status and category status.

        What this checks:
        - total budget critical / warning
        - category over budget
        - category nearing budget limit
        """
        alerts: List[FinancialAlert] = []

        budget_status = tracking_report.get("budget_status", {})
        category_tracking = tracking_report.get("category_tracking", {})

        overall_status = budget_status.get("status", "healthy")
        total_percent = float(budget_status.get("percent_used", 0))
        total_budget = float(budget_status.get("total_budget", 0))
        total_spent = float(budget_status.get("total_spent", 0))

        # Overall budget alert
        if overall_status == "critical":
            alerts.append(
                self._make_alert(
                    alert_type="overall_budget_critical",
                    severity="critical",
                    title="Overall budget is over the limit",
                    message=(
                        f"Your monthly budget has reached {total_percent:.1f}% used "
                        f"(${total_spent:.2f} of ${total_budget:.2f})."
                    ),
                    recommended_action=(
                        "Pause non-essential spending immediately and review this week's purchases."
                    ),
                    source="tracker",
                    metadata={
                        "percent_used": total_percent,
                        "total_budget": total_budget,
                        "total_spent": total_spent,
                    },
                )
            )

        elif overall_status == "warning":
            alerts.append(
                self._make_alert(
                    alert_type="overall_budget_warning",
                    severity="warning",
                    title="Overall budget is nearing its limit",
                    message=(
                        f"Your monthly budget is already at {total_percent:.1f}% used "
                        f"(${total_spent:.2f} of ${total_budget:.2f})."
                    ),
                    recommended_action=(
                        "Reduce discretionary spending this week and protect the remaining budget."
                    ),
                    source="tracker",
                    metadata={
                        "percent_used": total_percent,
                        "total_budget": total_budget,
                        "total_spent": total_spent,
                    },
                )
            )

        # Per-category budget alerts
        for category, info in category_tracking.items():
            status = info.get("status", "on_track")
            percent_used = float(info.get("percent_used", 0))
            spent = float(info.get("spent", 0))
            limit = float(info.get("limit", 0))

            if status == "over_budget":
                alerts.append(
                    self._make_alert(
                        alert_type="category_over_budget",
                        severity="critical",
                        title=f"{category} is over budget",
                        message=(
                            f"Your {category} spending is at {percent_used:.1f}% "
                            f"(${spent:.2f} of ${limit:.2f})."
                        ),
                        recommended_action=self._recommended_category_action(category, "critical"),
                        source="tracker",
                        category=category,
                        metadata={
                            "percent_used": percent_used,
                            "spent": spent,
                            "limit": limit,
                        },
                    )
                )

            elif status == "warning":
                alerts.append(
                    self._make_alert(
                        alert_type="category_near_limit",
                        severity="warning",
                        title=f"{category} is close to budget limit",
                        message=(
                            f"Your {category} spending is already at {percent_used:.1f}% "
                            f"(${spent:.2f} of ${limit:.2f})."
                        ),
                        recommended_action=self._recommended_category_action(category, "warning"),
                        source="tracker",
                        category=category,
                        metadata={
                            "percent_used": percent_used,
                            "spent": spent,
                            "limit": limit,
                        },
                    )
                )

        return alerts

    # -----------------------------------------------------
    # Pace alerts
    # -----------------------------------------------------

    def _pace_alerts(self, tracking_report: Dict[str, Any]) -> List[FinancialAlert]:
        """
        Build alerts for spending pace.

        Why pace matters:
        -----------------
        Even if the category is not yet technically over budget,
        the student may be spending too quickly for this point in the month.
        """
        alerts: List[FinancialAlert] = []

        budget_status = tracking_report.get("budget_status", {})
        category_tracking = tracking_report.get("category_tracking", {})

        overall_pace = budget_status.get("pace", {})
        overall_pace_status = overall_pace.get("pace", overall_pace.get("status", "on_track"))

        # Overall pace alert
        if overall_pace_status == "ahead_of_spend" and budget_status.get("status") == "healthy":
            alerts.append(
                self._make_alert(
                    alert_type="overall_spending_pace_warning",
                    severity="warning",
                    title="Spending pace is running high",
                    message=(
                        f"You have used {budget_status.get('percent_used', 0):.1f}% of your budget "
                        f"while the expected usage by now is "
                        f"{overall_pace.get('expected_used_percent_by_now', 0):.1f}%."
                    ),
                    recommended_action="Slow down discretionary spending this week before the budget becomes stressed.",
                    source="tracker",
                    metadata=overall_pace,
                )
            )

        # Category pace alerts
        ahead_categories: List[str] = []

        for category, info in category_tracking.items():
            pace_info = info.get("pace", {})
            pace_status = pace_info.get("pace", pace_info.get("status", "on_track"))
            status = info.get("status", "on_track")

            # Only raise pace alert if category is not already warning/critical,
            # otherwise the budget alert already covers it.
            if pace_status == "ahead_of_spend" and status == "on_track":
                ahead_categories.append(category)

                alerts.append(
                    self._make_alert(
                        alert_type="category_spending_pace_warning",
                        severity="info",
                        title=f"{category} spending is moving faster than expected",
                        message=(
                            f"{category} is at {info.get('percent_used', 0):.1f}% used, "
                            f"which is ahead of the expected pace for this point in the month."
                        ),
                        recommended_action=self._recommended_category_action(category, "pace"),
                        source="tracker",
                        category=category,
                        metadata=pace_info,
                    )
                )

        # If several categories are ahead of pace, raise one grouped warning too.
        if len(ahead_categories) >= 3:
            alerts.append(
                self._make_alert(
                    alert_type="multi_category_pace_warning",
                    severity="warning",
                    title="Several categories are ahead of spending pace",
                    message=(
                        f"Multiple categories are moving too fast this month: "
                        f"{', '.join(ahead_categories[:5])}."
                    ),
                    recommended_action="Reduce optional spending across these categories before they become budget problems.",
                    source="tracker",
                    metadata={"ahead_categories": ahead_categories},
                )
            )

        return alerts

    # -----------------------------------------------------
    # Goal alerts
    # -----------------------------------------------------

    def _goal_alerts(
        self,
        goals: List[Goal],
        tracking_report: Dict[str, Any],
    ) -> List[FinancialAlert]:
        """
        Build alerts related to financial goals.

        We look for:
        - behind goals
        - goal deadlines approaching with low progress
        - abandoned / expired risk situations
        """
        alerts: List[FinancialAlert] = []

        # Tracker may already contain goal_tracking
        goal_tracking = tracking_report.get("goal_tracking", [])

        # If tracker gave us structured goal progress, use that first
        if isinstance(goal_tracking, list) and goal_tracking:
            for g in goal_tracking:
                status = g.get("status", "")
                goal_name = g.get("name", "Goal")
                progress = float(g.get("progress_percent", 0))

                pace = g.get("pace", {})
                pace_status = pace.get("status", "")

                if pace_status == "behind":
                    alerts.append(
                        self._make_alert(
                            alert_type="goal_behind_schedule",
                            severity="warning",
                            title=f"{goal_name} is behind schedule",
                            message=(
                                f"Goal progress is {progress:.1f}% and is currently behind the expected pace."
                            ),
                            recommended_action="Increase contributions slightly or rebalance spending to protect this goal.",
                            source="goal",
                            goal_name=goal_name,
                            metadata={
                                "progress_percent": progress,
                                "pace": pace,
                            },
                        )
                    )

                if status in {"expired", "abandoned"}:
                    alerts.append(
                        self._make_alert(
                            alert_type="goal_at_risk",
                            severity="critical",
                            title=f"{goal_name} is no longer on track",
                            message=f"{goal_name} is marked as {status}.",
                            recommended_action="Reassess the goal timeline and decide whether to revive, revise, or pause it.",
                            source="goal",
                            goal_name=goal_name,
                            metadata=g,
                        )
                    )

            return alerts

        # Fallback: use Goal objects directly if tracker doesn't provide goal_tracking
        for goal in goals:
            progress = float(goal.progress_percent)
            days_left = goal.days_remaining
            status = goal.status.value if hasattr(goal.status, "value") else str(goal.status)

            if status in {"expired", "abandoned"}:
                alerts.append(
                    self._make_alert(
                        alert_type="goal_at_risk",
                        severity="critical",
                        title=f"{goal.name} is no longer on track",
                        message=f"{goal.name} is currently {status}.",
                        recommended_action="Review this goal and decide whether it should be revised or paused.",
                        source="goal",
                        goal_name=goal.name,
                        metadata={
                            "status": status,
                            "progress_percent": progress,
                            "days_left": days_left,
                        },
                    )
                )
                continue

            # If deadline is close but progress is low, raise warning
            if days_left is not None and days_left <= 45 and progress < 50:
                alerts.append(
                    self._make_alert(
                        alert_type="goal_deadline_warning",
                        severity="warning",
                        title=f"{goal.name} may miss its target date",
                        message=(
                            f"{goal.name} has only {days_left} days left and is at {progress:.1f}% progress."
                        ),
                        recommended_action="Increase contributions or revise the timeline before the deadline arrives.",
                        source="goal",
                        goal_name=goal.name,
                        metadata={
                            "progress_percent": progress,
                            "days_left": days_left,
                        },
                    )
                )

        return alerts

    # -----------------------------------------------------
    # Savings alerts
    # -----------------------------------------------------

    def _savings_alerts(
        self,
        student: Student,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> List[FinancialAlert]:
        """
        Build alerts related to savings behavior.

        Signals:
        - very low savings rate
        - savings rate below plan expectations
        - emergency fund weak relative to fixed expenses
        """
        alerts: List[FinancialAlert] = []

        summary = analysis.get("summary", {})
        amount_earned = float(summary.get("amount_earned", 0))
        amount_spent = float(summary.get("amount_spent", 0))

        savings_rate = 0.0
        if amount_earned > 0:
            savings_rate = ((amount_earned - amount_spent) / amount_earned) * 100

        # Low savings rate warning
        if amount_earned > 0 and savings_rate < 10:
            alerts.append(
                self._make_alert(
                    alert_type="low_savings_rate",
                    severity="warning",
                    title="Savings rate is low",
                    message=f"Current savings rate is about {savings_rate:.1f}%.",
                    recommended_action="Protect a small fixed amount for savings before optional spending happens.",
                    source="planner",
                    metadata={"savings_rate_percent": round(savings_rate, 1)},
                )
            )

        # Critical if negative cashflow
        if amount_earned > 0 and amount_spent > amount_earned:
            alerts.append(
                self._make_alert(
                    alert_type="negative_cashflow",
                    severity="critical",
                    title="Spending is higher than income",
                    message=(
                        f"Expenses (${amount_spent:.2f}) are currently above income (${amount_earned:.2f})."
                    ),
                    recommended_action="Cut discretionary spending immediately and stabilize the monthly plan before saving more.",
                    source="planner",
                    metadata={
                        "amount_earned": amount_earned,
                        "amount_spent": amount_spent,
                    },
                )
            )

        # Weak emergency cushion check using fixed monthly expenses if available
        if hasattr(student, "total_fixed_expenses"):
            fixed_exp = float(student.total_fixed_expenses())
            current_savings = float(getattr(student, "current_savings", 0.0))

            if fixed_exp > 0:
                months_covered = current_savings / fixed_exp

                if months_covered < 1:
                    alerts.append(
                        self._make_alert(
                            alert_type="very_low_emergency_cushion",
                            severity="critical",
                            title="Emergency cushion is very thin",
                            message=(
                                f"Current savings cover only about {months_covered:.1f} months of fixed expenses."
                            ),
                            recommended_action="Prioritize emergency savings until at least 1 month of fixed expenses is covered.",
                            source="planner",
                            metadata={"months_covered": round(months_covered, 1)},
                        )
                    )
                elif months_covered < 3:
                    alerts.append(
                        self._make_alert(
                            alert_type="low_emergency_cushion",
                            severity="warning",
                            title="Emergency fund could be stronger",
                            message=(
                                f"Current savings cover about {months_covered:.1f} months of fixed expenses."
                            ),
                            recommended_action="Gradually increase emergency fund contributions toward a safer cushion.",
                            source="planner",
                            metadata={"months_covered": round(months_covered, 1)},
                        )
                    )

        return alerts

    # -----------------------------------------------------
    # Pattern alerts
    # -----------------------------------------------------

    def _pattern_alerts(self, analysis: Dict[str, Any]) -> List[FinancialAlert]:
        """
        Convert analyzer patterns into user-facing alerts.

        We don't raise alerts for every pattern.
        We mainly surface:
        - warning patterns
        - critical patterns
        - especially meaningful informational patterns
        """
        alerts: List[FinancialAlert] = []

        patterns = analysis.get("patterns", [])

        for p in patterns:
            if not isinstance(p, dict):
                continue

            severity = p.get("severity", "info")
            name = p.get("name", "pattern")
            description = p.get("description", "")

            if severity == "critical":
                alerts.append(
                    self._make_alert(
                        alert_type=f"pattern_{name}",
                        severity="critical",
                        title="A high-risk spending pattern was detected",
                        message=description,
                        recommended_action="Review this pattern now and make one immediate spending adjustment this week.",
                        source="analyzer",
                        metadata=p,
                    )
                )

            elif severity == "warning":
                alerts.append(
                    self._make_alert(
                        alert_type=f"pattern_{name}",
                        severity="warning",
                        title="A spending pattern needs attention",
                        message=description,
                        recommended_action="Use this pattern as an early warning and adjust your spending before it grows.",
                        source="analyzer",
                        metadata=p,
                    )
                )

            elif severity == "info" and name == "subscriptions":
                alerts.append(
                    self._make_alert(
                        alert_type="subscription_review",
                        severity="info",
                        title="Recurring subscriptions are worth reviewing",
                        message=description,
                        recommended_action="Check which recurring services are still worth keeping this month.",
                        source="analyzer",
                        metadata=p,
                    )
                )

        return alerts

    # -----------------------------------------------------
    # Stress alerts
    # -----------------------------------------------------

    def _stress_alerts(
        self,
        student: Student,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
        tracking_report: Dict[str, Any],
    ) -> List[FinancialAlert]:
        """
        Build broader "financial stress" alerts by combining signals.

        These alerts are useful when the student is not in one obvious danger zone,
        but the overall situation is still fragile.
        """
        alerts: List[FinancialAlert] = []

        budget_status = tracking_report.get("budget_status", {})
        percent_used = float(budget_status.get("percent_used", 0))
        overall_status = budget_status.get("status", "healthy")

        baseline = plan.get("baseline", {})
        total_monthly_spend = float(baseline.get("total_spend_est_monthly", 0))
        monthly_income = float(getattr(student, "monthly_income", 0.0))

        # Planned spend higher than income -> major structural stress
        if monthly_income > 0 and total_monthly_spend > monthly_income:
            gap = total_monthly_spend - monthly_income
            alerts.append(
                self._make_alert(
                    alert_type="monthly_plan_under_stress",
                    severity="critical",
                    title="Monthly plan is under structural stress",
                    message=(
                        f"Estimated monthly spending (${total_monthly_spend:.2f}) is higher than income "
                        f"(${monthly_income:.2f}) by about ${gap:.2f}."
                    ),
                    recommended_action="Reduce discretionary categories first before adding more savings or new goals.",
                    source="planner",
                    metadata={
                        "monthly_income": monthly_income,
                        "total_spend_est_monthly": total_monthly_spend,
                        "gap": round(gap, 2),
                    },
                )
            )

        # Student has little disposable income
        if hasattr(student, "estimated_disposable_income"):
            disposable = float(student.estimated_disposable_income())
            if monthly_income > 0 and disposable <= monthly_income * 0.05:
                alerts.append(
                    self._make_alert(
                        alert_type="low_monthly_buffer",
                        severity="warning",
                        title="Monthly financial buffer is very small",
                        message=(
                            f"Only about ${disposable:.2f} remains after fixed monthly expenses."
                        ),
                        recommended_action="Avoid adding new recurring costs and keep this month's variable spending tightly controlled.",
                        source="planner",
                        metadata={"disposable_income": round(disposable, 2)},
                    )
                )

        # High budget usage + weak pace situation can become stressful
        pace_info = budget_status.get("pace", {})
        pace_status = pace_info.get("pace", pace_info.get("status", "on_track"))
        if overall_status == "warning" and pace_status == "ahead_of_spend" and percent_used >= 80:
            alerts.append(
                self._make_alert(
                    alert_type="budget_stress_escalating",
                    severity="critical",
                    title="Budget pressure is escalating quickly",
                    message=(
                        f"Budget use is already at {percent_used:.1f}% and spending pace is ahead of schedule."
                    ),
                    recommended_action="Switch to essentials-only spending for the rest of the week and recheck the budget.",
                    source="tracker",
                    metadata={"percent_used": percent_used, "pace": pace_info},
                )
            )

        return alerts

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def _make_alert(
        self,
        *,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        recommended_action: str,
        source: AlertSource,
        category: Optional[str] = None,
        goal_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FinancialAlert:
        """
        Create one alert object and generate a stable ID.

        We use a hash so repeated runs with the same content create the same ID shape.
        """
        raw_key = f"{alert_type}|{severity}|{title}|{category}|{goal_name}|{source}"
        alert_id = hashlib.md5(raw_key.encode("utf-8")).hexdigest()[:12]

        return FinancialAlert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            recommended_action=recommended_action,
            source=source,
            category=category,
            goal_name=goal_name,
            metadata=metadata or {},
        )

    def _recommended_category_action(self, category: str, mode: str) -> str:
        """
        Return a practical recommendation based on category and urgency mode.

        mode:
        - "critical"
        - "warning"
        - "pace"
        """
        if category == "groceries":
            if mode == "critical":
                return "Plan low-cost meals immediately and avoid unplanned grocery trips this week."
            if mode == "warning":
                return "Make a short grocery list and stick to it for the rest of the week."
            return "Check whether grocery spending is drifting upward and cut waste early."

        if category == "dining_out":
            if mode == "critical":
                return "Pause dining out for the rest of the week and switch to home-cooked meals."
            if mode == "warning":
                return "Replace at least 2 restaurant meals with groceries this week."
            return "Keep dining-out spend lower this week so the category does not become stressed."

        if category == "coffee":
            if mode == "critical":
                return "Pause café purchases for a few days and use a lower-cost alternative."
            if mode == "warning":
                return "Set a coffee cap for this week and reduce one or two purchases."
            return "Watch this category closely and avoid small impulse coffee buys."

        if category in {"shopping", "amazon", "clothing", "electronics"}:
            if mode == "critical":
                return f"Pause {category} purchases immediately unless they are essential."
            if mode == "warning":
                return f"Delay any non-essential {category} purchases until next week."
            return f"Keep {category} spending low for the rest of this week."

        if category in {"entertainment", "streaming", "games", "movies"}:
            if mode == "critical":
                return "Move to free or low-cost entertainment options for the rest of the week."
            if mode == "warning":
                return "Cap entertainment spending for this week and avoid impulse spending."
            return "Use a low-cost entertainment plan this week."

        if category in {"transport", "uber", "gas", "public_transit"}:
            if mode == "critical":
                return "Reduce optional trips this week and combine errands where possible."
            if mode == "warning":
                return "Review transport spending and avoid unnecessary extra trips."
            return "Watch transport costs closely for the next few days."

        if category in {"utilities", "internet", "phone"}:
            if mode == "critical":
                return "Review service usage and check whether bills or plans need adjustment."
            if mode == "warning":
                return "Check whether any service plans or add-ons can be trimmed next billing cycle."
            return "Keep an eye on this category and review upcoming bills."

        # Generic fallback
        if mode == "critical":
            return f"Reduce spending in {category} immediately and limit this category to essentials only."
        if mode == "warning":
            return f"Cut back on {category} spending this week before it crosses the limit."
        return f"Monitor {category} closely so it does not become a budget problem."

    def _deduplicate_alerts(self, alerts: List[FinancialAlert]) -> List[FinancialAlert]:
        """
        Deduplicate alerts by ID.

        If duplicates exist, keep the higher-severity version.
        """
        best_by_id: Dict[str, FinancialAlert] = {}

        for alert in alerts:
            existing = best_by_id.get(alert.id)

            if existing is None:
                best_by_id[alert.id] = alert
                continue

            if self.severity_rank[alert.severity] > self.severity_rank[existing.severity]:
                best_by_id[alert.id] = alert

        return list(best_by_id.values())

    def _sort_alerts(self, alerts: List[FinancialAlert]) -> List[FinancialAlert]:
        """
        Sort alerts by:
        1. severity descending
        2. title ascending

        This keeps output stable and UI-friendly.
        """
        return sorted(
            alerts,
            key=lambda a: (-self.severity_rank[a.severity], a.title.lower()),
        )

    def _get_overall_alert_level(self, alerts: List[FinancialAlert]) -> str:
        """
        Overall alert level is the highest alert severity present.
        """
        if not alerts:
            return "info"

        max_rank = max(self.severity_rank[a.severity] for a in alerts)

        if max_rank >= self.severity_rank["critical"]:
            return "critical"
        if max_rank >= self.severity_rank["warning"]:
            return "warning"
        return "info"

    def _build_summary(self, alerts: List[FinancialAlert]) -> Dict[str, Any]:
        """
        Build a small summary block for quick UI display.
        """
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        warning_count = sum(1 for a in alerts if a.severity == "warning")
        info_count = sum(1 for a in alerts if a.severity == "info")

        return {
            "total_alerts": len(alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": info_count,
        }


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------

def create_alert_agent() -> AlertAgent:
    """Create and return a new AlertAgent instance."""
    return AlertAgent()