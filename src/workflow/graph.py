"""
LangGraph Workflow Construction
Creates the refactoring workflow graph with self-healing loop.
"""

from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import audit_node, fix_node, test_node, error_node
from .conditions import should_retry_fix


def create_refactoring_graph():
    """
    Create the refactoring workflow graph.
    
    Workflow structure:
    
        START
          ↓
        AUDIT (analyze code, create plan)
          ↓
        FIX (apply fixes)
          ↓
        TEST (run tests, validate)
          ↓
        Decision point:
          - If tests pass → END
          - If tests fail & iterations left → FIX (retry with error logs)
          - If max iterations reached → ERROR → END
    """
    
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("audit", audit_node)
    workflow.add_node("fix", fix_node)
    workflow.add_node("test", test_node)
    workflow.add_node("error", error_node)
    
    workflow.set_entry_point("audit")
    
    # Add unconditional edges 
    workflow.add_edge("audit", "fix")  
    workflow.add_edge("fix", "test")  
    
    # Add CONDITIONAL edge from test
    workflow.add_conditional_edges(
        "test",                    # From the test node
        should_retry_fix,          # Use this function to decide
        {
            "fix": "fix",          # If should retry → go back to fix
            "done": END,           # If tests passed → end workflow
            "error": "error"       # If max iterations → error node
        }
    )
    
    workflow.add_edge("error", END)
    
    print("Compiling LangGraph workflow...")
    compiled = workflow.compile()
    print("Workflow compiled successfully")
    
    return compiled