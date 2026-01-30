"""
Refactoring Orchestrator
Coordinates the processing of multiple files through the workflow.
"""

import os
from pathlib import Path
from typing import Dict, List
from .graph import create_refactoring_graph
from .state import WorkflowState


class RefactoringOrchestrator:
    """
    Main orchestrator that processes all Python files in a directory.
    """
    
    def __init__(self, max_iterations: int = 10):
        """
        Initialize the orchestrator.
        
        Args:
            max_iterations: Maximum fix-test iterations per file
        """
        self.max_iterations = max_iterations
        self.graph = create_refactoring_graph()
        print(f"Orchestrator initialized (max iterations: {max_iterations})")
    
    def execute(self, target_dir: str) -> Dict:
        """
        Process all Python files in the target directory.
        
        Args:
            target_dir: Directory containing Python files to refactor
        
        Returns:
            Summary of results:
            {
                "success": bool,
                "files_processed": int,
                "files_successful": int,
                "files_failed": int,
                "details": List[Dict]
            }
        """
        print(f"\n{'='*60}")
        print(f"STARTING REFACTORING SWARM")
        print(f"{'='*60}")
        print(f"Target: {target_dir}")
        
        # Find all Python files
        python_files = self._get_python_files(target_dir)
        
        if not python_files:
            print("No Python files found")
            return {
                "success": False,
                "error": "No Python files found",
                "files_processed": 0,
                "files_successful": 0,
                "files_failed": 0,
                "details": []
            }
        
        print(f"Found {len(python_files)} Python file(s)")
        
        # Process each file
        results = []
        for i, file_path in enumerate(python_files, 1):
            print(f"\n{'='*60}")
            print(f"FILE {i}/{len(python_files)}: {Path(file_path).name}")
            print(f"{'='*60}")
            
            result = self._process_file(file_path)
            results.append(result)
            
            # Print file result
            if result["success"]:
                print(f"{Path(file_path).name} - SUCCESS")
            else:
                print(f"{Path(file_path).name} - FAILED")
        
        # Calculate summary
        success_count = len([r for r in results if r["success"]])
        fail_count = len(results) - success_count
        
        # Print final summary
        print(f"\n{'='*60}")
        print(f"FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Successful: {success_count}/{len(results)}")
        print(f"Failed: {fail_count}/{len(results)}")
        print(f"{'='*60}\n")
        
        return {
            "success": success_count > 0,
            "files_processed": len(results),
            "files_successful": success_count,
            "files_failed": fail_count,
            "details": results
        }
    
    def _get_python_files(self, directory: str) -> List[str]:
        """
        Find all Python files in directory (recursively).
        
        Args:
            directory: Directory to search
        
        Returns:
            List of Python file paths
        """
        python_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    python_files.append(full_path)
        
        return sorted(python_files)
    
    def _process_file(self, file_path: str) -> Dict:
        """
        Process a single file through the refactoring workflow.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            Result dictionary:
            {
                "file": str,
                "success": bool,
                "final_phase": str,
                "iterations": int,
                "error": Optional[str]
            }
        """
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"Read {len(content)} characters")
            
            # Create initial state
            initial_state: WorkflowState = {
                "target_dir": str(Path(file_path).parent),
                "current_file": file_path,
                "file_content": content,
                "current_phase": "audit",
                "iteration": 1,
                "max_iterations": self.max_iterations,
                "audit_report": None,
                "fix_result": None,
                "test_result": None,
                "fixed_content": None,
                "test_errors": [],
                "retry_count": 0,
                "agent_outputs": {},
                "processed_files": [],
                "success_files": [],
                "failed_files": [],
                "errors": []
            }
            
            # Run through the workflow
            print("Running workflow...")
            final_state = self.graph.invoke(initial_state)
            
            # Extract results
            final_phase = final_state.get("current_phase", "unknown")
            success = final_phase == "done"
            iterations = final_state.get("iteration", 1)
            
            # NE PAS LOGGER ICI - les agents le font déjà
            
            return {
                "file": file_path,
                "success": success,
                "final_phase": final_phase,
                "iterations": iterations
            }
        
        except Exception as e:
            print(f"Error processing file: {e}")
            
            # NE PAS LOGGER ICI - seulement les agents doivent logger
            
            return {
                "file": file_path,
                "success": False,
                "final_phase": "error",
                "iterations": 0,
                "error": str(e)
            }