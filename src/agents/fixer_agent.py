"""
Fixer Agent
Reads the refactoring plan and modifies code to fix issues.
"""

import json
import re
from typing import Dict, Any, List
from .base_agent import BaseAgent
from src.llm.client import LLMClient
from src.tools.file_tools import FileTools
from src.tools.analysis_tools import AnalysisTools
from src.utils.logger import log_experiment, ActionType


class FixerAgent(BaseAgent):
    """
    The Fixer applies corrections to code based on the audit report.
    """
    
    def __init__(self):
        super().__init__("FixerAgent")
        self.llm_client = LLMClient()
        self.file_tools = FileTools()
        self.analysis_tools = AnalysisTools()
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the fixer prompt from file."""
        try:
            with open("src/prompts/fixer_prompt.txt", 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
            self._log("Prompt template loaded")
        except FileNotFoundError:
            self._log("Prompt template not found, using default")
            self.prompt_template = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default prompt template."""
        return """You are an Expert Python Code Refactoring Specialist.

TASK: Fix the issues identified in the audit report by modifying the code.

ORIGINAL CODE:
```python
{code}
```

AUDIT REPORT:
{audit_report}

{test_errors}

REFACTORING INSTRUCTIONS:
1. Fix ALL critical issues first (these are security/syntax/logic errors)
2. Fix major issues (error handling, performance)
3. Fix minor issues (style, documentation) where possible
4. **ADD DOCSTRINGS TO ALL FUNCTIONS AND CLASSES** - This is MANDATORY
   - Every function must have a docstring explaining what it does
   - Every class must have a docstring explaining its purpose
   - Use triple quotes (''' or \"\"\") for docstrings
5. Maintain the original functionality - DO NOT change what the code does
6. Ensure all syntax is valid Python
7. Follow PEP 8 style guidelines

CRITICAL REQUIREMENTS:
- Return ONLY the complete fixed Python code
- NO explanations, NO markdown code blocks, NO comments about changes
- The output must be valid, executable Python code
- Start directly with the code (no "Here's the fixed code:" preamble)
- MUST include docstrings with triple quotes (''' or \"\"\") for all functions and classes

IMPORTANT: Your response will be written directly to a .py file, so it must be pure Python code only."""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the fix: modify code based on audit report and test errors.
        
        Args:
            state: Current workflow state
        
        Returns:
            State updates with fixed code
        """
        current_file = state.get('current_file', 'unknown')
        iteration = state.get('iteration', 1)
        self._log(f"Fixing: {current_file} (iteration {iteration})")
        
        # Get inputs
        code = state.get("file_content", "")
        audit_report = state.get("audit_report")
        test_errors = state.get("test_errors", [])
        
        # If we have fixed content from a previous iteration, use that
        if state.get("fixed_content"):
            code = state["fixed_content"]
            self._log("Using previously fixed code as base")
        
        if not code:
            return self._create_error_result(state, "No code to fix")
        
        if not audit_report:
            self._log("No audit report found, attempting basic fixes")
            audit_report = {"summary": {"refactoring_priority": ["Add docstrings"]}}
        
        # Prepare the prompt
        prompt = self._prepare_fix_prompt(code, audit_report, test_errors)
        
        # Call LLM to fix the code
        self._log("Calling LLM to generate fixes...")
        try:
            llm_response = self.llm_client.call(prompt, temperature=0.1)
        except Exception as e:
            self._log(f"LLM call failed: {e}")
            return self._create_error_result(state, f"LLM error: {e}")
        
        # Extract and clean the fixed code
        fixed_code = self._extract_code(llm_response)
        
        # Validate syntax
        syntax_check = self.analysis_tools.check_syntax(fixed_code)
        if not syntax_check["valid"]:
            self._log(f"  Fixed code has syntax error: {syntax_check['error']}")
            # Try to fix syntax issues
            fixed_code = self._attempt_syntax_fix(fixed_code, syntax_check)
        
        # Save to sandbox
        try:
            sandbox_path = self.file_tools.get_sandbox_path(
                f"fixed_{iteration}_{state.get('current_file', 'code.py').split('/')[-1]}"
            )
            self.file_tools.write_file(sandbox_path, fixed_code)
            self._log(f"Saved fixed code to: {sandbox_path}")
        except Exception as e:
            self._log(f"Failed to save fixed code: {e}")
        
        log_experiment(
            agent_name="FixerAgent",
            model_used=self.llm_client.model_name,
            action=ActionType.FIX,
            details={
                "file_fixed": current_file,
                "iteration": iteration,
                "input_prompt": prompt[:1000] + "..." if len(prompt) > 1000 else prompt,
                "output_response": llm_response[:1000] + "..." if len(llm_response) > 1000 else llm_response,
                "issues_addressed": self._count_issues(audit_report),
                "test_errors_count": len(test_errors),
                "syntax_valid": syntax_check["valid"],
                "docstrings_added": self._count_docstrings(fixed_code) > self._count_docstrings(code)
            },
            status="SUCCESS" if syntax_check["valid"] else "FAILURE"
        )
        
        # Return state updates
        return {
            "fixed_content": fixed_code,
            "fix_result": {
                "iteration": iteration,
                "syntax_valid": syntax_check["valid"],
                "code_length": len(fixed_code)
            },
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "fix_result": {
                    "iteration": iteration,
                    "syntax_valid": syntax_check["valid"]
                }
            }
        }
    
    def _prepare_fix_prompt(self, code: str, audit_report: Dict, test_errors: List[str]) -> str:
        """Prepare the fix prompt with all context."""
        prompt = self.prompt_template
        
        # Insert code
        prompt = prompt.replace("{code}", code)
        
        # Insert audit report
        audit_json = json.dumps(audit_report, indent=2)
        prompt = prompt.replace("{audit_report}", audit_json)
        
        # Insert test errors if any
        if test_errors:
            error_text = "\nTEST FAILURES FROM PREVIOUS ATTEMPT:\n"
            for i, error in enumerate(test_errors, 1):
                error_text += f"\nError {i}:\n{error}\n"
            error_text += "\nYou MUST fix these test failures in the code.\n"
        else:
            error_text = ""
        
        prompt = prompt.replace("{test_errors}", error_text)
        
        return prompt
    
    def _extract_code(self, response: str) -> str:
        """
        Extract Python code from LLM response.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Extracted Python code
        """
        # Remove common preambles
        response = response.strip()
        
        # Remove markdown code blocks if present
        if "```python" in response:
            match = re.search(r'```python\s*\n(.*?)\n```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        elif "```" in response:
            match = re.search(r'```\s*\n(.*?)\n```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Remove common preambles
        lines = response.split('\n')
        start_idx = 0
        
        for i, line in enumerate(lines):
            lower = line.lower().strip()
            if any(phrase in lower for phrase in [
                "here's the fixed",
                "here is the fixed",
                "fixed code:",
                "corrected code:",
                "refactored code:"
            ]):
                start_idx = i + 1
                break
        
        code = '\n'.join(lines[start_idx:]).strip()
        
        return code
    
    def _attempt_syntax_fix(self, code: str, syntax_check: Dict) -> str:
        """
        Attempt to automatically fix simple syntax errors.
        
        Args:
            code: Code with syntax error
            syntax_check: Syntax check result
        
        Returns:
            Potentially fixed code
        """
        
        self._log("  Cannot auto-fix syntax error, returning as-is")
        return code
    
    def _count_issues(self, audit_report: Dict) -> int:
        """Count total issues in audit report."""
        return (
            len(audit_report.get("critical_issues", [])) +
            len(audit_report.get("major_issues", [])) +
            len(audit_report.get("minor_issues", []))
        )
    
    def _count_docstrings(self, code: str) -> int:
        """Count docstrings in code."""
        return code.count('"""') // 2 + code.count("'''") // 2