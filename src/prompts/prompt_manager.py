"""
PROMPT MANAGER
Role: Prompt Engineer
Responsibility: Manages all AI prompts for the Refactoring Swarm
"""
import os
import json
from typing import Dict, Optional
from src.utils.logger import log_experiment, ActionType


class PromptManager:
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the prompt manager.
        
        Args:
            model_name: Name of the LLM model being used
        """
        self.model_name = model_name
        self.prompts_dir = os.path.join(os.path.dirname(__file__))
      
        self.auditor_prompt = self._load_prompt("auditor_prompt.txt")
        self.fixer_prompt = self._load_prompt("fixer_prompt.txt")
        self.judge_prompt = self._load_prompt("judge_prompt.txt")
    
    def _load_prompt(self, filename: str) -> str:
        """Load a prompt from a text file."""
        filepath = os.path.join(self.prompts_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: Prompt file {filename} not found")
            return f"# Placeholder for {filename}"
    
    def get_auditor_prompt(self, code: str) -> str:
        """Get the auditor prompt with code inserted."""
        log_experiment(
            agent_name="PromptManager",
            model_used=self.model_name,
            action=ActionType.GENERATION,
            details={
                "prompt_type": "auditor",
                "input_prompt": "Getting auditor prompt template",
                "output_response": "Prompt retrieved successfully",
                "code_length": len(code)
            },
            status="SUCCESS"
        )
        return self.auditor_prompt.replace("{code}", code)
    
    def get_fixer_prompt(self, code: str, audit_report: str) -> str:
        """Get the fixer prompt with code and audit inserted."""
        if isinstance(audit_report, dict):
            audit_report = json.dumps(audit_report, indent=2)
        
        prompt = self.fixer_prompt.replace("{code}", code)
        prompt = prompt.replace("{audit_report}", audit_report)
        
        log_experiment(
            agent_name="PromptManager",
            model_used=self.model_name,
            action=ActionType.GENERATION,
            details={
                "prompt_type": "fixer",
                "input_prompt": "Getting fixer prompt template",
                "output_response": "Prompt formatted with code and audit",
                "code_length": len(code)
            },
            status="SUCCESS"
        )
        return prompt
    
    def get_judge_prompt(self, code: str, test_results: str) -> str:
        """Get the judge prompt with code and test results."""
        if isinstance(test_results, dict):
            test_results = json.dumps(test_results, indent=2)
        
        prompt = self.judge_prompt.replace("{code}", code)
        prompt = prompt.replace("{test_results}", test_results)
        
        log_experiment(
            agent_name="PromptManager",
            model_used=self.model_name,
            action=ActionType.GENERATION,
            details={
                "prompt_type": "judge",
                "input_prompt": "Getting judge prompt template",
                "output_response": "Prompt formatted with code and test results",
                "code_length": len(code)
            },
            status="SUCCESS"
        )
        return prompt
    
    def save_prompt_version(self, agent_type: str, prompt: str, version: str, notes: str = ""):
        """Save a versioned copy of a prompt."""
        versions_dir = os.path.join(self.prompts_dir, "versions")
        os.makedirs(versions_dir, exist_ok=True)
        
        filename = f"{agent_type}_v{version}.txt"
        filepath = os.path.join(versions_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Version {version}\n# {notes}\n\n{prompt}")
        
        log_experiment(
            agent_name="PromptManager",
            model_used=self.model_name,
            action=ActionType.GENERATION,
            details={
                "action": "save_prompt_version",
                "agent_type": agent_type,
                "version": version,
                "file_saved": filename
            },
            status="SUCCESS"
        )
