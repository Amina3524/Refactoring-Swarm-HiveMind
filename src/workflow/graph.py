from langgraph.graph import StateGraph, END
from .state import WorkflowState
from .nodes import audit_node, fix_node, test_node

def create_refactoring_graph():
    """Create the factory conveyor belt"""
    
    # 1. Create the graph
    workflow = StateGraph(WorkflowState)
    
    # 2. Add the 3 stations
    workflow.add_node("audit", audit_node)
    workflow.add_node("fix", fix_node)
    workflow.add_node("test", test_node)
    
    # 3. Connect stations in order
    workflow.set_entry_point("audit")
    workflow.add_edge("audit", "fix")
    workflow.add_edge("fix", "test")
    workflow.add_edge("test", END)
    
    # 4. Compile and return
    return workflow.compile()