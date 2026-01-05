import os
from typing import Dict, List
from src.utils.logger import log_experiment, ActionType
from .graph import create_refactoring_graph
from src.workflow.state import WorkflowState

class RefactoringOrchestrator:
    def __init__(self):
        self.graph = create_refactoring_graph()
        print("LangGraph workflow created")
    
    def execute(self, target_dir: str) -> Dict:
        """Process all Python files in target directory"""
        print(f"Processing: {target_dir}")
        
        # Get all Python files
        python_files = self._get_python_files(target_dir)
        if not python_files:
            return {"success": False, "error": "No Python files found"}
        
        print(f"Found {len(python_files)} file(s)")
        
        # Process each file
        results = []
        for file_path in python_files:
            result = self._process_file(file_path)
            results.append(result)
        
        # Generate report
        success_count = len([r for r in results if r["success"]])
        
        return {
            "success": len(results) > 0,
            "files_processed": len(results),
            "files_successful": success_count,
            "details": results
        }
    
    def _get_python_files(self, directory: str) -> List[str]:
        """Find all Python files recursively"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _process_file(self, file_path: str) -> Dict:
        """Process a single file through the workflow"""
        print(f"\n📄 Processing: {os.path.basename(file_path)}")
        
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prepare initial state (whiteboard)
            initial_state = {
                "target_dir": os.path.dirname(file_path),
                "current_file": file_path,
                "file_content": content,
                "current_phase": "audit",
                "iteration": 1,
                "max_iterations": 10,
                "agent_outputs": {}, 
                "processed_files": [],
                "success_files": [],
                "failed_files": [],
                "errors": []
            }
            
            # Run through the workflow
            final_state = self.graph.invoke(initial_state)

            # DEBUG: Add these 3 lines
            print(f"  🔍 Final phase: {final_state.get('current_phase', 'unknown')}")
            print(f"  🔍 Success files list: {final_state.get('success_files', [])}")
            print(f"  🔍 Is file in success_files? {file_path in final_state.get('success_files', [])}")
            
            # Check result
            success = final_state.get("current_phase") == "done"
            
            return {
                "file": file_path,
                "success": success,
                "final_phase": final_state.get("current_phase", "unknown")
            }
            
        except Exception as e:
            print(f"Error: {e}")
            return {
                "file": file_path,
                "success": False,
                "error": str(e)
            }