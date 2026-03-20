from __future__ import annotations
from datetime import date, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import uuid
import math

from schemas.student import Student
from schemas.transaction import Transaction, TransactionType, Category
from schemas.budget import Budget, BudgetCategory, BudgetPeriod, BudgetStatus, RolloverRule
from schemas.goal import Goal, GoalCategory, GoalPriority, GoalStatus, RecurringType

"""
What is the Planner Agent?

Analyzer = “What happened?” (insights from past data)
Planner = “What should we do next?” (a concrete plan)

So the Planner Agent should take:
	•	Student profile (income, risk, fixed expenses)
	•	Transactions (spending reality)
	•	Analyzer output (patterns, top categories, subscriptions, velocity)
	•	Optional: Budget + Goals

…and produce:
	•	a budget plan
	•	a goal plan
	•	a step-by-step action plan (what to change this week/month)
	•	a projection (if you follow this plan, what happens)

⸻

Planner Agent Responsibilities (Real-world + small enough)

1) Build a “monthly baseline”

Compute:
	•	monthly income (already normalized in Student)
	•	fixed monthly expenses (from Student)
	•	estimated variable spending (from transactions, last 30/60/90 days)
	•	disposable income

Output example:
	•	Income: $2000
	•	Fixed: $900
	•	Typical variable: $800
	•	Leftover: $300

This baseline is the foundation for any plan.

⸻

2) Suggest a budget (category limits)

A simple v1 budget logic:
	•	Start with last 30 days category spend
	•	Apply gentle reduction targets
	•	If category concentration > 50% → reduce that category by 5–15%
	•	If weekend spike → add a “weekend fun cap”
	•	If subscriptions detected → mark them as “reviewable”
	•	Ensure total limits ≤ income - fixed - savings_target

Output:
	•	BudgetCategory list (limit per category)
	•	Alert threshold (like 0.8)

⸻

3) Build a savings plan (goals)

If the student has goals:
	•	check feasibility using Goal.is_feasible(disposable_income)
	•	recommend a monthly contribution

If the student has no goals:
	•	suggest a default goal:
	•	Emergency fund (3 months expenses) OR
	•	“Starter emergency fund” ($500–$1000) if student income is low

Output:
	•	recommended monthly savings amount
	•	suggested new goals (optional)

⸻

4) Give “actions” (the most important part)

The plan should not be just numbers. It should give small tasks:

Examples:
	•	“Cancel or downgrade Netflix/Spotify if unused — saves ~$25/mo”
	•	“Set groceries cap to $60/week”
	•	“Move $100/mo to emergency fund”
	•	“Avoid weekend spike: limit weekend spend to $X per day”

Output structure:
	•	action list with priority + impact estimate

⸻

5) Provide “what-if projections”

Very simple projection:
	•	If you reduce groceries by 10% and cancel 1 subscription → savings +$X/month
	•	How much you’d save in 3 months / 6 months

Output:
	•	projected monthly savings
	•	projected goal completion date estimate"""


"""
🧭 PLANNER AGENT - Turns analysis into a concrete budget + savings plan (no side effects)

What Planner does:
- Takes Student + Transactions + Analyzer output
- Produces:
  ✅ Baseline (income, fixed, variable, disposable)
  ✅ Recommended Budget (Budget + BudgetCategory limits)
  ✅ Savings recommendation + goal suggestions
  ✅ Action plan (prioritized steps with estimated impact)
  ✅ Simple projections (3 / 6 month savings impact)

Design principles:
- Pure planning (no DB writes, no UI, no network calls)
- Deterministic & explainable (rules-first)
"""

# -------------------------
# Small helper models
# -------------------------

@dataclass
class PlanAction:
    """
    One concrete recommendation step.
    impact_monthly_usd: estimated monthly saving or benefit (can be 0 if unknown)
    """
    title: str
    description: str
    priority: str = "medium"
    impact_monthly_usd: float = 0.0
    confidence: str = "medium"
    tags: List[str] = None

    def to_dict(self)-> Dict[str, Any]:
        d = asdict(self)
        if d["tags"] is None:
            d["tags"] = []
        d["impact_monthly_usd"] = round(float(d["impact_monthly_usd"] or 0.0), 2)
        return d

@dataclass
class PlanResult:
    baseline: Dict[str, Any]
    recommended_budget: Optional[Budget]
    budget_rationable: Dict[str, Any]
    recommended_savings: Dict[str, Any]
    suggested_goals: List[Goal]
    action_plan: List[PlanAction]
    projections: Dict[str, Any]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        budget_dict = None
        if self.recommended_budget:
            budget_dict = self.recommended_budget.model_dump()
            if "period" in budget_dict and hasattr(budget_dict['period'], 'value'):
                budget_dict['period'] = budget_dict['period'].value
        goals_list = []
        for g in self.suggested_goals:
            gd = g.model_dump()
            # fix enums
            if "recurring_type" in gd and hasattr(gd["recurring_type"], "value"):
                gd["recurring_type"] = gd["recurring_type"].value
            if "priority" in gd and hasattr(gd["priority"], "value"):
                gd["priority"] = gd["priority"].value
            goals_list.append(gd)
        return {
            "baseline": self.baseline,
            "recommended_budget": budget_dict,
            "recommended_savings": self.recommended_savings,
            "suggested_goals": goals_list,
            "action_plan": [a.to_dict() for a in self.action_plan],
            "projections": self.projections,
            "warnings": self.warnings

        }
    

# -------------------------
# Planner Agent
# -------------------------
class PlannerAgent:
    """
    🧠 PlannerAgent turns analysis into a plan.
    Think of it as: "given reality, propose next best actions".

    Inputs:
    - student: Student
    - transactions: List[Transaction]
    - analysis: Dict[str,Any] (output from AnalyzerAgent)
    - existing_budget: Optional[Budget]
    - goals: Optional[List[Goal]]

    Output:
    - PlanResult (budget + savings + actions + projections)
    """

    def __init__(self, *, name: str = "Planner Agent"):
        self.name = name

        # -------------------------
        # Public API
        # -------------------------
    
    def build_plan(
            self,
            *,
            student: Student,
            transactions: List[Transaction],
            analysis: Optional[Dict[str, Any]] = None,
            existing_budget: Optional[Budget] = None,
            goals: Optional[List[Goal]] = None,
            lookback_days: int = 60,
            budget_period: BudgetPeriod = BudgetPeriod.MONTHLY
    ) -> Dict[str, Any]:
        """
        Main entrypoint.

        Flow (high level):
        1) Filter transactions to lookback window
        2) Build baseline (income/fixed/variable/disposable)
        3) Pick a reasonable savings target (rule-based)
        4) Propose category limits using recent spend + nudges from analysis
        5) Suggest actions & projections
        6) Suggest goals if none exist or if useful
        """
        goals = goals or []
        analysis = analysis or {}

        txns = self._filter_recent(transactions, lookback_days)
        baseline = self._compute_baseline(student, txns)
        warnings: List[str] = []

        if not txns:
            return {
                "error": "No transaction data available for planning",
                "baseline": self._compute_baseline(student, []),
                "action_plan": [PlanAction(
                    title="Add your first transactions",
                    description="Start tracking expenses to get personalized budget recommendations.",
                    priority="high",
                    tags=["onboarding"]
                ).to_dict()]
            }
        if baseline["total_spend_est_monthly"] > baseline["monthly_income"]:
            excess = baseline["total_spend_est_monthly"] - baseline["monthly_income"]
            warnings.append(f"Estimated monthly spending exceeds income by ~${excess:.0f}. Current plan is under stress—focus on cuts before savings.")
        if baseline["monthly_income"] <= 0:
            warnings.append("Monthly income is 0 - planning quality will be limited untill income is provided.")
        if baseline["fixed_monthly_expenses"] > baseline["monthly_income"] and baseline["monthly_income"] >0:
            warnings.append("Fixed expenses exceed income - first priority is to reduce bills or increase fixed monthly income")
        
        # savings recommendation (simple and safe)
        savings_plan = self._recommend_savings(baseline, student, analysis)

        # Budget recommendataion  (only if we have expenses)
        recommended_budget, rationale = self._recommend_budget(
            student = student,
            transactions = txns,
            analysis = analysis,
            existing_budget = existing_budget,
            budget_period = budget_period,
            baseline = baseline,
            savings_plan = savings_plan
        )

        # SUggested goals (minimal defaults)
        suggested_goals = self._suggest_goals(student, baseline, goals, savings_plan)

        # Action plan (human readable steps)
        actions = self._build_action_plan(
            student = student,
            baseline = baseline,
            analysis = analysis,
            recommended_budget = recommended_budget,
            savings_plan = savings_plan,
            suggested_goals = suggested_goals
        )

        # projections: simple monthly impact * horizons
        projections = self._build_projections(
            baseline = baseline,
            savings_plan = savings_plan,
            action_plan = actions
        )

        plan = PlanResult(
            baseline=baseline,
            recommended_budget=recommended_budget,
            budget_rationable=rationale,
            recommended_savings=savings_plan,
            suggested_goals= suggested_goals,
            action_plan= actions,
            projections=projections,
            warnings=warnings
        )
        return plan.to_dict()
    
    # -------------------------
    # Core planning steps
    # -------------------------

    def _filter_recent(self,
                       transactions: List[Transaction],
                       lookback_days: int) -> List[Transaction]:
        """
        Keeps only transactions within the lookback window.
        Why: planning from very old spending can mislead the budget.
        """
        if lookback_days <= 0:
            return transactions
        cutoff = date.today() - timedelta(days=lookback_days)
        return [t for t in transactions if t.date >= cutoff]
    
    def _is_expense(self, t: Transaction) -> bool:
        return t.transaction_type == TransactionType.EXPENSE
    
    def _is_income(self, t:Transaction) -> bool:
        return t.transaction_type == TransactionType.INCOME
    
    def _compute_baseline(self, student: Student, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Baseline = the planner’s internal snapshot of finances.

        We prefer Student.monthly_income (normalized) as the stable source of truth.
        Transactions are used for:
        - estimating variable monthly spending (recent window)
        - estimating subscriptions cost from recurring flags/merchants (if present)

        Output fields:
        - monthly_income
        - fixed_monthly_expenses
        - variable_spend_est_monthly
        - total_spend_est_monthly
        - disposable_est_monthly (never negative)
        """
        monthly_income = float(student.monthly_income or 0.0)
        #fixed_expenses = float(student.fixed_monthly_expenses)
        fixed_expenses = sum(float(v) for v in student.fixed_monthly_expenses.values())

        # Estimate variable spend by annualizing lookback expenses to “per month”.
        # If lookback is 60 days, and spent $1200, monthly estimate ~ $600.
        # This is rough but good enough for MVP planning.
        expenses = [t for t in transactions if self._is_expense(t)]
        if transactions:
            # compute window length form min/ max txn date
            min_d = min((t.date for t in transactions), default= date.today())
            max_d = max((t.date for t in transactions), default=date.today())
            window_days = max(1, (max_d - min_d).days + 1)
        else:
            window_days = 1
        
        total_expenses = sum(t.amount for t in expenses)
        variable_monthly = (total_expenses / window_days) * 30.44

        total_spend_monthly = fixed_expenses + variable_monthly
        disposable = max(0.0, monthly_income - fixed_expenses)

        return{
            "monthly_income": round(monthly_income, 2),
            "fixed_monthly_expenses": round(fixed_expenses, 2),
            "variable_spend_est_monthly": round(variable_monthly, 2),
            "total_spend_est_monthly": round(total_spend_monthly, 2),
            "window_days_used": window_days,
            "disposable_est_monthly": round(disposable,2),
            "notes": "Baseline uses student.monthly_income + recent expense rate to estimate monthly behaviour."
        }
    
    def _recommend_savings(self, 
                           baseline: Dict[str, Any], 
                           student: Student, 
                           analysis: Dict[str, Any])->Dict[str, Any]:
        """
        Decide a savings target that is:
        - small enough to be realistic
        - big enough to matter

        Rules:
        - If disposable is 0: savings target = 0
        - Else:
            - conservative: 10% of disposable
            - moderate: 15% of disposable
            - aggressive: 20% of disposable
        - Cap savings to 30% of disposable (avoid overplanning)
        """
        disposable = float(baseline.get("disposable_est_monthly", 0.0))
        if disposable <= 0:
            return {
                "target_monthly_savings": 0.0,
                "startegy": "none",
                "rationale": "No disposable income after fixed expenses."
            }
        risk = (student.risk_profile or "moderate").lower()
        pct = 0.15
        if risk == "conservative":
            pct = 0.10
        if risk == "aggressive":
            pct = 0.20
        
        target = disposable * pct
        target = min(target, disposable * 0.30)

        # round to a number
        target_number = self._round_nice(target)

        return{
            "target_monthly_savings": round(target_number, 2),
            "strategy": f"{int(pct*100)}% of disposable income (risk_profile={student.risk_profile})",
            "rationale": "Rule- based savings target; adjust later based on goals"
        }
    
    def _recommend_budget(
            self,
            *,
            student: Student,
            transactions: List[Transaction],
            analysis: Dict[str, Any],
            existing_budget: Optional[Budget],
            budget_period: BudgetPeriod,
            baseline: Dict[str, Any],
            savings_plan: Dict[str, Any]
    ) -> Tuple[Optional[Budget], Dict[str, Any]]:
        """
        Build a monthly budget from recent spend, with nudges.

        Steps:
        1) Aggregate recent expenses per category
        2) Use those amounts as the initial "limits"
        3) Apply nudges:
           - If category_concentration pattern exists -> reduce top category slightly
           - If weekend_spending pattern exists -> reduce entertainment/dining_out slightly
        4) Ensure total budget <= (income - fixed - savings_target)
           If not, scale down variable category limits proportionally.
        """
        expenses = [t for t in transactions if self._is_expense(t)]

        if not expenses:
            return None, {"reason": "No expense data available to build"}
        
        # 1. recent spend by category
        spend_by_cat: Dict[str, float] = defaultdict(float)
        for t in expenses:
            spend_by_cat[str(t.category)] += float(t.amount)
        
        # convert spend in window -> monthly estimate
        # we use baseline window_days_used to scale
        window_days = max(1, int(baseline.get("window_days_used", 30)))
        multiplier = 30.44 / window_days
        monthly_by_cat = {cat: amt * multiplier for cat, amt in spend_by_cat.items()}

        # 2. initial limits = monthly estimate (rounded)
        limits: Dict[str, float] = {cat:self._round_nice(val) for cat, val in monthly_by_cat.items()}

        # 3. Nudges based on analysis patterns
        nudges: List[str] = []

        # Find category_concentration pattern (if analyzer sent it)
        # Analyzer patterns come as list[dict] under analysis["patterns"] usually
        patterns = analysis.get("patterns") or []

        # patterns might already be dicts, if they were dataclasses they were converted
        concentration_cat= None
        concentration_pct = None
        weekend_spike = False

        for p in patterns:
            if not isinstance(p, dict):
                continue
            if p.get("name") == "category_concentration":
                data = p.get("data") or {}
                concentration_cat = data.get("category")
                concentration_pct = data.get("pct")
            if p.get("name") == "weekend_spending":
                weekend_spike = True
        
        # Reduce the most concentrated category slightly
        if concentration_cat and concentration_cat in limits:
            # if >70% critical --> reduce 10%, else reduce 5%
            drop = 0.10 if (concentration_pct or 0) >= 70 else 0.05
            old = limits[concentration_cat]
            limits[concentration_cat] = self._round_nice(old*(1-drop))
            nudges.append(f"Reduced '{concentration_cat}' limit by {int(drop*100)}% due to high concentration ")

        # If weekend spike, nudge entertainment/dining_out if present
        if weekend_spike:
            for cat in ("entertainment", "dining_out", "games", "movies"):
                if cat in limits:
                    old = limits[cat]
                    limits[cat] = self._round_nice(old * 0.90)
                    nudges.append(f"Nudged '{cat}' down by 10% due to weekend spike pattern.")

        # 4) fit within capacity
        income = float(baseline.get("monthly_income", 0.0))
        fixed = float(baseline.get("fixed_monthly_expenses", 0.0))
        savings_target = float(savings_plan.get("target_monthly_savings", 0.0))

        # Capacity for variable categories
        capacity = max(0.0, income - fixed - savings_target)

        # total proposed variable budget
        proposed_total = sum(limits.values())
        scaled = False

        if proposed_total > capacity and proposed_total > 0:
            scale = capacity / proposed_total
            for cat in list(limits.keys()):
                limits[cat] = self._round_nice(limits[cat] * scale)
            scaled = True
            nudges.append("Scaled all category limits down to fit income - fixed - savings target.")

        # Create BudgetCategory list (must be valid Category values)
        # Only keep categories that are actually in the Category Literal set.
        budget_categories: List[BudgetCategory] = []
        for cat, limit in limits.items():
            # Category is a Literal in your schemas.transaction; we pass string values that match.
            # If a weird category slips in, skip it safely.
            try:
                bc = BudgetCategory(category=cat, limit=float(max(1.0, limit)))
                budget_categories.append(bc)
            except Exception:
                # skip unknown category values
                continue

        if not budget_categories:
            return None, {"reason": "No valid categories found to build budget."}

        # Budget window: monthly period from today
        start = date.today().replace(day=1)
        # end date: rough month end (safe enough for MVP)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        recommended = Budget(
            budget_id=self._new_id("bud"),
            student_id=student.student_id,
            name=f"{budget_period.value.capitalize()} Budget (recommended)",
            period=budget_period,
            start_date=start,
            end_date=end,
            categories=budget_categories,
            savings_goals=savings_target if savings_target > 0 else None,
            alert_threshold=0.8,
            notes="Auto-generated by PlannerAgent from recent spending + analysis nudges.",
        )

        rationale = {
            "method": "recent_spend_scaled_to_month + nudges + capacity_fit",
            "window_days_used": window_days,
            "capacity_variable_budget": round(capacity, 2),
            "proposed_total_before_fit": round(proposed_total, 2),
            "scaled_to_fit": scaled,
            "nudges": nudges,
        }
        return recommended, rationale
    
    def _suggest_goals(
            self,
            student: Student,
            baseline: Dict[str, Any],
            existing_goals: List[Goal],
            savings_plan: Dict[str, Any]
    ) -> List[Goal]:
        """
        Goal suggestions (minimal & safe).

        If there are no goals:
        - suggest a starter emergency fund goal.
        If goals exist:
        - do nothing (don’t overstep), but we could recommend contributions later.

        Starter emergency fund:
        - If expenses are known, target = 1 month of total spend estimate (fixed + variable)
        - Otherwise target = 500
        """
        if existing_goals:
            return []
        
        monthly_spend = float(baseline.get("total_spend_est_monthly", 0.0))
        if monthly_spend <= 0:
            target = 500.0
        else:
            # 1 month emergency fund for mvp, later we can do 3-6 months
            target = self._round_nice(monthly_spend)
        
        contrib = float(savings_plan.get("target_monthly_savings", 0.0))
        if contrib <= 0:
            contrib = None
        
        goal = Goal(
            goal_id=self._new_id("goal"),
            student_id=student.student_id,
            name="Started Emergency Fund",
            category = GoalCategory.EMERGENCY_FUND,
            target_amount=float(target),
            current_amount=0.0,
            target_date=None,
            recurring_type=RecurringType.MONTHLY if contrib else RecurringType.ONE_TIME,
            recurring_amount= contrib,
            priority=GoalPriority.HIGH,
            notes = "Auto-suggested goal: build a small safety cushion."
        )

        return [goal]
    
    def _build_action_plan(
            self,
            *,
            student: Student,
            baseline: Dict[str,Any],
            analysis: Dict[str, Any],
            recommended_budget: Optional[Budget],
            savings_plan: Dict[str, Any],
            suggested_goals: List[Goal]
    )-> List[PlanAction]:
        """
        Convert analysis + budget into human steps.

        We keep it:
        - small list (max ~8)
        - prioritized
        - actionable
        """

        actions: List[PlanAction] = []

        disposable = float(baseline.get("disposable_est_monthly", 0.0))
        savings_target = float(savings_plan.get("target_monthly_savings", 0.0))

        # 1. If fixed > income, biggest red flag
        if float(baseline.get("fixed_monthly_expenses", 0.0)) > float(baseline.get("monthly_income", 0.0)) > 0:
            actions.append(
                PlanAction(
                    title="Reduced fixed bills or increase income.",
                    description="Your fixed monthly expenses are greater than your income. Start by replanning or reducing bills (phone/internet), housing or car expenses like gas and monthly emi or may be try to increase income.",
                    priority="high",
                    impact_monthly_usd=0.0,
                    confidence="high",
                    tags=["fixed_expenses", "critical"]
                )
            )
        
        # 2. Savings autopilot suggestion
        if savings_target > 0 and disposable > 0:
            actions.append(
                PlanAction(
                    title="Automate Savings",
                    description=f"Set an automative transfer of Savings ${savings_target:.0f}/month to savings right after payday.",
                    priority="high",
                    impact_monthly_usd=savings_target,
                    confidence="high",
                    tags=["savings"]

                )
            )
        
        #3. Subscriptions review (from analysis if present)
        subs = self._extract_subscriptions_from_analysis(analysis)
        if subs:
            # estimate impact: if unknown a marginal of $15 will be considered
            est = min(30.0, sum(float(s.get("approx_amount", 0.0)) for s in subs[:2]) or 15)
            actions.append(
                PlanAction(
                    title="Review Subscription",
                    description=f"Review recurring charges ({', '.join(s.get('merchant','') for s in subs[:3])}). Cancel or downgrade unused ones.",
                    priority="medium",
                    impact_monthly_usd=est,
                    confidence="medium",
                    tags=["subscriptions"]
                )
            )
        
        # 4. Category concentration / weekend spike actions from patterns
        patterns = analysis.get("patterns") or []
        for p in patterns:
            if not isinstance(p, dict):
                continue

            if p.get("name") == "category_concentration":
                data = p.get('data') or {}
                cat = data.get("category")
                pct = data.get("pct")
                actions.append(PlanAction(
                    title="Reduce your biggest spending bucket",
                    description=f"Your spending is heavily concentrated in '{cat}' ({pct:.0f}%). Try a 5–10% reduction this month.",
                        priority="high",
                        impact_monthly_usd=0.0,
                        confidence="medium",
                        tags=["spending_pattern", "category"]
                ))
            
            if p.get("name") == "weekend_spending":
                actions.append(
                    PlanAction(
                        title="Add a weekend cap",
                        description="You spend more on weekends. Set a weekend daily cap and plan 1 low-cost activity.",
                        priority="medium",
                        impact_monthly_usd=0.0,
                        confidence="medium",
                        tags=["spending_pattern", "weekend"]

                    )
                )

        # 5) Budget usage action
        if recommended_budget:
            actions.append(
                PlanAction(
                    title="Track weekly against your budget",
                    description="Check your budget once per week and adjust the next week’s spending (small corrections beat big surprises).",
                    priority="medium",
                    impact_monthly_usd=0.0,
                    confidence="high",
                    tags=["budget"],
                )
            )

        # 6) Suggested goal action
        if suggested_goals:
            g = suggested_goals[0]
            actions.append(
                PlanAction(
                    title="Start a starter emergency fund",
                    description=f"Goal: ${g.target_amount:.0f}. Even small monthly progress helps build stability.",
                    priority="medium",
                    impact_monthly_usd=float(g.recurring_amount or 0.0),
                    confidence="high",
                    tags=["goals", "emergency_fund"],
                )
            )
        
        # trim and order by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda a: priority_order.get(a.priority, 9))
        return actions[:8]
    
    def _build_projections(self,
                           *,
                           baseline: Dict[str, Any],
                           savings_plan: Dict[str, Any],
                           action_plan: List[PlanAction]) -> Dict[str, Any]:
        
        """
        Simple “what-if” projection.

        We only use:
        - savings target
        - sum of action monthly impact estimates (some actions have 0 impact)
        """
        target = float(savings_plan.get("target_monthly_savings", 0.0))
        action_impact = sum(a.impact_monthly_usd for a in action_plan if "goals" not in (a.tags or []))
        monthly_total = max(0.0, action_impact)
        return {
            "estimated_monthly_improvement": round(monthly_total, 2),
            "estimated_3_month_improvement": round(monthly_total * 3, 2),
            "estimated_6_month_improvement": round(monthly_total * 6, 2),
            "note": "Projection is approximate and depends on consistency.",
        }
    
    # -------------------------
    # Small utilities
    # -------------------------

    def _extract_subscriptions_from_analysis(self,
                                             analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzer may produce subscriptions under patterns:
          pattern.name == "subscriptions"
          pattern.data["subscriptions"] == list[...]
        """
        patterns = analysis.get("patterns") or []
        for p in patterns:
            if isinstance(p, dict) and p.get("name") == "subscriptions":
                data = p.get("data") or {}
                subs = data.get("subscriptions") or []
                if isinstance(subs, list):
                    return subs
        return []
    
    def _round_nice(self,
                    value: float) -> float:
        """
        Rounds a number to a human-friendly value:
        - < 50: round to nearest 5
        - < 200: round to nearest 10
        - else: round to nearest 25
        """
        v= float(value or 0.0)
        if v<= 0:
            return 0.0
        if v<50:
            return round(v/5) * 5
        if v< 200:
            return(v/10) * 10
        return round(v/25) * 25
    
    def _new_id(self, prefix: str)-> str:
        """
        Simple ID helper for budgets/goals produced by planner"""
        return f"{prefix}_{uuid.uuid4().hex[:10]}"

# Factory
def create_planner() -> PlannerAgent:
    return PlannerAgent()











