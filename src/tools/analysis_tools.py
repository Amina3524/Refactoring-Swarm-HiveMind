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
        Run pylint on a Python file with enhanced scoring.
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
            
            # **AMÉLIORATION : Calculer notre propre score**
            score = self._calculate_enhanced_score(issues, result.stderr)
            
            print(f"📊 Pylint score: {score:.2f}/10 ({len(issues)} issues)")
            
            # Afficher les types d'issues pour debug
            if issues:
                types = {}
                for issue in issues:
                    t = issue.get('type', 'unknown')
                    types[t] = types.get(t, 0) + 1
                print(f"   Issues by type: {types}")
            
            return {
                "score": score,
                "issues": issues,
                "issue_count": len(issues),
                "raw_output": result.stderr[:500] if result.stderr else ""
            }
        
        except Exception as e:
            return {
                "score": 0.0,
                "issues": [],
                "error": str(e),
                "raw_output": ""
            }
    
    def _calculate_enhanced_score(self, issues: List[Dict], stderr: str) -> float:
        """
        Calculate a more useful quality score.
        
        Args:
            issues: List of pylint issues
            stderr: Pylint error output
        
        Returns:
            Score from 0.0 to 10.0
        """
        # 1. Essayer d'extraire le score original
        original_score = self._extract_score(stderr)
        
        # 2. Si on a un score > 0, l'utiliser
        if original_score > 0.0:
            return original_score
        
        # 3. Sinon, calculer notre propre score
        if not issues:
            return 8.0  # Code sans issues = bon
        
        # Compter les issues par sévérité
        error_count = 0
        warning_count = 0
        convention_count = 0
        
        for issue in issues:
            issue_type = issue.get('type', 'convention')
            if issue_type in ['error', 'fatal']:
                error_count += 1
            elif issue_type == 'warning':
                warning_count += 1
            else:
                convention_count += 1
        
        # Calcul du score (basé sur le nombre et sévérité des issues)
        # Formule : 10 - (erreurs * 0.5) - (warnings * 0.2) - (conventions * 0.05)
        calculated_score = 10.0
        calculated_score -= error_count * 0.5
        calculated_score -= warning_count * 0.2
        calculated_score -= convention_count * 0.05
        
        # S'assurer que le score est entre 0 et 10
        calculated_score = max(0.0, min(10.0, calculated_score))
        
        print(f"   Calculated score: errors={error_count}, warnings={warning_count}, conventions={convention_count}")
        
        return round(calculated_score, 2)
    
    def _extract_score(self, pylint_output: str) -> float:
        """
        Extract the pylint score from output.
        
        Args:
            pylint_output: Pylint stderr output
        
        Returns:
            Score as float (0.0 to 10.0)
        """
        if not pylint_output:
            return 0.0
        
        try:
            # Multiple possible score formats
            patterns = [
                r'rated at\s+([0-9.]+)/10',  # "rated at X.XX/10"
                r'Your code has been rated at\s+([0-9.]+)/10',
                r'Score:\s+([0-9.]+)/10',
                r'([0-9.]+)/10',  # Just find any X.XX/10 pattern
            ]
            
            for pattern in patterns:
                import re
                match = re.search(pattern, pylint_output)
                if match:
                    score = float(match.group(1))
                    # Ensure it's within valid range
                    if 0.0 <= score <= 10.0:
                        return score
            
            # If no pattern found, try to parse from issues
            if "issues found" in pylint_output.lower():
                # Try to extract from summary line
                lines = pylint_output.split('\n')
                for line in lines:
                    if "/10" in line:
                        parts = line.split()
                        for part in parts:
                            if "/10" in part:
                                try:
                                    score_str = part.split('/')[0]
                                    score = float(score_str)
                                    return max(0.0, min(10.0, score))
                                except:
                                    pass
        
        except Exception as e:
            print(f"⚠️  Error extracting pylint score: {e}")
        
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