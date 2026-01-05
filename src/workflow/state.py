# src/workflow/state.py
from typing import TypedDict, List, Dict, Any, Optional, Literal

class WorkflowState(TypedDict):
    # === INPUT ===
    target_dir: str
    current_file: str
    file_content: str
    
    # === PROGRESS ===
    current_phase: Literal["audit", "fix", "test", "done", "error"]
    iteration: int
    max_iterations: int
    
    # === CORE OUTPUTS ===
    audit_report: Optional[Dict[str, Any]]
    fix_result: Optional[Dict[str, Any]]
    test_result: Optional[Dict[str, Any]]
    
    # === FLEXIBLE STORAGE ===
    agent_outputs: Dict[str, Any]
    
    # === RESULTS ===
    processed_files: List[str]
    success_files: List[str]
    failed_files: List[str]
    errors: List[str]