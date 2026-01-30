"""
Workflow Nodes
These are the "stations" in our refactoring assembly line.
Each node wraps an agent's execution.
"""

from typing import Dict, Any
from .state import WorkflowState
from src.agents.auditor_agent import AuditorAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.judge_agent import JudgeAgent


_auditor = None
_fixer = None
_judge = None


def _get_auditor() -> AuditorAgent:
    """Get or create the Auditor agent."""
    global _auditor
    if _auditor is None:
        _auditor = AuditorAgent()
    return _auditor


def _get_fixer() -> FixerAgent:
    """Get or create the Fixer agent."""
    global _fixer
    if _fixer is None:
        _fixer = FixerAgent()
    return _fixer


def _get_judge() -> JudgeAgent:
    """Get or create the Judge agent."""
    global _judge
    if _judge is None:
        _judge = JudgeAgent()
    return _judge


def audit_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 1: Audit the code.
    
    This station analyzes the code and creates a refactoring plan.
    
    Args:
        state: Current workflow state
    
    Returns:
        State updates from the Auditor agent
    """
    print("\n" + "="*60)
    print("[AUDIT] STATION 1: AUDIT")
    print("="*60)
    
    auditor = _get_auditor()
    updates = auditor.execute(state)
    
    updates["current_phase"] = "fix"
    
    return updates


def fix_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 2: Fix the code.
    
    This station applies fixes based on the audit report.
    
    Args:
        state: Current workflow state
    
    Returns:
        State updates from the Fixer agent
    """
    print("\n" + "="*60)
    print("[FIX] STATION 2: FIX")
    print("="*60)
    
    fixer = _get_fixer()
    updates = fixer.execute(state)
    
    # Move to test phase
    updates["current_phase"] = "test"
    
    return updates


def test_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 3: Test the code.
    
    This station validates the fixes by running tests.
    The Judge will set current_phase to:
    - "done" if tests pass
    - "retry" if tests fail and we should retry
    - "error" if max iterations reached
    
    Args:
        state: Current workflow state
    
    Returns:
        State updates from the Judge agent
    """
    print("\n" + "="*60)
    print("[TEST] STATION 3: TEST")
    print("="*60)
    
    judge = _get_judge()
    updates = judge.execute(state)
    
    # The Judge sets current_phase based on test results
    
    return updates


def error_node(state: WorkflowState) -> Dict[str, Any]:
    """
    Node 4: Error handler.
    
    This station is reached when max iterations are exceeded.
    
    Args:
        state: Current workflow state
    
    Returns:
        State updates marking failure
    """
    print("\n" + "="*60)
    print("[ERROR] Max iterations reached")
    print("="*60)
    
    return {
        "current_phase": "error",
        "agent_outputs": {
            **(state.get("agent_outputs") or {}),
            "final_status": "FAILED - Max iterations"
        }
    }