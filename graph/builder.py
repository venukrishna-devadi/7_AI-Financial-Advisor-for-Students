"""
Graph Builder - Orchastrates the financial advisor pipeline with Langgraph

We need one place that decides - 
1. What runs
2. In what order
3. What shared state gets passed around

This builder creates a clean LangGraph workflow for the MVP

Current pipeline - 
1. intake / extraction
2. analyzer
3. planner
4. tracker
5. advisor
6. alert
7. finalize

Design Goals - 
1. Simple and readable orchestration
2. keep business logic out of UI
3. keep runner thin
4. support either - prebuilt transaction objects, vision_llm_wrapper output
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import START, END, StateGraph
from schemas.student import Student
from schemas.transaction import Transaction, TransactionType
from schemas.budget import Budget
from schemas.goal import Goal

from agents.analyzer import create_analyzer
from agents.planner import create_planner
from agents.tracker import create_tracker
from agents.advisor import create_advisor
from agents.alert import create_alert_agent

from utils.vision_transaction_bridge import vision_result_to_transactions

class FinancialGraphState(TypedDict, total = False):
    """
    Shared state object that moves across the path.
    Each node reads what it needs and write back only its output
    """

    student: Student
    transactions: List[Transaction]
    budget: Optional[Budget]
    goals: List[Goal]

    vision_output: Dict[str, Any]

    extraction_result: Dict[str, Any]
    analysis: Dict[str, Any]
    plan: Dict[str, Any]
    tracking_report: Dict[str, Any]
    advice_result: Dict[str, Any]
    alert_result: Dict[str, Any]

    lookback_days: int
    pipeline_status: str
    warnings: List[str]
    errors: List[str]

# =========================================================
# GRAPH BUILDER
# =========================================================

class FinancialGraphBuilder:
    """Builds and runs the Langgraph workflow for the financial advisor app"""

    def __init__(self):
        self.analyzer = create_analyzer()
        self.planner = create_planner()
        self.tracker = create_tracker()
        self.alert_agent = create_alert_agent()
        self.advisor = create_advisor()

    def _append_warning(self, state: FinancialGraphState, message: str)-> List[str]:
        """
        return a new warning list with one extra warning append
        """
        warnings = list(state.get("warnings", []))
        warnings.append(message)
        return warnings
    
    def _append_error(self, state: FinancialGraphState, message: str) -> List[str]:
        """
        return a new erros list with one extra error aooended
        """
        errors = list(state.get("errors"))
        errors.append(errors)
        return errors
    
    def _validate_state(self, state: FinancialGraphState) -> List[str]:
        """
        Validate input state before the graph runs
        """
        errors: List[str] = []

        if state.get("student") is None:
            errors.append("Missing required field: student")
        
        if "transactions" in state and state.get("transactions") is not None:
            if not isinstance(state["transactions"], list):
                errors.append("transactions must be a list")
        
        if "goals" in state and state.get("goals") is not None:
            if not isinstance(state["goals"], list):
                errors.append("goals must be a list")
        
        if "vision_output" in state and state.get("vision_output") is not None:
            if not isinstance(state["vision_output"], dict):
                errors.append("vision_output must be a dictionary")
        
        if "lookback_days" in state and state.get("lookback_days") is not None:
            value = state["lookback_days"]
            if not isinstance(value, int) or value <= 0:
                errors.append("lookback days must be a positive integer")
        
        return errors
    
    def _route_after_intake(self, state: FinancialGraphState)-> str:
        """
        Decide where to go after intake

        Rules - 
        1. if inatke marked pipeline as failed -> finalize
        2. if there are no transactions -> finalize
        3. otherwise -> analyzer
        """

        if state.get("pipeline_status") == "failed":
            return "finalize"
        
        if not state.get("transactions"):
            return "finalize"
        
        return "analyzer"
    
    def intake_node(self, state: FinancialGraphState) -> Dict[str, Any]:
        """
        Normalize the incoming date into the graph

        Supported modes:
        1. caller already gives Transaction objects
        2. caller gives vision_output which will be bridged into Transactions
        3. neither exists, so continue with empty transaction history
        """

        updates: Dict[str, Any] = {}

        student = state.get("student")
        transactions= state.get("transactions", [])
        vision_output = state.get("vision_output", {})

        if student is None:
            updates["errors"] = self._append_error(state, "Missing required input: student")
            updates["pipeline_status"] = "failed"
            return updates
        
        # case 1. transaction already exists
        if transactions:
            updates["transactions"] = transactions
            updates["extraction_result"] = {
                "mode": "prebuilt_transactions",
                "transaction_count": len(transactions),
                "skipped_items": [],
                "errors": []
            }
            return updates
        # case 2. bridge vision output intp Transaction objects
        if vision_output:
            bridge_results = vision_result_to_transactions(vision_output=vision_output,
                                                           student_id=student.student_id)
            
            updates["transactions"] = bridge_results.transactions
            #updates["extraction_result"] = bridge_results.to_dict()
            updates["extraction_result"] = {"mode": "vision/bridge",**bridge_results.to_dict()}

            warnings = list(state.get("warnings", []))
            errors = list(state.get("errors", []))

            if bridge_results.skipped_items:
                warnings.append(f"Skipped {len(bridge_results.skipped_items)} extracted itens during vision to transaction conversion.")
            
            if bridge_results.errors:
                errors.extend(bridge_results.errors)
            
            if warnings:
                updates["warnings"] = warnings
            
            if errors:
                updates["errors"] = errors
            
            return updates
        
        
        # case 3. nothing provided
        updates["transactions"] = []
        updates["warnings"] = self._append_warning(
            state,
            "No transactions or vision output provided. Continuning with empty transaction history"
        )
        updates["extraction_result"] = {
            "mode": "empty_input",
            "transaction_count": 0,
            "skipped_items": [],
            "errors": []
        }

        return updates
    
    def analyzer_node(self,
                      state: FinancialGraphState) -> Dict[str, Any]:
        """
        Analyze the student's transactions history to identify
        - spending patterns
        - trends
        - anomalies
        - budget insights
        """
        student = state.get("student")
        transactions = state.get("transactions", [])
        budget = state.get("budget")
        lookback_days = state.get("lookback_days", 90)

        if student is None:
            return {
                "errors": self._append_error(
                    state,
                    "Analyzer node could not run because student is missing"
                )
            }
        
        try:
            analysis = self.analyzer.analyze_student(
                student=student,
                transactions=transactions,
                budget=budget,
                lookback_days=lookback_days
            )
            return {"analysis": analysis}
        except Exception as e:
            return {
                "errors": self._append_error(state, f"Analyzer failed: {e}")
            }
        
    def planner_node(self,
                     state: FinancialGraphState)-> Dict[str, Any]:
        """
        Build a financial plan using student profile, transactions and analysis.

        Planner may produce
        -baseline estimates
        -savings plan
        -suggested budget
        -goal suggestions
        -action plan
        """

        student = state.get("student")
        transactions = state.get("transactions", [])
        analysis = state.get("analysis", {})
        goals= state.get("goals", [])

        if student is None:
            return {
                "errors": self._append_error(
                    state,
                    "Analyzer node could not run because student is missing"
                )
            }
        
        try:
            plan = self.planner.build_plan(
                student=student,
                transactions=transactions,
                analysis=analysis,
                goals=goals,
                )
            return {"plan":plan}
        except Exception as e:
            return {
                "errors": self._append_error(state, f"Planner failed: {e}")
            }
        
    
    def tracker_node(self, state: FinancialGraphState) -> Dict[str, Any]:
        """
        Compare actual spending against budget and goals.

        Tracker should still be allowed to run even when budget is missing,
        because the tracker can still provide partial status and goal monitoring.
        """

        student = state.get("student")
        transactions = state.get("transactions", [])
        budget = state.get("budget")
        goals = state.get("goals", [])

        if student is None:
            return {
                "errors": self._append_error(
                    state,
                    "Tracker node could not run because student is missing."
                )
            }

        try:
            tracking_report = self.tracker.track_student(
                student=student,
                transactions=transactions,
                budget=budget,
                goals=goals,
            )
            return {"tracking_report": tracking_report}
        except Exception as e:
            return {
                "errors": self._append_error(state, f"Tracker failed: {e}")
            }
        
    
    def advisor_node(self, state: FinancialGraphState) -> Dict[str, Any]:
        """
        Generate student-friendly financial advice using:
        - analyzer output
        - planner output
        - tracker output
        """
        student = state.get("student")
        analysis = state.get("analysis", {})
        plan = state.get("plan", {})
        tracking_report = state.get("tracking_report", {})
        goals = state.get("goals", [])

        if student is None:
            return {
                "errors": self._append_error(
                    state,
                    "Advisor node could not run because student is missing."
                )
            }

        try:
            advice_result = self.advisor.advice_student(
                student=student,
                analysis=analysis,
                plan=plan,
                tracking_report=tracking_report,
                goals=goals,
            )
            return {"advice_result": advice_result}
        except Exception as e:
            return {
                "errors": self._append_error(state, f"Advisor failed: {e}")
            }
        
    def alert_node(self, state: FinancialGraphState) -> Dict[str, Any]:
        """
        Generate alerts based on:
        - budget stress
        - spending pace
        - goal risk
        - patterns
        - savings stress
        """
        student = state.get("student")
        analysis = state.get("analysis", {})
        plan = state.get("plan", {})
        tracking_report = state.get("tracking_report", {})
        goals = state.get("goals", [])

        if student is None:
            return {
                "errors": self._append_error(
                    state,
                    "Alert node could not run because student is missing."
                )
            }

        try:
            alert_result = self.alert_agent.generate_alerts(
                student=student,
                analysis=analysis,
                plan=plan,
                tracking_report=tracking_report,
                goals=goals,
            )
            return {"alert_result": alert_result}
        except Exception as e:
            return {
                "errors": self._append_error(state, f"Alert generation failed: {e}")
            }
        
    def finalize_node(self, state: FinancialGraphState) -> Dict[str, Any]:
        """
        Final bookkeeping node.

        Sets a top-level pipeline status that UI and runner can use easily.
        """
        errors = state.get("errors", [])

        if state.get("pipeline_status") == "failed":
            return {"pipeline_status": "failed"}

        status = "completed_with_errors" if errors else "completed"
        return {"pipeline_status": status}
    

    def build_graph(self):
        """
        Create and compi;e the Lnaggraph workflow
        """

        graph = StateGraph(FinancialGraphState)

        graph.add_node("intake", self.intake_node)
        graph.add_node("analyzer", self.analyzer_node)
        graph.add_node("planner", self.planner_node)
        graph.add_node("tracker", self.tracker_node)
        graph.add_node("advisor", self.advisor_node)
        graph.add_node("alert", self.alert_node)
        graph.add_node("finalize", self.finalize_node)

        # entry point
        graph.set_entry_point("intake")

        graph.add_conditional_edges(
            "intake",
            self._route_after_intake,
            {
                "analyzer":"analyzer",
                "finalize":"finalize"
            }
        )

        graph.add_edge("analyzer", "planner")
        graph.add_edge("planner", "tracker")
        graph.add_edge("tracker", "advisor")
        graph.add_edge("advisor", "alert")
        graph.add_edge("alert", "finalize")
        graph.add_edge("finalize", END)

        return graph.compile()
    
    def run(self,
            initial_state: FinancialGraphState) -> FinancialGraphState:
        
        """Wrapper used so that callers do not have to seperately:
        1. build graph
        2. normalize defaults
        3. validate inputs
        4. invoke graph

        This will be the main entry point most callers should use
        """
        validation_errors = self._validate_state(initial_state)

        if validation_errors:
            return {
                **initial_state,
                "warnings": list(initial_state.get("warnings", [])),
                "errors": list(initial_state.get("errors", [])) + validation_errors,
                "pipeline_status": "failed"
            }
        app = self.build_graph()

        normalized_state: FinancialGraphState = {
            "lookback_days":90,
            "warnings":[],
            "errors" : [],
            "goals":[],
            **initial_state
        }

        return app.invoke(normalized_state)
    
def create_financial_graph_builder() -> FinancialGraphBuilder:
    """
    Create and return a graph builder instance.
    """
    return FinancialGraphBuilder()


def build_financial_graph():
    """
    Convenience function if caller only wants the compiled graph.
    """
    return FinancialGraphBuilder().build_graph()


# =========================================================
# EXAMPLE USAGE
# =========================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 FINANCIAL GRAPH BUILDER TEST")
    print("=" * 70)
    print("\nThis module is meant to be used by the runner/UI layer.")
    print("\nExample usage:\n")
    print(
        """
from graph.builder import create_financial_graph_builder

builder = create_financial_graph_builder()

result = builder.run({
    "student": student_obj,
    "transactions": txns,   # OR provide "vision_output" instead
    "budget": budget_obj,
    "goals": goal_list,
})
"""
    )




