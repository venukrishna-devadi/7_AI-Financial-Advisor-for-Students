"""
📊 DASHBOARD - Main Streamlit dashboard for the Student Financial Advisor

Purpose
-------
This is the primary UI page for the app.

It does:
- manage session state for student / transactions / goals / budget
- render the main dashboard experience
- let users create profile, add transactions, set goals, upload images
- run the financial pipeline via FinancialRunner
- display analysis, advice, alerts, and tracking in a polished way

It does NOT:
- contain agent logic
- contain graph logic
- perform raw extraction logic itself

Design goals
------------
- lively and demo-friendly
- stable with Streamlit reruns
- clear separation from business logic
"""

from __future__ import annotations

from datetime import date
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd

from schemas.student import Student
from schemas.transaction import Transaction
from schemas.goal import Goal
from schemas.budget import Budget

from ui.input_forms import (
    load_input_form_styles,
    render_input_welcome_card,
    render_student_profile_form,
    render_manual_transaction_form,
    render_quick_expense_form,
    render_goal_form,
    render_budget_form,
    render_input_summary_preview,
)

from ui.uploaders import (
    render_upload_and_extract_panel,
    render_upload_extract_and_convert_panel,
)
from runners.financial_runner import create_financial_runner


# =========================================================
# PAGE CONFIG
# =========================================================

# st.set_page_config(
#     page_title="Student Financial Advisor",
#     page_icon="📊",
#     layout="wide",
# )


# =========================================================
# COLORS / STYLES
# =========================================================

COLORS = {
    "primary": "#7C3AED",
    "secondary": "#10B981",
    "accent": "#F59E0B",
    "danger": "#EF4444",
    "info": "#3B82F6",
    "bg": "#F8FAFC",
    "card": "#FFFFFF",
    "text": "#111827",
    "muted": "#6B7280",
    "border": "#E5E7EB",
}

GRADIENTS = {
    "hero": "linear-gradient(135deg, #7C3AED 0%, #2563EB 100%)",
    "good": "linear-gradient(135deg, #10B981 0%, #059669 100%)",
    "warn": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
    "bad": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)",
    "info": "linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)",
}

# def initialize_dashboard_state():
#     if "student" not in st.session_state:
#         st.session_state.student = None
#     if "transactions" not in st.session_state:
#         st.session_state.transactions = []
#     if "budget" not in st.session_state:
#         st.session_state.budget = None
#     if "goals" not in st.session_state:
#         st.session_state.goals = []
#     if "runner_result" not in st.session_state:
#         st.session_state.runner_result = None
#     if "last_upload_result" not in st.session_state:
#         st.session_state.last_upload_result = None

# def refresh_financial_analysis():
#     student = st.session_state.student
#     transactions = st.session_state.transactions
#     budget = st.session_state.budget
#     goals = st.session_state.goals

#     if not student:
#         st.session_state.runner_result = None
#         return

#     runner = create_financial_runner()

#     result = runner.run_from_transactions(
#         student=student,
#         transactions=transactions,
#         budget=budget,
#         goals=goals,
#     )

#     st.session_state.runner_result = result

def load_dashboard_styles():
    st.markdown(
        f"""
        <style>
        .main {{
            background-color: {COLORS['bg']};
        }}

        .dash-hero {{
            border-radius: 24px;
            padding: 2rem 1.7rem;
            margin-bottom: 1.5rem;
            background: {GRADIENTS['hero']};
            color: white;
            box-shadow: 0 20px 40px rgba(124, 58, 237, 0.22);
        }}

        .dash-hero h1, .dash-hero p {{
            color: white !important;
            margin: 0;
        }}

        .dash-card {{
            border-radius: 20px;
            padding: 1.2rem 1.2rem;
            margin-bottom: 1rem;
            background: white;
            border: 1px solid {COLORS['border']};
            box-shadow: 0 8px 18px rgba(0,0,0,0.03);
        }}

        .dash-soft {{
            border-radius: 16px;
            padding: 1rem 1rem;
            margin-bottom: 0.85rem;
            background: rgba(124,58,237,0.05);
            border: 1px solid rgba(124,58,237,0.10);
        }}

        .dash-good {{
            border-radius: 16px;
            padding: 0.95rem 1rem;
            background: rgba(16,185,129,0.10);
            border: 1px solid rgba(16,185,129,0.18);
        }}

        .dash-warn {{
            border-radius: 16px;
            padding: 0.95rem 1rem;
            background: rgba(245,158,11,0.10);
            border: 1px solid rgba(245,158,11,0.18);
        }}

        .dash-bad {{
            border-radius: 16px;
            padding: 0.95rem 1rem;
            background: rgba(239,68,68,0.10);
            border: 1px solid rgba(239,68,68,0.18);
        }}

        .dash-pill {{
            display: inline-block;
            padding: 0.28rem 0.75rem;
            border-radius: 999px;
            background: rgba(59,130,246,0.10);
            color: #1D4ED8;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-top: 0.25rem;
        }}

        .dash-section-title {{
            font-size: 1.35rem;
            font-weight: 700;
            color: {COLORS['text']};
            margin-bottom: 0.8rem;
        }}

        div[data-testid="stMetric"] {{
            background: white;
            border: 1px solid {COLORS['border']};
            border-radius: 18px;
            padding: 0.8rem;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 1.75rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# SESSION STATE
# =========================================================

def init_session_state():
    defaults = {
    "student": None,
    "transactions": [],
    "goals": [],
    "budget": None,
    "last_runner_result": None,
    "last_upload_batch": None,
    "last_vision_result": None,
}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =========================================================
# HELPERS
# =========================================================

def render_hero():
    st.markdown(
        """
        <div class="dash-hero">
            <h1>📊 Student Financial Advisor Dashboard</h1>
            <p style="margin-top:0.5rem; font-size:1.12rem;">
                Track spending, upload receipts, build goals, and get personalized AI financial guidance.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_health_style(health: str) -> str:
    if health == "healthy":
        return "dash-good"
    if health == "warning":
        return "dash-warn"
    if health == "critical":
        return "dash-bad"
    return "dash-soft"


def run_pipeline_if_possible():
    student: Optional[Student] = st.session_state.student
    transactions: List[Transaction] = st.session_state.transactions
    goals: List[Goal] = st.session_state.goals
    budget: Optional[Budget] = st.session_state.budget

    if student is None:
        return None

    if not transactions:
        return None

    runner = create_financial_runner()
    result = runner.run_from_transactions(
        student=student,
        transactions=transactions,
        budget=budget,
        goals=goals,
    )
    st.session_state.last_runner_result = result
    return result


def transactions_to_df(transactions: List[Transaction]) -> pd.DataFrame:
    if not transactions:
        return pd.DataFrame(columns=["date", "description", "category", "merchant", "type", "amount"])

    rows = []
    for t in transactions:
        rows.append(
            {
                "date": str(t.date),
                "description": t.description,
                "category": t.category,
                "merchant": t.merchant or "",
                "type": t.transaction_type.value if hasattr(t.transaction_type, "value") else str(t.transaction_type),
                "amount": float(t.amount),
                "source": getattr(t, "source", ""),
                "confidence": getattr(t, "confidence", ""),
            }
        )
    return pd.DataFrame(rows)


def render_snapshot_cards():
    student: Optional[Student] = st.session_state.student
    transactions: List[Transaction] = st.session_state.transactions
    goals: List[Goal] = st.session_state.goals
    budget: Optional[Budget] = st.session_state.budget
    result = st.session_state.last_runner_result

    income = float(student.monthly_income) if student else 0.0
    fixed = float(student.total_fixed_expenses()) if student else 0.0
    disposable = float(student.estimated_disposable_income()) if student else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Monthly Income", f"${income:,.0f}")
    with c2:
        st.metric("Fixed Expenses", f"${fixed:,.0f}")
    with c3:
        st.metric("Disposable", f"${disposable:,.0f}")
    with c4:
        st.metric("Transactions", len(transactions))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Goals", len(goals))
    with c6:
        st.metric("Budget", "Set" if budget else "Not set")
    with c7:
        health = result.overall_health if result else "unknown"
        st.metric("Overall Health", health.title())
    with c8:
        alerts = result.alert_total if result else 0
        st.metric("Alerts", alerts)


def render_status_banner():
    result = st.session_state.last_runner_result
    if not result:
        st.info("Add a student profile and at least one transaction to generate insights.")
        return

    css_class = get_health_style(result.overall_health)
    st.markdown(
        f"""
        <div class="{css_class}">
            <strong>Current Health:</strong> {result.overall_health.title()}<br/>
            <strong>Budget Health:</strong> {result.budget_health.title()} |
            <strong>Budget Used:</strong> {result.budget_percent_used:.1f}% |
            <strong>Alerts:</strong> {result.alert_total}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_transactions_table():
    st.markdown('<div class="dash-section-title">💳 Transactions</div>', unsafe_allow_html=True)

    df = transactions_to_df(st.session_state.transactions)
    if df.empty:
        st.markdown('<div class="dash-soft">No transactions added yet.</div>', unsafe_allow_html=True)
        return

    st.dataframe(df, width="stretch", hide_index=True)

    if not df.empty:
        by_category = df.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        st.bar_chart(by_category.set_index("category"))


def render_goals_panel():
    st.markdown('<div class="dash-section-title">🎯 Goals</div>', unsafe_allow_html=True)

    goals: List[Goal] = st.session_state.goals
    if not goals:
        st.markdown('<div class="dash-soft">No goals created yet.</div>', unsafe_allow_html=True)
        return

    for goal in goals:
        progress = float(goal.current_amount / goal.target_amount * 100.0) if goal.target_amount > 0 else 0.0
        st.markdown(
            f"""
            <div class="dash-card">
                <strong>{goal.name}</strong><br/>
                Category: {goal.category.value if hasattr(goal.category, 'value') else goal.category} |
                Priority: {goal.priority.value if hasattr(goal.priority, 'value') else goal.priority}<br/>
                Saved: ${float(goal.current_amount):,.2f} / ${float(goal.target_amount):,.2f}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(progress, 100.0) / 100.0, text=f"Progress: {progress:.1f}%")


def render_budget_panel():
    st.markdown('<div class="dash-section-title">💰 Budget</div>', unsafe_allow_html=True)

    budget: Optional[Budget] = st.session_state.budget
    result = st.session_state.last_runner_result

    if budget is None:
        st.markdown('<div class="dash-soft">No budget created yet.</div>', unsafe_allow_html=True)
        return

    budget_categories = []
    for bc in budget.categories:
        budget_categories.append(
            {
                "category": str(bc.category),
                "limit": float(bc.limit),
            }
        )

    df = pd.DataFrame(budget_categories)
    st.dataframe(df, width="stretch", hide_index=True)

    if result and result.tracking_report:
        budget_status = result.tracking_report.get("budget_status", {})
        st.markdown(
            f"""
            <div class="dash-soft">
                <strong>Status:</strong> {budget_status.get("status", "unknown").title()}<br/>
                <strong>Percent Used:</strong> {budget_status.get("percent_used", 0):.1f}%<br/>
                <strong>Categories Over Budget:</strong> {budget_status.get("categories_over_budget", 0)}<br/>
                <strong>Categories in Warning:</strong> {budget_status.get("categories_in_warning", 0)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_advice_panel():
    st.markdown('<div class="dash-section-title">🧠 AI Advice</div>', unsafe_allow_html=True)

    result = st.session_state.last_runner_result
    if not result or not result.advice_result:
        st.markdown('<div class="dash-soft">Run the pipeline to see advice.</div>', unsafe_allow_html=True)
        return

    advice = result.advice_result.get("advice", {})

    st.markdown(
        f"""
        <div class="{get_health_style(advice.get('overall_financial_health', 'unknown'))}">
            <strong>Summary:</strong><br/>
            {advice.get("advisor_summary", "No summary available.")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🎯 Top Priorities")
        for item in advice.get("top_priorities", []):
            st.markdown(f"- {item}")

    with col2:
        st.markdown("#### ⚡ Immediate Actions")
        for item in advice.get("immediate_actions", []):
            st.markdown(f"- {item}")

    strategic = advice.get("strategic_advice", [])
    if strategic:
        st.markdown("#### 📈 Strategic Advice")
        for item in strategic:
            st.markdown(f"- {item}")

    encouragement = advice.get("encouragement", [])
    if encouragement:
        st.markdown("#### 🌟 Encouragement")
        for item in encouragement:
            st.markdown(f"- {item}")


def render_alerts_panel():
    st.markdown('<div class="dash-section-title">🚨 Alerts</div>', unsafe_allow_html=True)

    result = st.session_state.last_runner_result
    if not result or not result.alert_result:
        st.markdown('<div class="dash-soft">Run the pipeline to see alerts.</div>', unsafe_allow_html=True)
        return

    summary = result.alert_result.get("summary", {})
    alerts = result.alert_result.get("alerts", [])

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.metric("Total", summary.get("total_alerts", 0))
    with s2:
        st.metric("Critical", summary.get("critical_count", 0))
    with s3:
        st.metric("Warning", summary.get("warning_count", 0))
    with s4:
        st.metric("Info", summary.get("info_count", 0))

    if not alerts:
        st.markdown('<div class="dash-good">✅ No active alerts.</div>', unsafe_allow_html=True)
        return

    for alert in alerts:
        severity = alert.get("severity", "info")
        css = "dash-soft"
        if severity == "critical":
            css = "dash-bad"
        elif severity == "warning":
            css = "dash-warn"

        st.markdown(
            f"""
            <div class="{css}">
                <strong>{alert.get("title", "Alert")}</strong><br/>
                {alert.get("message", "")}<br/><br/>
                <strong>Recommended action:</strong> {alert.get("recommended_action", "")}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_upload_section():
    st.markdown('<div class="dash-section-title">📤 Upload & Extract</div>', unsafe_allow_html=True)

    student: Optional[Student] = st.session_state.student

    tab1, tab2 = st.tabs(["🔍 Extract Only", "⚡ Extract + Convert"])

    with tab1:
        batch_result = render_upload_and_extract_panel(
           allow_multiple=False,
           task_type="general_financial",
           uploader_key="dashboard_extract_only",)
        if batch_result:
            st.session_state.last_upload_batch = batch_result

    with tab2:
        if student is None:
            st.warning("Create a student profile first before converting uploads into transactions.")
            return

        upload_result = render_upload_extract_and_convert_panel(
    student_id=student.student_id,
    allow_multiple=False,
    task_type="general_financial",
    uploader_key="dashboard_extract_convert",
)

        if upload_result:
            st.session_state.last_upload_batch = upload_result

            if upload_result.get("vision_result"):
                st.session_state.last_vision_result = upload_result["vision_result"]

            if upload_result.get("success"):
                new_transactions = upload_result.get("transactions", [])
                existing_ids = {txn.transaction_id for txn in st.session_state.transactions}

                unique_new_transactions = [
                    txn for txn in new_transactions
                    if txn.transaction_id not in existing_ids
                ]

                if unique_new_transactions:
                    st.session_state.transactions.extend(unique_new_transactions)
                    st.success(f"Added {len(unique_new_transactions)} new transaction(s).")
                    run_pipeline_if_possible()
                    st.rerun()

# =========================================================
# SIDEBAR
# =========================================================

def render_sidebar():
    st.sidebar.markdown("## 🧭 Navigation")

    # Define steps in order
    steps = [
        "Overview",
        "Profile",
        "Transactions",
        "Goals",
        "Budget",
        "Upload",
        "Results",
    ]

    # Keep current section in session state
    if "section" not in st.session_state:
        st.session_state.section = "Overview"

    # Render steps as buttons
    for i, step in enumerate(steps, start=1):
        is_active = st.session_state.section == step
        # Visual marker: ✓ for completed, → for current, ○ for upcoming
        if i < steps.index(st.session_state.section) + 1:
            prefix = "✓"
        elif is_active:
            prefix = "→"
        else:
            prefix = "○"

        if st.sidebar.button(
            f"{prefix} {i}. {step}",
            key=f"nav_{step}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.section = step
            st.rerun()

    st.sidebar.markdown("---")

    # Action buttons
    if st.sidebar.button("🔄 Run Analysis", use_container_width=True):
        result = run_pipeline_if_possible()
        if result:
            st.sidebar.success("Analysis complete.")
            st.session_state.section = "Results"
            st.rerun()
        else:
            st.sidebar.warning("Need a student profile and transactions first.")

    if st.sidebar.button("🧹 Clear Session", use_container_width=True):
        for key in [
            "student",
            "transactions",
            "goals",
            "budget",
            "last_runner_result",
            "last_upload_batch",
            "last_vision_result",
            "section",
        ]:
            st.session_state[key] = None if key!= "transactions" and key!= "goals" else []
        st.rerun()

    return st.session_state.section


# =========================================================
# MAIN PAGE RENDERING
# =========================================================

def render_overview():
    if st.session_state.student and st.session_state.transactions and st.session_state.last_runner_result is None:
        run_pipeline_if_possible()
    
    render_snapshot_cards()
    render_status_banner()

    col1, col2 = st.columns([1.2, 1])
    with col1:
        render_transactions_table()
    with col2:
        render_goals_panel()

    col3, col4 = st.columns([1, 1])
    with col3:
        render_budget_panel()
    with col4:
        render_alerts_panel()

    render_advice_panel()

def render_profile_page():
    student = render_student_profile_form(existing_student=st.session_state.student)
    if student:
        st.session_state.student = student
        run_pipeline_if_possible()
        st.rerun()

    render_input_summary_preview(
        student=st.session_state.student,
        transactions=st.session_state.transactions,
        goals=st.session_state.goals,
        budget=st.session_state.budget,
    )


def render_transactions_page():
    st.markdown("## 💳 Add Transactions")

    t1, t2 = st.tabs(["⚡ Quick Add", "📝 Full Entry"])

    student = st.session_state.student
    if student is None:
        st.warning("Create a student profile first.")
        return

    with t1:
        txn = render_quick_expense_form(student.student_id)
        if txn:
            existing_ids = {t.transaction_id for t in st.session_state.transactions}
            if txn.transaction_id not in existing_ids:
                st.session_state.transactions.append(txn)
                run_pipeline_if_possible()
                st.rerun()

    with t2:
        txn = render_manual_transaction_form(student.student_id)
        if txn:
            existing_ids = {t.transaction_id for t in st.session_state.transactions}
            if txn.transaction_id not in existing_ids:
                st.session_state.transactions.append(txn)
                run_pipeline_if_possible()
                st.rerun()

    st.markdown("---")
    render_transactions_table()


def render_goals_page():
    st.markdown("## 🎯 Goals")

    student = st.session_state.student
    if student is None:
        st.warning("Create a student profile first.")
        return

    goal = render_goal_form(student.student_id)
    if goal:
        st.session_state.goals.append(goal)
        run_pipeline_if_possible()
        st.rerun()

    st.markdown("---")
    render_goals_panel()


def render_budget_page():
    st.markdown("## 💰 Budget")

    student = st.session_state.student
    if student is None:
        st.warning("Create a student profile first.")
        return

    budget = render_budget_form(
        student_id=student.student_id,
        monthly_income=student.monthly_income,
        existing_budget=st.session_state.budget,
    )
    if budget:
        st.session_state.budget = budget
        run_pipeline_if_possible()
        st.rerun()

    st.markdown("---")
    render_budget_panel()


def render_upload_page():
    st.markdown("## 📤 Upload Financial Documents")
    render_upload_section()


def render_results_page():
    st.markdown("## 🧠 Results")
    render_status_banner()

    tab1, tab2, tab3 = st.tabs(["Advice", "Alerts", "Raw Result"])

    with tab1:
        render_advice_panel()

    with tab2:
        render_alerts_panel()

    with tab3:
        result = st.session_state.last_runner_result
        if result:
            st.json(result.to_dict())
        else:
            st.info("No runner result yet.")


# =========================================================
# APP
# =========================================================

def main():
    init_session_state()
    load_input_form_styles()
    load_dashboard_styles()

    render_hero()
    if st.session_state.student is None:
        render_input_welcome_card()

    section = render_sidebar()

    if section == "Overview":
        render_overview()
    elif section == "Profile":
        render_profile_page()
    elif section == "Transactions":
        render_transactions_page()
    elif section == "Goals":
        render_goals_page()
    elif section == "Budget":
        render_budget_page()
    elif section == "Upload":
        render_upload_page()
    elif section == "Results":
        render_results_page()


if __name__ == "__main__":
    main()