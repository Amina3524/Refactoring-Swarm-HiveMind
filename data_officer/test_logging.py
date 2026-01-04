"""
TESTER DU LOGGER - Data Officer
Teste toutes les fonctionnalités du logging.
"""

import os
import sys
import json
from datetime import datetime

# Configuration des chemins
def setup_import_path():
    """Configure le chemin d'import correctement."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, ".."))
    
    # Ajouter à sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    return project_root


def test_logger_comprehensive():
    """
    Test complet du logger avec tous les cas possibles.
    """
    print("🧪 TEST COMPLET DU LOGGER")
    print("=" * 60)
    
    project_root = setup_import_path()
    print(f"📁 Racine projet: {project_root}")
    print(f"📁 Dossier actuel: {os.getcwd()}")
    
    try:
        from src.utils.logger import log_experiment, ActionType
        print("✅ Import réussi depuis src.utils.logger")
    except ImportError as e:
        print(f"❌ Import échoué: {e}")
        print("\n💡 Essayez d'exécuter depuis la racine du projet:")
        print("   cd /chemin/vers/projet")
        print("   python data_officer/logger_tester.py")
        sys.exit(1)
    
    # Nettoyer l'ancien fichier de test
    test_log_file = "logs/test_experiment_data.json"
    if os.path.exists(test_log_file):
        backup = f"{test_log_file}.backup"
        os.rename(test_log_file, backup)
        print(f"📁 Ancien fichier sauvegardé: {backup}")
    
    tests = [
        {
            "name": "ANALYSIS - Audit simple",
            "agent": "Auditor_Agent",
            "action": ActionType.ANALYSIS,
            "details": {
                "input_prompt": "Analyse ce code Python et identifie tous les bugs",
                "output_response": "J'ai trouvé 3 bugs: 1) Division par zéro, 2) Variable non initialisée, 3) Pas de gestion d'erreur",
                "file_analyzed": "buggy_code.py",
                "issues_found": 3,
                "pylint_score": 5.2
            },
            "status": "SUCCESS"
        },
        {
            "name": "FIX - Correction de bug",
            "agent": "Fixer_Agent",
            "action": ActionType.FIX,
            "details": {
                "input_prompt": "Corrige la division par zéro dans cette fonction",
                "output_response": "J'ai ajouté une vérification: if b != 0: return a/b else: return 0",
                "file_fixed": "buggy_code.py",
                "changes_made": ["Added zero check", "Added error handling"],
                "old_code": "return a/b",
                "new_code": "if b != 0: return a/b else: return 0"
            },
            "status": "SUCCESS"
        },
        {
            "name": "DEBUG - Analyse d'erreur",
            "agent": "Judge_Agent",
            "action": ActionType.DEBUG,
            "details": {
                "input_prompt": "Debug cette erreur: ZeroDivisionError: division by zero",
                "output_response": "L'erreur vient de la ligne 15: division par zéro sans vérification",
                "error_type": "ZeroDivisionError",
                "stack_trace": "File 'test.py', line 15, in calculate",
                "solution": "Ajouter une vérification avant la division"
            },
            "status": "SUCCESS"
        },
        {
            "name": "GENERATION - Création de tests",
            "agent": "Toolsmith_Agent",
            "action": ActionType.GENERATION,
            "details": {
                "input_prompt": "Génère des tests unitaires pour la fonction calculate_average",
                "output_response": "J'ai créé 5 tests: test_normal_case, test_empty_list, test_negative_numbers, etc.",
                "tests_created": 5,
                "file_generated": "test_average.py",
                "coverage_estimated": "85%"
            },
            "status": "SUCCESS"
        },
        {
            "name": "ÉCHEC - Test d'erreur",
            "agent": "Auditor_Agent",
            "action": ActionType.ANALYSIS,
            "details": {
                "input_prompt": "Analyse ce fichier inexistant",
                "output_response": "Erreur: Fichier non trouvé",
                "file_analyzed": "nonexistent.py",
                "error": "FileNotFoundError"
            },
            "status": "FAILURE"
        }
    ]
    
    print(f"\n📋 EXÉCUTION DE {len(tests)} TESTS...")
    print("-" * 60)
    
    results = {"passed": 0, "failed": 0, "errors": []}
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] {test['name']}")
        print(f"   Agent: {test['agent']}")
        print(f"   Action: {test['action'].value}")
        
        try:
            log_experiment(
                agent_name=test['agent'],
                model_used="gemini-1.5-flash-test",
                action=test['action'],
                details=test['details'],
                status=test['status']
            )
            print("   ✅ PASS")
            results["passed"] += 1
        except ValueError as e:
            print(f"   ❌ VALUE ERROR: {str(e)[:50]}...")
            results["failed"] += 1
            results["errors"].append(f"Test {i}: {str(e)}")
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)[:50]}...")
            results["failed"] += 1
            results["errors"].append(f"Test {i}: {type(e).__name__}: {str(e)}")
    
    # Vérifier que le fichier a été créé
    print("\n" + "=" * 60)
    print("📁 VÉRIFICATION DU FICHIER DE LOGS")
    print("=" * 60)
    
    actual_log_file = "logs/experiment_data.json"
    
    if os.path.exists(actual_log_file):
        try:
            with open(actual_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            print(f"✅ Fichier trouvé: {actual_log_file}")
            print(f"📊 Entrées loguées: {len(logs)}")
            
            # Vérifier que nos tests y sont
            test_entries = [log for log in logs if log.get('model') == 'gemini-1.5-flash-test']
            print(f"📝 Entrées de test: {len(test_entries)}/{len(tests)}")
            
            if len(test_entries) == len(tests):
                print("🎉 TOUS LES TESTS SONT DANS LE FICHIER!")
            else:
                print(f"⚠️  Manque {len(tests) - len(test_entries)} entrées")
                
        except json.JSONDecodeError as e:
            print(f"❌ Fichier JSON corrompu: {e}")
        except Exception as e:
            print(f"❌ Erreur de lecture: {e}")
    else:
        print(f"❌ Fichier non trouvé: {actual_log_file}")
        print("💡 Le logger n'a peut-être pas créé le fichier")
    
    # Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT FINAL DES TESTS")
    print("=" * 60)
    print(f"✅ Tests passés: {results['passed']}/{len(tests)}")
    print(f"❌ Tests échoués: {results['failed']}/{len(tests)}")
    
    if results['errors']:
        print("\n🚨 ERREURS DÉTECTÉES:")
        for error in results['errors'][:3]:  # Afficher max 3 erreurs
            print(f"  • {error}")
        if len(results['errors']) > 3:
            print(f"  ... et {len(results['errors']) - 3} autres")
    
    success_rate = (results['passed'] / len(tests)) * 100
    print(f"\n📈 Taux de succès: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 LOGGER VALIDÉ AVEC SUCCÈS!")
    elif success_rate >= 80:
        print("⚠️  LOGGER FONCTIONNEL MAIS AVEC QUELQUES PROBLÈMES")
    else:
        print("🚨 LOGGER PRÉSENTE DES PROBLÈMES GRAVES")
    
    return results['failed'] == 0


if __name__ == "__main__":
    success = test_logger_comprehensive()
    sys.exit(0 if success else 1)