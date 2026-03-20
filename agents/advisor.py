"""
🧠 ADVISOR AGENT - Personalized financial coaching using LLM reasoning

Why this agent exists
---------------------
1. Analyzer tells us: What patterns exist?
2. Planner tells us: What plan should the student follow?
3. Tracker tells us: How is the student doing right now?

Advisor's job
-------------
1. Read all the structured data from previous agents
2. Use the LLM to interpret it like a financial coach
3. Return student-friendly, practical, personalized advice

Important design principle
--------------------------
We use the LLM for:
- interpretation
- prioritization
- communication

We do NOT use the LLM for:
- raw math
- budget calculations
- severity calculation
- factual financial metrics

Those should already come from Analyzer / Planner / Tracker.

This agent is intentionally structured like your other agents:
1. one main public method
2. helper methods for context building
3. prompt building
4. validation
5. fallback response
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Any, Literal
import json

from schemas.student import Student
from schemas.goal import Goal
from utils.llm_wrapper import llm_wrapper


# ---------------------------------------------------------
# Type aliases
# ---------------------------------------------------------

HealthStatus = Literal["healthy", "warning", "critical", "unknown"]


# ---------------------------------------------------------
# Advisor Agent
# ---------------------------------------------------------

class AdvisorAgent:
    """
    AdvisorAgent answers:
    "Given the student's financial situation, what should they do next?"

    This agent:
    1. Collects structured outputs from other agents
    2. Builds a compact and useful LLM context
    3. Calls the LLM for coaching-style advice
    4. Validates the LLM output
    5. Applies deterministic guardrails so unsafe/wrong outputs get corrected
    6. Falls back safely if the LLM fails
    """

    def __init__(self, name: str = "Advisor Agent"):
        self.name = name

        # Future enhancement:
        # keep a lightweight conversation memory for follow-up questions.
        self.conversation_history: List[Dict[str, str]] = []

        # Fixed categories are hard to change quickly.
        # We don't want the LLM to over-focus on these for "this week" actions.
        self.fixed_expense_categories = {
            "housing", "rent", "utilities", "internet", "phone", "tuition", "insurance"
        }

        # Flexible categories are the first places where short-term coaching
        # can realistically help the student cut spending.
        self.flexible_expense_categories = {
            "food", "groceries", "dining_out", "coffee",
            "entertainment", "streaming", "games", "movies",
            "shopping", "clothing", "electronics", "amazon",
            "transport", "gas", "uber", "public_transit",
            "personal_care", "travel"
        }

        # Severity ranking helps us prevent the LLM from downgrading a bad situation.
        self.severity_rank = {
            "unknown": 0,
            "healthy": 1,
            "warning": 2,
            "critical": 3,
        }

    # -----------------------------------------------------
    # Public entrypoint
    # -----------------------------------------------------

    def advice_student(
        self,
        *,
        student: Student,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
        tracking_report: Dict[str, Any],
        goals: Optional[List[Goal]] = None,
        previous_advice: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main function to generate advisor output.

        Inputs
        ------
        student:
            Student profile / personal financial setup

        analysis:
            Output from Analyzer agent

        plan:
            Output from Planner agent

        tracking_report:
            Output from Tracker agent

        goals:
            Optional list of Goal objects

        previous_advice:
            Optional past advice so the model can avoid repeating itself

        Returns
        -------
        Structured dictionary:
        {
            "student_id": ...,
            "advisor_date": ...,
            "advice": ...,
            "metadata": ...
        }
        """

        goals = goals or []

        # Build compact context for the LLM.
        context = self._build_context(
            student=student,
            analysis=analysis,
            plan=plan,
            tracking_report=tracking_report,
            goals=goals,
        )

        # Deterministic health status used as a fallback and a guardrail.
        deterministic_health = self._detect_health_category(
            tracking_report=tracking_report,
            analysis=analysis,
            plan=plan,
        )
        

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            context=context,
            previous_advice=previous_advice,
        )

        try:
            response = llm_wrapper.generate_structured_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_format='''{
  "overall_financial_health": "healthy",
  "top_priorities": ["priority 1", "priority 2", "priority 3"],
  "immediate_actions": ["action 1", "action 2", "action 3"],
  "strategic_advice": ["advice 1", "advice 2"],
  "encouragement": ["encouragement 1"],
  "advisor_summary": "summary"
}'''
)

            if not response.get("success", False):
                return self._fallback_response(
                    student=student,
                    health_category=deterministic_health,
                    error=response.get("error", "Unknown LLM failure"),
                )

            # Step 1: validate structure
            advice = self._validate_llm_advice_structure(
                advice=response.get("data", {}),
                default_health=deterministic_health,
            )

            # Step 2: apply deterministic guardrails
            advice = self._apply_guardrails(
                advice=advice,
                deterministic_health=deterministic_health,
                context=context,
            )

            # Store compact history for future follow-up support.
            self.conversation_history.append({
                "role": "assistant",
                "content": json.dumps(advice),
            })

            # NOTE:
            # llm_wrapper currently exposes cumulative token usage, not per-call usage.
            # So "tokens_used" below is cumulative.
            #print(f"[DEBUG] deterministic_health = {deterministic_health}")
            #print(f"[DEBUG] llm_health_after_guardrails = {advice.get('overall_financial_health')}")
            return {
                "student_id": student.student_id,
                "advisor_date": date.today().isoformat(),
                "advice": advice,
                "metadata": {
                    "llm_success": True,
                    "health_category": deterministic_health,
                    "tokens_used_cumulative": response.get("metadata", {}).get("total_tokens_used", 0),
                    "model": response.get("metadata", {}).get("model", "unknown"),
                    "call_count": response.get("metadata", {}).get("call_count", 0),
                    "fallback": False,
                }
            }

        except Exception as e:
            return self._fallback_response(
                student=student,
                health_category=deterministic_health,
                error=str(e),
            )

    # -----------------------------------------------------
    # Context Builder
    # -----------------------------------------------------

    def _build_context(
        self,
        *,
        student: Student,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
        tracking_report: Dict[str, Any],
        goals: List[Goal],
    ) -> Dict[str, Any]:
        """
        Build compact prompt context for the LLM.

        Why not send everything?
        ------------------------
        Because giant raw JSON:
        - wastes tokens
        - reduces output stability
        - makes the model focus on irrelevant details

        So here we:
        - keep important summary metrics
        - keep the strongest patterns
        - split spending problems into fixed vs flexible categories
        - keep only the top planner actions
        """

        summary = analysis.get("summary", {})
        patterns = analysis.get("patterns", [])
        trends = analysis.get("trends", [])
        top_categories_raw = summary.get("top_categories", [])
        fixed = {"housing", "rent", "mortgage", "utilities", "insurance", "internet", "phone"}
        top_variable_categories = [
            c for c in top_categories_raw
            if c.get("category") not in fixed
        ][:4]

        # Keep only the most important patterns
        key_patterns: List[Dict[str, Any]] = []
        for p in patterns[:4]:
            if isinstance(p, dict):
                key_patterns.append({
                    "name": p.get("name", "pattern"),
                    "description": p.get("description", ""),
                    "severity": p.get("severity", "info"),
                })

        # Keep only the most important trends
        key_trends: List[Dict[str, Any]] = []
        for t in trends[:3]:
            if isinstance(t, dict):
                key_trends.append({
                    "type": t.get("type", ""),
                    "description": t.get("description", ""),
                    "severity": t.get("severity", "info"),
                })

        budget_status = tracking_report.get("budget_status", {})

        # IMPORTANT FIX:
        # Your tracker output uses "category_tracking", not "category_report".
        category_tracking = tracking_report.get("category_tracking", {})

        # Separate problem categories into fixed vs flexible.
        # This helps the LLM suggest more realistic immediate actions.
        fixed_problem_categories: List[Dict[str, Any]] = []
        flexible_problem_categories: List[Dict[str, Any]] = []

        for cat, info in category_tracking.items():
            status = info.get("status", "on_track")
            pace_block = info.get("pace", {})
            pace_status = pace_block.get("pace", pace_block.get("status", "on_track"))

            is_problem = (
                status in {"warning", "over_budget"} or
                pace_status == "ahead_of_spend"
            )

            if not is_problem:
                continue

            category_payload = {
                "category": cat,
                "status": status,
                "percent_used": info.get("percent_used", 0.0),
                "limit": info.get("limit", 0),
                "spent": info.get("spent", 0),
                "pace_status": pace_status,
            }

            if cat in self.fixed_expense_categories:
                fixed_problem_categories.append(category_payload)
            else:
                flexible_problem_categories.append(category_payload)

        # Goals summary for LLM
        goal_data: List[Dict[str, Any]] = []
        for g in goals:
            goal_data.append({
                "name": g.name,
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "progress_percent": round(float(g.progress_percent), 1),
                "priority": g.priority.value if hasattr(g.priority, "value") else str(g.priority),
                "days_left": g.days_remaining if getattr(g, "target_date", None) else None,
                "status": g.status.value if hasattr(g.status, "value") else str(g.status),
            })

        # Planner output: keep only top action titles and descriptions
        action_plan = plan.get("action_plan", [])
        compact_actions: List[Dict[str, Any]] = []
        for a in action_plan[:4]:
            if isinstance(a, dict):
                compact_actions.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "priority": a.get("priority", "medium"),
                    "impact_monthly_usd": a.get("impact_monthly_usd", 0),
                })

        # Estimate monthly spending more safely than amount_spent / 3
        monthly_spending_estimate = self._extract_monthly_spending_estimate(
            analysis=analysis,
            plan=plan,
        )
        top_categories_raw = summary.get("top_categories", [])
        top_variable_categories = [
                    c for c in top_categories_raw
                    if c.get("category") not in self.fixed_expense_categories
                ][:4]

        return {
            "student": {
                "name": student.name.split()[0] if getattr(student, "name", None) else "Student",
                "monthly_income": float(getattr(student, "monthly_income", 0.0)),
                "current_savings": float(getattr(student, "current_savings", 0.0)),
                "risk_profile": getattr(student, "risk_profile", "unknown"),
                "graduation_year": getattr(student, "graduation_year", None),
                "analysis_summary": summary,
                "top_categories": top_categories_raw[:4],
                "top_variable_categories": top_variable_categories,
                "estimated_disposable_income": (
                    student.estimated_disposable_income()
                    if hasattr(student, "estimated_disposable_income")
                    else None
                ),
            },
            
            "financial_summary": {
                "monthly_spending_estimate": round(monthly_spending_estimate, 2),
                "savings_rate_percent": self._calculate_savings_rate(summary),
                "net_flow": summary.get("net_flow", 0),
                "top_variable_categories": top_variable_categories,
                "top_categories": top_categories_raw[:4],
                
            "patterns": key_patterns,
            "trends": key_trends,
            "budget_health": {
                "status": budget_status.get("status", "healthy"),
                "percent_used": budget_status.get("percent_used", 0),
                "categories_over_budget": budget_status.get("categories_over_budget", 0),
                "categories_in_warning": budget_status.get("categories_in_warning", 0),
                "pace_status": budget_status.get("pace", {}).get("pace", budget_status.get("pace", {}).get("status", "on_track")),
            },
            "flexible_problem_categories": flexible_problem_categories[:5],
            "fixed_problem_categories": fixed_problem_categories[:3],
            "goals": goal_data,
            "recommended_actions": compact_actions,
            "total_goals": len(goal_data),
            "has_goals": len(goal_data) > 0,
        }
        }

    def _extract_monthly_spending_estimate(
        self,
        *,
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> float:
        """
        Estimate monthly spending in a safer way.

        Priority:
        1. Use planner baseline if present
        2. Else estimate from analysis summary + window_days
        3. Else return 0.0
        """

        baseline = plan.get("baseline", {})

        if isinstance(baseline, dict):
            val = baseline.get("total_spend_est_monthly")
            if isinstance(val, (int, float)):
                return float(val)

            val = baseline.get("variable_spend_est_monthly")
            if isinstance(val, (int, float)):
                return float(val)

        summary = analysis.get("summary", {})
        amount_spent = summary.get("amount_spent", 0)
        window_days = analysis.get("window_days", analysis.get("window_days_used", 90))

        if isinstance(amount_spent, (int, float)) and isinstance(window_days, (int, float)) and window_days > 0:
            return (float(amount_spent) / float(window_days)) * 30.0

        return 0.0

    def _calculate_savings_rate(self, summary: Dict[str, Any]) -> float:
        """
        Savings rate = (income - expenses) / income * 100

        If income is zero or missing, return 0.
        """

        income = summary.get("amount_earned", 0)
        spendings = summary.get("amount_spent", 0)

        if isinstance(income, (int, float)) and income > 0:
            return round(((income - spendings) / income) * 100, 1)

        return 0.0

    def _detect_health_category(
        self,
        *,
        tracking_report: Dict[str, Any],
        analysis: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> HealthStatus:
        """
        Detect overall health using deterministic signals.

        This is NOT the main advice engine.
        This is the safety layer used for fallback and guardrails.

        Priority:
        - critical patterns from analysis
        - tracker budget status
        - otherwise unknown
        """

        budget_status = tracking_report.get("budget_status", {})
        status = budget_status.get("status", "unknown")

        patterns = analysis.get("patterns", [])
        for p in patterns:
            if isinstance(p, dict) and p.get("severity") == "critical":
                return "critical"

        if status in {"healthy", "warning", "critical", "unknown"}:
            return status

        return "unknown"

    # -----------------------------------------------------
    # Prompt Engineering
    # -----------------------------------------------------

    def _build_system_prompt(self) -> str:
        """
        System prompt that defines advisor behavior.

        The key improvement here:
        - force realistic short-term actions
        - prefer flexible expenses before fixed expenses
        - do not downgrade severity
        """
        return """
You are a professional financial advisor for university students. Your job is to synthesize analysis, plan, and tracker outputs into human advice. Responses must be actionable, realistic, and sensitive to student life.

CONTEXT YOU RECEIVE:
- student: name, income, savings, risk profile, graduation_year
- top_variable_categories: flexible spending categories already filtered to exclude fixed costs
- top_categories: overall highest spend categories (may include rent/housing)
- flexible_problem_categories: categories with status warning/over_budget or pace ahead_of_spend that are NOT fixed
- fixed_problem_categories: same, but for fixed expenses (housing, utilities, etc.)
- budget_health: {status, percent_used, categories_over_budget, categories_in_warning, pace_status}
- goals, patterns, trends, recommended_actions

HOW TO THINK:
SHORT-TERM (immediate_actions, 7 days):
- Use ONLY flexible_problem_categories. If empty, use top_variable_categories.
- NEVER output housing/rent/utilities in immediate_actions.
- If flexible_problem_categories is empty and budget_health.status is critical, you may mention housing/rent/utilities only in top_priorities or strategic_advice, not as a this-week step.
- Make actions concrete: "Buy groceries and cook 5 dinners" not "spend less on food".

TOP_PRIORITIES:
- List up to 3 urgent items.
- If flexible problems exist, those come first.
- Make priorities category-specific or goal-specific whenever possible.
- Avoid vague phrases like "reduce biggest spending bucket" unless you also name the category.
- If housing is the only major problem, include it but frame it as a long-term lever, not a quick fix.

STRATEGIC_ADVICE (30–90 days):
- Fixed categories go here.
- "Consider cheaper housing at lease renewal" is valid.
- Goal progress and savings rate belong here.

ENCOURAGEMENT:
- If health is healthy, praise specific wins.
- If warning/critical, be direct but supportive.

ADVISOR_SUMMARY:
- 2–4 sentences max.
- Reference savings_rate, budget_health, and one clear priority.
- No invented numbers.

RULES:
- No invented figures. Use only supplied numbers.
- Respect budget_health.status. Do not downgrade a warning or critical situation to healthy.
- Sound like a supportive coach, not a scold.
- JSON ONLY, no preamble.

OUTPUT FORMAT:
{
 "overall_financial_health": "...",
 "top_priorities": ["...", "...", "..."],
 "immediate_actions": ["...", "...", "..."],
 "strategic_advice": ["...", "..."],
 "encouragement": ["..."],
 "advisor_summary": "..."
}
"""

    def _build_user_prompt(
        self,
        *,
        context: Dict[str, Any],
        previous_advice: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build the user prompt.

        This contains:
        - current student context
        - optional previous advice
        - scenario-specific instructions
        """

        prompt = f"""Analyze this student's financial situation and generate personalized advice.

STUDENT FINANCIAL CONTEXT:
{json.dumps(context, indent=2)}
"""

        if previous_advice:
            prompt += f"""

PREVIOUS ADVICE:
{json.dumps(previous_advice, indent=2)}

If the current data suggests improvement since previous advice, acknowledge that.
If the same issue still exists, mention it without sounding repetitive.
"""

        prompt += """

Instructions:
- Focus on the 3 most important priorities first
- Make immediate actions concrete and realistic for this week
- Make strategic advice useful for the next 1-3 months
- Use a supportive tone
- If budget health is healthy, still provide growth advice
- If budget health is warning or critical, focus more on control and prioritization
- Prefer flexible spending categories over fixed categories for immediate cost-cutting ideas
- Only mention fixed expenses like rent/housing as strategic issues unless clearly necessary
- Keep the summary clear, grounded, and scenario-specific

Return valid JSON only.
"""
        return prompt

    # -----------------------------------------------------
    # Validation / Normalization
    # -----------------------------------------------------

    def _validate_llm_advice_structure(
        self,
        *,
        advice: Dict[str, Any],
        default_health: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Validate and normalize the LLM output.

        LLMs sometimes return:
        - missing keys
        - wrong types
        - too many items
        - invalid status values

        So we normalize before returning to the app.
        """

        defaults = {
            "overall_financial_health": default_health,
            "top_priorities": [],
            "immediate_actions": [],
            "strategic_advice": [],
            "encouragement": ["You're taking a good step by reviewing your finances carefully."],
            "advisor_summary": "Here is a summary of the student's current financial situation.",
        }

        # Fill missing keys
        for key, default_value in defaults.items():
            if key not in advice:
                advice[key] = default_value

        # Validate health label
        if advice.get("overall_financial_health") not in {"healthy", "warning", "critical", "unknown"}:
            advice["overall_financial_health"] = default_health

        # Normalize list-like fields
        list_fields = ["top_priorities", "immediate_actions", "strategic_advice", "encouragement"]

        for field in list_fields:
            value = advice.get(field)

            if isinstance(value, str):
                advice[field] = [value.strip()] if value.strip() else defaults[field]

            elif not isinstance(value, list):
                advice[field] = defaults[field]

            else:
                cleaned_items = []
                for item in value:
                    if isinstance(item, str) and item.strip():
                        cleaned_items.append(item.strip())
                advice[field] = cleaned_items if cleaned_items else defaults[field]

        # Keep UI clean
        advice["top_priorities"] = advice["top_priorities"][:5]
        advice["immediate_actions"] = advice["immediate_actions"][:3]
        advice["strategic_advice"] = advice["strategic_advice"][:3]
        advice["encouragement"] = advice["encouragement"][:2]

        # Validate summary
        if not isinstance(advice.get("advisor_summary"), str) or not advice["advisor_summary"].strip():
            advice["advisor_summary"] = defaults["advisor_summary"]
        else:
            advice["advisor_summary"] = advice["advisor_summary"].strip()

        return advice

    # -----------------------------------------------------
    # Guardrails
    # -----------------------------------------------------

    def _apply_guardrails(
        self,
        *,
        advice: Dict[str, Any],
        deterministic_health: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply deterministic safety / quality guardrails AFTER LLM generation.

        This is the most important hardening step.

        Goals:
        1. Prevent the LLM from downgrading critical/warning situations
        2. Reduce unrealistic immediate actions focused on fixed costs
        3. Make summary match deterministic severity better
        """

        # -------------------------------------------------
        # 1. Severity guardrail
        # -------------------------------------------------
        llm_health = advice.get("overall_financial_health", "unknown")

        llm_rank = self.severity_rank.get(llm_health, 0)
        det_rank = self.severity_rank.get(deterministic_health, 0)

        # Final health should be at least as severe as the deterministic one.
        if det_rank > llm_rank:
            advice["overall_financial_health"] = deterministic_health

        # -------------------------------------------------
        # 2. Fixed-expense immediate-action guardrail
        # -------------------------------------------------
        # If the LLM puts too much weight on rent/housing in immediate actions,
        # soften/reframe it unless that is truly the only issue.
        flexible_problem_categories = context.get("flexible_problem_categories", [])
        fixed_problem_categories = context.get("fixed_problem_categories", [])

        has_flexible_problems = len(flexible_problem_categories) > 0

        rewritten_actions: List[str] = []
        for action in advice.get("immediate_actions", []):
            lower = action.lower()

            refers_to_fixed_housing = any(
                phrase in lower for phrase in [
                    "rent", "housing", "mortgage", "split rent", "roommate", "negotiate rent"
                ]
            )

            # If there are flexible problems available, steer the advice away
            # from unrealistic immediate housing changes.
            if refers_to_fixed_housing and has_flexible_problems:
                replacement = self._build_flexible_replacement_action(flexible_problem_categories)
                rewritten_actions.append(replacement)
            else:
                rewritten_actions.append(action)

        advice["immediate_actions"] = rewritten_actions[:3]

        # -------------------------------------------------
        # 3. Summary alignment guardrail
        # -------------------------------------------------
        # If the final status is critical or warning, make sure summary reflects it.
        summary = advice.get("advisor_summary", "")

        if advice["overall_financial_health"] == "critical":
            if "critical" not in summary.lower():
                advice["advisor_summary"] = (
                    "The student's financial situation is currently critical and needs immediate attention. "
                    + summary
                )
        elif advice["overall_financial_health"] == "warning":
            if "warning" not in summary.lower() and "risk" not in summary.lower():
                advice["advisor_summary"] = (
                    "The student's finances are showing warning signs that should be addressed soon. "
                    + summary
                )
        if self.severity_rank.get(advice["overall_financial_health"], 0) < self.severity_rank.get(deterministic_health, 0):
            advice["overall_financial_health"] = deterministic_health

        return advice

    def _build_flexible_replacement_action(self, flexible_problem_categories: List[Dict[str, Any]]) -> str:
        """
        Build a more realistic immediate action using flexible categories.

        Example:
        - dining_out close to limit -> "Pause dining out for the rest of the week"
        - coffee over pace -> "Set a small coffee cap for this week"
        """
        if not flexible_problem_categories:
            return "Review non-essential spending this week and pause at least one flexible category temporarily."

        top = flexible_problem_categories[0]
        cat = top.get("category", "non-essential spending")

        if cat == "dining_out":
            return "Pause or cut dining-out spending for the rest of this week and shift one or two meals to groceries instead."
        if cat == "coffee":
            return "Set a coffee spending cap for this week and reduce one or two café purchases."
        if cat in {"shopping", "amazon", "electronics", "clothing"}:
            return f"Pause {cat} purchases for the rest of this week unless they are absolutely necessary."
        if cat in {"entertainment", "streaming", "games", "movies"}:
            return f"Keep {cat} spending at zero or near-zero for the rest of this week while budget pressure is high."
        if cat in {"transport", "uber", "gas"}:
            return f"Review this week's {cat} spending and reduce optional trips where possible."

        return f"Reduce {cat} spending this week and set a small short-term cap until the budget stabilizes."

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    def _fallback_response(
        self,
        *,
        student: Student,
        health_category: str,
        error: str = "",
    ) -> Dict[str, Any]:
        """
        Safe fallback response if LLM fails.

        Notice:
        - user-facing advice stays clean
        - internal error stays in metadata only
        """
        fallback_advice = {
            "overall_financial_health": health_category if health_category in {"healthy", "warning", "critical", "unknown"} else "unknown",
            "top_priorities": [
                "Review recent spending patterns",
                "Check current budget progress",
                "Monitor savings and goals regularly",
            ],
            "immediate_actions": [
                "Review this month's largest spending categories",
                "Check whether you are on track with your budget",
                "Update your savings or goal progress",
            ],
            "strategic_advice": [
                "Set a regular weekly money check-in",
                "Review recurring subscriptions and non-essential expenses each month",
            ],
            "encouragement": [
                "You're already doing something valuable by paying attention to your finances."
            ],
            "advisor_summary": (
                f"Based on the available data, the student's financial health appears {health_category}. "
                "Continue tracking spending, reviewing budget progress, and staying consistent with savings habits."
            ),
        }

        return {
            "student_id": student.student_id,
            "advisor_date": date.today().isoformat(),
            "advice": fallback_advice,
            "metadata": {
                "fallback": True,
                "health_category": health_category,
                "error": error,
            }
        }

    # -----------------------------------------------------
    # Future enhancement
    # -----------------------------------------------------

    def follow_up(
        self,
        *,
        student: Student,
        question: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Placeholder for future multi-turn support.
        """
        raise NotImplementedError("follow_up() is reserved for future enhancement.")


# ---------------------------------------------------------
# Factory
# ---------------------------------------------------------

def create_advisor() -> AdvisorAgent:
    """Create and return a new advisor agent instance."""
    return AdvisorAgent()