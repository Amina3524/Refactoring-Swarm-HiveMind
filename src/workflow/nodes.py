# src/workflow/nodes.py - UPDATED VERSION
from typing import Dict, Any
from src.workflow.state import WorkflowState
from src.agents.auditor_agent import AuditorAgent
from src.agents.fixer_agent import FixerAgent
from src.agents.judge_agent import JudgeAgent

# Initialize agents (singleton pattern)
_auditor = None
_fixer = None
_judge = None

def _get_auditor():
    global _auditor
    if _auditor is None:
        _auditor = AuditorAgent()
    return _auditor

def _get_fixer():
    global _fixer
    if _fixer is None:
        _fixer = FixerAgent()
    return _fixer

def _get_judge():
    global _judge
    if _judge is None:
        _judge = JudgeAgent()
    return _judge

def audit_node(state: WorkflowState) -> Dict[str, Any]:
    """Station 1: Analyze the code"""
    auditor = _get_auditor()
    result = auditor.execute(state)
    
    # Move to next station
    state["current_phase"] = "fix"
    return {**state, **result}

def fix_node(state: WorkflowState) -> Dict[str, Any]:
    """Station 2: Fix the code"""
    fixer = _get_fixer()
    result = fixer.execute(state)
    
    state["current_phase"] = "test"
    return {**state, **result}

def test_node(state: WorkflowState) -> Dict[str, Any]:
    """Station 3: Test the code"""
    judge = _get_judge()
    result = judge.execute(state)
    
    if result.get("test_result", {}).get("passed", False):
        state["current_phase"] = "done"
        state["success_files"].append(state["current_file"])
    else:
        # TODO: Handle retry logic
        state["current_phase"] = "error"
        state["failed_files"].append(state["current_file"])
    
    return {**state, **result}