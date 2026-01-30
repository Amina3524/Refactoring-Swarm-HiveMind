"""
Auditor Agent
Reads code, runs static analysis, and produces a refactoring plan.
"""

import json
import re
from typing import Dict, Any
from .base_agent import BaseAgent
from src.llm.client import LLMClient
from src.tools.analysis_tools import AnalysisTools
from src.utils.logger import log_experiment, ActionType


class AuditorAgent(BaseAgent):
    """
    The Auditor analyzes code and creates a structured refactoring plan.
    """
    
    def __init__(self):
        super().__init__("AuditorAgent")
        self.llm_client = LLMClient()
        self.analysis_tools = AnalysisTools()
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the auditor prompt from file."""
        try:
            with open("src/prompts/auditor_prompt.txt", 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
            self._log("Prompt template loaded")
        except FileNotFoundError:
            self._log("Prompt template not found, using default")
            self.prompt_template = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default prompt template."""
        return """You are a Senior Python Code Auditor with expertise in code quality and best practices.

TASK: Analyze the provided Python code and create a detailed refactoring plan.

CODE TO ANALYZE:
```python
{code}
```

ANALYSIS REQUIREMENTS:
1. **Syntax Check**: Identify any syntax errors
2. **Critical Issues**: Security vulnerabilities, infinite loops, critical bugs
3. **Major Issues**: Runtime errors, poor error handling, logic errors
4. **Minor Issues**: PEP 8 violations, missing docstrings, code smells

OUTPUT FORMAT:
You MUST return ONLY a valid JSON object with this exact structure:

{{
    "critical_issues": [
        {{
            "line": <line_number>,
            "type": "syntax|security|logic",
            "description": "Clear description of the issue",
            "suggestion": "Specific fix to apply"
        }}
    ],
    "major_issues": [
        {{
            "line": <line_number>,
            "type": "error_handling|performance|compatibility",
            "description": "Clear description",
            "suggestion": "Specific fix"
        }}
    ],
    "minor_issues": [
        {{
            "line": <line_number>,
            "type": "style|documentation|naming",
            "description": "Clear description",
            "suggestion": "Specific fix"
        }}
    ],
    "summary": {{
        "total_issues": <number>,
        "estimated_pylint_score": <0.0-10.0>,
        "complexity": "low|medium|high",
        "refactoring_priority": ["Priority 1", "Priority 2"]
    }}
}}

CRITICAL: Return ONLY the JSON object. No markdown, no explanations, no code blocks."""
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the audit: analyze code and create refactoring plan.
        
        Args:
            state: Current workflow state
        
        Returns:
            State updates with audit report
        """
        current_file = state.get('current_file', 'unknown')
        self._log(f"Analyzing: {current_file}")
        
        # Get code from state
        code = state.get("file_content", "")
        if not code:
            return self._create_error_result(state, "No code content to analyze")
        
        # Step 1: Run static analysis (pylint)
        self._log("Running pylint analysis...")
        pylint_result = self.analysis_tools.run_pylint(current_file)
        
        # Step 2: Check syntax
        syntax_check = self.analysis_tools.check_syntax(code)
        
        # Step 3: Get code metrics
        function_count = self.analysis_tools.count_functions(code)
        class_count = self.analysis_tools.count_classes(code)
        complexity = self.analysis_tools.get_complexity_estimate(code)
        
        # Step 4: Prepare prompt for LLM
        prompt = self.prompt_template.replace("{code}", code)
        
        # Add context from static analysis
        context = f"""
STATIC ANALYSIS RESULTS:
- Pylint score: {pylint_result.get('score', 'N/A')}/10
- Syntax valid: {syntax_check.get('valid', False)}
- Functions: {function_count}
- Classes: {class_count}
- Complexity: {complexity}
"""
        prompt = context + "\n" + prompt
        
        # Step 5: Call LLM for detailed analysis
        self._log("Calling LLM for detailed analysis...")
        try:
            llm_response = self.llm_client.call_with_json(prompt)
        except Exception as e:
            self._log(f"LLM call failed: {e}")
            return self._create_error_result(state, f"LLM error: {e}")
        
        # Step 6: Parse LLM response
        refactoring_plan = self._parse_response(llm_response, pylint_result)
        
        # Step 7: Log the experiment
        log_experiment(
            agent_name="AuditorAgent",
            model_used=self.llm_client.model_name,
            action=ActionType.ANALYSIS,
            details={
                "file_analyzed": current_file,
                "input_prompt": prompt,
                "output_response": llm_response,
                "pylint_score": pylint_result.get('score', 0.0),
                "issues_found": refactoring_plan.get('summary', {}).get('total_issues', 0)
            },
            status="SUCCESS"
        )
        
        # Step 8: Return state updates
        return {
            "audit_report": refactoring_plan,
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "audit_report": refactoring_plan,
                "original_pylint_score": pylint_result.get('score', 0.0)
            }
        }
    
    def _parse_response(self, response: str, pylint_result: Dict) -> Dict[str, Any]:
        """
        Parse the LLM response into a structured refactoring plan.
        
        Args:
            response: Raw LLM response
            pylint_result: Results from pylint
        
        Returns:
            Structured refactoring plan
        """
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Extract content between code fences
                match = re.search(r'```(?:json)?\s*\n(.*?)\n```', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1)
            
            # Parse JSON
            plan = json.loads(cleaned)
            
            # Validate structure
            if not isinstance(plan, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure required keys exist
            plan.setdefault("critical_issues", [])
            plan.setdefault("major_issues", [])
            plan.setdefault("minor_issues", [])
            plan.setdefault("summary", {})
            
            # Add total issues count
            total = (len(plan["critical_issues"]) + 
                    len(plan["major_issues"]) + 
                    len(plan["minor_issues"]))
            plan["summary"]["total_issues"] = total
            
            self._log(f"Found {total} issues to address")
            
            return plan
        
        except (json.JSONDecodeError, ValueError) as e:
            self._log(f"Failed to parse LLM response: {e}")
            
            # Fallback: Create plan from pylint results
            return self._create_fallback_plan(pylint_result)
    
    def _create_fallback_plan(self, pylint_result: Dict) -> Dict[str, Any]:
        """
        Create a basic refactoring plan from pylint results.
        
        Args:
            pylint_result: Pylint analysis results
        
        Returns:
            Basic refactoring plan
        """
        issues = pylint_result.get('issues', [])
        
        plan = {
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
            "summary": {
                "total_issues": len(issues),
                "estimated_pylint_score": pylint_result.get('score', 0.0),
                "complexity": "medium",
                "refactoring_priority": ["Fix pylint issues"]
            }
        }
        
        # Categorize pylint issues
        for issue in issues:
            issue_dict = {
                "line": issue.get('line', 0),
                "type": issue.get('type', 'unknown'),
                "description": issue.get('message', 'Unknown issue'),
                "suggestion": f"Fix {issue.get('message-id', 'issue')}"
            }
            
            # Categorize by severity
            if issue.get('type') in ['error', 'fatal']:
                plan["critical_issues"].append(issue_dict)
            elif issue.get('type') == 'warning':
                plan["major_issues"].append(issue_dict)
            else:
                plan["minor_issues"].append(issue_dict)
        
        return plan