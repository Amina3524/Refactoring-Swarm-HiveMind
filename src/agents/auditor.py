"""
Auditor Agent that analyzes code and produces a refactoring plan.
"""

from typing import Dict, Any, Optional  
import json
import os
import re
from .base_agent import BaseAgent
from src.llm.gemini_client import LLMClient

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AuditorAgent")
        print(f"{self.name} initialized with robust parsing")
        
        # Try to initialize LLM client
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        """Initialize the LLM client if available."""
        try:
            
            client = LLMClient()
            print(f"LLM client initialized")
            return client
        except ImportError:
            print(f"LLM client not found, using simulation mode")
            return None
        except Exception as e:
            print(f"LLM client error: {e}, using simulation mode")
            return None
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code using LLM and produce refactoring plan."""
        current_file = state.get('current_file', 'unknown')
        print(f"{self.name} analyzing: {current_file}")
        
        # Get the code from state
        code = state.get("file_content", "")
        if not code:
            print("No code to analyze")
            return self._create_error_result(state, "No code content")
        
        print(f"  Code length: {len(code)} characters")
        
        # Prepare the prompt
        prompt = self._prepare_analysis_prompt(code)
        print(f"  Prompt prepared: {len(prompt)} chars")
        
        # Call LLM for analysis
        print("Calling LLM for analysis...")
        llm_response = self._call_llm_analysis(prompt, current_file)
        
        # Parse the analysis into a refactoring plan
        refactoring_plan = self._parse_llm_response_safely(llm_response, current_file, code)
        
        # Log the action
        self._log_analysis(current_file, prompt, llm_response, refactoring_plan)
        
        # Return state updates
        return {
        "file_content": code,  # <-- CONSERVE THE CODE
        "current_file": current_file,  # <-- CONSERVE THE FILE NAME
        "agent_outputs": {
            **(state.get("agent_outputs") or {}),
            "audit_report": refactoring_plan
        },
        "current_phase": "fix",
        "original_code": code  # <-- Optional: keep original copy
    }
    
    def _prepare_analysis_prompt(self, code: str) -> str:
        """Prepare the analysis prompt with strict JSON requirements."""
        # First, try to load from prompt file
        prompt_template = self._load_prompt_template()
        
        if prompt_template:
            if "{code}" in prompt_template:
                prompt = prompt_template.replace("{code}", code)
            else:
                prompt = prompt_template + "\n\nCODE TO ANALYZE:\n```python\n" + code + "\n```"
        else:
            # Use default prompt
            prompt = self._get_default_prompt().replace("{code}", code)
        
        # Add strict JSON requirement
        if "IMPORTANT: Return ONLY valid JSON" not in prompt:
            prompt += "\n\nIMPORTANT: Return ONLY valid JSON. Do not include explanations, markdown, or other text. Just the JSON object."
        
        return prompt
    
    def _load_prompt_template(self) -> str:
        """Load the auditor prompt from file."""
        try:
            prompt_path = "src/prompts/auditor_prompt.txt"
            if not os.path.exists(prompt_path):
                prompt_path = "prompts/auditor_prompt.txt"
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def _get_default_prompt(self) -> str:
        """Get a default prompt."""
        return """ROLE: Senior Python Code Auditor
TASK: Analyze Python code for bugs and quality issues

CODE TO ANALYZE:
{code}

ANALYSIS INSTRUCTIONS:
1. Check for CRITICAL issues: Syntax errors, security risks, infinite loops
2. Check for MAJOR issues: Runtime errors, logical errors, missing error handling
3. Check for MINOR issues: PEP 8 violations, poor variable names, missing docstrings

OUTPUT FORMAT (JSON ONLY):
{
    "critical_issues": [
        {"line": 10, "type": "syntax", "description": "Issue description", "suggestion": "How to fix"}
    ],
    "major_issues": [],
    "minor_issues": [],
    "summary": {
        "pylint_score": 7.5,
        "function_count": 5,
        "overall_risk": "high|medium|low",
        "refactoring_priority": ["Fix critical issues first"]
    }
}"""
    
    def _call_llm_analysis(self, prompt: str, filename: str) -> str:
        """Call LLM to analyze the code."""
        if self.llm_client:
            try:
                print("Making real LLM call...")
                response = self.llm_client.call(prompt)
                print(f"LLM response received: {len(response)} chars")
                return response
            except Exception as e:
                print(f"LLM call failed: {e}")
                return self._simulate_llm_response(filename)
        else:
            print("No LLM client, using simulation")
            return self._simulate_llm_response(filename)
    
    def _simulate_llm_response(self, filename: str) -> str:
        """Simulate an LLM response."""
        return json.dumps({
            "critical_issues": [
                {
                    "line": 20,
                    "type": "security",
                    "description": "eval() with user input - security risk",
                    "suggestion": "Remove eval() or sanitize input"
                }
            ],
            "major_issues": [
                {
                    "line": 28,
                    "type": "error_handling",
                    "description": "Bare except clause",
                    "suggestion": "Specify exception types"
                }
            ],
            "minor_issues": [
                {
                    "line": 33,
                    "type": "style",
                    "description": "Missing spaces around operators",
                    "suggestion": "Add spaces: x = 5"
                }
            ],
            "summary": {
                "pylint_score": 5.5,
                "function_count": 3,
                "overall_risk": "medium",
                "refactoring_priority": ["Fix security issues", "Improve error handling"]
            }
        }, indent=2)
    
    def _parse_llm_response_safely(self, response: str, filename: str, code: str) -> Dict[str, Any]:
     """Safely parse LLM response with multiple fallback strategies."""
     print("Parsing LLM response...")
    
     # Ajouter du debug
     print(f"Response length: {len(response)} chars")
    
     # Strategy 0: Debug - save response for inspection
     try:
         import os
         debug_file = f"auditor_response_{os.path.basename(filename).replace('.py', '')}.txt"
         with open(debug_file, 'w', encoding='utf-8') as f:
             f.write(response)
         print(f"💾 Response saved to: {debug_file}")
     except:
         pass
    
     # Strategy 1: Try to use json_parser if available
     try:
         from src.utils.json_parser import parse_llm_response
         print("  Trying json_parser...")
         plan = parse_llm_response(response)
         
         # Debug: voir ce que json_parser a retourné
         print(f"  json_parser result keys: {list(plan.keys())}")
         
         if not plan.get("_error") and not plan.get("_note"):
             print("✅ Parsed with json_parser")
             # Debug: compter les issues trouvés
             crit = len(plan.get("critical_issues", []))
             maj = len(plan.get("major_issues", []))
             min_issues = len(plan.get("minor_issues", []))
             print(f"  Found {crit} critical, {maj} major, {min_issues} minor issues")
             return self._validate_plan(plan, code, filename)
         else:
             error_msg = plan.get("_error", plan.get("_note", "Unknown error"))
             print(f"❌ json_parser error: {error_msg}")
     except ImportError:
         print("json_parser not available")
     except Exception as e:
         print(f"json_parser exception: {e}")
    
     # Strategy 2: Try direct JSON parse avec plus de debug
     try:
         print("  Trying direct JSON parse...")
         parsed = json.loads(response.strip())
         print("✅ Direct JSON parse successful")
         return self._validate_plan(parsed, code, filename)
     except json.JSONDecodeError as e:
         print(f"❌ Direct JSON parse failed: {e}")
         print(f"   Error at position {e.pos}, line {e.lineno}, col {e.colno}")
         
         # Montrer le contexte autour de l'erreur
         start_idx = max(0, e.pos - 50)
         end_idx = min(len(response), e.pos + 50)
         print(f"   Context around error: ...{response[start_idx:end_idx]}...")
    
     # Strategy 3: Try to extract JSON from markdown avec plus de debug
     print("  Trying markdown extraction...")
     json_str = self._extract_json_from_text(response)
     if json_str:
         print(f"  Extracted {len(json_str)} chars")
         try:
             parsed = json.loads(json_str)
             print("✅ Extracted JSON from markdown")
             return self._validate_plan(parsed, code, filename)
         except json.JSONDecodeError as e:
             print(f"❌ Extracted JSON also invalid: {e}")
             # Montrer le début de ce qu'on a extrait
             print(f"   Extracted start: {json_str[:100]}...")
     else:
         print("  No JSON found in markdown")
    
     # Strategy 4: Simple regex extraction améliorée
     print("  Trying enhanced regex extraction...")
     json_str = self._enhanced_json_extraction(response)
     if json_str:
         print(f"  Enhanced extraction got {len(json_str)} chars")
         try:
             parsed = json.loads(json_str)
             print("✅ Enhanced extraction worked")
             return self._validate_plan(parsed, code, filename)
         except json.JSONDecodeError as e:
             print(f"❌ Enhanced extraction failed: {e}")
    
    # Strategy 5: Fallback to simulated analysis
     print("❌ All parsing failed, using fallback")
     return self._create_fallback_plan(filename, response, code)

    def _enhanced_json_extraction(self, text: str) -> Optional[str]:
        """Enhanced JSON extraction with better pattern matching."""
        # Chercher le pattern JSON le plus commun
        patterns = [
            # Pattern 1: { ... } avec équilibre d'accolades
            r'(\{(?:[^{}]|\{[^{}]*\})*\})',
            # Pattern 2: contenu entre accolades (simplifié)
            r'(\{[^{}]*\})',
            # Pattern 3: JSON avec des listes
            r'(\{\s*".*?"\s*:\s*\[.*?\]\s*\})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if match and match.startswith('{') and match.endswith('}'):
                    # Vérifier que ça ressemble à du JSON
                    if ':' in match and ('"' in match or '[' in match):
                        # Compter les accolades
                        if match.count('{') == match.count('}'):
                            return match
        return None
     
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON from text that might contain markdown."""
        # Look for ```json ... ```
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for ``` ... ``` (assume JSON)
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Look for { ... } directly
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        
        return None
    
    def _simple_json_extraction(self, text: str) -> Optional[str]:
        """Simple JSON extraction by finding matching braces."""
        start = text.find('{')
        if start == -1:
            return None
        
        brace_count = 0
        result = []
        
        for i in range(start, len(text)):
            char = text[i]
            result.append(char)
            
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return ''.join(result)
        
        return None
    
    def _validate_plan(self, plan: Dict[str, Any], code: str, filename: str) -> Dict[str, Any]:
        """Validate and enhance the refactoring plan."""
        # Ensure required structure
        plan.setdefault("critical_issues", [])
        plan.setdefault("major_issues", [])
        plan.setdefault("minor_issues", [])
        plan.setdefault("summary", {})
        
        # Enhance summary
        summary = plan["summary"]
        summary.setdefault("pylint_score", 6.0)
        summary.setdefault("function_count", code.count("def "))
        summary.setdefault("overall_risk", "medium")
        summary.setdefault("refactoring_priority", ["Review issues"])
        
        # Add metadata
        plan["file"] = filename
        
        return plan
    
    def _create_fallback_plan(self, filename: str, response: str, code: str) -> Dict[str, Any]:
        """Create a fallback plan when all parsing fails."""
        return {
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
            "summary": {
                "pylint_score": 4.0,
                "function_count": code.count("def "),
                "overall_risk": "unknown",
                "refactoring_priority": ["Manual review needed"],
                "note": "LLM response parsing failed"
            },
            "file": filename,
            "fallback": True
        }
    
    def _log_analysis(self, filename: str, prompt: str, response: str, plan: Dict[str, Any]):
        """Log the analysis."""
        critical = len(plan.get("critical_issues", []))
        major = len(plan.get("major_issues", []))
        minor = len(plan.get("minor_issues", []))
        total = critical + major + minor
        
        log_details = {
            "input_prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "output_response": response[:500] + "..." if len(response) > 500 else response,
            "file": filename,
            "issues_found": total,
            "critical_issues": critical,
            "major_issues": major,
            "minor_issues": minor
        }
        
        self.log_action("analyze", log_details)
        print(f"Logged analysis with {total} issues found")
    
    def _create_error_result(self, state: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Create error result."""
        print(f"Error: {error_msg}")
        
        self.log_action("analyze", {
            "input_prompt": f"Analyzing {state.get('current_file', 'unknown')}",
            "output_response": f"Error: {error_msg}",
            "file": state.get("current_file", "unknown"),
            "error": True
        })
        
        return {
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "audit_report": {
                    "error": error_msg,
                    "critical_issues": [],
                    "major_issues": [],
                    "minor_issues": []
                }
            },
            "current_phase": "error"
        }