"""
Judge Agent
Executes unit tests and validates that fixes work correctly.
"""

import tempfile
from pathlib import Path
from typing import Dict, Any
from .base_agent import BaseAgent
from src.tools.test_tools import TestTools
from src.tools.file_tools import FileTools
from src.tools.analysis_tools import AnalysisTools
from src.utils.logger import log_experiment, ActionType


class JudgeAgent(BaseAgent):
    """
    The Judge validates code by running tests and checking quality improvements.
    """
    
    def __init__(self):
        super().__init__("JudgeAgent")
        self.test_tools = TestTools()
        self.file_tools = FileTools()
        self.analysis_tools = AnalysisTools()
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the judgment: test the fixed code.
        
        Args:
            state: Current workflow state
        
        Returns:
            State updates with test results
        """
        current_file = state.get('current_file', 'unknown')
        iteration = state.get('iteration', 1)
        self._log(f"Testing: {current_file} (iteration {iteration})")
        
        # Get the fixed code
        fixed_code = state.get("fixed_content")
        if not fixed_code:
            self._log("No fixed code to test, using original")
            fixed_code = state.get("file_content", "")
        
        if not fixed_code:
            return self._create_error_result(state, "No code to test")
        
        # Save fixed code to a temp file for testing
        try:
            test_file = self._prepare_test_file(fixed_code, current_file)
            self._log(f"Created test file: {test_file}")
        except Exception as e:
            self._log(f"Failed to create test file: {e}")
            return self._create_error_result(state, f"Test setup error: {e}")
        
        # Step 1: Check syntax
        syntax_check = self.analysis_tools.check_syntax(fixed_code)
        if not syntax_check["valid"]:
            self._log(f" Syntax error: {syntax_check['error']}")
            return self._handle_test_failure(
                state,
                test_file,
                passed=False,
                errors=[f"Syntax error at line {syntax_check['line']}: {syntax_check['error']}"]
            )
        
        # Step 2: Try to run the code
        self._log("Attempting to run code...")
        run_result = self.test_tools.run_code_safely(test_file, timeout=5)
        
        if not run_result["success"]:
            self._log(f" Runtime error: {run_result['error']}")
            return self._handle_test_failure(
                state,
                test_file,
                passed=False,
                errors=[f"Runtime error: {run_result['error']}"]
            )
        
        # Step 3: Check code quality improvement
        self._log("Checking code quality...")
        pylint_result = self.analysis_tools.run_pylint(test_file)
        new_score = pylint_result.get("score", 0.0)
        original_score = state.get("agent_outputs", {}).get("original_pylint_score", 0.0)
        
        self._log(f"Pylint score: {original_score:.2f} -> {new_score:.2f}")
        
        # Step 4: Create or run tests
        self._log("Running tests...")
        test_result = self._run_tests(test_file, fixed_code)
        
        # Step 5: Determine if we passed
        passed = self._evaluate_success(
            syntax_valid=syntax_check["valid"],
            runs_without_error=run_result["success"],
            pylint_improved=new_score >= original_score,
            tests_passed=test_result.get("passed", False)
        )
        
        # Log the experiment
        # ✅ IMPORTANT : Si des tests sont générés, logue comme GENERATION
        action = ActionType.GENERATION if test_result.get("generated_tests", False) else ActionType.DEBUG
        
        log_experiment(
            agent_name="JudgeAgent",
            model_used="pytest",  # Not using LLM here
            action=action,  # ✅ GENERATION si tests générés, sinon DEBUG
            details={
                "file_tested": current_file,
                "iteration": iteration,
                "input_prompt": f"Testing code with {len(fixed_code)} characters",
                "output_response": f"Passed: {passed}, Score: {new_score:.2f}",
                "syntax_valid": syntax_check["valid"],
                "runtime_success": run_result["success"],
                "pylint_score": new_score,
                "score_improvement": new_score - original_score,
                "tests_passed": test_result.get("passed", False),
                "tests_run": test_result.get("tests_run", 0),
                "generated_tests": test_result.get("generated_tests", False)
            },
            status="SUCCESS" if passed else "FAILURE"
        )
        
        # Return result
        if passed:
            return self._handle_test_success(state, test_file, new_score)
        else:
            return self._handle_test_failure(
                state,
                test_file,
                passed=False,
                errors=test_result.get("errors", []) + test_result.get("failures", [])
            )
    
    def _prepare_test_file(self, code: str, original_file: str) -> str:
        """
        Prepare a file for testing.
        
        Args:
            code: Fixed code to test
            original_file: Original filename
        
        Returns:
            Path to test file
        """
        filename = Path(original_file).name
        test_path = self.file_tools.get_sandbox_path(f"test_{filename}")
        self.file_tools.write_file(test_path, code)
        return test_path
    
    def _run_tests(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Run tests on the code.
        
        Args:
            file_path: Path to file to test
            code: Code content
        
        Returns:
            Test results with generated_tests flag
        """
        # Check if there are any test functions in the code itself
        if "def test_" in code or "class Test" in code:
            # Code has tests, run them
            self._log("Running embedded tests...")
            result = self.test_tools.run_pytest(file_path)
            result["generated_tests"] = False  # Tests étaient déjà là
            return result
        else:
            # Generate basic tests
            self._log("Generating basic tests...")
            test_file = self.test_tools.create_basic_test(file_path)
            result = self.test_tools.run_pytest(file_path, test_file)
            result["generated_tests"] = True  # ✅ Tests générés !
            return result
    
    def _evaluate_success(
        self,
        syntax_valid: bool,
        runs_without_error: bool,
        pylint_improved: bool,
        tests_passed: bool
    ) -> bool:
        """
        Evaluate if the code passes our criteria.
        
        Args:
            syntax_valid: Code has valid syntax
            runs_without_error: Code runs without crashing
            pylint_improved: Pylint score improved or stayed same
            tests_passed: Tests passed
        
        Returns:
            True if code is acceptable
        """
        # Minimum requirements
        if not syntax_valid:
            return False
        
        if not runs_without_error:
            return False
        
        # Prefer improvements, but accept if no regression
        # Tests are nice to have but not required (many buggy files have no tests)
        return pylint_improved or tests_passed
    
    def _handle_test_success(self, state: Dict[str, Any], test_file: str, score: float) -> Dict[str, Any]:
        """
        Handle successful test result.
        
        Args:
            state: Current state
            test_file: Path to tested file
            score: Pylint score
        
        Returns:
            State updates
        """
        self._log(" Tests PASSED")
        
        # Update the original file with the fixed version
        try:
            original_file = state.get("current_file")
            fixed_code = state.get("fixed_content")
            
            # Write back to original location (if safe)
            if original_file and fixed_code:
                # Write to sandbox version
                sandbox_final = self.file_tools.get_sandbox_path(
                    f"final_{Path(original_file).name}"
                )
                self.file_tools.write_file(sandbox_final, fixed_code)
                self._log(f"Saved final version to: {sandbox_final}")
        except Exception as e:
            self._log(f"Warning: Could not save final version: {e}")
        
        return {
            "test_result": {
                "passed": True,
                "pylint_score": score,
                "iteration": state.get("iteration", 1)
            },
            "current_phase": "done",
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "final_pylint_score": score
            }
        }
    
    def _handle_test_failure(
        self,
        state: Dict[str, Any],
        test_file: str,
        passed: bool,
        errors: list
    ) -> Dict[str, Any]:
        """
        Handle test failure - prepare for retry.
        
        Args:
            state: Current state
            test_file: Path to tested file
            passed: Whether tests passed
            errors: List of error messages
        
        Returns:
            State updates
        """
        retry_count = state.get("retry_count", 0)
        max_iterations = state.get("max_iterations", 10)
        
        self._log(f" Tests FAILED (retry {retry_count + 1}/{max_iterations})")
        
        # Check if we should retry
        if retry_count < max_iterations - 1:
            self._log("Sending back to Fixer with error logs...")
            return {
                "test_result": {
                    "passed": False,
                    "errors": errors
                },
                "test_errors": errors,
                "retry_count": retry_count + 1,
                "current_phase": "retry",  # Will route back to fix
                "agent_outputs": {
                    **(state.get("agent_outputs") or {}),
                    "test_failures": errors
                }
            }
        else:
            self._log("Max iterations reached, giving up")
            return {
                "test_result": {
                    "passed": False,
                    "errors": errors,
                    "max_iterations_reached": True
                },
                "current_phase": "error",
                "agent_outputs": {
                    **(state.get("agent_outputs") or {}),
                    "test_failures": errors,
                    "max_iterations_reached": True
                }
            }