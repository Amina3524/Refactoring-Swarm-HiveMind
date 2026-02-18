"""
VALIDATEUR STRICT DES LOGS - Data Officer (VERSION 2.0)
Verifie que experiment_data.json respecte les criteres du TP.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

# === CONFIGURATIONS ===

AGENT_PATTERNS = {
    'Auditor': ['auditor', 'analyzer', 'analysis'],
    'Fixer': ['fixer', 'corrector', 'fix'],
    'Judge': ['judge', 'validator', 'tester', 'test']
}

VALID_ACTIONS = ['CODE_ANALYSIS', 'CODE_GEN', 'DEBUG', 'FIX']

VALID_MODELS = [
    'gemini-2.5-flash', 'gemini-pro', 'gpt-4', 'gpt-3.5-turbo',
    'claude-3', 'claude-opus', 'test-model'
]

VALID_STATUSES = ['SUCCESS', 'FAILURE']

# === FONCTIONS UTILITAIRES ===

def get_agent_base_name(agent_name: str) -> str:
    """Detecte le type d'agent avec pattern matching."""
    if not agent_name:
        return "UNKNOWN"
    
    name_lower = agent_name.lower()
    
    for base_agent, patterns in AGENT_PATTERNS.items():
        if any(pattern in name_lower for pattern in patterns):
            return base_agent
    
    if '_' in agent_name:
        return agent_name.split('_')[0]
    
    return agent_name


def validate_timestamp(timestamp_str: str) -> bool:
    """Valide un timestamp ISO 8601."""
    try:
        if timestamp_str.endswith('Z'):
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            datetime.fromisoformat(timestamp_str)
        return True
    except (ValueError, AttributeError):
        return False


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


# === FONCTION PRINCIPALE DE VALIDATION ===

def validate_strict_format() -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validation STRICTE selon les criteres du TP.
    Retourne: (is_valid, errors, statistics)
    """
    
    log_file = get_log_file_path()
    
    print("[VALIDATION] VALIDATION STRICTE DES LOGS - VERSION 2.0")
    print("=" * 80)
    print(f"Fichier: {log_file}")
    print(f"Validation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    errors = []
    warnings = []
    statistics = {
        "total_entries": 0,
        "by_agent": {},
        "by_action": {},
        "by_status": {"SUCCESS": 0, "FAILURE": 0},
        "prompt_analysis": {},
        "security_issues": [],
        "max_iteration": 0,
        "agents_detected": set()
    }
    
    # ===== CRITERE 1: FICHIER EXISTE =====
    if not os.path.exists(log_file):
        error_msg = "[ERROR] CRITIQUE: Fichier logs/experiment_data.json introuvable"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    # ===== CRITERE 2: TAILLE MINIMALE =====
    size = os.path.getsize(log_file)
    statistics["file_size"] = size
    print(f"[INFO] Taille fichier: {size} octets")
    
    if size < 100:
        warning = "[WARNING] Fichier tres petit (moins de 100 octets)"
        warnings.append(warning)
        print(warning)
    
    # ===== CRITERE 3: JSON VALIDE =====
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"[ERROR] JSON INVALIDE: {str(e)[:100]}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    except Exception as e:
        error_msg = f"[ERROR] ERREUR LECTURE: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    # Normaliser si dict seul
    if isinstance(logs, dict):
        logs = [logs]
    
    statistics["total_entries"] = len(logs)
    
    if len(logs) == 0:
        error_msg = "[ERROR] Fichier vide - aucune entree de log"
        print(error_msg)
        errors.append(error_msg)
        return False, errors, statistics
    
    print(f"[INFO] Entrees trouvees: {len(logs)}")
    
    # ===== CRITERES OBLIGATOIRES DU TP =====
    required_fields = ['agent', 'model', 'action', 'details', 'timestamp', 'status']
    required_agents = {'Auditor', 'Fixer', 'Judge'}
    
    all_prompts = []
    all_responses = []
    
    # ===== BOUCLE DE VALIDATION =====
    for i, entry in enumerate(logs):
        entry_errors = []
        entry_warnings = []
        
        # === CHAMPS OBLIGATOIRES ===
        for field in required_fields:
            if field not in entry:
                entry_errors.append(f"Champ '{field}' manquant")
        
        # === ACTIONS VALIDES ===
        if 'action' in entry:
            action = entry['action']
            if action not in VALID_ACTIONS:
                entry_errors.append(
                    f"Action invalide: '{action}' "
                    f"(attendus: {VALID_ACTIONS})"
                )
            else:
                statistics["by_action"][action] = \
                    statistics["by_action"].get(action, 0) + 1
        
        # === STATUS VALIDES ===
        if 'status' in entry:
            status = entry['status']
            if status not in VALID_STATUSES:
                entry_errors.append(
                    f"Status invalide: '{status}' (attendus: {VALID_STATUSES})"
                )
            else:
                statistics["by_status"][status] = \
                    statistics["by_status"].get(status, 0) + 1
        
        # === VALIDATION MODEL ===
        if 'model' in entry:
            model = entry.get('model')
            if not model:
                entry_errors.append("'model' ne peut pas etre vide")
            elif not isinstance(model, str):
                entry_errors.append("'model' doit etre un string")
        
        # === AGENT VALIDE ===
        if 'agent' in entry:
            agent = entry['agent']
            if not agent:
                entry_errors.append("'agent' ne peut pas etre vide")
            elif not isinstance(agent, str):
                entry_errors.append("'agent' doit etre un string")
            else:
                statistics["by_agent"][agent] = \
                    statistics["by_agent"].get(agent, 0) + 1
                base_name = get_agent_base_name(agent)
                statistics["agents_detected"].add(base_name)
        
        # === DETAILS (Bloc principal) ===
        if 'details' in entry:
            details = entry['details']
            
            if not isinstance(details, dict):
                entry_errors.append("'details' doit etre un dictionnaire")
                if entry_errors:
                    errors.append(f"Entree {i}: {'; '.join(entry_errors)}")
                if entry_warnings:
                    warnings.extend([f"Entree {i}: {w}" for w in entry_warnings])
                continue
            
            # Validation conditionnelle selon action
            action = entry.get('action', '')
            
            # Pour ANALYSIS, FIX, GENERATION : input_prompt OBLIGATOIRE
            if action in VALID_ACTIONS:
                if 'input_prompt' not in details:
                    entry_errors.append(
                        f"'input_prompt' OBLIGATOIRE dans details pour {action}"
                    )
                elif not details.get('input_prompt'):
                    entry_errors.append(
                        f"'input_prompt' est vide pour {action}"
                    )
                else:
                    prompt = str(details['input_prompt']).strip()
                    all_prompts.append(prompt[:200])
                    if len(prompt) < 15:
                        entry_warnings.append(
                            f"'input_prompt' tres court ({len(prompt)} chars)"
                        )
                
                # output_response OBLIGATOIRE
                if 'output_response' not in details:
                    entry_errors.append(
                        f"'output_response' OBLIGATOIRE dans details pour {action}"
                    )
                elif not details.get('output_response'):
                    entry_errors.append(
                        f"'output_response' est vide pour {action}"
                    )
                else:
                    response = str(details['output_response']).strip()
                    all_responses.append(response[:200])
                    if len(response) < 5:
                        entry_warnings.append(
                            f"'output_response' tres court ({len(response)} chars)"
                        )
            
            # === DETECTION ITERATION COUNT (TP Requirement) ===
            if 'metadata' in details:
                metadata = details.get('metadata')
                if isinstance(metadata, dict) and 'iteration' in metadata:
                    iteration = metadata.get('iteration', 0)
                    
                    if not isinstance(iteration, int):
                        entry_warnings.append(
                            f"'metadata.iteration' doit etre entier"
                        )
                    elif iteration > 10:
                        entry_errors.append(
                            f"Iteration {iteration} depasse le maximum (10)"
                        )
                    
                    statistics["max_iteration"] = max(
                        statistics.get("max_iteration", 0), iteration
                    )
            
            # === SECURITE SANDBOX ===
            for key, value in details.items():
                if isinstance(value, str) and '..' in value:
                    if 'sandbox' not in value.lower():
                        if 'test' not in value.lower():
                            security_issue = f"Chemin potentiel hors sandbox: {value[:40]}..."
                            if security_issue not in statistics["security_issues"]:
                                statistics["security_issues"].append(security_issue)
        
        # === TIMESTAMP ISO 8601 ===
        if 'timestamp' in entry:
            timestamp = entry['timestamp']
            if not validate_timestamp(timestamp):
                entry_errors.append(
                    f"Format timestamp invalide: '{timestamp}' "
                    f"(doit etre ISO 8601)"
                )
        
        if entry_errors:
            errors.append(f"Entree {i}: {'; '.join(entry_errors)}")
        if entry_warnings:
            warnings.extend([f"Entree {i}: {w}" for w in entry_warnings])
    
    # ===== POST-PROCESSING =====
    
    # === AGENTS MINIMUM REQUIS ===
    agents_found = statistics["agents_detected"]
    missing_agents = required_agents - agents_found
    
    if missing_agents:
        error_msg = f"Agents requis manquants: {', '.join(missing_agents)}"
        print(f"[ERROR] {error_msg}")
        errors.append(error_msg)
    else:
        print(f"[SUCCESS] Tous les agents requis detectes: {', '.join(sorted(agents_found))}")
    
    # === SUFFISAMMENT D'ENTREES ===
    if len(logs) < 5:
        warning_msg = f"[WARNING] Peu d'entrees ({len(logs)}). Minimum: 5"
        warnings.append(warning_msg)
        print(warning_msg)
    
    # === ANALYSE PROMPTS ===
    statistics["prompt_analysis"] = {
        "unique_prompts": len(set(all_prompts)),
        "total_prompts": len(all_prompts),
        "unique_responses": len(set(all_responses)),
        "total_responses": len(all_responses)
    }
    
    # ===== AFFICHAGE RESULTATS =====
    print("\n" + "=" * 80)
    print("RESULTATS DE VALIDATION")
    print("=" * 80)
    
    if errors:
        print(f"[ERROR] {len(errors)} ERREUR(S) CRITIQUE(S):")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... et {len(errors) - 5} autres erreurs")
    else:
        print("[SUCCESS] AUCUNE ERREUR CRITIQUE DETECTEE")
    
    if warnings:
        print(f"\n[WARNING] {len(warnings)} AVERTISSEMENT(S):")
        for warning in warnings[:5]:
            print(f"  - {warning}")
        if len(warnings) > 5:
            print(f"  ... et {len(warnings) - 5} autres")
    
    # === STATISTIQUES ===
    print("\nSTATISTIQUES DETAILLEES:")
    print(f"  Entrees totales: {statistics['total_entries']}")
    
    if statistics['by_action']:
        print("  Repartition par action:")
        for action, count in sorted(statistics['by_action'].items()):
            percentage = (count / statistics['total_entries']) * 100
            print(f"    - {action}: {count} ({percentage:.1f}%)")
    
    if statistics['by_agent']:
        print("  Repartition par agent:")
        for agent, count in sorted(
            statistics['by_agent'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]:
            percentage = (count / statistics['total_entries']) * 100
            print(f"    - {agent}: {count} ({percentage:.1f}%)")
    
    print("  Repartition par status:")
    for status in ['SUCCESS', 'FAILURE']:
        count = statistics['by_status'].get(status, 0)
        percentage = (count / statistics['total_entries']) * 100 \
                     if statistics['total_entries'] > 0 else 0
        print(f"    - {status}: {count} ({percentage:.1f}%)")
    
    # === SCORE QUALITE ===
    quality_score = calculate_quality_score(statistics, errors, warnings)
    statistics['quality_score'] = quality_score
    
    print(f"\nSCORE DE QUALITE: {quality_score}/100")
    if quality_score >= 90:
        print("   [EXCELLENT] Pret pour soumission")
    elif quality_score >= 70:
        print("   [BON] Quelques ameliorations possibles")
    elif quality_score >= 50:
        print("   [MOYEN] Corrections recommandees")
    else:
        print("   [FAIBLE] Corrections critiques necessaires")
    
    # === VALIDATION FINALE ===
    is_ready_for_evaluation = len(errors) == 0 and quality_score >= 70
    
    print("\n" + "=" * 80)
    if is_ready_for_evaluation:
        print("[SUCCESS] VALIDATION REUSSIE!")
        print("   Les logs respectent TOUS les criteres du TP.")
        print("   Pret pour l'evaluation automatisee.")
    else:
        if errors:
            print("[ERROR] VALIDATION ECHOUEE")
            print("   Erreurs critiques detectees.")
        else:
            print("[WARNING] VALIDATION PARTIELLE")
            print("   Score < 70. Corriger les warnings.")
        print("   -> Corriger les problemes avant la soumission.")
    
    print("=" * 80)
    
    # Convertir set en list pour serialisation
    statistics["agents_detected"] = list(statistics["agents_detected"])
    
    return is_ready_for_evaluation, errors, statistics


def calculate_quality_score(statistics: Dict, errors: List[str], warnings: List[str]) -> int:
    """Calcule un score de qualite sur 100."""
    score = 100
    
    score -= len(errors) * 15
    score -= len(warnings) * 2
    
    total_entries = statistics.get('total_entries', 0)
    
    if total_entries >= 100:
        score += 15
    elif total_entries >= 50:
        score += 10
    elif total_entries >= 20:
        score += 5
    
    agents = statistics.get('by_agent', {})
    if len(agents) >= 5:
        score += 10
    elif len(agents) >= 3:
        score += 5
    
    max_iteration = statistics.get('max_iteration', 0)
    if max_iteration > 0 and max_iteration <= 10:
        score += 10
    elif max_iteration > 10:
        score -= 20
    
    return max(0, min(100, score))


def main():
    """Fonction principale."""
    success, errors, statistics = validate_strict_format()
    
    print(f"\nRESUME EXECUTIF:")
    print(f"   Fichier valide: {get_log_file_path()}")
    print(f"   Entrees analysees: {statistics.get('total_entries', 0)}")
    print(f"   Agents detectes: {len(statistics.get('by_agent', {}))}")
    success_count = statistics.get('by_status', {}).get('SUCCESS', 0)
    total = statistics.get('total_entries', 0)
    if total > 0:
        print(f"   Taux de succes: {success_count}/{total} ({success_count/total*100:.1f}%)")
    print(f"   Score de qualite: {statistics.get('quality_score', 0)}/100")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrompue")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)