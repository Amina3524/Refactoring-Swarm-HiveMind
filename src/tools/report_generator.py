"""
Générateur de rapports - Data Officer (VERSION SIMPLIFIÉE)
Crée des rapports statistiques et d'analyse automatiques.
SANS dépendances complexes - fonctionne directement.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List


class ReportGenerator:
    """
    Génère des rapports détaillés sur le système.
    Version simplifiée sans dépendances.
    """
    
    def __init__(self, log_file: str = "logs/experiment_data.json"):
        """
        Initialiser le générateur.
        
        Args:
            log_file: Chemin du fichier de logs
        """
        self.log_file = log_file
        self.logs = []
        self.report_dir = "data_officer/reports"
        
        # Créer le dossier de rapports
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Charger les logs
        self._load_logs()
    
    def _load_logs(self) -> bool:
        """Charger les logs depuis le fichier."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.logs = data if isinstance(data, list) else [data]
                return True
            return False
        except Exception as e:
            print(f"[REPORT] Erreur lors du chargement des logs: {e}")
            return False
    
    def generate_robustness_report(self) -> Dict[str, Any]:
        """
        Générer un rapport de robustesse.
        """
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "ROBUSTNESS",
            "metrics": {
                "total_logs": len(self.logs),
                "success_rate": 0,
                "failure_rate": 0,
                "max_iteration": 0,
                "avg_iteration": 0,
                "agents_count": 0,
                "stability_score": 0
            },
            "verdict": "NO_DATA"
        }
        
        if not self.logs:
            return report
        
        # Calculer les stats
        success_count = 0
        failure_count = 0
        iterations = []
        agents = set()
        
        for log in self.logs:
            # Status
            if log.get("status") == "SUCCESS":
                success_count += 1
            elif log.get("status") == "FAILURE":
                failure_count += 1
            
            # Agents
            if "agent" in log:
                agents.add(log["agent"])
            
            # Itérations
            if "metadata" in log and "iteration" in log["metadata"]:
                iteration = log["metadata"]["iteration"]
                iterations.append(iteration)
        
        total = success_count + failure_count
        
        # Remplir le rapport
        if total > 0:
            report["metrics"]["success_rate"] = (success_count / total * 100)
            report["metrics"]["failure_rate"] = (failure_count / total * 100)
        
        report["metrics"]["agents_count"] = len(agents)
        
        if iterations:
            report["metrics"]["max_iteration"] = max(iterations)
            report["metrics"]["avg_iteration"] = sum(iterations) / len(iterations)
        
        # Score de stabilité (0-100)
        stability_score = report["metrics"]["success_rate"]
        if report["metrics"]["max_iteration"] <= 10:
            stability_score += 10
        if failure_count == 0:
            stability_score += 10
        
        report["metrics"]["stability_score"] = min(100, stability_score)
        
        # Verdict
        if report["metrics"]["stability_score"] >= 80:
            report["verdict"] = "EXCELLENT"
        elif report["metrics"]["stability_score"] >= 60:
            report["verdict"] = "BON"
        elif report["metrics"]["stability_score"] >= 40:
            report["verdict"] = "MOYEN"
        else:
            report["verdict"] = "FAIBLE"
        
        return report
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Générer un rapport de qualité.
        """
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "QUALITY",
            "metrics": {
                "json_validity": "VALID",
                "required_fields_present": True,
                "prompt_diversity": 0,
                "response_diversity": 0,
                "unique_prompts": 0,
                "unique_responses": 0,
                "quality_score": 0
            },
            "verdict": "NO_DATA"
        }
        
        if not self.logs:
            return report
        
        # Vérifications
        all_prompts = []
        all_responses = []
        fields_missing = 0
        required_fields = ["timestamp", "agent", "action", "status"]
        
        for i, log in enumerate(self.logs):
            # Vérifier les champs obligatoires
            for field in required_fields:
                if field not in log:
                    fields_missing += 1
            
            # Collecter prompts et responses
            if "details" in log:
                details = log["details"]
                if "input_prompt" in details:
                    all_prompts.append(str(details["input_prompt"]))
                if "output_response" in details:
                    all_responses.append(str(details["output_response"]))
        
        # Calculer diversité
        unique_prompts = len(set(all_prompts))
        unique_responses = len(set(all_responses))
        total_prompts = len(all_prompts)
        total_responses = len(all_responses)
        
        diversity_prompts = (unique_prompts / total_prompts * 100) if total_prompts > 0 else 0
        diversity_responses = (unique_responses / total_responses * 100) if total_responses > 0 else 0
        
        report["metrics"]["unique_prompts"] = unique_prompts
        report["metrics"]["unique_responses"] = unique_responses
        report["metrics"]["prompt_diversity"] = diversity_prompts
        report["metrics"]["response_diversity"] = diversity_responses
        report["metrics"]["required_fields_present"] = fields_missing == 0
        
        # Score de qualité
        quality_score = 100
        if fields_missing > 0:
            quality_score -= fields_missing * 5
        if diversity_prompts < 50:
            quality_score -= 10
        if diversity_responses < 50:
            quality_score -= 10
        
        report["metrics"]["quality_score"] = max(0, quality_score)
        
        # Verdict
        if quality_score >= 80:
            report["verdict"] = "EXCELLENT"
        elif quality_score >= 60:
            report["verdict"] = "BON"
        elif quality_score >= 40:
            report["verdict"] = "MOYEN"
        else:
            report["verdict"] = "FAIBLE"
        
        return report
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """
        Générer un rapport d'exécution.
        """
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "EXECUTION",
            "metrics": {
                "total_actions": len(self.logs),
                "first_action": None,
                "last_action": None,
                "agent_distribution": {},
                "action_sequence": []
            },
            "timeline": []
        }
        
        if not self.logs:
            return report
        
        # Extraire timeline
        agent_counts = {}
        action_sequence = []
        
        for i, log in enumerate(self.logs):
            # Timeline
            report["timeline"].append({
                "index": i,
                "timestamp": log.get("timestamp"),
                "agent": log.get("agent"),
                "action": log.get("action"),
                "status": log.get("status")
            })
            
            # Distribution d'agents
            agent = log.get("agent", "UNKNOWN")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            # Séquence d'actions
            action = log.get("action", "UNKNOWN")
            if not action_sequence or action_sequence[-1] != action:
                action_sequence.append(action)
        
        # Remplir le rapport
        if self.logs:
            report["metrics"]["first_action"] = {
                "timestamp": self.logs[0].get("timestamp"),
                "agent": self.logs[0].get("agent"),
                "action": self.logs[0].get("action")
            }
            report["metrics"]["last_action"] = {
                "timestamp": self.logs[-1].get("timestamp"),
                "agent": self.logs[-1].get("agent"),
                "action": self.logs[-1].get("action")
            }
        
        report["metrics"]["agent_distribution"] = agent_counts
        report["metrics"]["action_sequence"] = action_sequence
        
        return report
    
    def generate_final_summary(self) -> Dict[str, Any]:
        """
        Générer le rapport final résumé.
        """
        
        robustness = self.generate_robustness_report()
        quality = self.generate_quality_report()
        execution = self.generate_execution_report()
        
        # Score global
        robustness_score = robustness["metrics"].get("stability_score", 0)
        quality_score = quality["metrics"].get("quality_score", 0)
        execution_score = min(100, (execution["metrics"].get("total_actions", 1) / 100) * 100)
        
        global_score = (
            robustness_score * 0.3 +
            quality_score * 0.4 +
            execution_score * 0.3
        )
        
        global_score = min(100, max(0, global_score))
        
        # Recommandations
        recommendations = []
        
        if robustness_score < 80:
            recommendations.append("[ERROR] Améliorer le taux de succès")
        
        if quality_score < 70:
            recommendations.append("[DOC] Améliorer la qualité des logs")
        
        if execution["metrics"]["total_actions"] < 10:
            recommendations.append("[DATA] Ajouter plus de logs")
        
        if not recommendations:
            recommendations.append("[SUCCESS] Tous les critères sont satisfaits!")
        
        # Verdict global
        if global_score >= 85:
            verdict = "EXCELLENT - Prêt pour la production"
        elif global_score >= 70:
            verdict = "BON - Quelques améliorations"
        elif global_score >= 50:
            verdict = "MOYEN - Révisions recommandées"
        else:
            verdict = "FAIBLE - Corrections essentielles"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "report_type": "FINAL_SUMMARY",
            "global_score": round(global_score, 1),
            "verdict": verdict,
            "sub_scores": {
                "robustness": round(robustness_score, 1),
                "quality": round(quality_score, 1),
                "execution_volume": round(execution_score, 1)
            },
            "recommendations": recommendations
        }
        
        return summary
    
    def save_all_reports(self) -> Dict[str, str]:
        """
        Sauvegarder tous les rapports en JSON.
        """
        
        files = {}
        
        try:
            # Rapport de robustesse
            robustness = self.generate_robustness_report()
            robustness_file = os.path.join(self.report_dir, "robustness_report.json")
            with open(robustness_file, 'w') as f:
                json.dump(robustness, f, indent=2)
            files["robustness"] = robustness_file
            
            # Rapport de qualité
            quality = self.generate_quality_report()
            quality_file = os.path.join(self.report_dir, "quality_report.json")
            with open(quality_file, 'w') as f:
                json.dump(quality, f, indent=2)
            files["quality"] = quality_file
            
            # Rapport d'exécution
            execution = self.generate_execution_report()
            execution_file = os.path.join(self.report_dir, "execution_report.json")
            with open(execution_file, 'w') as f:
                json.dump(execution, f, indent=2)
            files["execution"] = execution_file
            
            # Rapport final
            summary = self.generate_final_summary()
            summary_file = os.path.join(self.report_dir, "final_summary.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            files["summary"] = summary_file
        
        except Exception as e:
            print(f"[REPORT] Erreur lors de la sauvegarde des rapports: {e}")
        
        return files
    
    def print_summary(self):
        """Afficher un résumé dans la console."""
        summary = self.generate_final_summary()
        
        print("\n" + "=" * 80)
        print("[REPORT] RAPPORT FINAL - DATA OFFICER")
        print("=" * 80)
        print(f"\n{summary['verdict']}")
        print(f"\n[SCORE] Score Global: {summary['global_score']}/100")
        print("\n[METRICS] Scores par catégorie:")
        print(f"  • Robustesse: {summary['sub_scores']['robustness']}/100")
        print(f"  • Qualité: {summary['sub_scores']['quality']}/100")
        print(f"  • Volume d'exécution: {summary['sub_scores']['execution_volume']}/100")
        print("\n[RECOMMEND] Recommandations:")
        for rec in summary["recommendations"]:
            print(f"  • {rec}")
        print("\n" + "=" * 80)


# ===== FONCTIONS SIMPLES =====

def generate_all_reports(log_file: str = "logs/experiment_data.json") -> Dict[str, Any]:
    """Générer tous les rapports en une seule fonction."""
    generator = ReportGenerator(log_file)
    return generator.generate_final_summary()


def print_report_summary(log_file: str = "logs/experiment_data.json"):
    """Afficher un résumé du rapport."""
    generator = ReportGenerator(log_file)
    generator.print_summary()