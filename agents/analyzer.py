"""
📊 ANALYZER AGENT - Spots patterns in transaction data
Pure analysis functions - no state modification, just insights!

What this file does:
- Takes a Student + list[Transaction] (+ optional Budget)
- Returns a single JSON-friendly dict containing:
  - summary stats (spend/income/net/top categories/large txns)
  - patterns (weekend spend, concentration, subscriptions, payday-spend)
  - trends (month-to-month increase/decrease)
  - anomalies (IQR outliers per category)
  - budget insights (warning/over by category)
  - advice (simple rule-based suggestions)
  - spending velocity (last 7 days vs previous 7 days)
  - top merchants (by total spend)

Design principles:
- NO state mutation on Student/Budget/Transaction objects.
- Output is UI-ready and can be stored in your LangGraph state.
- Patterns are returned as dicts (not Python objects) for JSON safety.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, stdev


from schemas.transaction import Transaction, TransactionType
from schemas.student import Student
from schemas.budget import Budget


# # -------------------------
# # Small models (JSON-friendly)
# # -------------------------
# @dataclass
# class SpendingPattern:
#     """
#     Small container for a detected pattern.

#     We keep it lightweight so patterns can be:
#     - easily printed
#     - easily shown in UI
#     - easily serialized into JSON
#     """
#     name: str
#     description: str
#     severity: str = "info"  # "info" | "warning" | "critical"
#     data: Optional[Dict[str, Any]] = None

#     def to_dict(self) -> Dict[str, Any]:
#         """
#         Convert to a JSON-friendly dict.
#         Ensures `data` is always a dict (never None).
#         """
#         d = asdict(self)
#         if d["data"] is None:
#             d["data"] = {}
#         return d


# # -------------------------
# # Subscription detection hints
# # -------------------------
# # Known subscription merchants are the most reliable indicator (high precision).
# KNOWN_SUBSCRIPTION_MERCHANTS = {
#     "netflix", "spotify", "hulu", "disney+", "disneyplus", "amazon prime", "prime video",
#     "apple music", "apple tv", "youtube premium", "youtube music", "paramount+",
#     "peacock", "hbomax", "hbo max", "max", "starz", "showtime", "slack", "zoom",
#     "microsoft 365", "office 365", "adobe", "creative cloud", "dropbox", "google one",
#     "icloud", "apple storage", "xbox live", "xbox game pass", "playstation plus",
#     "nintendo online", "discord nitro", "patreon", "medium", "substack"
# }

# # Categories that are often subscription-like (we treat these as "weak evidence").
# SUBSCRIPTION_CATEGORIES = {"streaming", "entertainment", "software", "cloud", "gaming"}


# # -------------------------
# # Analyzer
# # -------------------------
# class AnalyzerAgent:
#     """
#     🔍 Analyzes transaction history to find patterns and insights.

#     Pure analysis:
#     - No DB writes
#     - No file writes
#     - No modifications of input objects
#     """

#     def __init__(self):
#         self.name = "Analyzer Agent"

#     def analyze_student(
#         self,
#         student: Student,
#         transactions: List[Transaction],
#         budget: Optional[Budget] = None,
#         *,
#         lookback_days: int = 90,
#     ) -> Dict[str, Any]:
#         """
#         Main entry point.

#         Flow:
#         1) Filter to recent window (lookback_days)
#         2) Compute summary stats
#         3) Detect patterns (weekend / subscriptions / concentration / payday)
#         4) Compute trends
#         5) Detect anomalies (IQR per category)
#         6) Compare with budget (optional)
#         7) Generate advice (based on savings rate + patterns + student profile)
#         8) Compute velocity + top merchants for quick UI panels
#         """
#         txns = self._filter_recent(transactions, lookback_days)

#         summary = self._create_summary(txns, lookback_days=lookback_days)
#         patterns = self._find_patterns(txns)
#         trends = self._find_trends(txns)
#         anomalies = self._find_anomalies_iqr(txns)
#         budget_insights = self._analyze_budget(txns, budget) if budget else {}
#         advice = self._generate_advice(txns, student, patterns)
#         velocity = self._calculate_spending_velocity(txns)
#         top_merchants = self._find_top_merchants(txns)

#         return {
#             "student_id": student.student_id,
#             "analysis_date": date.today().isoformat(),
#             "window_days": lookback_days,
#             "summary": summary,
#             "patterns": [p.to_dict() for p in patterns],
#             "trends": trends,
#             "anomalies": anomalies,
#             "budget_insights": budget_insights,
#             "advice": advice,
#             "spending_velocity": velocity,
#             "top_merchants": top_merchants,
#         }

#     # -------------------------
#     # Basic helpers
#     # -------------------------
#     def _filter_recent(self, transactions: List[Transaction], lookback_days: int) -> List[Transaction]:
#         """
#         Keep only transactions within the lookback window.
#         If lookback_days <= 0, return everything (useful for debugging).
#         """
#         if lookback_days <= 0:
#             return list(transactions)
#         cutoff = date.today() - timedelta(days=lookback_days)
#         return [t for t in transactions if t.date >= cutoff]

#     def _is_expense(self, t: Transaction) -> bool:
#         """True if this transaction is an EXPENSE."""
#         return t.transaction_type == TransactionType.EXPENSE

#     def _is_income(self, t: Transaction) -> bool:
#         """True if this transaction is INCOME."""
#         return t.transaction_type == TransactionType.INCOME

#     def _normalize_merchant(self, t: Transaction) -> str:
#         """
#         Normalize merchant for grouping.

#         We prefer the structured `merchant` field.
#         If missing, we fall back to a cleaned version of description.

#         Important: we avoid "first token only" because that can create junk buckets
#         like 'pos', 'purchase', 'online', etc.
#         """
#         m = (t.merchant or "").strip()
#         if m:
#             return " ".join(m.lower().split())

#         d = " ".join((t.description or "").strip().split()).lower()
#         if not d:
#             return "unknown"

#         # Remove common leading noise patterns (best-effort)
#         noise_prefixes = ("pos", "purchase", "debit", "credit", "online", "payment", "withdrawal", "deposit")
#         parts = d.split()
#         # Drop first word if it is a noisy prefix
#         if parts and parts[0] in noise_prefixes:
#             parts = parts[1:]

#         # Take first 2-3 words to keep "amazon com" style merchants meaningful
#         cleaned = " ".join(parts[:3]).strip()
#         return cleaned if cleaned else "unknown"

#     # -------------------------
#     # Summary
#     # -------------------------
#     def _create_summary(self, transactions: List[Transaction], *, lookback_days: int) -> Dict[str, Any]:
#         """
#         Compute summary stats:
#         - total spent / earned / net flow
#         - avg spend per day (last 30d and lookback window)
#         - top categories + largest income/expense
#         """
#         if not transactions:
#             return {"error": "No transactions to analyze"}

#         expenses = [t for t in transactions if self._is_expense(t)]
#         income = [t for t in transactions if self._is_income(t)]

#         total_spent = sum(t.amount for t in expenses)
#         total_income = sum(t.amount for t in income)
#         net_flow = total_income - total_spent

#         # 30-day spend pace (more useful for "current behavior")
#         cutoff_30 = date.today() - timedelta(days=30)
#         exp_30 = [t for t in expenses if t.date >= cutoff_30]
#         spent_30 = sum(t.amount for t in exp_30)
#         avg_daily_30 = spent_30 / 30.0

#         # Lookback daily average (use the window days, NOT number of transactions)
#         # This is important: dividing by len(transactions) is incorrect.
#         window_days = max(1, lookback_days)
#         avg_daily_lookback = total_spent / float(window_days)

#         # Category totals
#         category_totals: Dict[str, float] = defaultdict(float)
#         for t in expenses:
#             category_totals[str(t.category)] += float(t.amount)

#         top_categories = sorted(
#             [
#                 {
#                     "category": k,
#                     "amount": round(v, 2),
#                     "share_pct": round((v / total_spent) * 100, 1) if total_spent else 0.0,
#                 }
#                 for k, v in category_totals.items()
#             ],
#             key=lambda x: x["amount"],
#             reverse=True,
#         )[:5]

#         return {
#             "total_transactions": len(transactions),
#             "total_expenses": len(expenses),
#             "total_income": len(income),
#             "amount_spent": round(total_spent, 2),
#             "amount_earned": round(total_income, 2),
#             "net_flow": round(net_flow, 2),
#             "spent_last_30d": round(spent_30, 2),
#             "avg_daily_spend_30d": round(avg_daily_30, 2),
#             "avg_daily_spend_lookback": round(avg_daily_lookback, 2),
#             "top_categories": top_categories,
#             "largest_expense": self._largest_transaction(expenses),
#             "largest_income": self._largest_transaction(income),
#         }

#     def _largest_transaction(self, txns: List[Transaction]) -> Optional[Dict[str, Any]]:
#         """
#         Return a small dict for the largest transaction in a list (by amount).
#         If list is empty, return None.
#         """
#         if not txns:
#             return None
#         t = max(txns, key=lambda x: x.amount)
#         return {
#             "amount": round(t.amount, 2),
#             "date": t.date.isoformat(),
#             "description": t.description,
#             "category": str(t.category),
#             "merchant": t.merchant,
#         }

#     # -------------------------
#     # Patterns
#     # -------------------------
#     def _find_patterns(self, transactions: List[Transaction]) -> List[SpendingPattern]:
#         """
#         Collect all pattern detectors.
#         Each detector returns either:
#         - SpendingPattern (if detected)
#         - None (if not detected / insufficient data)
#         """
#         patterns: List[SpendingPattern] = []

#         p = self._weekend_spend(transactions)
#         if p:
#             patterns.append(p)

#         p = self._category_concentration(transactions)
#         if p:
#             patterns.append(p)

#         p = self._subscriptions_enhanced(transactions)
#         if p:
#             patterns.append(p)

#         p = self._payday_spend(transactions)
#         if p:
#             patterns.append(p)

#         return patterns

#     def _weekend_spend(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
#         """
#         Detect if the user tends to spend more per transaction on weekends.

#         Logic:
#         - Split expense transactions into weekend vs weekday
#         - Compare averages
#         - Trigger if weekend avg is 30% higher than weekday avg
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         if len(exp) < 6:
#             return None

#         weekend_amounts = [t.amount for t in exp if t.date.weekday() >= 5]  # Sat/Sun
#         weekday_amounts = [t.amount for t in exp if t.date.weekday() < 5]   # Mon-Fri

#         if not weekend_amounts or not weekday_amounts:
#             return None

#         w_avg = mean(weekend_amounts)
#         d_avg = mean(weekday_amounts)
#         if d_avg <= 0:
#             return None

#         ratio = w_avg / d_avg
#         if ratio >= 1.3:
#             return SpendingPattern(
#                 name="weekend_spending",
#                 description=f"You spend {(ratio - 1) * 100:.0f}% more per transaction on weekends than weekdays.",
#                 severity="warning",
#                 data={
#                     "weekend_avg": round(w_avg, 2),
#                     "weekday_avg": round(d_avg, 2),
#                     "ratio": round(ratio, 2),
#                     "weekend_txn_count": len(weekend_amounts),
#                     "weekday_txn_count": len(weekday_amounts),
#                 },
#             )
#         return None

#     def _category_concentration(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
#         """
#         Detect if spending is heavily concentrated in one category.

#         Logic:
#         - Compute total expense spend
#         - Find top category share
#         - Trigger if top category >= 50% of total expense spend
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         total = sum(t.amount for t in exp)
#         if total <= 0:
#             return None

#         by_cat: Dict[str, float] = defaultdict(float)
#         for t in exp:
#             by_cat[str(t.category)] += t.amount

#         top_cat, top_amt = max(by_cat.items(), key=lambda x: x[1])
#         pct = (top_amt / total) * 100
#         if pct >= 50:
#             return SpendingPattern(
#                 name="category_concentration",
#                 description=f"{pct:.0f}% of your spending is in '{top_cat}'.",
#                 severity="critical" if pct >= 70 else "warning",
#                 data={"category": top_cat, "amount": round(top_amt, 2), "pct": round(pct, 1)},
#             )
#         return None

#     def _subscriptions_enhanced(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
#         """
#         Detect subscriptions using:
#         1) Known subscription merchant list (high precision)
#         2) Gap consistency (monthly/weekly cadence)
#         3) Weak evidence from category (streaming/software/etc.)

#         Why this is better than naive detection:
#         - Walmart groceries repeat weekly/monthly but are NOT subscriptions.
#         - We require cadence consistency and/or known merchants.
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         if len(exp) < 6:
#             return None

#         # Bucket by (merchant_normalized, rounded_amount)
#         buckets: Dict[Tuple[str, int], List[Transaction]] = defaultdict(list)
#         for t in exp:
#             merchant = self._normalize_merchant(t)
#             amount_bucket = int(round(t.amount))
#             buckets[(merchant, amount_bucket)].append(t)

#         subscriptions: List[Dict[str, Any]] = []

#         for (merchant, amount_bucket), txs in buckets.items():
#             # Need at least 2 occurrences to even consider "recurring"
#             if len(txs) < 2:
#                 continue

#             # Strong evidence: known subscription merchant
#             is_known = merchant in KNOWN_SUBSCRIPTION_MERCHANTS

#             # Weak evidence: category matches subscription-like buckets
#             cat_is_sub = any(str(t.category) in SUBSCRIPTION_CATEGORIES for t in txs)

#             # Sort by date and compute gaps between occurrences
#             txs_sorted = sorted(txs, key=lambda x: x.date)
#             gaps = [(txs_sorted[i].date - txs_sorted[i - 1].date).days for i in range(1, len(txs_sorted))]
#             if not gaps:
#                 continue

#             avg_gap = mean(gaps)
#             gap_std = stdev(gaps) if len(gaps) > 1 else 0.0

#             # Monthly cadence typically around 30 days (give it a tolerance window)
#             is_monthly = 25 <= avg_gap <= 35
#             # Weekly cadence around 7 days
#             is_weekly = 6 <= avg_gap <= 8

#             # Consistency: small std dev implies consistent billing cycle
#             is_consistent = True if len(gaps) == 1 else (gap_std < 5)

#             # Decision:
#             # - If known merchant => treat as subscription even if cadence is "regular"
#             # - Else require cadence + consistency + enough occurrences
#             is_sub = False
#             cadence = None

#             if is_known:
#                 is_sub = True
#                 cadence = "monthly" if is_monthly else "weekly" if is_weekly else "regular"
#             elif is_monthly and is_consistent and (len(txs_sorted) >= 3 or cat_is_sub):
#                 is_sub = True
#                 cadence = "monthly"
#             elif is_weekly and is_consistent and (len(txs_sorted) >= 4 or cat_is_sub):
#                 is_sub = True
#                 cadence = "weekly"

#             if is_sub:
#                 confidence = "high" if is_known else ("medium" if is_consistent else "low")
#                 subscriptions.append(
#                     {
#                         "merchant": merchant,
#                         "approx_amount": float(amount_bucket),
#                         "count": len(txs_sorted),
#                         "cadence": cadence,
#                         "avg_gap_days": round(avg_gap, 1),
#                         "gap_std_days": round(gap_std, 1),
#                         "confidence": confidence,
#                         "last_date": txs_sorted[-1].date.isoformat(),
#                     }
#                 )

#         if not subscriptions:
#             return None

#         # Sort: most repeated & most confident first
#         subscriptions.sort(key=lambda x: (x["confidence"] == "high", x["count"]), reverse=True)

#         return SpendingPattern(
#             name="subscriptions",
#             description=f"Detected {len(subscriptions)} subscription services.",
#             severity="info",
#             data={"subscriptions": subscriptions[:8]},
#         )

#     def _payday_spend(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
#         """
#         Detect if spending spikes shortly after income transactions.

#         Logic:
#         - Identify income dates (paydays)
#         - Consider expenses within 0..3 days after each income date as "after payday"
#         - Compare average expense amount after payday vs other days
#         - Trigger if after-payday avg is 20% higher

#         Note:
#         - This is a heuristic; later you can refine by detecting regular income cadence.
#         """
#         income_dates = sorted({t.date for t in transactions if self._is_income(t)})
#         exp = [t for t in transactions if self._is_expense(t)]
#         if not income_dates or len(exp) < 6:
#             return None

#         after_payday_amounts: List[float] = []
#         normal_amounts: List[float] = []

#         for t in exp:
#             is_after = any(0 <= (t.date - pd).days <= 3 for pd in income_dates)
#             if is_after:
#                 after_payday_amounts.append(t.amount)
#             else:
#                 normal_amounts.append(t.amount)

#         if len(after_payday_amounts) < 3 or len(normal_amounts) < 3:
#             return None

#         after_avg = mean(after_payday_amounts)
#         normal_avg = mean(normal_amounts)

#         if normal_avg <= 0:
#             return None

#         ratio = after_avg / normal_avg
#         if ratio >= 1.2:
#             return SpendingPattern(
#                 name="payday_spending",
#                 description="You spend noticeably more within 3 days after income hits.",
#                 severity="warning",
#                 data={
#                     "after_payday_avg": round(after_avg, 2),
#                     "normal_avg": round(normal_avg, 2),
#                     "ratio": round(ratio, 2),
#                     "after_payday_txn_count": len(after_payday_amounts),
#                     "normal_txn_count": len(normal_amounts),
#                 },
#             )

#         return None

#     # -------------------------
#     # Trends
#     # -------------------------
#     def _find_trends(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
#         """
#         Month-to-month spending trend.

#         Logic:
#         - Sum expenses per YYYY-MM
#         - Compare first vs last month in the window
#         - If change >= +20% => increasing
#         - If change <= -20% => decreasing
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         by_month: Dict[str, float] = defaultdict(float)
#         for t in exp:
#             by_month[t.date.strftime("%Y-%m")] += t.amount

#         if len(by_month) < 2:
#             return []

#         months = sorted(by_month.items())
#         first_m, first_v = months[0]
#         last_m, last_v = months[-1]

#         if first_v <= 0:
#             return []

#         change = (last_v / first_v) - 1.0

#         if change >= 0.2:
#             return [
#                 {
#                     "type": "increasing",
#                     "severity": "warning",
#                     "description": f"Spending increased by ~{change * 100:.0f}% from {first_m} to {last_m}.",
#                 }
#             ]
#         if change <= -0.2:
#             return [
#                 {
#                     "type": "decreasing",
#                     "severity": "positive",
#                     "description": f"Nice! Spending decreased by ~{abs(change) * 100:.0f}% from {first_m} to {last_m}.",
#                 }
#             ]
#         return []

#     # -------------------------
#     # Spending Velocity
#     # -------------------------
#     def _calculate_spending_velocity(self, transactions: List[Transaction]) -> Dict[str, Any]:
#         """
#         Spending velocity: compare last 7 days vs previous 7 days.

#         Output:
#         {
#           "last_7_days": ...,
#           "previous_7_days": ...,
#           "change_percent": ...,
#           "trend": "increasing|decreasing|stable",
#           "alert": "⚠️ ..." (optional)
#         }
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         today_date = date.today()

#         # last 7 days (inclusive)
#         last_7_start = today_date - timedelta(days=7)
#         last_7_total = sum(t.amount for t in exp if t.date >= last_7_start)

#         # previous 7 days: 8..14 days ago
#         prev_7_start = today_date - timedelta(days=14)
#         prev_7_end = today_date - timedelta(days=8)
#         prev_7_total = sum(t.amount for t in exp if prev_7_start <= t.date <= prev_7_end)

#         out: Dict[str, Any] = {
#             "last_7_days": round(last_7_total, 2),
#             "previous_7_days": round(prev_7_total, 2),
#         }

#         if prev_7_total > 0:
#             change_pct = ((last_7_total - prev_7_total) / prev_7_total) * 100.0
#             out["change_percent"] = round(change_pct, 1)
#             out["trend"] = "increasing" if change_pct > 10 else "decreasing" if change_pct < -10 else "stable"
#             if change_pct > 30:
#                 out["alert"] = "⚠️ Spending spike detected!"
#         else:
#             # If there was no spending in the previous window, we can’t compute percent change safely.
#             out["trend"] = "unknown"

#         return out

#     # -------------------------
#     # Top Merchants
#     # -------------------------
#     def _find_top_merchants(self, transactions: List[Transaction], limit: int = 10) -> List[Dict[str, Any]]:
#         """
#         Top merchants by total spending.

#         Logic:
#         - Normalize merchant
#         - Sum amounts + count txns per merchant
#         - Sort by total_spent desc
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         totals: Dict[str, float] = defaultdict(float)
#         counts: Dict[str, int] = defaultdict(int)

#         for t in exp:
#             m = self._normalize_merchant(t)
#             totals[m] += t.amount
#             counts[m] += 1

#         rows = []
#         for m, total in totals.items():
#             c = counts[m]
#             rows.append(
#                 {
#                     "merchant": m,
#                     "total_spent": round(total, 2),
#                     "transaction_count": c,
#                     "avg_per_transaction": round(total / c, 2) if c else 0.0,
#                 }
#             )

#         rows.sort(key=lambda x: x["total_spent"], reverse=True)
#         return rows[:limit]

#     # -------------------------
#     # Anomalies (IQR)
#     # -------------------------
#     def _find_anomalies_iqr(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
#         """
#         Find unusually large expenses per category using IQR rule.

#         IQR method:
#         - For each category, collect expense amounts
#         - Compute Q1 and Q3
#         - Upper bound = Q3 + 1.5 * IQR
#         - Any amount > upper bound is flagged as "high_spend_outlier"

#         Why IQR?
#         - More robust than mean/std when distributions are skewed.
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         by_cat: Dict[str, List[Transaction]] = defaultdict(list)
#         for t in exp:
#             by_cat[str(t.category)].append(t)

#         anomalies: List[Dict[str, Any]] = []

#         for cat, txs in by_cat.items():
#             # Need a minimum sample size; too small => unreliable quartiles
#             if len(txs) < 6:
#                 continue

#             amounts = sorted([t.amount for t in txs])
#             # Simple quartile estimate by index (good enough for MVP)
#             q1 = amounts[int(0.25 * (len(amounts) - 1))]
#             q3 = amounts[int(0.75 * (len(amounts) - 1))]
#             iqr = q3 - q1
#             if iqr <= 0:
#                 continue

#             upper = q3 + 1.5 * iqr

#             for t in txs:
#                 if t.amount > upper:
#                     anomalies.append(
#                         {
#                             "type": "high_spend_outlier",
#                             "category": cat,
#                             "amount": round(t.amount, 2),
#                             "threshold": round(upper, 2),
#                             "date": t.date.isoformat(),
#                             "description": t.description,
#                             "severity": "warning",
#                         }
#                     )

#         # Limit output so UI doesn’t get overwhelmed
#         return anomalies[:20]

#     # -------------------------
#     # Budget insights
#     # -------------------------
#     def _analyze_budget(self, transactions: List[Transaction], budget: Budget) -> Dict[str, Any]:
#         """
#         Compare actual spending (from transactions) against budget limits.

#         Logic:
#         - Sum expense amounts per category
#         - For each budget category:
#             - if spent >= limit => "over"
#             - elif spent >= limit*alert_threshold => "warning"
#         """
#         exp = [t for t in transactions if self._is_expense(t)]
#         spending_by_cat: Dict[str, float] = defaultdict(float)
#         for t in exp:
#             spending_by_cat[str(t.category)] += t.amount

#         insights: Dict[str, Any] = {}
#         for bc in budget.categories:
#             cat = str(bc.category)
#             spent = float(spending_by_cat.get(cat, 0.0))
#             limit = float(bc.limit)
#             if limit <= 0:
#                 continue

#             pct = (spent / limit) * 100.0

#             if spent >= limit:
#                 insights[cat] = {
#                     "status": "over",
#                     "spent": round(spent, 2),
#                     "limit": round(limit, 2),
#                     "overshoot": round(spent - limit, 2),
#                     "percent": round(pct, 1),
#                 }
#             elif spent >= limit * float(budget.alert_threshold):
#                 insights[cat] = {
#                     "status": "warning",
#                     "spent": round(spent, 2),
#                     "limit": round(limit, 2),
#                     "remaining": round(limit - spent, 2),
#                     "percent": round(pct, 1),
#                 }

#         return insights

#     # -------------------------
#     # Advice
#     # -------------------------
#     def _generate_advice(self, transactions: List[Transaction], student: Student, patterns: List[SpendingPattern]) -> List[str]:
#         """
#         Generate a few simple, user-friendly suggestions.

#         Logic:
#         - savings rate (income - spend) / income
#         - include warnings/critical patterns as advice bullets
#         - include risk-profile based hint
#         """
#         advice: List[str] = []

#         income = sum(t.amount for t in transactions if self._is_income(t))
#         spent = sum(t.amount for t in transactions if self._is_expense(t))

#         # Savings rate guidance
#         if income > 0:
#             savings_rate = ((income - spent) / income) * 100.0
#             if savings_rate < 10:
#                 advice.append("💰 Try targeting at least a 10% savings rate (income minus expenses).")
#             elif savings_rate >= 20:
#                 advice.append(f"🎯 Nice! Your savings rate is about {savings_rate:.0f}%.")

#         # Pattern-based nudges
#         for p in patterns:
#             if p.severity == "critical":
#                 advice.append(f"🚨 {p.description}")
#             elif p.severity == "warning":
#                 advice.append(f"⚠️ {p.description}")

#         # Student profile-based guidance
#         if getattr(student, "risk_profile", None) == "conservative":
#             advice.append("🛡️ Conservative profile: prioritize emergency fund + stable savings before investing.")
#         elif getattr(student, "risk_profile", None) == "aggressive":
#             advice.append("⚡ Aggressive profile: once budget is stable, consider higher-growth investing (simulated).")

#         # Cap list size for UI cleanliness
#         return advice[:6]


# def create_analyzer() -> AnalyzerAgent:
#     """Simple factory function used by tests and graph builder."""
#     return AnalyzerAgent()








from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from statistics import mean, stdev

from schemas.transaction import Transaction, TransactionType
from schemas.student import Student
from schemas.budget import Budget


# -------------------------
# Small models (JSON-friendly)
# -------------------------
@dataclass
class SpendingPattern:
    """
    Small container for a detected pattern.
    """
    name: str
    description: str
    severity: str = "info"  # "info" | "warning" | "critical"
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["data"] is None:
            d["data"] = {}
        return d


# -------------------------
# Subscription detection hints
# -------------------------
KNOWN_SUBSCRIPTION_MERCHANTS = {
    "netflix", "spotify", "hulu", "disney+", "disneyplus", "amazon prime", "prime video",
    "apple music", "apple tv", "youtube premium", "youtube music", "paramount+",
    "peacock", "hbomax", "hbo max", "max", "starz", "showtime", "slack", "zoom",
    "microsoft 365", "office 365", "adobe", "creative cloud", "dropbox", "google one",
    "icloud", "apple storage", "xbox live", "xbox game pass", "playstation plus",
    "nintendo online", "discord nitro", "patreon", "medium", "substack"
}

SUBSCRIPTION_CATEGORIES = {"streaming", "entertainment", "software", "cloud", "gaming"}


# -------------------------
# Analyzer
# -------------------------
class AnalyzerAgent:
    """
    Analyzes transaction history to find patterns and insights.
    """

    def __init__(self):
        self.name = "Analyzer Agent"

    def analyze_student(
        self,
        student: Student,
        transactions: List[Transaction],
        budget: Optional[Budget] = None,
        *,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        txns = self._filter_recent(transactions, lookback_days)

        summary = self._create_summary(txns, lookback_days=lookback_days)
        patterns = self._find_patterns(txns, summary)
        trends = self._find_trends(txns)
        anomalies = self._find_anomalies_iqr(txns)
        budget_insights = self._analyze_budget(txns, budget) if budget else {}
        advice = self._generate_advice(txns, student, patterns, summary)
        velocity = self._calculate_spending_velocity(txns)
        top_merchants = self._find_top_merchants(txns)

        return {
            "student_id": student.student_id,
            "analysis_date": date.today().isoformat(),
            "window_days": lookback_days,
            "summary": summary,
            "patterns": [p.to_dict() for p in patterns],
            "trends": trends,
            "anomalies": anomalies,
            "budget_insights": budget_insights,
            "advice": advice,
            "spending_velocity": velocity,
            "top_merchants": top_merchants,
        }

    # -------------------------
    # Basic helpers
    # -------------------------
    def _filter_recent(self, transactions: List[Transaction], lookback_days: int) -> List[Transaction]:
        if lookback_days <= 0:
            return list(transactions)
        cutoff = date.today() - timedelta(days=lookback_days)
        return [t for t in transactions if t.date >= cutoff]

    def _is_expense(self, t: Transaction) -> bool:
        return t.transaction_type == TransactionType.EXPENSE

    def _is_income(self, t: Transaction) -> bool:
        return t.transaction_type == TransactionType.INCOME

    def _is_transfer(self, t: Transaction) -> bool:
        return t.transaction_type == TransactionType.TRANSFER

    def _normalize_merchant(self, t: Transaction) -> str:
        m = (t.merchant or "").strip()
        if m:
            return " ".join(m.lower().split())

        d = " ".join((t.description or "").strip().split()).lower()
        if not d:
            return "unknown"

        noise_prefixes = ("pos", "purchase", "debit", "credit", "online", "payment", "withdrawal", "deposit")
        parts = d.split()
        if parts and parts[0] in noise_prefixes:
            parts = parts[1:]

        cleaned = " ".join(parts[:3]).strip()
        return cleaned if cleaned else "unknown"

    def _data_quality_flags(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Small data quality helper so analysis can be less overconfident.
        """
        expenses = [t for t in transactions if self._is_expense(t)]
        incomes = [t for t in transactions if self._is_income(t)]
        transfers = [t for t in transactions if self._is_transfer(t)]

        total = len(transactions)
        transfer_ratio = (len(transfers) / total) if total > 0 else 0.0

        return {
            "transaction_count": total,
            "expense_count": len(expenses),
            "income_count": len(incomes),
            "transfer_count": len(transfers),
            "transfer_ratio": round(transfer_ratio, 2),
            "limited_income_visibility": len(incomes) == 0,
            "small_expense_sample": len(expenses) < 5,
            "transfer_heavy_dataset": transfer_ratio >= 0.4,
        }

    # -------------------------
    # Summary
    # -------------------------
    def _create_summary(self, transactions: List[Transaction], *, lookback_days: int) -> Dict[str, Any]:
        if not transactions:
            return {"error": "No transactions to analyze"}

        expenses = [t for t in transactions if self._is_expense(t)]
        income = [t for t in transactions if self._is_income(t)]
        transfers = [t for t in transactions if self._is_transfer(t)]

        total_spent = sum(t.amount for t in expenses)
        total_income = sum(t.amount for t in income)
        net_flow = total_income - total_spent

        cutoff_30 = date.today() - timedelta(days=30)
        exp_30 = [t for t in expenses if t.date >= cutoff_30]
        spent_30 = sum(t.amount for t in exp_30)
        avg_daily_30 = spent_30 / 30.0

        window_days = max(1, lookback_days)
        avg_daily_lookback = total_spent / float(window_days)

        category_totals: Dict[str, float] = defaultdict(float)
        for t in expenses:
            category_totals[str(t.category)] += float(t.amount)

        top_categories = sorted(
            [
                {
                    "category": k,
                    "amount": round(v, 2),
                    "share_pct": round((v / total_spent) * 100, 1) if total_spent else 0.0,
                }
                for k, v in category_totals.items()
            ],
            key=lambda x: x["amount"],
            reverse=True,
        )[:5]

        return {
            "total_transactions": len(transactions),
            "total_expenses": len(expenses),
            "total_income": len(income),
            "total_transfers": len(transfers),
            "amount_spent": round(total_spent, 2),
            "amount_earned": round(total_income, 2),
            "net_flow": round(net_flow, 2),
            "spent_last_30d": round(spent_30, 2),
            "avg_daily_spend_30d": round(avg_daily_30, 2),
            "avg_daily_spend_lookback": round(avg_daily_lookback, 2),
            "top_categories": top_categories,
            "largest_expense": self._largest_transaction(expenses),
            "largest_income": self._largest_transaction(income),
            "data_quality": self._data_quality_flags(transactions),
        }

    def _largest_transaction(self, txns: List[Transaction]) -> Optional[Dict[str, Any]]:
        if not txns:
            return None
        t = max(txns, key=lambda x: x.amount)
        return {
            "amount": round(t.amount, 2),
            "date": t.date.isoformat(),
            "description": t.description,
            "category": str(t.category),
            "merchant": t.merchant,
        }

    # -------------------------
    # Patterns
    # -------------------------
    def _find_patterns(self, transactions: List[Transaction], summary: Dict[str, Any]) -> List[SpendingPattern]:
        patterns: List[SpendingPattern] = []

        p = self._weekend_spend(transactions)
        if p:
            patterns.append(p)

        p = self._category_concentration(transactions, summary)
        if p:
            patterns.append(p)

        p = self._subscriptions_enhanced(transactions)
        if p:
            patterns.append(p)

        p = self._payday_spend(transactions)
        if p:
            patterns.append(p)

        return patterns

    def _weekend_spend(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
        exp = [t for t in transactions if self._is_expense(t)]
        if len(exp) < 6:
            return None

        weekend_amounts = [t.amount for t in exp if t.date.weekday() >= 5]
        weekday_amounts = [t.amount for t in exp if t.date.weekday() < 5]

        if not weekend_amounts or not weekday_amounts:
            return None

        w_avg = mean(weekend_amounts)
        d_avg = mean(weekday_amounts)
        if d_avg <= 0:
            return None

        ratio = w_avg / d_avg
        if ratio >= 1.3:
            return SpendingPattern(
                name="weekend_spending",
                description=f"You spend {(ratio - 1) * 100:.0f}% more per transaction on weekends than weekdays.",
                severity="warning",
                data={
                    "weekend_avg": round(w_avg, 2),
                    "weekday_avg": round(d_avg, 2),
                    "ratio": round(ratio, 2),
                    "weekend_txn_count": len(weekend_amounts),
                    "weekday_txn_count": len(weekday_amounts),
                },
            )
        return None

    def _category_concentration(self, transactions: List[Transaction], summary: Dict[str, Any]) -> Optional[SpendingPattern]:
        """
        Safer version:
        - require enough expense rows
        - ignore tiny datasets
        - 50% no longer means automatic danger
        - 70%+ only becomes warning unless supported by stronger evidence
        """
        exp = [t for t in transactions if self._is_expense(t)]
        total = sum(t.amount for t in exp)
        dq = summary.get("data_quality", {})

        if total <= 0:
            return None

        if len(exp) < 5:
            return None

        if dq.get("transfer_heavy_dataset"):
            return None

        by_cat: Dict[str, float] = defaultdict(float)
        by_cat_count: Dict[str, int] = defaultdict(int)

        for t in exp:
            cat = str(t.category)
            by_cat[cat] += t.amount
            by_cat_count[cat] += 1

        top_cat, top_amt = max(by_cat.items(), key=lambda x: x[1])
        pct = (top_amt / total) * 100
        txn_count = by_cat_count[top_cat]

        # Require both high share and some repeated evidence
        if pct >= 80 and txn_count >= 2:
            severity = "warning"
        elif pct >= 65 and txn_count >= 3:
            severity = "warning"
        else:
            return None

        return SpendingPattern(
            name="category_concentration",
            description=f"{pct:.0f}% of your spending is in '{top_cat}'.",
            severity=severity,
            data={
                "category": top_cat,
                "amount": round(top_amt, 2),
                "pct": round(pct, 1),
                "transaction_count": txn_count,
            },
        )

    def _subscriptions_enhanced(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
        exp = [t for t in transactions if self._is_expense(t)]
        if len(exp) < 6:
            return None

        buckets: Dict[Tuple[str, int], List[Transaction]] = defaultdict(list)
        for t in exp:
            merchant = self._normalize_merchant(t)
            amount_bucket = int(round(t.amount))
            buckets[(merchant, amount_bucket)].append(t)

        subscriptions: List[Dict[str, Any]] = []

        for (merchant, amount_bucket), txs in buckets.items():
            if len(txs) < 2:
                continue

            is_known = merchant in KNOWN_SUBSCRIPTION_MERCHANTS
            cat_is_sub = any(str(t.category) in SUBSCRIPTION_CATEGORIES for t in txs)

            txs_sorted = sorted(txs, key=lambda x: x.date)
            gaps = [(txs_sorted[i].date - txs_sorted[i - 1].date).days for i in range(1, len(txs_sorted))]
            if not gaps:
                continue

            avg_gap = mean(gaps)
            gap_std = stdev(gaps) if len(gaps) > 1 else 0.0

            is_monthly = 25 <= avg_gap <= 35
            is_weekly = 6 <= avg_gap <= 8
            is_consistent = True if len(gaps) == 1 else (gap_std < 5)

            is_sub = False
            cadence = None

            if is_known:
                is_sub = True
                cadence = "monthly" if is_monthly else "weekly" if is_weekly else "regular"
            elif is_monthly and is_consistent and (len(txs_sorted) >= 3 or cat_is_sub):
                is_sub = True
                cadence = "monthly"
            elif is_weekly and is_consistent and (len(txs_sorted) >= 4 or cat_is_sub):
                is_sub = True
                cadence = "weekly"

            if is_sub:
                confidence = "high" if is_known else ("medium" if is_consistent else "low")
                subscriptions.append(
                    {
                        "merchant": merchant,
                        "approx_amount": float(amount_bucket),
                        "count": len(txs_sorted),
                        "cadence": cadence,
                        "avg_gap_days": round(avg_gap, 1),
                        "gap_std_days": round(gap_std, 1),
                        "confidence": confidence,
                        "last_date": txs_sorted[-1].date.isoformat(),
                    }
                )

        if not subscriptions:
            return None

        subscriptions.sort(key=lambda x: (x["confidence"] == "high", x["count"]), reverse=True)

        return SpendingPattern(
            name="subscriptions",
            description=f"Detected {len(subscriptions)} subscription services.",
            severity="info",
            data={"subscriptions": subscriptions[:8]},
        )

    def _payday_spend(self, transactions: List[Transaction]) -> Optional[SpendingPattern]:
        income_dates = sorted({t.date for t in transactions if self._is_income(t)})
        exp = [t for t in transactions if self._is_expense(t)]
        if not income_dates or len(exp) < 6:
            return None

        after_payday_amounts: List[float] = []
        normal_amounts: List[float] = []

        for t in exp:
            is_after = any(0 <= (t.date - pd).days <= 3 for pd in income_dates)
            if is_after:
                after_payday_amounts.append(t.amount)
            else:
                normal_amounts.append(t.amount)

        if len(after_payday_amounts) < 3 or len(normal_amounts) < 3:
            return None

        after_avg = mean(after_payday_amounts)
        normal_avg = mean(normal_amounts)

        if normal_avg <= 0:
            return None

        ratio = after_avg / normal_avg
        if ratio >= 1.2:
            return SpendingPattern(
                name="payday_spending",
                description="You spend noticeably more within 3 days after income hits.",
                severity="warning",
                data={
                    "after_payday_avg": round(after_avg, 2),
                    "normal_avg": round(normal_avg, 2),
                    "ratio": round(ratio, 2),
                    "after_payday_txn_count": len(after_payday_amounts),
                    "normal_txn_count": len(normal_amounts),
                },
            )

        return None

    # -------------------------
    # Trends
    # -------------------------
    def _find_trends(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """
        Safer trend detection:
        - require at least 2 months
        - require both months to have enough expense rows
        - compare last full-ish month buckets carefully
        """
        exp = [t for t in transactions if self._is_expense(t)]
        by_month: Dict[str, float] = defaultdict(float)
        by_month_count: Dict[str, int] = defaultdict(int)

        for t in exp:
            month_key = t.date.strftime("%Y-%m")
            by_month[month_key] += t.amount
            by_month_count[month_key] += 1

        if len(by_month) < 2:
            return []

        months = sorted(by_month.items())
        first_m, first_v = months[0]
        last_m, last_v = months[-1]

        if first_v <= 0:
            return []

        # Avoid fake trends from tiny partial month counts
        if by_month_count[first_m] < 3 or by_month_count[last_m] < 3:
            return []

        change = (last_v / first_v) - 1.0

        if change >= 0.3:
            return [
                {
                    "type": "increasing",
                    "severity": "warning",
                    "description": f"Spending increased by ~{change * 100:.0f}% from {first_m} to {last_m}.",
                }
            ]
        if change <= -0.3:
            return [
                {
                    "type": "decreasing",
                    "severity": "positive",
                    "description": f"Spending decreased by ~{abs(change) * 100:.0f}% from {first_m} to {last_m}.",
                }
            ]
        return []

    # -------------------------
    # Spending Velocity
    # -------------------------
    def _calculate_spending_velocity(self, transactions: List[Transaction]) -> Dict[str, Any]:
        exp = [t for t in transactions if self._is_expense(t)]
        today_date = date.today()

        last_7_start = today_date - timedelta(days=7)
        last_7_total = sum(t.amount for t in exp if t.date >= last_7_start)

        prev_7_start = today_date - timedelta(days=14)
        prev_7_end = today_date - timedelta(days=8)
        prev_7_total = sum(t.amount for t in exp if prev_7_start <= t.date <= prev_7_end)

        out: Dict[str, Any] = {
            "last_7_days": round(last_7_total, 2),
            "previous_7_days": round(prev_7_total, 2),
        }

        if prev_7_total > 0:
            change_pct = ((last_7_total - prev_7_total) / prev_7_total) * 100.0
            out["change_percent"] = round(change_pct, 1)
            out["trend"] = "increasing" if change_pct > 10 else "decreasing" if change_pct < -10 else "stable"
            if change_pct > 30:
                out["alert"] = "⚠️ Spending spike detected!"
        else:
            out["trend"] = "unknown"

        return out

    # -------------------------
    # Top Merchants
    # -------------------------
    def _find_top_merchants(self, transactions: List[Transaction], limit: int = 10) -> List[Dict[str, Any]]:
        exp = [t for t in transactions if self._is_expense(t)]
        totals: Dict[str, float] = defaultdict(float)
        counts: Dict[str, int] = defaultdict(int)

        for t in exp:
            m = self._normalize_merchant(t)
            totals[m] += t.amount
            counts[m] += 1

        rows = []
        for m, total in totals.items():
            c = counts[m]
            rows.append(
                {
                    "merchant": m,
                    "total_spent": round(total, 2),
                    "transaction_count": c,
                    "avg_per_transaction": round(total / c, 2) if c else 0.0,
                }
            )

        rows.sort(key=lambda x: x["total_spent"], reverse=True)
        return rows[:limit]

    # -------------------------
    # Anomalies (IQR)
    # -------------------------
    def _find_anomalies_iqr(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        exp = [t for t in transactions if self._is_expense(t)]
        by_cat: Dict[str, List[Transaction]] = defaultdict(list)
        for t in exp:
            by_cat[str(t.category)].append(t)

        anomalies: List[Dict[str, Any]] = []

        for cat, txs in by_cat.items():
            if len(txs) < 6:
                continue

            amounts = sorted([t.amount for t in txs])
            q1 = amounts[int(0.25 * (len(amounts) - 1))]
            q3 = amounts[int(0.75 * (len(amounts) - 1))]
            iqr = q3 - q1
            if iqr <= 0:
                continue

            upper = q3 + 1.5 * iqr

            for t in txs:
                if t.amount > upper:
                    anomalies.append(
                        {
                            "type": "high_spend_outlier",
                            "category": cat,
                            "amount": round(t.amount, 2),
                            "threshold": round(upper, 2),
                            "date": t.date.isoformat(),
                            "description": t.description,
                            "severity": "warning",
                        }
                    )

        return anomalies[:20]

    # -------------------------
    # Budget insights
    # -------------------------
    def _analyze_budget(self, transactions: List[Transaction], budget: Budget) -> Dict[str, Any]:
        exp = [t for t in transactions if self._is_expense(t)]
        spending_by_cat: Dict[str, float] = defaultdict(float)
        for t in exp:
            spending_by_cat[str(t.category)] += t.amount

        insights: Dict[str, Any] = {}
        for bc in budget.categories:
            cat = str(bc.category)
            spent = float(spending_by_cat.get(cat, 0.0))
            limit = float(bc.limit)
            if limit <= 0:
                continue

            pct = (spent / limit) * 100.0

            if spent >= limit:
                insights[cat] = {
                    "status": "over",
                    "spent": round(spent, 2),
                    "limit": round(limit, 2),
                    "overshoot": round(spent - limit, 2),
                    "percent": round(pct, 1),
                }
            elif spent >= limit * float(budget.alert_threshold):
                insights[cat] = {
                    "status": "warning",
                    "spent": round(spent, 2),
                    "limit": round(limit, 2),
                    "remaining": round(limit - spent, 2),
                    "percent": round(pct, 1),
                }

        return insights

    # -------------------------
    # Advice
    # -------------------------
    def _generate_advice(
        self,
        transactions: List[Transaction],
        student: Student,
        patterns: List[SpendingPattern],
        summary: Dict[str, Any],
    ) -> List[str]:
        advice: List[str] = []

        income = sum(t.amount for t in transactions if self._is_income(t))
        spent = sum(t.amount for t in transactions if self._is_expense(t))
        dq = summary.get("data_quality", {})

        # If no income is visible in transaction history, do not over-interpret savings rate.
        if income > 0:
            savings_rate = ((income - spent) / income) * 100.0
            if savings_rate < 10:
                advice.append("💰 Try targeting at least a 10% savings rate (income minus expenses).")
            elif savings_rate >= 20:
                advice.append(f"🎯 Nice! Your savings rate is about {savings_rate:.0f}%.")
        elif dq.get("limited_income_visibility"):
            advice.append("ℹ️ Income transactions are limited in this dataset, so savings-rate insights may be incomplete.")

        for p in patterns:
            if p.severity == "critical":
                advice.append(f"🚨 {p.description}")
            elif p.severity == "warning":
                advice.append(f"⚠️ {p.description}")

        if getattr(student, "risk_profile", None) == "conservative":
            advice.append("🛡️ Conservative profile: prioritize emergency fund + stable savings before investing.")
        elif getattr(student, "risk_profile", None) == "aggressive":
            advice.append("⚡ Aggressive profile: once your spending picture is stable, consider higher-growth investing approaches.")

        return advice[:6]


def create_analyzer() -> AnalyzerAgent:
    return AnalyzerAgent()