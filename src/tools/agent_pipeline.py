"""
Pipeline d'intégration des agents - Data Officer
Teste que les agents Auditor, Fixer, Judge fonctionnent ensemble.
"""

import json
import os
from typing import Dict, Any, List, Tuple


class AgentPipeline:
    """
    Pipeline d'intégration : Auditor → Fixer → Judge
    Simule le workflow complet de refactoring.
    """
    
    def __init__(self):
        """Initialiser le pipeline."""
        self.logs = []
        self.iterations = 0
        self.max_iterations = 10
    
    def run_auditor(self, code: str) -> Dict[str, Any]:
        """
        Simule l'Auditor Agent.
        
        Rôle : Analyser le code et créer un plan de refactoring.
        
        Returns:
            {
                "status": "success",
                "analysis": str,
                "issues": list,
                "plan": str
            }
        """
        
        result = {
            "status": "success",
            "analysis": f"Code analysé : {len(code)} caractères",
            "issues": [],
            "plan": ""
        }
        
        # Vérifier certains critères
        if "def " not in code:
            result["issues"].append("Pas de fonctions détectées")
        
        if '"""' not in code and "'''" not in code:
            result["issues"].append("Pas de docstrings détectées")
        
        if "import" not in code:
            result["issues"].append("Pas d'imports détectées")
        
        # Créer un plan
        result["plan"] = f"Corriger {len(result['issues'])} problèmes"
        
        # Enregistrer dans les logs
        self.logs.append({
            "agent": "Auditor_Agent",
            "action": "ANALYSIS",
            "timestamp": self._get_timestamp(),
            "details": {
                "input_prompt": f"Analyse ce code: {code[:50]}...",
                "output_response": result["analysis"],
                "issues_found": len(result["issues"])
            },
            "status": "SUCCESS"
        })
        
        return result
    
    def run_fixer(self, code: str, plan: str) -> Dict[str, Any]:
        """
        Simule le Fixer Agent.
        
        Rôle : Modifier le code selon le plan.
        
        Returns:
            {
                "status": "success",
                "fixed_code": str,
                "changes": list
            }
        """
        
        result = {
            "status": "success",
            "fixed_code": code,
            "changes": []
        }
        
        # Simuler des corrections
        if "def " in code and '"""' not in code:
            result["fixed_code"] = code.replace("def ", 'def """Fixed"""\n    def ')
            result["changes"].append("Docstrings ajoutées")
        
        if "  " in code:  # Double espace
            result["fixed_code"] = result["fixed_code"].replace("  ", " ")
            result["changes"].append("Espaces corrigés")
        
        # Enregistrer dans les logs
        self.logs.append({
            "agent": "Fixer_Agent",
            "action": "FIX",
            "timestamp": self._get_timestamp(),
            "details": {
                "input_prompt": f"Corrige ce code selon le plan: {plan}",
                "output_response": f"Corrections appliquées: {result['changes']}",
                "changes_made": len(result["changes"])
            },
            "status": "SUCCESS"
        })
        
        return result
    
    def run_judge(self, code: str) -> Dict[str, Any]:
        """
        Simule le Judge Agent.
        
        Rôle : Valider que le code fonctionne (tests passent).
        
        Returns:
            {
                "status": "success",
                "all_tests_pass": bool,
                "test_results": dict
            }
        """
        
        result = {
            "status": "success",
            "all_tests_pass": True,
            "test_results": {
                "passed": 0,
                "failed": 0
            }
        }
        
        # Simuler une validation
        if "def " in code:
            result["test_results"]["passed"] += 1
        else:
            result["test_results"]["failed"] += 1
            result["all_tests_pass"] = False
        
        if len(code) > 20:
            result["test_results"]["passed"] += 1
        
        # Enregistrer dans les logs
        self.logs.append({
            "agent": "Judge_Agent",
            "action": "DEBUG" if not result["all_tests_pass"] else "ANALYSIS",
            "timestamp": self._get_timestamp(),
            "details": {
                "input_prompt": f"Valide ce code: {code[:50]}...",
                "output_response": f"Tests: {result['test_results']['passed']} passed, {result['test_results']['failed']} failed",
                "tests_passed": result["test_results"]["passed"]
            },
            "status": "SUCCESS" if result["all_tests_pass"] else "FAILURE"
        })
        
        return result
    
    def run_pipeline(self, code: str) -> Dict[str, Any]:
        """
        Lance le pipeline complet : Auditor → Fixer → Judge (boucle).
        
        Returns:
            {
                "status": "success",
                "final_code": str,
                "iterations": int,
                "logs": list
            }
        """
        
        current_code = code
        self.iterations = 0
        
        while self.iterations < self.max_iterations:
            self.iterations += 1
            
            # Étape 1 : Auditor analyse
            analysis = self.run_auditor(current_code)
            
            if not analysis["plan"] or not analysis["issues"]:
                # Pas de problèmes détectés
                break
            
            # Étape 2 : Fixer corrige
            fix_result = self.run_fixer(current_code, analysis["plan"])
            current_code = fix_result["fixed_code"]
            
            # Étape 3 : Judge valide
            judge_result = self.run_judge(current_code)
            
            # Si tous les tests passent, arrêter
            if judge_result["all_tests_pass"]:
                break
        
        return {
            "status": "success",
            "final_code": current_code,
            "iterations": self.iterations,
            "logs": self.logs
        }
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Retourner les logs générés."""
        return self.logs
    
    def save_logs_to_file(self, filepath: str = "logs/experiment_data.json") -> bool:
        """
        Sauvegarder les logs dans un fichier JSON.
        
        Returns:
            True si succès, False sinon
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    @staticmethod
    def _get_timestamp() -> str:
        """Retourner un timestamp ISO 8601."""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"


# ===== FUNCTIONS SIMPLES (pour compatibilité avec tests) =====

def simulate_auditor_agent(code: str) -> Dict[str, Any]:
    """Simule simplement l'Auditor."""
    return {
        "status": "success",
        "analysis": f"Analysé: {len(code)} chars",
        "issues": [],
        "plan": "Refactor"
    }


def simulate_fixer_agent(code: str, plan: str) -> Dict[str, Any]:
    """Simule simplement le Fixer."""
    return {
        "status": "success",
        "fixed_code": code,
        "changes": ["refactored"]
    }


def simulate_judge_agent(code: str) -> Dict[str, Any]:
    """Simule simplement le Judge."""
    return {
        "status": "success",
        "all_tests_pass": True,
        "test_count": 1
    }


def run_agent_workflow(code: str) -> Dict[str, Any]:
    """
    Lance un workflow simple d'agents.
    
    Returns:
        {
            "status": "success",
            "final_code": str,
            "workflow_completed": bool
        }
    """
    
    # Étape 1
    auditor_result = simulate_auditor_agent(code)
    if auditor_result["status"] != "success":
        return {"status": "failed", "error": "Auditor failed"}
    
    # Étape 2
    fixer_result = simulate_fixer_agent(code, auditor_result["plan"])
    if fixer_result["status"] != "success":
        return {"status": "failed", "error": "Fixer failed"}
    
    fixed_code = fixer_result["fixed_code"]
    
    # Étape 3
    judge_result = simulate_judge_agent(fixed_code)
    if judge_result["status"] != "success":
        return {"status": "failed", "error": "Judge failed"}
    
    return {
        "status": "success",
        "final_code": fixed_code,
        "workflow_completed": True,
        "tests_passed": judge_result["all_tests_pass"]
    }