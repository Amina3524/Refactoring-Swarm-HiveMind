"""
Analysis Tools - Code Quality Analysis
Provides pylint integration and code analysis utilities.
"""

import subprocess
import json
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional


class AnalysisTools:
    """
    Tools for analyzing Python code quality.
    """
    
    def __init__(self):
        """Initialize analysis tools."""
        print("🔍 Analysis tools initialized")
    
    def run_pylint(self, file_path: str) -> Dict[str, Any]:
        """
        Run pylint on a Python file.
        
        Args:
            file_path: Path to Python file
        
        Returns:
            Dictionary with pylint results:
            {
                "score": float,
                "issues": List[Dict],
                "raw_output": str
            }
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                "score": 0.0,
                "issues": [],
                "error": f"File not found: {file_path}",
                "raw_output": ""
            }
        
        try:
            # Run pylint with JSON output
            result = subprocess.run(
                ["pylint", str(path), "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse JSON output
            try:
                issues = json.loads(result.stdout) if result.stdout else []
            except json.JSONDecodeError:
                issues = []
            
            # Extract score from stderr (pylint prints score there)
            score = self._extract_score(result.stderr)
            
            print(f"📊 Pylint score: {score:.2f}/10")
            
            return {
                "score": score,
                "issues": issues,
                "issue_count": len(issues),
                "raw_output": result.stderr
            }
        
        except subprocess.TimeoutExpired:
            return {
                "score": 0.0,
                "issues": [],
                "error": "Pylint timeout",
                "raw_output": ""
            }
        except Exception as e:
            return {
                "score": 0.0,
                "issues": [],
                "error": str(e),
                "raw_output": ""
            }
    
    def _extract_score(self, pylint_output: str) -> float:
        """
        Extract the pylint score from output.
        
        Args:
            pylint_output: Pylint stderr output
        
        Returns:
            Score as float (0.0 to 10.0)
        """
        try:
            # Look for "Your code has been rated at X.XX/10"
            for line in pylint_output.split('\n'):
                if 'rated at' in line:
                    # Extract number
                    parts = line.split('rated at')[1].split('/')[0]
                    score = float(parts.strip())
                    return score
        except:
            pass
        
        return 0.0
    
    def check_syntax(self, code: str) -> Dict[str, Any]:
        """
        Check if Python code has valid syntax using AST.
        
        Args:
            code: Python code as string
        
        Returns:
            {
                "valid": bool,
                "error": Optional[str],
                "line": Optional[int]
            }
        """
        try:
            ast.parse(code)
            return {
                "valid": True,
                "error": None,
                "line": None
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "line": None
            }
    
    def count_functions(self, code: str) -> int:
        """
        Count the number of functions defined in code.
        
        Args:
            code: Python code as string
        
        Returns:
            Number of functions
        """
        try:
            tree = ast.parse(code)
            return len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        except:
            return 0
    
    def count_classes(self, code: str) -> int:
        """
        Count the number of classes defined in code.
        
        Args:
            code: Python code as string
        
        Returns:
            Number of classes
        """
        try:
            tree = ast.parse(code)
            return len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        except:
            return 0
    
    def get_complexity_estimate(self, code: str) -> str:
        """
        Estimate code complexity.
        
        Args:
            code: Python code as string
        
        Returns:
            "low", "medium", or "high"
        """
        lines = len(code.split('\n'))
        functions = self.count_functions(code)
        classes = self.count_classes(code)
        
        score = lines / 10 + functions * 2 + classes * 5
        
        if score < 20:
            return "low"
        elif score < 50:
            return "medium"
        else:
            return "high"
    
    def extract_docstrings(self, code: str) -> Dict[str, List[str]]:
        """
        Extract docstrings from code.
        
        Args:
            code: Python code as string
        
        Returns:
            Dictionary with module, class, and function docstrings
        """
        result = {
            "module": None,
            "classes": [],
            "functions": []
        }
        
        try:
            tree = ast.parse(code)
            
            # Module docstring
            if (ast.get_docstring(tree)):
                result["module"] = ast.get_docstring(tree)
            
            # Class and function docstrings
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node)
                    if doc:
                        result["classes"].append({
                            "name": node.name,
                            "docstring": doc
                        })
                
                elif isinstance(node, ast.FunctionDef):
                    doc = ast.get_docstring(node)
                    if doc:
                        result["functions"].append({
                            "name": node.name,
                            "docstring": doc
                        })
        except:
            pass
        
        return result