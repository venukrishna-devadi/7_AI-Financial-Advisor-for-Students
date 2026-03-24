"""
🏃 FINANCIAL RUNNER - Application service layer for the Financial Advisor

What this file does
-------------------
Acts as the clean bridge between UI/API and the LangGraph workflow.

Mental model:
- UI says: "Run this student's data through the full financial pipeline"
- Runner prepares graph state
- Runner calls the builder
- Runner normalizes result into something easy for UI / API / demos

Why this layer matters
----------------------
It keeps:
- UI simple
- graph internals hidden
- app-facing execution methods clean and reusable

Main responsibilities
---------------------
1. Input preparation
2. Graph invocation
3. Result normalization
4. Top-level error handling
5. Convenience methods for common app actions
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
import traceback
import threading
import queue
import time
import json

from schemas.student import Student
from schemas.transaction import Transaction
from schemas.budget import Budget
from schemas.goal import Goal

from graph.builder import create_financial_graph_builder, FinancialGraphState
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel
from dataclasses import is_dataclass, asdict

def _safe_serialize(obj, seen=None):
    if seen is None:
        seen = set()

    # primitives
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # circular reference protection
    obj_id = id(obj)
    if obj_id in seen:
        return "<circular_reference>"

    # simple special cases
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, Path):
        return str(obj)

    # pydantic
    if isinstance(obj, BaseModel):
        seen.add(obj_id)
        return _safe_serialize(obj.model_dump(), seen)

    # dataclass
    if is_dataclass(obj):
        seen.add(obj_id)
        return _safe_serialize(asdict(obj), seen)

    # dict
    if isinstance(obj, dict):
        seen.add(obj_id)
        return {str(k): _safe_serialize(v, seen) for k, v in obj.items()}

    # list / tuple / set
    if isinstance(obj, (list, tuple, set)):
        seen.add(obj_id)
        return [_safe_serialize(v, seen) for v in obj]

    # fallback
    return str(obj)

class FinancialRunnerResult:
    """
    Normalized result object for UI/API consumption.

    This wraps raw graph output and exposes:
    - success/failure
    - normalized sections
    - summary fields for quick UI access
    - warnings/errors
    - extraction details
    """

    def __init__(self, graph_output: Dict[str, Any]):
        self.raw = graph_output

        # Core status
        self.pipeline_status = graph_output.get("pipeline_status", "unknown")
        self.success = self.pipeline_status != "failed"
        self.has_partial_results = self.pipeline_status == "completed_with_errors"

        # Top-level warnings / errors
        self.warnings: List[str] = graph_output.get("warnings", []) or []
        self.errors: List[str] = graph_output.get("errors", []) or []

        # Student identity
        student_obj = graph_output.get("student")
        self.student_id = getattr(student_obj, "student_id", graph_output.get("student_id", None))

        # Normalized pipeline sections
        self.transactions: List[Transaction] = graph_output.get("transactions", []) or []
        self.extraction_result: Dict[str, Any] = graph_output.get("extraction_result") or {}
        self.analysis: Dict[str, Any] = graph_output.get("analysis") or {}
        self.plan: Dict[str, Any] = graph_output.get("plan") or {}
        self.tracking_report: Dict[str, Any] = graph_output.get("tracking_report") or {}
        self.advice_result: Dict[str, Any] = graph_output.get("advice_result") or {}
        self.alert_result: Dict[str, Any] = graph_output.get("alert_result") or {}

        # Convenience summary fields
        self.overall_health: str = "unknown"
        self.budget_health: str = "unknown"
        self.budget_percent_used: float = 0.0
        self.alert_total: int = 0
        self.alert_critical: int = 0
        self.alert_warning: int = 0
        self.top_priorities: List[str] = []
        self.immediate_actions: List[str] = []
        self.advisor_summary: str = ""

        # Optional metadata added by runner
        self.execution_time_seconds: Optional[float] = graph_output.get("execution_time_seconds")

        self._extract_summaries()

    def _extract_summaries(self):
        """
        Pull out the most useful summary fields so UI does not need
        to repeatedly navigate deep nested dictionaries.
        """
        # Advice summary
        advice_payload = self.advice_result.get("advice", {}) if isinstance(self.advice_result, dict) else {}
        self.overall_health = advice_payload.get("overall_financial_health", "unknown")
        self.top_priorities = advice_payload.get("top_priorities", []) or []
        self.immediate_actions = advice_payload.get("immediate_actions", []) or []
        self.advisor_summary = advice_payload.get("advisor_summary", "") or ""

        # Tracking summary
        tracking_payload = self.tracking_report.get("budget_status", {}) if isinstance(self.tracking_report, dict) else {}
        self.budget_health = tracking_payload.get("status", "unknown")
        self.budget_percent_used = tracking_payload.get("percent_used", 0.0)

        # Alert summary
        alert_summary = self.alert_result.get("summary", {}) if isinstance(self.alert_result, dict) else {}
        self.alert_total = alert_summary.get("total_alerts", 0)
        self.alert_critical = alert_summary.get("critical_count", 0)
        self.alert_warning = alert_summary.get("warning_count", 0)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "success": self.success,
            "pipeline_status": self.pipeline_status,
            "has_partial_results": self.has_partial_results,
            "student_id": self.student_id,
            "overall_health": self.overall_health,
            "budget_health": self.budget_health,
            "budget_percent_used": self.budget_percent_used,
            "alert_summary": {
                "total": self.alert_total,
                "critical": self.alert_critical,
                "warning": self.alert_warning,
            },
            "top_priorities": self.top_priorities,
            "immediate_actions": self.immediate_actions,
            "advisor_summary": self.advisor_summary,
            "warnings": self.warnings,
            "errors": self.errors,
            "execution_time_seconds": self.execution_time_seconds,
            "extraction_result": self.extraction_result,
            "result": {
                "transactions": [t.model_dump(mode="json") for t in self.transactions],
                "analysis": self.analysis,
                "plan": self.plan,
                "tracking_report": self.tracking_report,
                "advice_result": self.advice_result,
                "alert_result": self.alert_result,
            },
        }

        return _safe_serialize(payload)
        
    def __str__(self) -> str:
        status = "✅ Success" if self.success else "❌ Failed"
        return (
            f"FinancialRunnerResult("
            f"{status}, "
            f"pipeline_status={self.pipeline_status}, "
            f"health={self.overall_health}, "
            f"alerts={self.alert_total})"
        )
    

def error_result(
    error_message: str,
    student_id: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized safe error payload.
    Useful when something unexpected happens outside the graph.
    """
    return {
        "success": False,
        "pipeline_status": "failed",
        "has_partial_results": False,
        "student_id": student_id,
        "overall_health": "unknown",
        "budget_health": "unknown",
        "budget_percent_used": 0.0,
        "alert_summary": {
            "total": 0,
            "critical": 0,
            "warning": 0,
        },
        "top_priorities": [],
        "immediate_actions": [],
        "advisor_summary": "",
        "warnings": warnings or [],
        "errors": [error_message],
        "execution_time_seconds": None,
        "extraction_result": {},
        "result": {
            "transactions": [],
            "analysis": {},
            "plan": {},
            "tracking_report": {},
            "advice_result": {},
            "alert_result": {},
        },
    }


class FinancialRunner:
    """
    Application service layer for the Financial Advisor app.

    Public methods here are what UI / API code should call.
    """

    def __init__(self):
        self.builder = create_financial_graph_builder()
        self.call_count = 0

    def run(
            self,
            *,
            student: Student,
            transactions: Optional[List[Transaction]] = None,
            vision_output: Optional[Dict[str, Any]] = None,
            budget: Optional[Budget] = None,
            goals: Optional[List[Goal]] = None,
            lookback_days: int = 90,
            timeout_seconds: Optional[int] = None,
    )->FinancialRunnerResult:
        """
        Unified pipeline entrypoint.

        Supports either:
        - prebuilt transactions
        - vision_output (which graph intake will bridge into transactions)

        Args:
            student: required student object
            transactions: optional transaction history
            vision_output: optional structured output from vision wrapper
            budget: optional budget
            goals: optional goals
            lookback_days: how far analysis should look back
            timeout_seconds: optional timeout wrapper

        Returns:
            FinancialRunnerResult
        """

        self.call_count += 1
        start_time = time.time()

        # Build clean graph state
        state: FinancialGraphState = {
            "student": student,
            "transactions": transactions or [],
            "budget": budget,
            "goals": goals or [],
            "lookback_days": lookback_days,
            "warnings": [],
            "errors": [],
        }

        if vision_output is not None:
            state["vision_output"] = vision_output

        # Run graph
        if timeout_seconds is not None:
            result_dict = self._run_with_timeout(state, timeout_seconds)
        else:
            result_dict = self.builder.run(state)

        # Attach execution time at runner layer
        result_dict["execution_time_seconds"] = round(time.time() - start_time, 3)

        return FinancialRunnerResult(result_dict)
    
    def run_from_transactions(
        self,
        *,
        student: Student,
        transactions: List[Transaction],
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
        lookback_days: int = 90,
        timeout_seconds: Optional[int] = None,
    ) -> FinancialRunnerResult:
        """
        Convenience method when transactions already exist.
        """
        return self.run(
            student=student,
            transactions=transactions,
            budget=budget,
            goals=goals,
            lookback_days=lookback_days,
            timeout_seconds=timeout_seconds,
        )
    
    def run_from_vision(
        self,
        *,
        student: Student,
        vision_output: Dict[str, Any],
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
        lookback_days: int = 90,
        timeout_seconds: Optional[int] = None,
    ) -> FinancialRunnerResult:
        """
        Convenience method when the caller already has vision extraction output.
        """
        return self.run(
            student=student,
            vision_output=vision_output,
            budget=budget,
            goals=goals,
            lookback_days=lookback_days,
            timeout_seconds=timeout_seconds,
        )
    
    def add_transaction_and_rerun(
        self,
        *,
        student: Student,
        existing_transactions: List[Transaction],
        new_transaction: Transaction,
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
        lookback_days: int = 90,
    ) -> FinancialRunnerResult:
        """
        Append one new manual transaction and rerun the whole pipeline.
        Useful for form-based transaction entry in UI.
        """
        updated_transactions = list(existing_transactions) + [new_transaction]

        return self.run(
            student=student,
            transactions=updated_transactions,
            budget=budget,
            goals=goals,
            lookback_days=lookback_days,
        )
    
    def add_vision_and_rerun(
        self,
        *,
        student: Student,
        existing_transactions: List[Transaction],
        vision_output: Dict[str, Any],
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
        lookback_days: int = 90,
    ) -> FinancialRunnerResult:
        """
        Add transactions extracted from vision output into an existing history,
        then rerun the full pipeline.

        Current MVP approach:
        1. run vision through graph once to get bridged transactions
        2. merge with existing history
        3. rerun the full graph

        This is slightly redundant but simple and safe for MVP.
        """
        vision_result = self.run_from_vision(
            student=student,
            vision_output=vision_output,
            budget=budget,
            goals=goals,
            lookback_days=lookback_days,
        )

        if not vision_result.success:
            return vision_result

        merged_transactions = list(existing_transactions) + list(vision_result.transactions)

        return self.run(
            student=student,
            transactions=merged_transactions,
            budget=budget,
            goals=goals,
            lookback_days=lookback_days,
        )
    
    def quick_health_check(
        self,
        *,
        student: Student,
        transactions: Optional[List[Transaction]] = None,
        vision_output: Optional[Dict[str, Any]] = None,
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
    ) -> Dict[str, Any]:
        """
        Lightweight convenience wrapper for dashboard previews.

        Still uses the pipeline, but returns only a compact summary.
        """
        result = self.run(
            student=student,
            transactions=transactions,
            vision_output=vision_output,
            budget=budget,
            goals=goals,
            lookback_days=30,
        )

        return {
            "success": result.success,
            "pipeline_status": result.pipeline_status,
            "overall_health": result.overall_health,
            "budget_health": result.budget_health,
            "budget_percent_used": result.budget_percent_used,
            "alert_summary": {
                "total": result.alert_total,
                "critical": result.alert_critical,
                "warning": result.alert_warning,
            },
            "top_priorities": result.top_priorities[:2],
            "has_errors": len(result.errors) > 0,
            "warnings": result.warnings[:3],
        }
    
    def run_safe(
        self,
        *,
        student: Student,
        transactions: Optional[List[Transaction]] = None,
        vision_output: Optional[Dict[str, Any]] = None,
        budget: Optional[Budget] = None,
        goals: Optional[List[Goal]] = None,
        lookback_days: int = 90,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Exception-safe wrapper.
        Always returns a dict and never lets unexpected exceptions escape.
        """
        try:
            result = self.run(
                student=student,
                transactions=transactions,
                vision_output=vision_output,
                budget=budget,
                goals=goals,
                lookback_days=lookback_days,
                timeout_seconds=timeout_seconds,
            )
            return result.to_dict()

        except Exception as e:
            traceback.print_exc()
            return error_result(
                error_message=f"Unexpected runner error: {str(e)}",
                student_id=getattr(student, "student_id", None),
            )
        
    def _run_with_timeout(
        self,
        state: FinancialGraphState,
        timeout_seconds: int,
    ) -> Dict[str, Any]:
        """
        Run the graph with a timeout wrapper to prevent hanging.
        """
        result_queue: queue.Queue = queue.Queue()

        def run_graph():
            try:
                result = self.builder.run(state)
                result_queue.put(("success", result))
            except Exception as e:
                result_queue.put(("error", str(e)))

        thread = threading.Thread(target=run_graph, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            return {
                **state,
                "pipeline_status": "failed",
                "errors": list(state.get("errors", [])) + [
                    f"Graph execution timed out after {timeout_seconds} seconds"
                ],
            }

        try:
            status, payload = result_queue.get_nowait()
            if status == "success":
                return payload

            return {
                **state,
                "pipeline_status": "failed",
                "errors": list(state.get("errors", [])) + [payload],
            }

        except queue.Empty:
            return {
                **state,
                "pipeline_status": "failed",
                "errors": list(state.get("errors", [])) + [
                    "Unknown error during graph execution"
                ],
            }
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Return lightweight runner statistics.
        """
        return {
            "call_count": self.call_count,
            "builder_initialized": self.builder is not None,
        }
    
def create_financial_runner() -> FinancialRunner:
    """
    Create and return a FinancialRunner instance.
    """
    return FinancialRunner()


if __name__ == "__main__":
    print("=" * 70)
    print("🏃 FINANCIAL RUNNER EXAMPLE")
    print("=" * 70)

    print(
        """
Example usage:

from runners.financial_runner import create_financial_runner

runner = create_financial_runner()

# 1) Run from existing transactions
result = runner.run_from_transactions(
    student=student,
    transactions=transactions,
    budget=budget,
    goals=goals,
)

# 2) Run from vision extraction output
result = runner.run_from_vision(
    student=student,
    vision_output=vision_output,
    budget=budget,
    goals=goals,
)

# 3) Add one new manual transaction and rerun
result = runner.add_transaction_and_rerun(
    student=student,
    existing_transactions=transactions,
    new_transaction=manual_txn,
    budget=budget,
    goals=goals,
)
"""
    )