"""
Workflow State Definition
This defines the "shared whiteboard" that all agents read and write to.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class WorkflowState(TypedDict):
    """
    Complete state for the refactoring workflow.
    Think of this as a shared whiteboard that all agents can read/write to.
    """
    
    # === INPUT INFORMATION ===
    target_dir: str  # Original directory path
    current_file: str  # Path to file being processed
    file_content: str  # Original file content
    
    # === WORKFLOW CONTROL ===
    current_phase: Literal["audit", "fix", "test", "done", "error"]
    iteration: int  # Current iteration number
    max_iterations: int  # Maximum allowed iterations
    
    # === AGENT OUTPUTS ===
    audit_report: Optional[Dict[str, Any]]  # Auditor's analysis
    fix_result: Optional[Dict[str, Any]]  # Fixer's modifications
    test_result: Optional[Dict[str, Any]]  # Judge's test results
    
    # === MODIFIED CODE ===
    fixed_content: Optional[str]  # Latest version of the code
    
    # === ERROR TRACKING ===
    test_errors: List[str]  # Test failures for fixer to address
    retry_count: int  # Number of fix-test retry attempts
    
    # === FLEXIBLE STORAGE ===
    agent_outputs: Dict[str, Any]  # Additional agent data
    
    # === OVERALL RESULTS ===
    processed_files: List[str]  # Files that have been processed
    success_files: List[str]  # Files that passed all tests
    failed_files: List[str]  # Files that failed
    errors: List[str]  # Error messages