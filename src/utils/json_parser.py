"""
Utility functions for parsing LLM JSON responses.
"""

import json
import re
from typing import Any, Dict, Optional

def extract_json_from_response(response: str) -> Optional[str]:
    """
    Extract JSON from an LLM response that might contain markdown, explanations, etc.
    """
    if not response:
        return None
    
    # Remove leading/trailing whitespace
    response = response.strip()
    
    # Common patterns for JSON in markdown
    patterns = [
        # Pattern 1: ```json ... ```
        r'```json\s*(.*?)\s*```',
        # Pattern 2: ``` ... ``` (assuming JSON inside)
        r'```\s*(.*?)\s*```',
        # Pattern 3: { ... } (direct JSON object)
        r'(\{.*\})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            candidate = matches[0].strip()
            if candidate.startswith('{'):
                return candidate
    
    # If no patterns matched, try to find JSON by looking for braces
    try:
        start = response.find('{')
        if start != -1:
            # Simple approach: find matching brace
            brace_count = 0
            for i, char in enumerate(response[start:], start=start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return response[start:i+1]
    except:
        pass
    
    return None

def safe_json_parse(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON with error handling.
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        fixed = json_str
        
        # Remove trailing commas before } or ]
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
        
        try:
            return json.loads(fixed)
        except:
            return {
                "error": str(e),
                "raw_preview": json_str[:200],
                "default": default
            }

def parse_llm_response(response: str, expected_structure: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Parse LLM response into structured data with fallbacks.
    """
    if expected_structure is None:
        expected_structure = {
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
            "summary": {}
        }
    
    # Extract JSON from response
    json_str = extract_json_from_response(response)
    
    if not json_str:
        result = expected_structure.copy()
        result["_note"] = "No JSON found in response"
        result["_raw_preview"] = response[:500]
        return result
    
    # Parse JSON
    parsed = safe_json_parse(json_str, default=expected_structure.copy())
    
    if isinstance(parsed, dict) and "error" in parsed:
        result = expected_structure.copy()
        result["_error"] = parsed["error"]
        result["_raw_preview"] = parsed.get("raw_preview", "")
        return result
    
    # Ensure all expected keys exist
    for key, default_value in expected_structure.items():
        if key not in parsed:
            parsed[key] = default_value
    
    return parsed