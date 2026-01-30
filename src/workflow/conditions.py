"""
Workflow Conditions
Defines conditional routing logic for the LangGraph workflow.
"""

from typing import Literal
from .state import WorkflowState


def should_retry_fix(state: WorkflowState) -> Literal["fix", "done", "error"]:
    """
    Decide if we should retry fixing or end the workflow.
    
    This is called after the Judge agent runs tests.
    
    Args:
        state: Current workflow state
    
    Returns:
        "fix" - Go back to Fixer with error feedback
        "done" - Tests passed, we're done
        "error" - Max iterations reached, give up
    """
    current_phase = state.get("current_phase", "unknown")
    
    # Check current phase
    if current_phase == "done":
        print(" Phase: DONE - Tests passed!")
        return "done"
    
    elif current_phase == "error":
        print(" Phase: ERROR - Max iterations reached")
        return "error"
    
    elif current_phase == "retry":
        retry_count = state.get("retry_count", 0)
        max_iterations = state.get("max_iterations", 10)
        
        if retry_count < max_iterations:
            print(f" Phase: RETRY - Attempt {retry_count + 1}/{max_iterations}")
            return "fix"
        else:
            print(f" Phase: ERROR - Max retries exceeded")
            return "error"
    
    else:
        # Unknown phase, default to error
        print(f"  Unknown phase: {current_phase}, ending")
        return "error"


def increment_iteration(state: WorkflowState) -> WorkflowState:
    """
    Increment the iteration counter when retrying.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    state["iteration"] = state.get("iteration", 1) + 1
    return state