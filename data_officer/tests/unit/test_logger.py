"""
VALIDATEUR STRICT DES LOGS - Data Officer (VERSION CORRIGÉE selon logger)
Vérifie TOUS les critères du TP pour l'évaluation automatisée.
COMPATIBLE avec le logger officiel.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

def get_log_file_path() -> str:
    """Retourne le chemin absolu vers le fichier de logs."""
    possible_paths = [
        "logs/experiment_data.json",
        "../logs/experiment_data.json",
        "./logs/experiment_data.json",
        os.path.join(os.getcwd(), "logs", "experiment_data.json")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return os.path.join(os.getcwd(), "logs", "experiment_data.json")


def validate_strict_format() -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validation STRICTE selon les critères du TP.
    COMPATIBLE avec le logger officiel.
    """
    
    log_file = get_log_file_path()
    
    print("🔍 VALIDATION STRICTE DES LOGS - COMPATIBLE LOGGER")
    print("=" * 70)
    print(f"Fichier: {log_file}")
    print(f"Validation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    errors = []
    warnings = []
    statistics = {
        "total_entries": 0,
        "by_agent": {},
        "by_action": {},
        "by_status": {"SUCCESS": 0, "FAILURE": 0},
        "prompt_analysis": {},
        "security_issues": []
    }
    
    # ===== CRITÈRE 1: FICHIER EXISTE =====
    if not os.path.exists(log_file):
        error_msg = "❌ CRITIQUE: Fichier logs/experiment_data.json introuvable"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    # ===== CRITÈRE 2: TAILLE MINIMALE =====
    size = os.path.getsize(log_file)
    statistics["file_size"] = size
    
    print(f"📏 Taille fichier: {size} octets")
    
    if size < 100:
        warning = "⚠️  Fichier très petit (moins de 100 octets)"
        warnings.append(warning)
        print(warning)
    
    # ===== CRITÈRE 3: JSON VALIDE =====
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            
    except json.JSONDecodeError as e:
        error_msg = f"❌ JSON INVALIDE: {str(e)[:100]}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    except Exception as e:
        error_msg = f"❌ ERREUR LECTURE: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    statistics["total_entries"] = len(logs)
    
    if len(logs) == 0:
        error_msg = "❌ Fichier vide - aucune entrée de log"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    print(f"📊 Entrées trouvées: {len(logs)}")
    
    
    # ===== CRITÈRES OBLIGATOIRES DU TP  =====
    required_fields = ['agent', 'model', 'action', 'details', 'timestamp', 'status']
    
    valid_actions = ['ANALYSIS', 'GENERATION', 'DEBUG', 'FIX']

    valid_statuses = ['SUCCESS', 'FAILURE']
    
    # Agents minimum requis par le TP
    required_agents = {'Auditor', 'Fixer', 'Judge'}
    agents_found = set()
    
    # Pour détection plagiat
    all_prompts = []
    all_responses = []
    
    for i, entry in enumerate(logs):
        entry_errors = []
        entry_warnings = []
        
        # ===== CRITÈRE 4: CHAMPS OBLIGATOIRES =====
        for field in required_fields:
            if field not in entry:
                entry_errors.append(f"Champ '{field}' manquant")
        
        # ===== CRITÈRE 5: ACTIONS VALIDES =====
        if 'action' in entry:
            action = entry['action']
            if action not in valid_actions:
                entry_errors.append(f"Action invalide: '{action}' (attendus: {valid_actions})")
            else:
                statistics["by_action"][action] = statistics["by_action"].get(action, 0) + 1
        
        # ===== CRITÈRE 6: STATUS VALIDES =====
        if 'status' in entry:
            status = entry['status']
            if status not in valid_statuses:
                entry_errors.append(f"Status invalide: '{status}' (attendus: {valid_statuses})")
            else:
                statistics["by_status"][status] = statistics["by_status"].get(status, 0) + 1
        
        # ===== CRITÈRE 7: DÉTAILS OBLIGATOIRES =====
        if 'details' in entry:
            details = entry['details']
            
            if not isinstance(details, dict):
                entry_errors.append("'details' doit être un dictionnaire")
            else:
                # === CRITÈRE CRITIQUE: input_prompt et output_response ===
                # CORRECTION ICI: Indentation fixée
                if action == 'DEBUG':
                    # Pour DEBUG, on peut accepter des valeurs génériques
                    if 'input_prompt' not in details or not details.get('input_prompt'):
                        entry_warnings.append("'input_prompt' manquant pour DEBUG (acceptable)")
                else:
                    # Pour ANALYSIS, FIX, GENERATION : OBLIGATOIRE
                    if 'input_prompt' not in details or not details.get('input_prompt'):
                        entry_errors.append(f"'input_prompt' OBLIGATOIRE pour {action}")
                
                if 'output_response' not in details:
                    entry_errors.append("'output_response' manquant dans details (OBLIGATOIRE)")
                elif not details.get('output_response'):
                    entry_errors.append("'output_response' est vide")
                elif str(details.get('output_response')).strip().upper() in ['N/A', 'NONE', '']:
                    entry_errors.append("'output_response' ne peut pas être 'N/A', 'None' ou vide")
                
                # Vérifier la longueur minimale
                if 'input_prompt' in details:
                    prompt = str(details['input_prompt']).strip()
                    if len(prompt) < 20:
                        entry_warnings.append(f"'input_prompt' très court ({len(prompt)} chars, min recommandé: 20)")
                    all_prompts.append(prompt[:200])
                
                if 'output_response' in details:
                    response = str(details['output_response']).strip()
                    if len(response) < 10:
                        entry_warnings.append(f"'output_response' très court ({len(response)} chars, min recommandé: 10)")
                    all_responses.append(response[:200])
                
                # === CRITÈRE 8: SÉCURITÉ SANDBOX ===
                for key, value in details.items():
                    if isinstance(value, str) and '..' in value:
                        if 'sandbox' not in value.lower() and 'test' not in value.lower():
                            security_warning = f"Accès potentiel hors sandbox: {value[:50]}..."
                            if security_warning not in statistics["security_issues"]:
                                statistics["security_issues"].append(security_warning)
        
        # ===== CRITÈRE 9: TIMESTAMP ISO 8601 =====
        if 'timestamp' in entry:
            try:
                datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                entry_errors.append("Format timestamp invalide (doit être ISO 8601)")
        
        # ===== CRITÈRE 10: AGENT VALIDE =====
        if 'agent' in entry:
            agent = entry['agent']
            agents_found.add(agent)
            statistics["by_agent"][agent] = statistics["by_agent"].get(agent, 0) + 1
        
        # Collecter les erreurs
        if entry_errors:
            errors.append(f"Entrée {i}: {', '.join(entry_errors)}")
        
        if entry_warnings:
            warnings.extend([f"Entrée {i}: {w}" for w in entry_warnings])
    
    # ===== CRITÈRE 11: AGENTS MINIMUM REQUIS =====
    agents_base_names = set()
    for agent in agents_found:
        if '_' in agent:
            base_name = agent.split('_')[0]
        else:
            for req_agent in required_agents:
                if req_agent.lower() in agent.lower():
                    base_name = req_agent
                    break
            else:
                base_name = agent
        agents_base_names.add(base_name)
    
    missing_agents = required_agents - agents_base_names
    if missing_agents:
        error_msg = f"Agents requis manquants: {', '.join(missing_agents)}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
    
    # ===== CRITÈRE 12: SUFFISAMMENT D'ENTRÉES =====
    if len(logs) < 5:
        warning_msg = f"⚠️  Peu d'entrées ({len(logs)}). Minimum recommandé: 10 pour l'évaluation"
        warnings.append(warning_msg)
        print(warning_msg)
    elif len(logs) < 10:
        warning_msg = f"⚠️  Nombre d'entrées acceptable ({len(logs)}) mais 50+ recommandé"
        warnings.append(warning_msg)
    
    # ===== CRITÈRE 13: DÉTECTION PLAGIAT SIMPLIFIÉE ====
    statistics["prompt_analysis"] = {
        "unique_prompts": len(set(all_prompts)),
        "total_prompts": len(all_prompts),
        "avg_prompt_length": sum(len(p) for p in all_prompts) / len(all_prompts) if all_prompts else 0
    }
    
    if all_prompts and len(set(all_prompts)) < len(all_prompts) * 0.3:
        warning = "⚠️  Peu de diversité dans les prompts (risque de plagiat)"
        warnings.append(warning)
    
    # ===== AFFICHER RÉSULTATS =====
    print("\n" + "=" * 70)
    print("📋 RÉSULTATS DE VALIDATION")
    print("=" * 70)
    
    if errors:
        print(f"❌ {len(errors)} ERREUR(S) CRITIQUE(S):")
        for error in errors[:5]:
            print(f"  • {error}")
        if len(errors) > 5:
            print(f"  ... et {len(errors) - 5} autres erreurs")
    else:
        print("✅ AUCUNE ERREUR CRITIQUE")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} AVERTISSEMENT(S):")
        for warning in warnings[:3]:
            print(f"  • {warning}")
        if len(warnings) > 3:
            print(f"  ... et {len(warnings) - 3} autres")
    
    # ===== STATISTIQUES DÉTAILLÉES =====
    print("\n📈 STATISTIQUES DÉTAILLÉES:")
    print(f"  Entrées totales: {statistics['total_entries']}")
    
    print("  Répartition par action:")
    for action, count in sorted(statistics['by_action'].items()):
        percentage = (count / statistics['total_entries']) * 100
        print(f"    • {action}: {count} ({percentage:.1f}%)")
    
    print("  Répartition par agent:")
    for agent, count in sorted(statistics['by_agent'].items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / statistics['total_entries']) * 100
        print(f"    • {agent}: {count} ({percentage:.1f}%)")
    
    print("  Répartition par status:")
    for status in ['SUCCESS', 'FAILURE']:
        count = statistics['by_status'].get(status, 0)
        percentage = (count / statistics['total_entries']) * 100 if statistics['total_entries'] > 0 else 0
        icon = {'SUCCESS': '✅', 'FAILURE': '❌'}.get(status, '❓')
        print(f"    {icon} {status}: {count} ({percentage:.1f}%)")
    
    # Calcul du score de qualité
    quality_score = calculate_quality_score(statistics, errors, warnings)
    statistics['quality_score'] = quality_score
    
    print(f"\n🎯 SCORE DE QUALITÉ: {quality_score}/100")
    if quality_score >= 90:
        print("   🟢 EXCELLENT - Prêt pour soumission")
    elif quality_score >= 70:
        print("   🟡 BON - Quelques améliorations possibles")
    elif quality_score >= 50:
        print("   🟠 MOYEN - Corrections recommandées")
    else:
        print("   🔴 FAIBLE - Corrections critiques nécessaires")
    
    # ===== CRITÈRE FINAL: PRÊT POUR ÉVALUATION =====
    is_ready_for_evaluation = len(errors) == 0 and quality_score >= 70
    
    print("\n" + "=" * 70)
    if is_ready_for_evaluation:
        print("🎉 VALIDATION RÉUSSIE!")
        print("   Les logs respectent TOUS les critères du TP.")
        print("   Prêt pour l'évaluation automatisée.")
    else:
        print("🚨 VALIDATION ÉCHOUÉE" if errors else "⚠️  VALIDATION PARTIELLE")
        print("   Corriger les problèmes avant la soumission.")
    
    print("=" * 70)
    
    return is_ready_for_evaluation, errors, statistics


def calculate_quality_score(statistics: Dict, errors: List[str], warnings: List[str]) -> int:
    """
    Calcule un score de qualité sur 100.
    """
    score = 100
    
    # Pénalités
    score -= len(errors) * 10
    score -= len(warnings) * 2
    
    # Bonus
    total_entries = statistics.get('total_entries', 0)
    
    if total_entries >= 50:
        score += 10
    elif total_entries >= 20:
        score += 5
    
    prompt_analysis = statistics.get('prompt_analysis', {})
    unique_prompts = prompt_analysis.get('unique_prompts', 0)
    
    if unique_prompts > 20:
        score += 5
    
    success_count = statistics.get('by_status', {}).get('SUCCESS', 0)
    if total_entries > 0:
        success_rate = success_count / total_entries
        if success_rate >= 0.9:
            score += 5
    
    agents = statistics.get('by_agent', {})
    if len(agents) >= 3:
        score += 5
    
    return max(0, min(100, score))


def save_validation_report(errors: List[str], statistics: Dict[str, Any]) -> str:
    """Sauvegarde un rapport détaillé de validation."""
    report = {
        "validation_date": datetime.now().isoformat(),
        "success": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "statistics": statistics,
        "recommendations": []
    }
    
    # Ajouter recommandations
    if statistics.get("total_entries", 0) < 10:
        report["recommendations"].append("Ajouter plus d'entrées de log (minimum 10 recommandé, 50+ idéal)")
    
    if statistics.get("by_action", {}).get("FIX", 0) == 0:
        report["recommendations"].append("Ajouter des logs d'action FIX (corrections de code)")
    
    if statistics.get("by_action", {}).get("DEBUG", 0) == 0:
        report["recommendations"].append("Ajouter des logs d'action DEBUG (analyse d'erreurs)")
    
    success_count = statistics.get("by_status", {}).get("SUCCESS", 0)
    total = statistics.get("total_entries", 1)
    success_rate = success_count / total if total > 0 else 0
    
    if success_rate < 0.7:
        report["recommendations"].append(f"Améliorer le taux de succès (actuellement {success_rate*100:.1f}%)")
    
    # Sauvegarder
    report_dir = "logs/validation_reports"
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = os.path.join(report_dir, f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Rapport sauvegardé: {report_file}")
    return report_file


def main():
    """Fonction principale."""
    success, errors, statistics = validate_strict_format()
    
    # Sauvegarder le rapport
    report_file = save_validation_report(errors, statistics)
    
    # Créer un résumé
    print(f"\n📋 RÉSUMÉ EXÉCUTIF:")
    print(f"   Fichier validé: {get_log_file_path()}")
    print(f"   Entrées analysées: {statistics.get('total_entries', 0)}")
    print(f"   Agents détectés: {len(statistics.get('by_agent', {}))}")
    success_count = statistics.get('by_status', {}).get('SUCCESS', 0)
    total = statistics.get('total_entries', 0)
    print(f"   Taux de succès: {success_count}/{total} ({success_count/total*100:.1f}%)" if total > 0 else "   Taux de succès: N/A")
    print(f"   Score de qualité: {statistics.get('quality_score', 0)}/100")
    print(f"   Rapport complet: {report_file}")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)