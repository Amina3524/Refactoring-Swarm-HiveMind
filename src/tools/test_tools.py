"""
Test Tools - Pytest Integration
Provides utilities for running tests on Python code.
"""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List, Optional


class TestTools:
    """
    Tools for running tests on Python code.
    """
    
    def __init__(self):
        """Initialize test tools."""
        print("🧪 Test tools initialized")
    
    def run_pytest(self, file_path: str, test_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run pytest on a file or with a separate test file.
        
        Args:
            file_path: Path to Python file to test
            test_file_path: Optional path to test file
        
        Returns:
            Dictionary with test results:
            {
                "passed": bool,
                "tests_run": int,
                "failures": List[str],
                "errors": List[str],
                "raw_output": str
            }
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                "passed": False,
                "tests_run": 0,
                "failures": ["File not found"],
                "errors": [f"File not found: {file_path}"],
                "raw_output": ""
            }
        
        try:
            # Determine what to test
            test_path = test_file_path if test_file_path else str(path)
            
            # Run pytest
            result = subprocess.run(
                ["pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=path.parent  # Run in the file's directory
            )
            
            # Parse output
            output = result.stdout + "\n" + result.stderr
            passed = result.returncode == 0
            
            # Count tests
            tests_run = output.count(" PASSED") + output.count(" FAILED")
            failures = self._extract_failures(output)
            errors = self._extract_errors(output)
            
            print(f"🧪 Tests: {tests_run} run, {len(failures)} failed")
            
            return {
                "passed": passed,
                "tests_run": tests_run,
                "failures": failures,
                "errors": errors,
                "raw_output": output
            }
        
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "tests_run": 0,
                "failures": ["Test timeout"],
                "errors": ["Tests took too long to execute (>30s)"],
                "raw_output": ""
            }
        except Exception as e:
            return {
                "passed": False,
                "tests_run": 0,
                "failures": [str(e)],
                "errors": [str(e)],
                "raw_output": ""
            }
    
    def _extract_failures(self, output: str) -> List[str]:
        """Extract failure messages from pytest output."""
        failures = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if 'FAILED' in line:
                # Get the next few lines for context
                context = '\n'.join(lines[i:min(i+5, len(lines))])
                failures.append(context)
        
        return failures
    
    def _extract_errors(self, output: str) -> List[str]:
        """Extract error messages from pytest output."""
        errors = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if 'ERROR' in line or 'Error' in line:
                # Get context
                context = '\n'.join(lines[max(0, i-1):min(i+3, len(lines))])
                errors.append(context)
        
        return errors
    
    def create_basic_test(self, code_path: str) -> str:
        """
        Generate a basic test file for given code.
        
        Args:
            code_path: Path to code file
        
        Returns:
            Path to generated test file
        """
        code_file = Path(code_path)
        test_file = code_file.parent / f"test_{code_file.stem}.py"
        
        # Simple test template
        test_content = f'''"""
Auto-generated tests for {code_file.name}
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the module
import {code_file.stem}


def test_import():
    """Test that the module can be imported."""
    assert {code_file.stem} is not None


def test_no_syntax_errors():
    """Test that there are no syntax errors."""
    # If we got here, syntax is OK
    assert True
'''
        
        # Write test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"📝 Generated basic test: {test_file.name}")
        
        return str(test_file)
    
    def run_code_safely(self, file_path: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Try to run a Python file and capture output/errors.
        
        Args:
            file_path: Path to Python file
            timeout: Maximum execution time in seconds
        
        Returns:
            {
                "success": bool,
                "output": str,
                "error": Optional[str]
            }
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                "success": False,
                "output": "",
                "error": f"File not found: {file_path}"
            }
        
        try:
            result = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "output": result.stdout,
                "error": result.stderr if not success else None
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Execution timeout (possible infinite loop)"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }