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
          - If tests pass → END (done!)
          - If tests fail & iterations left → FIX (retry with error logs)
          - If max iterations reached → ERROR → END
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # Create the graph with our state schema
    workflow = StateGraph(WorkflowState)
    
    # Add nodes (stations in our assembly line)
    workflow.add_node("audit", audit_node)
    workflow.add_node("fix", fix_node)
    workflow.add_node("test", test_node)
    workflow.add_node("error", error_node)
    
    # Set entry point
    workflow.set_entry_point("audit")
    
    # Add unconditional edges (always follow this path)
    workflow.add_edge("audit", "fix")  # Audit → Fix
    workflow.add_edge("fix", "test")   # Fix → Test
    
    # Add CONDITIONAL edge from test (this creates the self-healing loop!)
    # After testing, decide where to go based on test results
    workflow.add_conditional_edges(
        "test",                    # From the test node
        should_retry_fix,          # Use this function to decide
        {
            "fix": "fix",          # If should retry → go back to fix
            "done": END,           # If tests passed → end workflow
            "error": "error"       # If max iterations → error node
        }
    )
    
    # Error node always ends
    workflow.add_edge("error", END)
    
    # Compile the graph
    print("Compiling LangGraph workflow...")
    compiled = workflow.compile()
    print("Workflow compiled successfully")
    
    return compiled


def visualize_graph():
    """
    Generate a visualization of the workflow graph.
    Requires graphviz and IPython (optional).
    
    Returns:
        Graph visualization (if available)
    """
    try:
        graph = create_refactoring_graph()
        
        # Try to generate visualization
        try:
            from IPython.display import Image, display  # type: ignore
            display(Image(graph.get_graph().draw_mermaid_png()))
        except ImportError:
            print("Visualization requires graphviz and IPython (optional)")
            print("\nWorkflow structure:")
            print("  START → audit → fix → test")
            print("                        ↓")
            print("                  [conditional]")
            print("                  ↓     ↓    ↓")
            print("                fix  done error → END")
    except Exception as e:
        print(f"Could not visualize graph: {e}")