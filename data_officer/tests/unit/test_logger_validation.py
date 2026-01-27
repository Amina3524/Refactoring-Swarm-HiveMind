"""
TESTS CRITIQUES pour Data Officer - VERSION CORRIGÉE
"""

import pytest
import json
import os
import tempfile
import sys
import importlib.util

# === CONFIGURATION DES IMPORTS ===
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# 1. Importer TON validateur (dans data_officer/)
sys.path.append(os.path.join(project_root, "data_officer"))

try:
    from validate_logs import validate_strict_format, calculate_quality_score
    VALIDATOR_AVAILABLE = True
    print("✅ Validateur Data Officer importé")
except ImportError as e:
    print(f"❌ Impossible d'importer validate_logs: {e}")
    VALIDATOR_AVAILABLE = False

# 2. Essayer d'importer le logger officiel
src_path = os.path.join(project_root, "src")
if os.path.exists(src_path):
    sys.path.insert(0, src_path)
    try:
        from utils.logger import log_experiment, ActionType
        OFFICIAL_LOGGER_AVAILABLE = True
        print("✅ Logger officiel importé")
    except ImportError:
        OFFICIAL_LOGGER_AVAILABLE = False
else:
    OFFICIAL_LOGGER_AVAILABLE = False

if not VALIDATOR_AVAILABLE:
    pytestmark = pytest.mark.skip(reason="Validateur non disponible")


class TestLoggerValidation:
    """Tests de validation STRICTE des logs selon critères TP"""
    
    def test_input_prompt_mandatory(self):
        """CRITIQUE: Vérifie que input_prompt est obligatoire"""
        test_logs = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "agent": "Auditor",
                "model": "gemini",
                "action": "ANALYSIS",
                "details": {
                    # MANQUE input_prompt → DOIT ÉCHOUER
                    "output_response": "Test response"
                },
                "status": "SUCCESS"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_logs, f)
            temp_file = f.name
        
        # Mock pour utiliser notre fichier
        import validate_logs
        original_get_path = validate_logs.get_log_file_path
        validate_logs.get_log_file_path = lambda: temp_file
        
        try:
            is_valid, errors, stats = validate_strict_format()
            
            # Doit échouer car input_prompt manquant
            assert is_valid == False, f"Devrait échouer mais valid={is_valid}"
            assert any("input_prompt" in error.lower() for error in errors), f"Erreurs: {errors}"
            
        finally:
            # Restaurer
            validate_logs.get_log_file_path = original_get_path
            os.unlink(temp_file)
    
    def test_output_response_always_mandatory(self):
        """CRITIQUE: output_response est TOUJOURS obligatoire"""
        test_logs = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "agent": "Auditor",
                "model": "gemini",
                "action": "DEBUG",
                "details": {
                    "input_prompt": "Test",
                    # MANQUE output_response → DOIT ÉCHOUER
                },
                "status": "SUCCESS"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_logs, f)
            temp_file = f.name
        
        import validate_logs
        original_get_path = validate_logs.get_log_file_path
        validate_logs.get_log_file_path = lambda: temp_file
        
        try:
            is_valid, errors, stats = validate_strict_format()
            
            assert is_valid == False
            assert any("output_response" in error.lower() for error in errors)
        
        finally:
            validate_logs.get_log_file_path = original_get_path
            os.unlink(temp_file)
    
    def test_valid_log_passes_validation(self):
        """Test qu'un log valide passe la validation"""
        test_logs = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "agent": "Auditor_Agent",
                "model": "gemini-2.5-flash",
                "action": "ANALYSIS",
                "details": {
                    "input_prompt": "Analyse ce code Python",
                    "output_response": "J'ai trouvé des problèmes",
                    "file_analyzed": "test.py",
                    "issues_found": 2
                },
                "status": "SUCCESS"
            },
            {
                "timestamp": "2024-01-01T10:01:00",
                "agent": "Fixer_Agent",
                "model": "gemini-2.5-flash",
                "action": "FIX",
                "details": {
                    "input_prompt": "Corrige les problèmes",
                    "output_response": "Problèmes corrigés",
                    "file_modified": "test.py",
                    "changes_made": "Ajout docstring, correction syntaxe"
                },
                "status": "SUCCESS"
            },
            {
            "timestamp": "2024-01-01T10:02:00",
            "agent": "Judge_Agent",
            "model": "gemini-2.5-flash",
            "action": "DEBUG",  # Ou GENERATION pour les tests
            "details": {
                "input_prompt": "Vérifie si les tests passent",
                "output_response": "Tests exécutés avec succès",
                "test_results": "3 passed, 0 failed"
            },
            "status": "SUCCESS"
            }
       ]
    
        
        
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_logs, f)
            temp_file = f.name

        import validate_logs
        original_get_path = validate_logs.get_log_file_path
        validate_logs.get_log_file_path = lambda: temp_file

        try:
            is_valid, errors, stats = validate_strict_format()

            assert is_valid == True, f"Log valide mais erreurs: {errors}"
            assert stats["total_entries"] == 3  # ← CORRECTION ICI !
            
            # Optionnel: vérifier que les 3 agents sont là
            assert "Auditor_Agent" in stats.get("by_agent", {})
            assert "Fixer_Agent" in stats.get("by_agent", {})
            assert "Judge_Agent" in stats.get("by_agent", {})

        finally:
            # Restaurer
            validate_logs.get_log_file_path = original_get_path
            os.unlink(temp_file)
    
    def test_quality_score_calculation(self):
        """Test le calcul du score de qualité"""
        stats = {
            "total_entries": 50,
            "by_status": {"SUCCESS": 45, "FAILURE": 5},
            "by_agent": {"Auditor": 20, "Fixer": 20, "Judge": 10},
            "prompt_analysis": {"unique_prompts": 30}
        }
        
        score = calculate_quality_score(stats, errors=[], warnings=[])
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        print(f"✅ Score calculé: {score}")
    
    def test_detect_empty_log_file(self):
        """Détection d'un fichier de logs vide"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)  # FICHIER VIDE
            temp_file = f.name
        
        import validate_logs
        original_get_path = validate_logs.get_log_file_path
        validate_logs.get_log_file_path = lambda: temp_file
        
        try:
            is_valid, errors, stats = validate_strict_format()
            
            assert is_valid == False
            assert any("vide" in error.lower() or "empty" in error.lower() for error in errors)
        
        finally:
            validate_logs.get_log_file_path = original_get_path
            os.unlink(temp_file)


# Tests qui ne dépendent pas du validateur
class TestDataOfficerBasics:
    """Tests basiques du rôle Data Officer"""
    
    def test_json_validation(self):
        """Test la validation JSON de base"""
        valid_json = '{"test": "value", "number": 123}'
        invalid_json = '{"test": "value", number: 123}'  # Pas de guillemets
        
        # Valide
        data = json.loads(valid_json)
        assert data["test"] == "value"
        
        # Invalide
        try:
            json.loads(invalid_json)
            pytest.fail("Devrait lever JSONDecodeError")
        except json.JSONDecodeError:
            pass  # OK
    
    def test_log_file_paths(self):
        """Test les chemins de fichiers de logs"""
        # Créer une structure de test
        test_dir = tempfile.mkdtemp()
        log_file = os.path.join(test_dir, "experiment_data.json")
        
        # Créer un log vide
        with open(log_file, 'w') as f:
            json.dump([], f)
        
        assert os.path.exists(log_file)
        
        # Nettoyer
        os.unlink(log_file)
        os.rmdir(test_dir)
    
    def test_required_fields_check(self):
        """Vérifie les champs requis manuellement"""
        required_fields = ["timestamp", "agent", "action", "details", "status"]
        
        # Entrée complète
        complete_entry = {field: "test" for field in required_fields}
        complete_entry["details"] = {"input_prompt": "test", "output_response": "test"}
        
        for field in required_fields:
            assert field in complete_entry
        
        # Entrée incomplète
        incomplete_entry = {"timestamp": "test", "agent": "test"}
        missing_fields = [f for f in required_fields if f not in incomplete_entry]
        
        assert len(missing_fields) > 0
        print(f"✅ Champs manquants détectés: {missing_fields}")