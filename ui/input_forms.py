# """
# 📝 INPUT FORMS - Clean, reusable Streamlit form components

# Purpose
# -------
# This file renders UI-only forms and returns schema-compatible objects.

# It does:
# - render form inputs
# - perform light validation
# - build Student / Transaction / Goal / Budget objects

# It does NOT:
# - call agents
# - call the graph
# - call runner
# - perform business logic / financial reasoning

# Design notes
# ------------
# - aligned to the current schemas you shared
# - avoids fields not present in your current Student schema
# - uses concrete transaction/budget categories that work better with tracker/analyzer
# """


# from __future__ import annotations

# from datetime import date, timedelta
# from typing import Optional, List, Dict
# import uuid

# import streamlit as st
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# from schemas.student import Student
# from schemas.transaction import Transaction, TransactionType
# from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType
# from schemas.budget import Budget, BudgetCategory, BudgetPeriod



# # =========================================================
# # VIBRANT COLOR CONSTANTS
# # =========================================================

# # COLORS = {
# #     "primary": "#E2E1E5",  # Rich purple
# #     "primary_light": "#E3DDF0",
# #     "primary_dark": "#E4E0EB",
# #     "secondary": "#10B981",  # Emerald green
# #     "secondary_light": "#34D399",
# #     "secondary_dark": "#059669",
# #     "accent": "#F59E0B",  # Amber
# #     "accent_light": "#FBBF24",
# #     "accent_dark": "#D97706",
# #     "danger": "#EF4444",  # Red
# #     "danger_light": "#F87171",
# #     "danger_dark": "#DC2626",
# #     "info": "#D9E0EB",  # Blue
# #     "info_light": "#D8E3F0",
# #     "info_dark": "#D9E1F1",
# #     "success": "#10B981",  # Green
# #     "warning": "#F59E0B",  # Amber
# #     "purple": "#E4DFF1",
# #     "pink": "#EC4899",
# #     "indigo": "#DDDDF0",
# #     "background": "#36393B",
# #     "card_bg": "#090D4704",
# #     "text_primary": "#AEBDD2",
# #     "text_secondary": "#AEC0D8",
# #     "text_tertiary": "#C4D5F4",
# #     "border": "#E5E7EB",
# # }

# # GRADIENTS = {
# #     "primary": "linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)",
# #     "secondary": "linear-gradient(135deg, #10B981 0%, #059669 100%)",
# #     "accent": "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
# #     "info": "linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)",
# #     "danger": "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)",
# #     "purple_pink": "linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%)",
# #     "blue_green": "linear-gradient(135deg, #3B82F6 0%, #10B981 100%)",
# # }

# # =========================================================
# # VIBRANT COLOR CONSTANTS - FIXED FOR READABILITY
# # =========================================================

# COLORS = {
#     "primary": "#4361EE",  # Vibrant blue
#     "primary_light": "#4895EF",
#     "primary_dark": "#3F37C9",
#     "secondary": "#4CC9F0",  # Cyan
#     "secondary_light": "#90F1EF",
#     "secondary_dark": "#3A86FF",
#     "accent": "#F72585",  # Pink
#     "accent_light": "#B5179E",
#     "accent_dark": "#7209B7",
#     "danger": "#EF233C",  # Red
#     "danger_light": "#F87171",
#     "danger_dark": "#D9042B",
#     "info": "#4895EF",  # Light blue
#     "info_light": "#4CC9F0",
#     "info_dark": "#3F37C9",
#     "success": "#06D6A0",  # Mint green
#     "warning": "#FF9F1C",  # Orange
#     "purple": "#9D4EDD",
#     "pink": "#F72585",
#     "indigo": "#560BAD",
#     "background": "#F8F9FA",  # Light gray background
#     "card_bg": "#FFFFFF",  # Pure white cards
#     "text_primary": "#C1C5C8",  # Dark gray - VERY readable
#     "text_secondary": "#E7E7E7",  # Medium gray
#     "text_tertiary": "#ADB5BD",  # Light gray
#     "border": "#DEE2E6",  # Light border
# }

# GRADIENTS = {
#     "primary": "linear-gradient(135deg, #4361EE 0%, #3F37C9 100%)",
#     "secondary": "linear-gradient(135deg, #4CC9F0 0%, #3A86FF 100%)",
#     "accent": "linear-gradient(135deg, #F72585 0%, #7209B7 100%)",
#     "info": "linear-gradient(135deg, #4895EF 0%, #3F37C9 100%)",
#     "danger": "linear-gradient(135deg, #EF233C 0%, #D9042B 100%)",
#     "purple_pink": "linear-gradient(135deg, #9D4EDD 0%, #F72585 100%)",
#     "blue_green": "linear-gradient(135deg, #4361EE 0%, #06D6A0 100%)",
# }

# # =========================================================
# # VIBRANT COLOR CONSTANTS
# # =========================================================



# # =========================================================
# # CONSTANTS
# # =========================================================

# RISK_PROFILE_OPTIONS = ["conservative", "moderate", "aggressive"]

# COMMON_TRANSACTION_CATEGORIES = [
#     "groceries",
#     "dining_out",
#     "coffee",
#     "rent",
#     "housing",
#     "utilities",
#     "internet",
#     "phone",
#     "transport",
#     "gas",
#     "uber",
#     "public_transit",
#     "shopping",
#     "amazon",
#     "electronics",
#     "streaming",
#     "entertainment",
#     "movies",
#     "games",
#     "education",
#     "tuition",
#     "books",
#     "supplies",
#     "health",
#     "medical",
#     "gym",
#     "salary",
#     "refund",
#     "investment",
#     "student_loan",
#     "credit_card",
#     "car_payment",
#     "insurance",
#     "other",
# ]

# CATEGORY_ICONS = {
#     "groceries": "🛒",
#     "dining_out": "🍽️",
#     "coffee": "☕",
#     "rent": "🏠",
#     "housing": "🏠",
#     "utilities": "💡",
#     "internet": "🌐",
#     "phone": "📱",
#     "transport": "🚗",
#     "gas": "⛽",
#     "uber": "🚕",
#     "public_transit": "🚌",
#     "shopping": "🛍️",
#     "amazon": "📦",
#     "electronics": "💻",
#     "streaming": "📺",
#     "entertainment": "🎮",
#     "movies": "🎬",
#     "games": "🕹️",
#     "education": "📚",
#     "tuition": "🎓",
#     "books": "📖",
#     "supplies": "✏️",
#     "health": "🏥",
#     "medical": "💊",
#     "gym": "💪",
#     "salary": "💵",
#     "refund": "↩️",
#     "investment": "📈",
#     "student_loan": "🎒",
#     "credit_card": "💳",
#     "car_payment": "🚘",
#     "insurance": "🛡️",
#     "other": "📌",
# }

# RISK_PROFILE_HELP = {
#     "conservative": "You prefer safer, steadier financial decisions.",
#     "moderate": "You like a balance between safety and growth.",
#     "aggressive": "You are comfortable taking more risk for higher upside.",
# }

# DEFAULT_BUDGET_CATEGORIES = [
#     ("groceries", 400.0),
#     ("dining_out", 250.0),
#     ("coffee", 80.0),
#     ("shopping", 200.0),
#     ("transport", 120.0),
#     ("streaming", 40.0),
#     ("entertainment", 100.0),
#     ("books", 60.0),
# ]


# # =========================================================
# # SHARED STYLES
# # =========================================================

# def load_input_form_styles():
#     """Load custom CSS for polished but stable UI with larger fonts."""
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             font-size: 16px;
#             background-color: {COLORS['background']};
#         }}

#         h1 {{
#             font-size: 3rem !important;
#             font-weight: 700 !important;
#             margin-bottom: 1rem !important;
#         }}

#         h2 {{
#             font-size: 2.4rem !important;
#             font-weight: 650 !important;
#             margin-bottom: 0.75rem !important;
#         }}

#         h3 {{
#             font-size: 1.9rem !important;
#             font-weight: 600 !important;
#             margin-bottom: 0.5rem !important;
#         }}

#         h4 {{
#             font-size: 1.35rem !important;
#             font-weight: 550 !important;
#         }}

#         p, li {{
#             font-size: 1.05rem !important;
#             line-height: 1.6 !important;
#             color: {COLORS['text_secondary']};
#         }}

#         .stTextInput input,
#         .stNumberInput input,
#         .stDateInput input {{
#             font-size: 1.05rem !important;
#             padding: 0.65rem !important;
#         }}

#         .stTextInput label,
#         .stNumberInput label,
#         .stSelectbox label,
#         .stDateInput label,
#         .stMultiSelect label,
#         .stCheckbox label {{
#             font-size: 1.05rem !important;
#             font-weight: 500 !important;
#             margin-bottom: 0.25rem !important;
#         }}

#         .stButton button {{
#             font-size: 1.1rem !important;
#             font-weight: 600 !important;
#             padding: 0.75rem 1.5rem !important;
#             border-radius: 12px !important;
#             transition: all 0.25s ease !important;
#         }}

#         .stButton button:hover {{
#             transform: translateY(-2px);
#             box-shadow: 0 10px 20px rgba(0,0,0,0.08);
#         }}

#         [data-testid="stMetricValue"] {{
#             font-size: 1.8rem !important;
#             font-weight: 700 !important;
#         }}

#         [data-testid="stMetricLabel"] {{
#             font-size: 1rem !important;
#             font-weight: 500 !important;
#             color: {COLORS['text_secondary']} !important;
#         }}

#         .fa-hero {{
#             border-radius: 24px;
#             padding: 2rem 1.75rem;
#             margin-bottom: 2rem;
#             background: {GRADIENTS['primary']};
#             color: white;
#             box-shadow: 0 20px 40px rgba(124, 58, 237, 0.25);
#         }}

#         .fa-hero h1, .fa-hero h2, .fa-hero h3, .fa-hero p {{
#             color: white !important;
#             margin: 0;
#         }}

#         .fa-card {{
#             border-radius: 20px;
#             padding: 1.4rem 1.4rem;
#             margin-bottom: 1.25rem;
#             background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(139,92,246,0.04));
#             border: 1.5px solid rgba(124,58,237,0.12);
#             box-shadow: 0 8px 20px rgba(0,0,0,0.03);
#         }}

#         .fa-soft-box {{
#             border-radius: 16px;
#             padding: 1rem 1rem;
#             margin-bottom: 1rem;
#             background: {COLORS['card_bg']};
#             border: 1.5px solid {COLORS['border']};
#             box-shadow: 0 4px 12px rgba(0,0,0,0.02);
#         }}

#         .fa-success {{
#             border-radius: 16px;
#             padding: 1rem 1.2rem;
#             background: rgba(16,185,129,0.10);
#             border: 1.5px solid rgba(16,185,129,0.22);
#             font-size: 1.05rem;
#         }}

#         .fa-warning {{
#             border-radius: 16px;
#             padding: 1rem 1.2rem;
#             background: rgba(245,158,11,0.10);
#             border: 1.5px solid rgba(245,158,11,0.22);
#             font-size: 1.05rem;
#         }}

#         div[data-testid="stForm"] {{
#             border: 1.5px solid {COLORS['border']};
#             border-radius: 24px;
#             padding: 1.5rem 1.5rem 1rem 1.5rem;
#             background: {COLORS['card_bg']};
#             box-shadow: 0 10px 25px rgba(0,0,0,0.03);
#         }}

#         div[data-testid="stMetric"] {{
#             background: {COLORS['card_bg']};
#             border: 1.5px solid {COLORS['border']};
#             border-radius: 16px;
#             padding: 1rem;
#         }}

#         .stProgress > div > div > div {{
#             background: {GRADIENTS['secondary']} !important;
#             height: 12px !important;
#             border-radius: 999px !important;
#         }}

#         hr {{
#             margin: 2rem 0 !important;
#             border: 1px solid {COLORS['border']} !important;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True,
#     )


# # =========================================================
# # HELPERS
# # =========================================================

# def _safe_enum_values(enum_cls) -> List[str]:
#     return [member.value for member in enum_cls]


# def _current_month_range() -> tuple[date, date]:
#     today = date.today()
#     start_date = date(today.year, today.month, 1)

#     if today.month == 12:
#         end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
#     else:
#         end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

#     return start_date, end_date


# def _build_fixed_expenses(
#     rent: float,
#     utilities: float,
#     internet: float,
#     phone: float,
#     insurance: float,
#     student_loan: float,
#     credit_card: float,
#     car_payment: float,
# ) -> Dict[str, float]:
#     fixed_expenses: Dict[str, float] = {}

#     if rent > 0:
#         fixed_expenses["rent"] = float(rent)
#     if utilities > 0:
#         fixed_expenses["utilities"] = float(utilities)
#     if internet > 0:
#         fixed_expenses["internet"] = float(internet)
#     if phone > 0:
#         fixed_expenses["phone"] = float(phone)
#     if insurance > 0:
#         fixed_expenses["insurance"] = float(insurance)
#     if student_loan > 0:
#         fixed_expenses["student_loan"] = float(student_loan)
#     if credit_card > 0:
#         fixed_expenses["credit_card"] = float(credit_card)
#     if car_payment > 0:
#         fixed_expenses["car_payment"] = float(car_payment)

#     return fixed_expenses


# def _render_hero(title: str, subtitle: str):
#     st.markdown(
#         f"""
#         <div class="fa-hero">
#             <h1>{title}</h1>
#             <p style="font-size: 1.25rem !important; margin-top:0.5rem;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def _render_section_header(title: str, subtitle: str, emoji: str = "✨"):
#     st.markdown(
#         f"""
#         <div class="fa-card">
#             <h3 style="margin-bottom:0.25rem;">{emoji} {title}</h3>
#             <p style="margin-bottom:0;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def _profile_completion_score(
#     name: str,
#     monthly_income: float,
#     fixed_expenses: Dict[str, float],
#     preferred_categories: List[str],
# ) -> int:
#     score = 0
#     if name.strip():
#         score += 30
#     if monthly_income > 0:
#         score += 25
#     if fixed_expenses:
#         score += 25
#     if preferred_categories:
#         score += 20
#     return min(score, 100)


# def _render_budget_guide(monthly_income: float):
#     if monthly_income <= 0:
#         st.info("💰 Enter monthly income to unlock a budget guide.")
#         return

#     needs = monthly_income * 0.50
#     wants = monthly_income * 0.30
#     savings = monthly_income * 0.20

#     st.markdown(
#         f"""
#         <div style="
#             background: linear-gradient(135deg, {COLORS['primary']}10, {COLORS['secondary']}08);
#             border-radius: 20px;
#             padding: 1.25rem;
#             margin: 1rem 0 1.5rem 0;
#             border: 1.5px solid {COLORS['border']};
#         ">
#             <h4 style="margin-bottom: 0.9rem;">📊 50 / 30 / 20 Budget Guide</h4>
#             <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
#                 <div style="text-align:center;">
#                     <div style="font-size: 1.9rem; font-weight:700; color:{COLORS['info']};">${needs:,.0f}</div>
#                     <div style="font-size: 1rem; color:{COLORS['text_secondary']};">Needs (50%)</div>
#                 </div>
#                 <div style="text-align:center;">
#                     <div style="font-size: 1.9rem; font-weight:700; color:{COLORS['accent']};">${wants:,.0f}</div>
#                     <div style="font-size: 1rem; color:{COLORS['text_secondary']};">Wants (30%)</div>
#                 </div>
#                 <div style="text-align:center;">
#                     <div style="font-size: 1.9rem; font-weight:700; color:{COLORS['success']};">${savings:,.0f}</div>
#                     <div style="font-size: 1rem; color:{COLORS['text_secondary']};">Savings (20%)</div>
#                 </div>
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# # =========================================================
# # OPTIONAL INPUT PAGE HERO
# # =========================================================

# def render_input_welcome_card():
#     load_input_form_styles()
#     _render_hero(
#         "🎓 Student Financial Advisor",
#         "Build your financial foundation with interactive tools that feel modern, clear, and motivating.",
#     )

#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.markdown(
#             """
#             <div class="fa-soft-box" style="text-align:center;">
#                 <div style="font-size:2.3rem;">👤</div>
#                 <div style="font-size:1.15rem; font-weight:600;">Profile</div>
#                 <div style="font-size:0.95rem;">Income + bills</div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
#     with col2:
#         st.markdown(
#             """
#             <div class="fa-soft-box" style="text-align:center;">
#                 <div style="font-size:2.3rem;">💰</div>
#                 <div style="font-size:1.15rem; font-weight:600;">Transactions</div>
#                 <div style="font-size:0.95rem;">Track spending</div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
#     with col3:
#         st.markdown(
#             """
#             <div class="fa-soft-box" style="text-align:center;">
#                 <div style="font-size:2.3rem;">🎯</div>
#                 <div style="font-size:1.15rem; font-weight:600;">Goals</div>
#                 <div style="font-size:0.95rem;">Savings targets</div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )
#     with col4:
#         st.markdown(
#             """
#             <div class="fa-soft-box" style="text-align:center;">
#                 <div style="font-size:2.3rem;">📊</div>
#                 <div style="font-size:1.15rem; font-weight:600;">Budget</div>
#                 <div style="font-size:0.95rem;">Spending limits</div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )


# # =========================================================
# # STUDENT PROFILE FORM
# # =========================================================

# def render_student_profile_form(existing_student: Optional[Student] = None) -> Optional[Student]:
#     """
#     Interactive student profile form aligned to current Student schema.
#     """
#     load_input_form_styles()
#     _render_section_header(
#         "Student Profile",
#         "Create a personalized financial profile that powers advice, budget tracking, and alerts.",
#         "👤",
#     )

#     existing_fixed = existing_student.fixed_monthly_expenses if existing_student else {}
#     default_name = existing_student.name if existing_student else ""
#     default_age = int(existing_student.age) if existing_student and existing_student.age is not None else 20
#     default_income = float(existing_student.monthly_income) if existing_student else 0.0
#     default_risk = existing_student.risk_profile if existing_student else "moderate"
#     default_categories = existing_student.preferred_categories if existing_student else []

#     preview_fixed = _build_fixed_expenses(
#         float(existing_fixed.get("rent", 0.0)),
#         float(existing_fixed.get("utilities", 0.0)),
#         float(existing_fixed.get("internet", 0.0)),
#         float(existing_fixed.get("phone", 0.0)),
#         float(existing_fixed.get("insurance", 0.0)),
#         float(existing_fixed.get("student_loan", 0.0)),
#         float(existing_fixed.get("credit_card", 0.0)),
#         float(existing_fixed.get("car_payment", 0.0)),
#     )

#     completion_score = _profile_completion_score(
#         default_name,
#         default_income,
#         preview_fixed,
#         default_categories,
#     )

#     st.progress(completion_score / 100.0, text=f"Profile completion: {completion_score}%")

#     with st.form("student_profile_form"):
#         col1, col2 = st.columns(2)

#         with col1:
#             name = st.text_input(
#                 "📝 Full Name",
#                 value=default_name,
#                 placeholder="e.g. Alex Johnson",
#             )

#             age = st.number_input(
#                 "🎂 Age",
#                 min_value=13,
#                 max_value=70,
#                 value=default_age,
#                 step=1,
#             )

#             monthly_income = st.number_input(
#                 "💰 Monthly Income ($)",
#                 min_value=0.0,
#                 value=default_income,
#                 step=100.0,
#                 format="%.2f",
#                 help="Use a realistic monthly after-tax amount if possible.",
#             )

#         with col2:
#             risk_profile = st.selectbox(
#                 "⚡ Risk Profile",
#                 options=RISK_PROFILE_OPTIONS,
#                 index=RISK_PROFILE_OPTIONS.index(default_risk),
#                 format_func=lambda x: {
#                     "conservative": "🛡️ Conservative - Safety first",
#                     "moderate": "⚖️ Moderate - Balanced approach",
#                     "aggressive": "🚀 Aggressive - Growth focused",
#                 }.get(x, x),
#             )

#             preferred_categories = st.multiselect(
#                 "⭐ Preferred Categories",
#                 options=COMMON_TRANSACTION_CATEGORIES,
#                 default=default_categories,
#                 format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
#                 help="These categories help personalize your experience.",
#             )

#             st.markdown(
#                 f"""
#                 <div class="fa-soft-box">
#                     <strong>{RISK_PROFILE_HELP[risk_profile]}</strong>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )

#         st.markdown("### 🏠 Fixed Monthly Expenses")
#         st.caption("Approximate amounts are fine. These are your recurring monthly commitments.")

#         row1 = st.columns(4)
#         with row1[0]:
#             rent = st.number_input("🏠 Rent / Housing", min_value=0.0, value=float(existing_fixed.get("rent", 0.0)), step=50.0, format="%.2f")
#         with row1[1]:
#             utilities = st.number_input("💡 Utilities", min_value=0.0, value=float(existing_fixed.get("utilities", 0.0)), step=20.0, format="%.2f")
#         with row1[2]:
#             internet = st.number_input("🌐 Internet", min_value=0.0, value=float(existing_fixed.get("internet", 0.0)), step=10.0, format="%.2f")
#         with row1[3]:
#             phone = st.number_input("📱 Phone", min_value=0.0, value=float(existing_fixed.get("phone", 0.0)), step=10.0, format="%.2f")

#         row2 = st.columns(4)
#         with row2[0]:
#             insurance = st.number_input("🛡️ Insurance", min_value=0.0, value=float(existing_fixed.get("insurance", 0.0)), step=10.0, format="%.2f")
#         with row2[1]:
#             student_loan = st.number_input("🎒 Student Loan", min_value=0.0, value=float(existing_fixed.get("student_loan", 0.0)), step=25.0, format="%.2f")
#         with row2[2]:
#             credit_card = st.number_input("💳 Credit Card Minimum", min_value=0.0, value=float(existing_fixed.get("credit_card", 0.0)), step=25.0, format="%.2f")
#         with row2[3]:
#             car_payment = st.number_input("🚘 Car Payment", min_value=0.0, value=float(existing_fixed.get("car_payment", 0.0)), step=25.0, format="%.2f")

#         fixed_expenses = _build_fixed_expenses(
#             rent,
#             utilities,
#             internet,
#             phone,
#             insurance,
#             student_loan,
#             credit_card,
#             car_payment,
#         )

#         total_fixed = sum(fixed_expenses.values())
#         disposable = max(0.0, monthly_income - total_fixed)
#         fixed_ratio = (total_fixed / monthly_income * 100.0) if monthly_income > 0 else 0.0

#         m1, m2, m3 = st.columns(3)
#         with m1:
#             st.metric("Fixed Expenses", f"${total_fixed:,.2f}")
#         with m2:
#             st.metric("Disposable Income", f"${disposable:,.2f}")
#         with m3:
#             st.metric("Fixed Expense Ratio", f"{fixed_ratio:.1f}%")

#         if monthly_income > 0:
#             if fixed_ratio >= 75:
#                 st.markdown('<div class="fa-warning"><strong>⚠️ Warning:</strong> Your fixed expenses are consuming a large share of income. Flexibility may be tight.</div>', unsafe_allow_html=True)
#             elif fixed_ratio <= 45:
#                 st.markdown('<div class="fa-success"><strong>✅ Great:</strong> Your recurring costs look relatively manageable.</div>', unsafe_allow_html=True)

#         submitted = st.form_submit_button("💾 Save Profile", type="primary",width = "stretch")

#         if submitted:
#             if not name.strip():
#                 st.error("❌ Name is required.")
#                 return None

#             try:
#                 student = Student(
#                     student_id=existing_student.student_id if existing_student else f"STU_{uuid.uuid4().hex[:8].upper()}",
#                     name=name.strip(),
#                     age=int(age),
#                     status="student",
#                     currency="USD",
#                     monthly_income=float(monthly_income),
#                     income_frequency="monthly",
#                     risk_profile=risk_profile,
#                     preferred_categories=preferred_categories,
#                     fixed_monthly_expenses=fixed_expenses,
#                 )
#                 st.success("✅ Profile saved successfully!")
#                 return student
#             except Exception as e:
#                 st.error(f"❌ Could not save profile: {e}")
#                 return None

#         return None


# # =========================================================
# # MANUAL TRANSACTION FORM
# # =========================================================

# def render_manual_transaction_form(student_id: str) -> Optional[Transaction]:
#     """
#     Detailed transaction entry form with live category/amount preview.
#     """
#     load_input_form_styles()
#     _render_section_header(
#         "Manual Transaction Entry",
#         "Add a full transaction with category, merchant, description, and type.",
#         "➕",
#     )

#     with st.form("manual_transaction_form", clear_on_submit=True):
#         col1, col2 = st.columns(2)

#         with col1:
#             amount = st.number_input(
#                 "💰 Amount ($)",
#                 min_value=0.01,
#                 max_value=100000.0,
#                 value=1.00,
#                 step=1.0,
#                 format="%.2f",
#             )

#             txn_type_str = st.selectbox(
#                 "📊 Transaction Type",
#                 options=["expense", "income", "transfer"],
#                 index=0,
#                 format_func=lambda x: {
#                     "expense": "💸 Expense - Money out",
#                     "income": "💵 Income - Money in",
#                     "transfer": "🔄 Transfer - Between accounts",
#                 }.get(x, x),
#             )

#             category = st.selectbox(
#                 "🏷️ Category",
#                 options=COMMON_TRANSACTION_CATEGORIES,
#                 index=COMMON_TRANSACTION_CATEGORIES.index("groceries"),
#                 format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
#             )

#         with col2:
#             txn_date = st.date_input(
#                 "📅 Date",
#                 value=date.today(),
#                 max_value=date.today(),
#             )

#             description = st.text_input(
#                 "📝 Description",
#                 placeholder="e.g. Walmart groceries, Uber ride, Netflix subscription",
#             )

#             merchant = st.text_input(
#                 "🏢 Merchant (optional)",
#                 placeholder="e.g. Walmart, Uber, Starbucks",
#             )

#         st.markdown(
#             f"""
#             <div class="fa-soft-box" style="margin-top: 1rem;">
#                 <strong>📋 Preview:</strong><br>
#                 {CATEGORY_ICONS.get(category, '📌')} {category.replace('_', ' ').title()} |
#                 {txn_type_str.title()} |
#                 <span style="color: {COLORS['secondary']}; font-weight: 600;">${amount:,.2f}</span>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#         submitted = st.form_submit_button("➕ Add Transaction", type="primary",width = "stretch")

#         if submitted:
#             if not description.strip():
#                 st.error("❌ Description is required.")
#                 return None

#             type_map = {
#                 "expense": TransactionType.EXPENSE,
#                 "income": TransactionType.INCOME,
#                 "transfer": TransactionType.TRANSFER,
#             }

#             try:
#                 transaction = Transaction(
#                     transaction_id=f"manual_{uuid.uuid4().hex[:8]}",
#                     student_id=student_id,
#                     amount=float(amount),
#                     transaction_type=type_map[txn_type_str],
#                     date=txn_date,
#                     description=description.strip(),
#                     merchant=merchant.strip() if merchant.strip() else None,
#                     category=category,
#                     payment_method="other",
#                     source="manual",
#                     confidence="high",
#                     raw_data={},
#                     notes="",
#                     tags=[],
#                 )
#                 st.success("✅ Transaction added successfully!")
#                 return transaction
#             except Exception as e:
#                 st.error(f"❌ Could not create transaction: {e}")
#                 return None

#         return None


# # =========================================================
# # QUICK EXPENSE FORM
# # =========================================================

# def render_quick_expense_form(student_id: str) -> Optional[Transaction]:
#     """
#     Fast one-line expense entry for quick daily usage.
#     """
#     load_input_form_styles()
#     _render_section_header(
#         "Quick Expense Add",
#         "Perfect for coffee, snacks, rides, and other small daily spending.",
#         "⚡",
#     )

#     with st.form("quick_expense_form", clear_on_submit=True):
#         col1, col2, col3, col4 = st.columns([2.2, 1.1, 1.3, 0.8])

#         with col1:
#             description = st.text_input(
#                 "Description",
#                 placeholder="e.g. Coffee, Lunch, Uber",
#                 label_visibility="collapsed",
#             )

#         with col2:
#             amount = st.number_input(
#                 "Amount",
#                 min_value=0.01,
#                 value=1.00,
#                 step=1.0,
#                 format="%.2f",
#                 label_visibility="collapsed",
#             )

#         with col3:
#             category = st.selectbox(
#                 "Category",
#                 options=["coffee", "groceries", "dining_out", "transport", "shopping", "entertainment", "other"],
#                 format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
#                 label_visibility="collapsed",
#                 key="quick_expense_category",
#             )

#         with col4:
#             submitted = st.form_submit_button("➕",width = "stretch")

#         st.markdown(
#             f"""
#             <div style="margin-top: 0.5rem; font-size: 1.05rem;">
#                 ⚡ Preview: {CATEGORY_ICONS.get(category, '📌')} {category.replace('_', ' ').title()} |
#                 <span style="color: {COLORS['secondary']}; font-weight: 600;">${amount:,.2f}</span>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#         if submitted:
#             if not description.strip():
#                 st.error("❌ Please enter a short description.")
#                 return None

#             try:
#                 transaction = Transaction(
#                     transaction_id=f"quick_{uuid.uuid4().hex[:8]}",
#                     student_id=student_id,
#                     amount=float(amount),
#                     transaction_type=TransactionType.EXPENSE,
#                     date=date.today(),
#                     description=description.strip(),
#                     merchant=None,
#                     category=category,
#                     payment_method="other",
#                     source="manual",
#                     confidence="high",
#                     raw_data={},
#                     notes="quick_add",
#                     tags=[],
#                 )
#                 st.success("✅ Quick expense added!")
#                 return transaction
#             except Exception as e:
#                 st.error(f"❌ Could not create quick expense: {e}")
#                 return None

#         return None


# # =========================================================
# # GOAL FORM
# # =========================================================

# def render_goal_form(student_id: str, existing_goal: Optional[Goal] = None) -> Optional[Goal]:
#     """
#     Interactive goal creation/edit form with progress preview.
#     """
#     load_input_form_styles()
#     _render_section_header(
#         "Financial Goal",
#         "Track a savings target that matters to you.",
#         "🎯",
#     )

#     goal_category_values = _safe_enum_values(GoalCategory)
#     goal_priority_values = _safe_enum_values(GoalPriority)
#     recurring_values = [
#         RecurringType.WEEKLY.value,
#         RecurringType.BIWEEKLY.value,
#         RecurringType.MONTHLY.value,
#     ]

#     with st.form("goal_form"):
#         col1, col2 = st.columns(2)

#         with col1:
#             name = st.text_input(
#                 "🎯 Goal Name",
#                 value=existing_goal.name if existing_goal else "",
#                 placeholder="e.g. Emergency Fund, New Laptop, Summer Trip",
#             )

#             category_str = st.selectbox(
#                 "📌 Goal Category",
#                 options=goal_category_values,
#                 index=goal_category_values.index(existing_goal.category.value) if existing_goal else 0,
#                 format_func=lambda x: x.replace('_', ' ').title(),
#             )

#             target_amount = st.number_input(
#                 "💰 Target Amount ($)",
#                 min_value=1.0,
#                 max_value=1_000_000.0,
#                 value=float(existing_goal.target_amount) if existing_goal else 1000.0,
#                 step=100.0,
#                 format="%.2f",
#             )

#             current_amount = st.number_input(
#                 "💵 Current Saved ($)",
#                 min_value=0.0,
#                 max_value=float(target_amount),
#                 value=float(existing_goal.current_amount) if existing_goal else 0.0,
#                 step=50.0,
#                 format="%.2f",
#             )

#         with col2:
#             priority_str = st.selectbox(
#                 "⚡ Priority",
#                 options=goal_priority_values,
#                 index=goal_priority_values.index(existing_goal.priority.value) if existing_goal else 1,
#                 format_func=lambda x: {
#                     "critical": "🔴 Critical",
#                     "high": "🟠 High",
#                     "medium": "🟡 Medium",
#                     "low": "🟢 Low",
#                     "ambitious": "💫 Ambitious",
#                 }.get(x, x),
#             )

#             has_deadline = st.checkbox(
#                 "📅 Set target date",
#                 value=bool(existing_goal and existing_goal.target_date),
#             )

#             selected_target_date = None
#             if has_deadline:
#                 selected_target_date = st.date_input(
#                     "Target Date",
#                     value=existing_goal.target_date if existing_goal and existing_goal.target_date else date.today() + timedelta(days=180),
#                     min_value=date.today(),
#                 )

#             recurring_enabled = st.checkbox(
#                 "🔄 Recurring contribution",
#                 value=bool(existing_goal and existing_goal.recurring_type != RecurringType.ONE_TIME),
#             )

#             recurring_type = RecurringType.ONE_TIME
#             recurring_amount = None

#             if recurring_enabled:
#                 rc1, rc2 = st.columns(2)

#                 with rc1:
#                     recurring_type_str = st.selectbox(
#                         "Frequency",
#                         options=recurring_values,
#                         index=2,
#                         format_func=lambda x: {
#                             "weekly": "📅 Weekly",
#                             "biweekly": "📅 Bi-weekly",
#                             "monthly": "📅 Monthly",
#                         }.get(x, x),
#                     )
#                     recurring_type = RecurringType(recurring_type_str)

#                 with rc2:
#                     recurring_amount = st.number_input(
#                         "Amount per period ($)",
#                         min_value=1.0,
#                         value=float(existing_goal.recurring_amount) if existing_goal and existing_goal.recurring_amount else 50.0,
#                         step=10.0,
#                         format="%.2f",
#                     )

#         progress_pct = (current_amount / target_amount * 100.0) if target_amount > 0 else 0.0
#         st.progress(min(progress_pct, 100.0) / 100.0, text=f"Progress: {progress_pct:.1f}%")

#         if progress_pct >= 75:
#             st.markdown('<div class="fa-success"><strong>🏆 Almost there:</strong> You are close to this goal. Keep it up!</div>', unsafe_allow_html=True)
#         elif progress_pct > 0:
#             st.markdown('<div class="fa-soft-box"><strong>✨ Good start:</strong> You already have progress. Keep building on it.</div>', unsafe_allow_html=True)
#         else:
#             st.markdown('<div class="fa-soft-box"><strong>🚀 Fresh goal:</strong> Every big win starts small.</div>', unsafe_allow_html=True)

#         submitted = st.form_submit_button("💾 Save Goal", type="primary",width = "stretch")

#         if submitted:
#             if not name.strip():
#                 st.error("❌ Goal name is required.")
#                 return None

#             try:
#                 goal = Goal(
#                     goal_id=existing_goal.goal_id if existing_goal else f"goal_{uuid.uuid4().hex[:8]}",
#                     student_id=student_id,
#                     name=name.strip(),
#                     category=GoalCategory(category_str),
#                     target_amount=float(target_amount),
#                     current_amount=min(float(current_amount), float(target_amount)),
#                     target_date=selected_target_date,
#                     priority=GoalPriority(priority_str),
#                     recurring_type=recurring_type,
#                     recurring_amount=float(recurring_amount) if recurring_amount is not None else None,
#                     notes="",
#                 )
#                 st.success("✅ Goal saved successfully!")
#                 return goal
#             except Exception as e:
#                 st.error(f"❌ Could not save goal: {e}")
#                 return None

#         return None


# # =========================================================
# # BUDGET FORM
# # =========================================================

# def render_budget_form(
#     student_id: str,
#     monthly_income: float = 0.0,
#     existing_budget: Optional[Budget] = None,
# ) -> Optional[Budget]:
#     """
#     Interactive category-based budget form aligned to current tracker/analyzer flow.
#     """
#     load_input_form_styles()
#     _render_section_header(
#         "Monthly Budget",
#         "Set realistic category limits that your tracker and alerts can actually use.",
#         "💰",
#     )

#     _render_budget_guide(monthly_income)

#     default_limits = {name: default_limit for name, default_limit in DEFAULT_BUDGET_CATEGORIES}
#     if existing_budget:
#         for bc in existing_budget.categories:
#             default_limits[str(bc.category)] = float(bc.limit)

#     with st.form("budget_form"):
#         row1 = st.columns(4)
#         with row1[0]:
#             groceries_limit = st.number_input(f"{CATEGORY_ICONS['groceries']} Groceries", min_value=0.0, value=float(default_limits.get("groceries", 400.0)), step=20.0, format="%.2f")
#         with row1[1]:
#             dining_out_limit = st.number_input(f"{CATEGORY_ICONS['dining_out']} Dining Out", min_value=0.0, value=float(default_limits.get("dining_out", 250.0)), step=20.0, format="%.2f")
#         with row1[2]:
#             coffee_limit = st.number_input(f"{CATEGORY_ICONS['coffee']} Coffee", min_value=0.0, value=float(default_limits.get("coffee", 80.0)), step=10.0, format="%.2f")
#         with row1[3]:
#             transport_limit = st.number_input(f"{CATEGORY_ICONS['transport']} Transport", min_value=0.0, value=float(default_limits.get("transport", 120.0)), step=10.0, format="%.2f")

#         row2 = st.columns(4)
#         with row2[0]:
#             shopping_limit = st.number_input(f"{CATEGORY_ICONS['shopping']} Shopping", min_value=0.0, value=float(default_limits.get("shopping", 200.0)), step=20.0, format="%.2f")
#         with row2[1]:
#             streaming_limit = st.number_input(f"{CATEGORY_ICONS['streaming']} Streaming", min_value=0.0, value=float(default_limits.get("streaming", 40.0)), step=5.0, format="%.2f")
#         with row2[2]:
#             entertainment_limit = st.number_input(f"{CATEGORY_ICONS['entertainment']} Entertainment", min_value=0.0, value=float(default_limits.get("entertainment", 100.0)), step=10.0, format="%.2f")
#         with row2[3]:
#             books_limit = st.number_input(f"{CATEGORY_ICONS['books']} Books / Supplies", min_value=0.0, value=float(default_limits.get("books", 60.0)), step=10.0, format="%.2f")

#         alert_threshold_pct = st.slider(
#             "🔔 Alert Threshold",
#             min_value=50,
#             max_value=95,
#             value=int((existing_budget.alert_threshold if existing_budget else 0.8) * 100),
#             step=5,
#             format="%d%%",
#             help="Alert when category spending reaches this % of budget",
#         )

#         categories = [
#             BudgetCategory(category="groceries", limit=float(groceries_limit)),
#             BudgetCategory(category="dining_out", limit=float(dining_out_limit)),
#             BudgetCategory(category="coffee", limit=float(coffee_limit)),
#             BudgetCategory(category="transport", limit=float(transport_limit)),
#             BudgetCategory(category="shopping", limit=float(shopping_limit)),
#             BudgetCategory(category="streaming", limit=float(streaming_limit)),
#             BudgetCategory(category="entertainment", limit=float(entertainment_limit)),
#             BudgetCategory(category="books", limit=float(books_limit)),
#         ]

#         total_budget_limit = sum(float(c.limit) for c in categories)
#         suggested_savings = max(0.0, monthly_income - total_budget_limit) if monthly_income > 0 else 0.0
#         usage_pct = (total_budget_limit / monthly_income * 100.0) if monthly_income > 0 else 0.0

#         m1, m2, m3 = st.columns(3)
#         with m1:
#             st.metric("Total Variable Budget", f"${total_budget_limit:,.2f}")
#         with m2:
#             st.metric("Remaining for Savings", f"${suggested_savings:,.2f}")
#         with m3:
#             st.metric("Budget vs Income", f"{usage_pct:.1f}%")

#         if monthly_income > 0:
#             if usage_pct > 70:
#                 st.markdown('<div class="fa-warning"><strong>⚠️ Warning:</strong> Your variable budget uses a large share of income. Double-check if these limits feel realistic.</div>', unsafe_allow_html=True)
#             else:
#                 st.markdown('<div class="fa-success"><strong>✅ Good balance:</strong> This leaves breathing room for savings.</div>', unsafe_allow_html=True)

#         submitted = st.form_submit_button("💾 Save Budget", type="primary",width = "stretch")

#         if submitted:
#             try:
#                 start_date, end_date = _current_month_range()

#                 budget = Budget(
#                     budget_id=existing_budget.budget_id if existing_budget else f"budget_{uuid.uuid4().hex[:8]}",
#                     student_id=student_id,
#                     name=f"Monthly Budget - {start_date.strftime('%B %Y')}",
#                     period=BudgetPeriod.MONTHLY,
#                     start_date=start_date,
#                     end_date=end_date,
#                     is_active=True,
#                     categories=categories,
#                     savings_goal=float(suggested_savings),
#                     alert_threshold=float(alert_threshold_pct / 100.0),
#                     notes="Interactive category budget created from UI form",
#                 )
#                 st.success("✅ Budget saved successfully!")
#                 return budget
#             except Exception as e:
#                 st.error(f"❌ Could not save budget: {e}")
#                 return None

#         return None


# # =========================================================
# # MINI LIVE PREVIEW
# # =========================================================

# def render_input_summary_preview(
#     student: Optional[Student] = None,
#     transactions: Optional[List[Transaction]] = None,
#     goals: Optional[List[Goal]] = None,
#     budget: Optional[Budget] = None,
# ):
#     """
#     Small live preview strip so the input page feels active and responsive.
#     """
#     load_input_form_styles()
#     transactions = transactions or []
#     goals = goals or []

#     st.markdown("### 📊 Live Setup Preview")

#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.metric("Profile", "✅ Ready" if student else "⏳ Not set")
#     with c2:
#         st.metric("Transactions", len(transactions))
#     with c3:
#         st.metric("Goals", len(goals))
#     with c4:
#         st.metric("Budget", "✅ Set" if budget else "⏳ Not set")

#     if student:
#         st.markdown(
#             f"""
#             <div class="fa-soft-box" style="margin-top: 1rem;">
#                 <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
#                     <div>
#                         <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Monthly Income</div>
#                         <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['success']};">${student.monthly_income:,.0f}</div>
#                     </div>
#                     <div>
#                         <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Fixed Expenses</div>
#                         <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['danger']};">${student.total_fixed_expenses():,.0f}</div>
#                     </div>
#                     <div>
#                         <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Disposable</div>
#                         <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['info']};">${student.estimated_disposable_income():,.0f}</div>
#                     </div>
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )


# # =========================================================
# # DEMO
# # =========================================================

# if __name__ == "__main__":
#     st.set_page_config(page_title="Financial Input Forms", layout="wide")
#     load_input_form_styles()

#     render_input_welcome_card()

#     student = render_student_profile_form()

#     if student:
#         with st.expander("📋 View Student Data"):
#             st.json(student.model_dump())

#         render_input_summary_preview(student=student)

#         budget = render_budget_form(
#             student_id=student.student_id,
#             monthly_income=student.monthly_income,
#         )
#         if budget:
#             with st.expander("📋 View Budget Data"):
#                 st.json(budget.model_dump())

#         goal = render_goal_form(student.student_id)
#         if goal:
#             with st.expander("📋 View Goal Data"):
#                 st.json(goal.model_dump())

#         quick_txn = render_quick_expense_form(student.student_id)
#         if quick_txn:
#             with st.expander("📋 View Quick Transaction"):
#                 st.json(quick_txn.model_dump())

#         manual_txn = render_manual_transaction_form(student.student_id)
#         if manual_txn:
#             with st.expander("📋 View Manual Transaction"):
#                 st.json(manual_txn.model_dump())















"""
📝 INPUT FORMS - Clean, reusable Streamlit form components

Purpose
-------
This file renders UI-only forms and returns schema-compatible objects.

It does:
- render form inputs
- perform light validation
- build Student / Transaction / Goal / Budget objects

It does NOT:
- call agents
- call the graph
- call runner
- perform business logic / financial reasoning
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, List, Dict
import uuid

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.goal import Goal, GoalCategory, GoalPriority, RecurringType
from schemas.budget import Budget, BudgetCategory, BudgetPeriod


# =========================================================
# COLOR CONSTANTS - HIGH CONTRAST FOR READABILITY
# =========================================================

COLORS = {
    "primary": "#4361EE",  # Vibrant blue
    "primary_light": "#4895EF",
    "primary_dark": "#3F37C9",
    "secondary": "#4CC9F0",  # Cyan
    "secondary_light": "#90F1EF",
    "secondary_dark": "#3A86FF",
    "accent": "#F72585",  # Pink
    "accent_light": "#B5179E",
    "accent_dark": "#7209B7",
    "danger": "#EF233C",  # Red
    "danger_light": "#F87171",
    "danger_dark": "#D9042B",
    "info": "#4895EF",  # Light blue
    "info_light": "#4CC9F0",
    "info_dark": "#3F37C9",
    "success": "#06D6A0",  # Mint green
    "warning": "#FF9F1C",  # Orange
    "purple": "#9D4EDD",
    "pink": "#F72585",
    "indigo": "#560BAD",
    "background": "#0E1117",  # Dark background
    "card_bg": "#262730",  # Slightly lighter card background
    "text_primary": "#FFFFFF",  # White text
    "text_secondary": "#E0E0E0",  # Light gray text
    "text_tertiary": "#A0A0A0",  # Medium gray text
    "border": "#404040",  # Dark border
}

GRADIENTS = {
    "primary": "linear-gradient(135deg, #4361EE 0%, #3F37C9 100%)",
    "secondary": "linear-gradient(135deg, #4CC9F0 0%, #3A86FF 100%)",
    "accent": "linear-gradient(135deg, #F72585 0%, #7209B7 100%)",
    "info": "linear-gradient(135deg, #4895EF 0%, #3F37C9 100%)",
    "danger": "linear-gradient(135deg, #EF233C 0%, #D9042B 100%)",
    "purple_pink": "linear-gradient(135deg, #9D4EDD 0%, #F72585 100%)",
    "blue_green": "linear-gradient(135deg, #4361EE 0%, #06D6A0 100%)",
}


# =========================================================
# CONSTANTS
# =========================================================

RISK_PROFILE_OPTIONS = ["conservative", "moderate", "aggressive"]

COMMON_TRANSACTION_CATEGORIES = [
    "groceries",
    "dining_out",
    "coffee",
    "rent",
    "housing",
    "utilities",
    "internet",
    "phone",
    "transport",
    "gas",
    "uber",
    "public_transit",
    "shopping",
    "amazon",
    "electronics",
    "streaming",
    "entertainment",
    "movies",
    "games",
    "education",
    "tuition",
    "books",
    "supplies",
    "health",
    "medical",
    "gym",
    "salary",
    "refund",
    "investment",
    "other",
]

CATEGORY_ICONS = {
    "groceries": "🛒",
    "dining_out": "🍽️",
    "coffee": "☕",
    "rent": "🏠",
    "housing": "🏠",
    "utilities": "💡",
    "internet": "🌐",
    "phone": "📱",
    "transport": "🚗",
    "gas": "⛽",
    "uber": "🚕",
    "public_transit": "🚌",
    "shopping": "🛍️",
    "amazon": "📦",
    "electronics": "💻",
    "streaming": "📺",
    "entertainment": "🎮",
    "movies": "🎬",
    "games": "🕹️",
    "education": "📚",
    "tuition": "🎓",
    "books": "📖",
    "supplies": "✏️",
    "health": "🏥",
    "medical": "💊",
    "gym": "💪",
    "salary": "💵",
    "refund": "↩️",
    "investment": "📈",
    "other": "📌",
}

RISK_PROFILE_HELP = {
    "conservative": "You prefer safer, steadier financial decisions.",
    "moderate": "You like a balance between safety and growth.",
    "aggressive": "You are comfortable taking more risk for higher upside.",
}

DEFAULT_BUDGET_CATEGORIES = [
    ("groceries", 400.0),
    ("dining_out", 250.0),
    ("coffee", 80.0),
    ("shopping", 200.0),
    ("transport", 120.0),
    ("streaming", 40.0),
    ("entertainment", 100.0),
    ("books", 60.0),
]


# =========================================================
# SHARED STYLES - FIXED FOR DARK MODE READABILITY
# =========================================================

def load_input_form_styles():
    """Load custom CSS for polished UI with dark mode support."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {COLORS['background']};
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS['text_primary']} !important;
        }}

        p, li, .stMarkdown p, .stMarkdown li {{
            color: {COLORS['text_secondary']} !important;
            font-size: 1.05rem !important;
            line-height: 1.6 !important;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stSelectbox select,
        .stTextArea textarea {{
            background-color: {COLORS['card_bg']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['border']} !important;
            font-size: 1.05rem !important;
            padding: 0.65rem !important;
        }}

        .stTextInput label,
        .stNumberInput label,
        .stSelectbox label,
        .stDateInput label,
        .stMultiSelect label,
        .stCheckbox label {{
            color: {COLORS['text_secondary']} !important;
            font-size: 1.05rem !important;
            font-weight: 500 !important;
        }}

        .stButton button {{
            background: {GRADIENTS['primary']} !important;
            color: white !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 12px !important;
            border: none !important;
        }}

        .stButton button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(67, 97, 238, 0.3);
        }}

        [data-testid="stMetricValue"] {{
            color: {COLORS['text_primary']} !important;
            font-size: 1.8rem !important;
            font-weight: 700 !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS['text_secondary']} !important;
            font-size: 1rem !important;
        }}

        .fa-hero {{
            border-radius: 24px;
            padding: 2rem 1.75rem;
            margin-bottom: 2rem;
            background: {GRADIENTS['primary']};
            color: white;
            box-shadow: 0 20px 40px rgba(67, 97, 238, 0.3);
        }}

        .fa-hero h1, .fa-hero h2, .fa-hero h3, .fa-hero p {{
            color: white !important;
        }}

        .fa-card {{
            border-radius: 20px;
            padding: 1.4rem 1.4rem;
            margin-bottom: 1.25rem;
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }}

        .fa-card h3 {{
            color: {COLORS['primary_light']} !important;
            margin-bottom: 0.25rem;
        }}

        .fa-soft-box {{
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            color: {COLORS['text_secondary']} !important;
        }}

        .fa-soft-box strong {{
            color: {COLORS['primary_light']} !important;
        }}

        .fa-success {{
            border-radius: 16px;
            padding: 1rem 1.2rem;
            background: rgba(6, 214, 160, 0.15);
            border: 1px solid {COLORS['success']};
            color: {COLORS['success']} !important;
        }}

        .fa-success strong {{
            color: {COLORS['success']} !important;
        }}

        .fa-warning {{
            border-radius: 16px;
            padding: 1rem 1.2rem;
            background: rgba(255, 159, 28, 0.15);
            border: 1px solid {COLORS['warning']};
            color: {COLORS['warning']} !important;
        }}

        .fa-warning strong {{
            color: {COLORS['warning']} !important;
        }}

        div[data-testid="stForm"] {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 24px;
            padding: 1.5rem 1.5rem 1rem 1.5rem;
        }}

        div[data-testid="stMetric"] {{
            background: {COLORS['card_bg']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1rem;
        }}

        .stProgress > div > div > div {{
            background: {GRADIENTS['secondary']} !important;
            height: 12px !important;
            border-radius: 999px !important;
        }}

        hr {{
            border: 1px solid {COLORS['border']} !important;
            margin: 2rem 0 !important;
        }}

        .stExpander {{
            background: {COLORS['card_bg']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 12px !important;
        }}

        .stExpander summary {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600 !important;
        }}

        .stAlert {{
            background: {COLORS['card_bg']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['border']} !important;
        }}

        .stInfo, .stSuccess, .stWarning, .stError {{
            background: {COLORS['card_bg']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['border']} !important;
        }}

        .stSelectbox div[data-baseweb="select"] span {{
            color: {COLORS['text_primary']} !important;
        }}

        .stMultiSelect div[data-baseweb="select"] span {{
            color: {COLORS['text_primary']} !important;
        }}

        .stCheckbox span {{
            color: {COLORS['text_secondary']} !important;
        }}

        .stRadio div {{
            color: {COLORS['text_secondary']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HELPERS
# =========================================================

def _safe_enum_values(enum_cls) -> List[str]:
    return [member.value for member in enum_cls]


def _current_month_range() -> tuple[date, date]:
    today = date.today()
    start_date = date(today.year, today.month, 1)

    if today.month == 12:
        end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    return start_date, end_date


def _build_fixed_expenses(
    rent: float,
    utilities: float,
    internet: float,
    phone: float,
    insurance: float,
    student_loan: float,
    credit_card: float,
    car_payment: float,
) -> Dict[str, float]:
    fixed_expenses: Dict[str, float] = {}

    if rent > 0:
        fixed_expenses["rent"] = float(rent)
    if utilities > 0:
        fixed_expenses["utilities"] = float(utilities)
    if internet > 0:
        fixed_expenses["internet"] = float(internet)
    if phone > 0:
        fixed_expenses["phone"] = float(phone)
    if insurance > 0:
        fixed_expenses["insurance"] = float(insurance)
    if student_loan > 0:
        fixed_expenses["student_loan"] = float(student_loan)
    if credit_card > 0:
        fixed_expenses["credit_card"] = float(credit_card)
    if car_payment > 0:
        fixed_expenses["car_payment"] = float(car_payment)

    return fixed_expenses


def _render_hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="fa-hero">
            <h1>{title}</h1>
            <p style="font-size: 1.25rem !important; margin-top:0.5rem;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_section_header(title: str, subtitle: str, emoji: str = "✨"):
    st.markdown(
        f"""
        <div class="fa-card">
            <h3 style="margin-bottom:0.25rem;">{emoji} {title}</h3>
            <p style="margin-bottom:0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _profile_completion_score(
    name: str,
    monthly_income: float,
    fixed_expenses: Dict[str, float],
    preferred_categories: List[str],
) -> int:
    score = 0
    if name.strip():
        score += 30
    if monthly_income > 0:
        score += 25
    if fixed_expenses:
        score += 25
    if preferred_categories:
        score += 20
    return min(score, 100)


def _render_budget_guide(monthly_income: float):
    if monthly_income <= 0:
        st.info("💰 Enter monthly income to unlock a budget guide.")
        return

    needs = monthly_income * 0.50
    wants = monthly_income * 0.30
    savings = monthly_income * 0.20

    st.markdown(
        f"""
        <div style="
            background: {COLORS['card_bg']};
            border-radius: 20px;
            padding: 1.25rem;
            margin: 1rem 0 1.5rem 0;
            border: 1px solid {COLORS['border']};
        ">
            <h4 style="margin-bottom: 0.9rem; color: {COLORS['text_primary']};">📊 50 / 30 / 20 Budget Guide</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div style="text-align:center;">
                    <div style="font-size: 1.9rem; font-weight:700; color: {COLORS['info']};">${needs:,.0f}</div>
                    <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Needs (50%)</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size: 1.9rem; font-weight:700; color: {COLORS['accent']};">${wants:,.0f}</div>
                    <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Wants (30%)</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size: 1.9rem; font-weight:700; color: {COLORS['success']};">${savings:,.0f}</div>
                    <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Savings (20%)</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# OPTIONAL INPUT PAGE HERO
# =========================================================

def render_input_welcome_card():
    load_input_form_styles()
    _render_hero(
        "🎓 Student Financial Advisor",
        "Build your financial foundation with interactive tools that feel modern, clear, and motivating.",
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="fa-soft-box" style="text-align:center;">
                <div style="font-size:2.3rem;">👤</div>
                <div style="font-size:1.15rem; font-weight:600; color: {COLORS['text_primary']};">Profile</div>
                <div style="font-size:0.95rem; color: {COLORS['text_secondary']};">Income + bills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="fa-soft-box" style="text-align:center;">
                <div style="font-size:2.3rem;">💰</div>
                <div style="font-size:1.15rem; font-weight:600; color: {COLORS['text_primary']};">Transactions</div>
                <div style="font-size:0.95rem; color: {COLORS['text_secondary']};">Track spending</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="fa-soft-box" style="text-align:center;">
                <div style="font-size:2.3rem;">🎯</div>
                <div style="font-size:1.15rem; font-weight:600; color: {COLORS['text_primary']};">Goals</div>
                <div style="font-size:0.95rem; color: {COLORS['text_secondary']};">Savings targets</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="fa-soft-box" style="text-align:center;">
                <div style="font-size:2.3rem;">📊</div>
                <div style="font-size:1.15rem; font-weight:600; color: {COLORS['text_primary']};">Budget</div>
                <div style="font-size:0.95rem; color: {COLORS['text_secondary']};">Spending limits</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# STUDENT PROFILE FORM
# =========================================================

def render_student_profile_form(existing_student: Optional[Student] = None) -> Optional[Student]:
    """
    Interactive student profile form aligned to current Student schema.
    """
    load_input_form_styles()
    _render_section_header(
        "Student Profile",
        "Create a personalized financial profile that powers advice, budget tracking, and alerts.",
        "👤",
    )

    existing_fixed = existing_student.fixed_monthly_expenses if existing_student else {}
    default_name = existing_student.name if existing_student else ""
    default_age = int(existing_student.age) if existing_student and existing_student.age is not None else 20
    default_income = float(existing_student.monthly_income) if existing_student else 0.0
    default_risk = existing_student.risk_profile if existing_student else "moderate"
    default_categories = existing_student.preferred_categories if existing_student else []

    preview_fixed = _build_fixed_expenses(
        float(existing_fixed.get("rent", 0.0)),
        float(existing_fixed.get("utilities", 0.0)),
        float(existing_fixed.get("internet", 0.0)),
        float(existing_fixed.get("phone", 0.0)),
        float(existing_fixed.get("insurance", 0.0)),
        float(existing_fixed.get("student_loan", 0.0)),
        float(existing_fixed.get("credit_card", 0.0)),
        float(existing_fixed.get("car_payment", 0.0)),
    )

    completion_score = _profile_completion_score(
        default_name,
        default_income,
        preview_fixed,
        default_categories,
    )

    st.progress(completion_score / 100.0, text=f"Profile completion: {completion_score}%")

    with st.form("student_profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "📝 Full Name",
                value=default_name,
                placeholder="e.g. Alex Johnson",
            )

            age = st.number_input(
                "🎂 Age",
                min_value=13,
                max_value=70,
                value=default_age,
                step=1,
            )

            monthly_income = st.number_input(
                "💰 Monthly Income ($)",
                min_value=0.0,
                value=default_income,
                step=100.0,
                format="%.2f",
                help="Use a realistic monthly after-tax amount if possible.",
            )

        with col2:
            risk_profile = st.selectbox(
                "⚡ Risk Profile",
                options=RISK_PROFILE_OPTIONS,
                index=RISK_PROFILE_OPTIONS.index(default_risk),
                format_func=lambda x: {
                    "conservative": "🛡️ Conservative - Safety first",
                    "moderate": "⚖️ Moderate - Balanced approach",
                    "aggressive": "🚀 Aggressive - Growth focused",
                }.get(x, x),
            )

            preferred_categories = st.multiselect(
                "⭐ Preferred Categories",
                options=COMMON_TRANSACTION_CATEGORIES,
                default=default_categories,
                format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
                help="These categories help personalize your experience.",
            )

            st.markdown(
                f"""
                <div class="fa-soft-box">
                    <span style="color: {COLORS['text_secondary']};">{RISK_PROFILE_HELP[risk_profile]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🏠 Fixed Monthly Expenses")
        st.caption("Approximate amounts are fine. These are your recurring monthly commitments.")

        row1 = st.columns(4)
        with row1[0]:
            rent = st.number_input("🏠 Rent / Housing", min_value=0.0, value=float(existing_fixed.get("rent", 0.0)), step=50.0, format="%.2f")
        with row1[1]:
            utilities = st.number_input("💡 Utilities", min_value=0.0, value=float(existing_fixed.get("utilities", 0.0)), step=20.0, format="%.2f")
        with row1[2]:
            internet = st.number_input("🌐 Internet", min_value=0.0, value=float(existing_fixed.get("internet", 0.0)), step=10.0, format="%.2f")
        with row1[3]:
            phone = st.number_input("📱 Phone", min_value=0.0, value=float(existing_fixed.get("phone", 0.0)), step=10.0, format="%.2f")

        row2 = st.columns(4)
        with row2[0]:
            insurance = st.number_input("🛡️ Insurance", min_value=0.0, value=float(existing_fixed.get("insurance", 0.0)), step=10.0, format="%.2f")
        with row2[1]:
            student_loan = st.number_input("🎒 Student Loan", min_value=0.0, value=float(existing_fixed.get("student_loan", 0.0)), step=25.0, format="%.2f")
        with row2[2]:
            credit_card = st.number_input("💳 Credit Card Minimum", min_value=0.0, value=float(existing_fixed.get("credit_card", 0.0)), step=25.0, format="%.2f")
        with row2[3]:
            car_payment = st.number_input("🚘 Car Payment", min_value=0.0, value=float(existing_fixed.get("car_payment", 0.0)), step=25.0, format="%.2f")

        fixed_expenses = _build_fixed_expenses(
            rent,
            utilities,
            internet,
            phone,
            insurance,
            student_loan,
            credit_card,
            car_payment,
        )

        total_fixed = sum(fixed_expenses.values())
        disposable = max(0.0, monthly_income - total_fixed)
        fixed_ratio = (total_fixed / monthly_income * 100.0) if monthly_income > 0 else 0.0

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Fixed Expenses", f"${total_fixed:,.2f}")
        with m2:
            st.metric("Disposable Income", f"${disposable:,.2f}")
        with m3:
            st.metric("Fixed Expense Ratio", f"{fixed_ratio:.1f}%")

        if monthly_income > 0:
            if fixed_ratio >= 75:
                st.markdown('<div class="fa-warning"><strong>⚠️ Warning:</strong> Your fixed expenses are consuming a large share of income. Flexibility may be tight.</div>', unsafe_allow_html=True)
            elif fixed_ratio <= 45:
                st.markdown('<div class="fa-success"><strong>✅ Great:</strong> Your recurring costs look relatively manageable.</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Save Profile", type="primary",width = "stretch")

        if submitted:
            if not name.strip():
                st.error("❌ Name is required.")
                return None

            try:
                student = Student(
                    student_id=existing_student.student_id if existing_student else f"STU_{uuid.uuid4().hex[:8].upper()}",
                    name=name.strip(),
                    age=int(age),
                    status="student",
                    currency="USD",
                    monthly_income=float(monthly_income),
                    income_frequency="monthly",
                    risk_profile=risk_profile,
                    preferred_categories=preferred_categories,
                    fixed_monthly_expenses=fixed_expenses,
                )
                st.success("✅ Profile saved successfully!")
                return student
            except Exception as e:
                st.error(f"❌ Could not save profile: {e}")
                return None

        return None


# =========================================================
# MANUAL TRANSACTION FORM
# =========================================================

def render_manual_transaction_form(student_id: str) -> Optional[Transaction]:
    """
    Detailed transaction entry form with live category/amount preview.
    """
    load_input_form_styles()
    _render_section_header(
        "Manual Transaction Entry",
        "Add a full transaction with category, merchant, description, and type.",
        "➕",
    )

    with st.form("manual_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "💰 Amount ($)",
                min_value=0.01,
                max_value=100000.0,
                value=1.00,
                step=1.0,
                format="%.2f",
            )

            txn_type_str = st.selectbox(
                "📊 Transaction Type",
                options=["expense", "income", "transfer"],
                index=0,
                format_func=lambda x: {
                    "expense": "💸 Expense - Money out",
                    "income": "💵 Income - Money in",
                    "transfer": "🔄 Transfer - Between accounts",
                }.get(x, x),
            )

            category = st.selectbox(
                "🏷️ Category",
                options=COMMON_TRANSACTION_CATEGORIES,
                index=COMMON_TRANSACTION_CATEGORIES.index("groceries"),
                format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
            )

        with col2:
            txn_date = st.date_input(
                "📅 Date",
                value=date.today(),
                max_value=date.today(),
            )

            description = st.text_input(
                "📝 Description",
                placeholder="e.g. Walmart groceries, Uber ride, Netflix subscription",
            )

            merchant = st.text_input(
                "🏢 Merchant (optional)",
                placeholder="e.g. Walmart, Uber, Starbucks",
            )

        st.markdown(
            f"""
            <div class="fa-soft-box" style="margin-top: 1rem;">
                <strong>📋 Preview:</strong><br>
                {CATEGORY_ICONS.get(category, '📌')} {category.replace('_', ' ').title()} |
                {txn_type_str.title()} |
                <span style="color: {COLORS['success']}; font-weight: 600;">${amount:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("➕ Add Transaction", type="primary",width = "stretch")

        if submitted:
            if not description.strip():
                st.error("❌ Description is required.")
                return None

            type_map = {
                "expense": TransactionType.EXPENSE,
                "income": TransactionType.INCOME,
                "transfer": TransactionType.TRANSFER,
            }

            try:
                transaction = Transaction(
                    transaction_id=f"manual_{uuid.uuid4().hex[:8]}",
                    student_id=student_id,
                    amount=float(amount),
                    transaction_type=type_map[txn_type_str],
                    date=txn_date,
                    description=description.strip(),
                    merchant=merchant.strip() if merchant.strip() else None,
                    category=category,
                    payment_method="other",
                    source="manual",
                    confidence="high",
                    raw_data={},
                    notes="",
                    tags=[],
                )
                st.success("✅ Transaction added successfully!")
                return transaction
            except Exception as e:
                st.error(f"❌ Could not create transaction: {e}")
                return None

        return None


# =========================================================
# QUICK EXPENSE FORM
# =========================================================

def render_quick_expense_form(student_id: str) -> Optional[Transaction]:
    """
    Fast one-line expense entry for quick daily usage.
    """
    load_input_form_styles()
    _render_section_header(
        "Quick Expense Add",
        "Perfect for coffee, snacks, rides, and other small daily spending.",
        "⚡",
    )

    with st.form("quick_expense_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([2.2, 1.1, 1.3, 0.8])

        with col1:
            description = st.text_input(
                "Description",
                placeholder="e.g. Coffee, Lunch, Uber",
                label_visibility="collapsed",
            )

        with col2:
            amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=1.00,
                step=1.0,
                format="%.2f",
                label_visibility="collapsed",
            )

        with col3:
            category = st.selectbox(
                "Category",
                options=["coffee", "groceries", "dining_out", "transport", "shopping", "entertainment", "other"],
                format_func=lambda x: f"{CATEGORY_ICONS.get(x, '📌')} {x.replace('_', ' ').title()}",
                label_visibility="collapsed",
                key="quick_expense_category",
            )

        with col4:
            submitted = st.form_submit_button("➕",width = "stretch")

        st.markdown(
            f"""
            <div style="margin-top: 0.5rem; font-size: 1.05rem; color: {COLORS['text_secondary']};">
                ⚡ Preview: {CATEGORY_ICONS.get(category, '📌')} {category.replace('_', ' ').title()} |
                <span style="color: {COLORS['success']}; font-weight: 600;">${amount:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if submitted:
            if not description.strip():
                st.error("❌ Please enter a short description.")
                return None

            try:
                transaction = Transaction(
                    transaction_id=f"quick_{uuid.uuid4().hex[:8]}",
                    student_id=student_id,
                    amount=float(amount),
                    transaction_type=TransactionType.EXPENSE,
                    date=date.today(),
                    description=description.strip(),
                    merchant=None,
                    category=category,
                    payment_method="other",
                    source="manual",
                    confidence="high",
                    raw_data={},
                    notes="quick_add",
                    tags=[],
                )
                st.success("✅ Quick expense added!")
                return transaction
            except Exception as e:
                st.error(f"❌ Could not create quick expense: {e}")
                return None

        return None


# =========================================================
# GOAL FORM
# =========================================================

def render_goal_form(student_id: str, existing_goal: Optional[Goal] = None) -> Optional[Goal]:
    """
    Interactive goal creation/edit form with progress preview.
    """
    load_input_form_styles()
    _render_section_header(
        "Financial Goal",
        "Track a savings target that matters to you.",
        "🎯",
    )

    goal_category_values = _safe_enum_values(GoalCategory)
    goal_priority_values = _safe_enum_values(GoalPriority)
    recurring_values = [
        RecurringType.WEEKLY.value,
        RecurringType.BIWEEKLY.value,
        RecurringType.MONTHLY.value,
    ]

    with st.form("goal_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input(
                "🎯 Goal Name",
                value=existing_goal.name if existing_goal else "",
                placeholder="e.g. Emergency Fund, New Laptop, Summer Trip",
            )

            category_str = st.selectbox(
                "📌 Goal Category",
                options=goal_category_values,
                index=goal_category_values.index(existing_goal.category.value) if existing_goal else 0,
                format_func=lambda x: x.replace('_', ' ').title(),
            )

            target_amount = st.number_input(
                "💰 Target Amount ($)",
                min_value=1.0,
                max_value=1_000_000.0,
                value=float(existing_goal.target_amount) if existing_goal else 1000.0,
                step=100.0,
                format="%.2f",
            )

            current_amount = st.number_input(
                "💵 Current Saved ($)",
                min_value=0.0,
                max_value=float(target_amount),
                value=float(existing_goal.current_amount) if existing_goal else 0.0,
                step=50.0,
                format="%.2f",
            )

        with col2:
            priority_str = st.selectbox(
                "⚡ Priority",
                options=goal_priority_values,
                index=goal_priority_values.index(existing_goal.priority.value) if existing_goal else 1,
                format_func=lambda x: {
                    "critical": "🔴 Critical",
                    "high": "🟠 High",
                    "medium": "🟡 Medium",
                    "low": "🟢 Low",
                    "ambitious": "💫 Ambitious",
                }.get(x, x),
            )

            has_deadline = st.checkbox(
                "📅 Set target date",
                value=bool(existing_goal and existing_goal.target_date),
            )

            selected_target_date = None
            if has_deadline:
                selected_target_date = st.date_input(
                    "Target Date",
                    value=existing_goal.target_date if existing_goal and existing_goal.target_date else date.today() + timedelta(days=180),
                    min_value=date.today(),
                )

            recurring_enabled = st.checkbox(
                "🔄 Recurring contribution",
                value=bool(existing_goal and existing_goal.recurring_type != RecurringType.ONE_TIME),
            )

            recurring_type = RecurringType.ONE_TIME
            recurring_amount = None

            if recurring_enabled:
                rc1, rc2 = st.columns(2)

                with rc1:
                    recurring_type_str = st.selectbox(
                        "Frequency",
                        options=recurring_values,
                        index=2,
                        format_func=lambda x: {
                            "weekly": "📅 Weekly",
                            "biweekly": "📅 Bi-weekly",
                            "monthly": "📅 Monthly",
                        }.get(x, x),
                    )
                    recurring_type = RecurringType(recurring_type_str)

                with rc2:
                    recurring_amount = st.number_input(
                        "Amount per period ($)",
                        min_value=1.0,
                        value=float(existing_goal.recurring_amount) if existing_goal and existing_goal.recurring_amount else 50.0,
                        step=10.0,
                        format="%.2f",
                    )

        progress_pct = (current_amount / target_amount * 100.0) if target_amount > 0 else 0.0
        st.progress(min(progress_pct, 100.0) / 100.0, text=f"Progress: {progress_pct:.1f}%")

        if progress_pct >= 75:
            st.markdown('<div class="fa-success"><strong>🏆 Almost there:</strong> You are close to this goal. Keep it up!</div>', unsafe_allow_html=True)
        elif progress_pct > 0:
            st.markdown('<div class="fa-soft-box"><strong>✨ Good start:</strong> You already have progress. Keep building on it.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fa-soft-box"><strong>🚀 Fresh goal:</strong> Every big win starts small.</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Save Goal", type="primary",width = "stretch")

        if submitted:
            if not name.strip():
                st.error("❌ Goal name is required.")
                return None

            try:
                goal = Goal(
                    goal_id=existing_goal.goal_id if existing_goal else f"goal_{uuid.uuid4().hex[:8]}",
                    student_id=student_id,
                    name=name.strip(),
                    category=GoalCategory(category_str),
                    target_amount=float(target_amount),
                    current_amount=min(float(current_amount), float(target_amount)),
                    target_date=selected_target_date,
                    priority=GoalPriority(priority_str),
                    recurring_type=recurring_type,
                    recurring_amount=float(recurring_amount) if recurring_amount is not None else None,
                    notes="",
                )
                st.success("✅ Goal saved successfully!")
                return goal
            except Exception as e:
                st.error(f"❌ Could not save goal: {e}")
                return None

        return None


# =========================================================
# BUDGET FORM
# =========================================================

def render_budget_form(
    student_id: str,
    monthly_income: float = 0.0,
    existing_budget: Optional[Budget] = None,
) -> Optional[Budget]:
    """
    Interactive category-based budget form aligned to current tracker/analyzer flow.
    """
    load_input_form_styles()
    _render_section_header(
        "Monthly Budget",
        "Set realistic category limits that your tracker and alerts can actually use.",
        "💰",
    )

    _render_budget_guide(monthly_income)

    default_limits = {name: default_limit for name, default_limit in DEFAULT_BUDGET_CATEGORIES}
    if existing_budget:
        for bc in existing_budget.categories:
            default_limits[str(bc.category)] = float(bc.limit)

    with st.form("budget_form"):
        row1 = st.columns(4)
        with row1[0]:
            groceries_limit = st.number_input(f"{CATEGORY_ICONS['groceries']} Groceries", min_value=0.0, value=float(default_limits.get("groceries", 400.0)), step=20.0, format="%.2f")
        with row1[1]:
            dining_out_limit = st.number_input(f"{CATEGORY_ICONS['dining_out']} Dining Out", min_value=0.0, value=float(default_limits.get("dining_out", 250.0)), step=20.0, format="%.2f")
        with row1[2]:
            coffee_limit = st.number_input(f"{CATEGORY_ICONS['coffee']} Coffee", min_value=0.0, value=float(default_limits.get("coffee", 80.0)), step=10.0, format="%.2f")
        with row1[3]:
            transport_limit = st.number_input(f"{CATEGORY_ICONS['transport']} Transport", min_value=0.0, value=float(default_limits.get("transport", 120.0)), step=10.0, format="%.2f")

        row2 = st.columns(4)
        with row2[0]:
            shopping_limit = st.number_input(f"{CATEGORY_ICONS['shopping']} Shopping", min_value=0.0, value=float(default_limits.get("shopping", 200.0)), step=20.0, format="%.2f")
        with row2[1]:
            streaming_limit = st.number_input(f"{CATEGORY_ICONS['streaming']} Streaming", min_value=0.0, value=float(default_limits.get("streaming", 40.0)), step=5.0, format="%.2f")
        with row2[2]:
            entertainment_limit = st.number_input(f"{CATEGORY_ICONS['entertainment']} Entertainment", min_value=0.0, value=float(default_limits.get("entertainment", 100.0)), step=10.0, format="%.2f")
        with row2[3]:
            books_limit = st.number_input(f"{CATEGORY_ICONS['books']} Books / Supplies", min_value=0.0, value=float(default_limits.get("books", 60.0)), step=10.0, format="%.2f")

        alert_threshold_pct = st.slider(
            "🔔 Alert Threshold",
            min_value=50,
            max_value=95,
            value=int((existing_budget.alert_threshold if existing_budget else 0.8) * 100),
            step=5,
            format="%d%%",
            help="Alert when category spending reaches this % of budget",
        )

        categories = [
            BudgetCategory(category="groceries", limit=float(groceries_limit)),
            BudgetCategory(category="dining_out", limit=float(dining_out_limit)),
            BudgetCategory(category="coffee", limit=float(coffee_limit)),
            BudgetCategory(category="transport", limit=float(transport_limit)),
            BudgetCategory(category="shopping", limit=float(shopping_limit)),
            BudgetCategory(category="streaming", limit=float(streaming_limit)),
            BudgetCategory(category="entertainment", limit=float(entertainment_limit)),
            BudgetCategory(category="books", limit=float(books_limit)),
        ]

        total_budget_limit = sum(float(c.limit) for c in categories)
        suggested_savings = max(0.0, monthly_income - total_budget_limit) if monthly_income > 0 else 0.0
        usage_pct = (total_budget_limit / monthly_income * 100.0) if monthly_income > 0 else 0.0

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Variable Budget", f"${total_budget_limit:,.2f}")
        with m2:
            st.metric("Remaining for Savings", f"${suggested_savings:,.2f}")
        with m3:
            st.metric("Budget vs Income", f"{usage_pct:.1f}%")

        if monthly_income > 0:
            if usage_pct > 70:
                st.markdown('<div class="fa-warning"><strong>⚠️ Warning:</strong> Your variable budget uses a large share of income. Double-check if these limits feel realistic.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="fa-success"><strong>✅ Good balance:</strong> This leaves breathing room for savings.</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("💾 Save Budget", type="primary",width = "stretch")

        if submitted:
            try:
                start_date, end_date = _current_month_range()

                budget = Budget(
                    budget_id=existing_budget.budget_id if existing_budget else f"budget_{uuid.uuid4().hex[:8]}",
                    student_id=student_id,
                    name=f"Monthly Budget - {start_date.strftime('%B %Y')}",
                    period=BudgetPeriod.MONTHLY,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True,
                    categories=categories,
                    savings_goal=float(suggested_savings),
                    alert_threshold=float(alert_threshold_pct / 100.0),
                    notes="Interactive category budget created from UI form",
                )
                st.success("✅ Budget saved successfully!")
                return budget
            except Exception as e:
                st.error(f"❌ Could not save budget: {e}")
                return None

        return None


# =========================================================
# MINI LIVE PREVIEW
# =========================================================

def render_input_summary_preview(
    student: Optional[Student] = None,
    transactions: Optional[List[Transaction]] = None,
    goals: Optional[List[Goal]] = None,
    budget: Optional[Budget] = None,
):
    """
    Small live preview strip so the input page feels active and responsive.
    """
    load_input_form_styles()
    transactions = transactions or []
    goals = goals or []

    st.markdown("### 📊 Live Setup Preview")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Profile", "✅ Ready" if student else "⏳ Not set")
    with c2:
        st.metric("Transactions", len(transactions))
    with c3:
        st.metric("Goals", len(goals))
    with c4:
        st.metric("Budget", "✅ Set" if budget else "⏳ Not set")

    if student:
        st.markdown(
            f"""
            <div class="fa-soft-box" style="margin-top: 1rem;">
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                    <div>
                        <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Monthly Income</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['success']};">${student.monthly_income:,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Fixed Expenses</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['danger']};">${student.total_fixed_expenses():,.0f}</div>
                    </div>
                    <div>
                        <div style="font-size: 1rem; color: {COLORS['text_secondary']};">Disposable</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: {COLORS['info']};">${student.estimated_disposable_income():,.0f}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# DEMO
# =========================================================
if __name__ == "__main__":
    st.set_page_config(page_title="Financial Input Forms", layout="wide")
    load_input_form_styles()
    render_input_welcome_card()

    student = render_student_profile_form()

    if student:
        with st.expander("📋 View Student Data"):
            st.json(student.model_dump())

        render_input_summary_preview(student=student)

        budget = render_budget_form(
            student_id=student.student_id,
            monthly_income=student.monthly_income,
        )
        if budget:
            with st.expander("📋 View Budget Data"):
                st.json(budget.model_dump())

        goal = render_goal_form(student.student_id)
        if goal:
            with st.expander("📋 View Goal Data"):
                st.json(goal.model_dump())

        quick_txn = render_quick_expense_form(student.student_id)
        if quick_txn:
            with st.expander("📋 View Quick Transaction"):
                st.json(quick_txn.model_dump())

        manual_txn = render_manual_transaction_form(student.student_id)
        if manual_txn:
            with st.expander("📋 View Manual Transaction"):
                st.json(manual_txn.model_dump())