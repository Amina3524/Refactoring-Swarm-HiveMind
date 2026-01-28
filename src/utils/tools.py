import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from src.utils.logger import log_experiment, ActionType  


TOOLSMITH_MODEL = "gemini-2.0-flash"
class GardeSecurite:
    """Empêche les agents d'écrire en dehors du sandbox."""
    
    def __init__(self, chemin_sandbox: str = "sandbox"):
        self.chemin_sandbox = os.path.abspath(chemin_sandbox)
        os.makedirs(self.chemin_sandbox, exist_ok=True)
    
    def chemin_est_securise(self, chemin_cible: str) -> bool:
        """Vérifie que le chemin est dans le sandbox."""
        try:
            chemin_absolu_cible = os.path.abspath(chemin_cible)
            chemin_absolu_sandbox = os.path.abspath(self.chemin_sandbox)
            return chemin_absolu_cible.startswith(chemin_absolu_sandbox + os.sep) or chemin_absolu_cible == chemin_absolu_sandbox
        except Exception:
            return False
    
    def obtenir_chemin_securise(self, chemin_relatif: str) -> str:
        """Convertit un chemin relatif en chemin absolu sécurisé."""
        # Éliminer les tentatives de traversal (../)
        chemin_nettoye = os.path.normpath(chemin_relatif)
        
        # Reconstruire dans le sandbox
        chemin_complet = os.path.join(self.chemin_sandbox, chemin_nettoye)
        
        # Vérifier la sécurité
        if not self.chemin_est_securise(chemin_complet):
            raise ErreurSecurite(f"Tentative d'accès hors sandbox: {chemin_relatif}")
        
        return chemin_complet


class ErreurSecurite(Exception):
    """Exception pour les violations de sécurité."""
    pass


class OutilsCode:
    """Outils de base pour la manipulation de code."""
    
    def __init__(self, chemin_sandbox: str = "sandbox"):
        self.securite = GardeSecurite(chemin_sandbox)
    
    # ---------- LECTURE ----------
    def lire_fichier(self, chemin_fichier: str) -> str:
        """
        Lit un fichier et retourne son contenu.
        
        Args:
            chemin_fichier: Chemin relatif au sandbox
            
        Returns:
            Contenu du fichier en string
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ErreurSecurite: Si le chemin n'est pas dans le sandbox
        """
        try:
            chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
            
            if not os.path.isfile(chemin_securise):
                raise FileNotFoundError(f"Fichier non trouvé: {chemin_fichier}")
            
            # Essayer différents encodages
            encodages = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            for encodage in encodages:
                try:
                    with open(chemin_securise, 'r', encoding=encodage) as f:
                        contenu = f.read()
                    
                    # LOG SUCCÈS
                    log_experiment(
                        agent_name="AuditorAgent",
                        model_used=TOOLSMITH_MODEL,
                        action=ActionType.ANALYSIS,
                        details={
                            "input_prompt": f"Lecture du fichier {chemin_fichier}",
                            "output_response": f"Fichier lu avec succès: {len(contenu)} caractères"
                        },
                        status="SUCCESS"
                    )
                    
                    return contenu
                except UnicodeDecodeError:
                    continue
            
            raise UnicodeDecodeError(f"Impossible de décoder le fichier: {chemin_fichier}")
            
        except Exception as e:
            # LOG ERREUR
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Lecture du fichier {chemin_fichier}",
                    "output_response": f"Erreur: {str(e)}"
                    
                },
                status="FAILURE"
            )
            raise
    
    # ---------- ÉCRITURE ----------
    def ecrire_fichier(self, chemin_fichier: str, contenu: str, sauvegarde: bool = True) -> Dict[str, Any]:
        """
        Écrit dans un fichier et retourne un statut structuré.
        
        Args:
            chemin_fichier: Chemin relatif au sandbox
            contenu: Contenu à écrire
            sauvegarde: Créer une sauvegarde du fichier original
            
        Returns:
            Dictionnaire avec le statut de l'opération
            
        Raises:
            ErreurSecurite: Si le chemin n'est pas dans le sandbox
        """
        try:
            chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
            
            # Créer les dossiers parents si nécessaire
            dossier_parent = os.path.dirname(chemin_securise)
            if dossier_parent:
                os.makedirs(dossier_parent, exist_ok=True)
            
            # Sauvegarde du fichier original
            chemin_sauvegarde = None
            if sauvegarde and os.path.exists(chemin_securise):
                chemin_sauvegarde = f"{chemin_securise}.bak"
                with open(chemin_securise, 'r', encoding='utf-8') as src:
                    with open(chemin_sauvegarde, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Écrire le nouveau contenu
            with open(chemin_securise, 'w', encoding='utf-8') as f:
                f.write(contenu)
            
            # Vérifier l'écriture
            with open(chemin_securise, 'r', encoding='utf-8') as f:
                contenu_verifie = f.read()
            
            succes = contenu_verifie == contenu
            
            # LOG RÉSULTAT
            log_experiment(
                agent_name="FixerAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.FIX,
                details={
                    "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                    "output_response": f"Écriture {'réussie' if succes else 'échouée'}: {len(contenu)} caractères"
                },
                status="SUCCESS" if succes else "FAILURE"
            )
            
            resultat = {
                "succes": succes,
                "chemin": chemin_fichier,
                "chemin_absolu": chemin_securise,
                "taille": len(contenu),
                "sauvegarde_creee": chemin_sauvegarde is not None,
                "chemin_sauvegarde": chemin_sauvegarde,
                "message": "Écriture réussie" if succes else "Écriture vérifiée mais contenu différent"
            }
            
            return resultat
            
        except Exception as e:
            # LOG ERREUR
            log_experiment(
                agent_name="FixerAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.FIX,
                details={
                    "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                    "output_response": f"Erreur: {str(e)}"
                },
                status="FAILURE"
            )
            raise
    
    # ---------- ANALYSE PYLINT ----------
    def analyser_pylint(self, chemin_fichier: str) -> Dict[str, Any]:
        """
        Exécute Pylint sur un fichier Python.
        
        Args:
            chemin_fichier: Chemin relatif au sandbox
            
        Returns:
            Dictionnaire avec les résultats de l'analyse
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si ce n'est pas un fichier Python
        """
        try:
            chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
            
            if not os.path.exists(chemin_securise):
                raise FileNotFoundError(f"Fichier non trouvé: {chemin_fichier}")
            
            if not chemin_securise.endswith('.py'):
                raise ValueError(f"Ce n'est pas un fichier Python: {chemin_fichier}")
            
            # LOG DÉBUT
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                    "output_response": "Début de l'analyse Pylint"
                },
                status="SUCCESS"
            )
            
            # Exécuter Pylint en format JSON
            resultat = subprocess.run(
                ["pylint", "--output-format=json", chemin_securise],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if resultat.returncode in [0, 1, 2, 4, 8, 16, 32]:  # Codes de sortie acceptables
                try:
                    problemes = json.loads(resultat.stdout) if resultat.stdout else []
                    
                    # Calculer les statistiques
                    erreurs = sum(1 for p in problemes if p.get("type") == "error")
                    avertissements = sum(1 for p in problemes if p.get("type") == "warning")
                    conventions = sum(1 for p in problemes if p.get("type") == "convention")
                    refactor = sum(1 for p in problemes if p.get("type") == "refactor")
                    
                    # Calculer un score (10 = parfait, 0 = très mauvais)
                    score = 10.0
                    score -= erreurs * 1.0
                    score -= avertissements * 0.5
                    score -= conventions * 0.1
                    score -= refactor * 0.2
                    score = max(0.0, min(10.0, score))
                    
                    resultat_dict = {
                        "succes": True,
                        "chemin_fichier": chemin_fichier,
                        "code_sortie": resultat.returncode,
                        "score_pylint": round(score, 2),
                        "problemes": problemes[:20],  # Limiter à 20 problèmes pour éviter les logs trop longs
                        "statistiques": {
                            "total": len(problemes),
                            "erreurs": erreurs,
                            "avertissements": avertissements,
                            "conventions": conventions,
                            "refactor": refactor
                        },
                        "sortie_brute": resultat.stdout[:500] if resultat.stdout else "",
                        "erreur_brute": resultat.stderr[:500] if resultat.stderr else ""
                    }
                    
                    # LOG SUCCÈS
                    log_experiment(
                        agent_name="AuditorAgent",
                        model_used=TOOLSMITH_MODEL,
                        action=ActionType.ANALYSIS,
                        details={
                            "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                            "output_response": f"Analyse terminée. Score: {score:.2f}/10, Problèmes: {len(problemes)}"
                        },
                        status="SUCCESS"
                    )
                    
                    return resultat_dict
                    
                except json.JSONDecodeError:
                    resultat_dict = {
                        "succes": False,
                        "erreur": "Impossible de parser la sortie JSON de Pylint",
                        "sortie_brute": resultat.stdout[:500]
                    }
                    
                    # LOG ERREUR JSON
                    log_experiment(
                        agent_name="AuditorAgent",
                        model_used=TOOLSMITH_MODEL,
                        action=ActionType.ANALYSIS,
                        details={
                            "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                            "output_response": "Erreur: Impossible de parser JSON Pylint"
                        },
                        status="FAILURE"
                    )
                    
                    return resultat_dict
                    
            else:
                resultat_dict = {
                    "succes": False,
                    "erreur": f"Pylint a échoué avec le code {resultat.returncode}",
                    "code_sortie": resultat.returncode,
                    "erreur_brute": resultat.stderr[:500]
                }
                
                # LOG ERREUR CODE
                log_experiment(
                    agent_name="AuditorAgent",
                    model_used=TOOLSMITH_MODEL,
                    action=ActionType.ANALYSIS,
                    details={
                        "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                        "output_response": f"Erreur Pylint: code {resultat.returncode}"
                    },
                    status="FAILURE"
                )
                
                return resultat_dict
                
        except subprocess.TimeoutExpired:
            resultat_dict = {
                "succes": False,
                "erreur": "Timeout Pylint (30 secondes)",
                "chemin_fichier": chemin_fichier
            }
            
            # LOG TIMEOUT
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                    "output_response": "Timeout: analyse trop longue (>30s)"
                },
                status="FAILURE"
            )
            
            return resultat_dict
            
        except FileNotFoundError:
            resultat_dict = {
                "succes": False,
                "erreur": "Pylint n'est pas installé ou non trouvé dans PATH"
            }
            
            # LOG FICHIER NON TROUVÉ
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                    "output_response": "Pylint non trouvé dans PATH"
                },
                status="FAILURE"
            )
            
            return resultat_dict
            
        except Exception as e:
            resultat_dict = {
                "succes": False,
                "erreur": f"Exception inattendue: {str(e)}",
                "chemin_fichier": chemin_fichier
            }
            
            # LOG EXCEPTION GÉNÉRIQUE
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse Pylint du fichier {chemin_fichier}",
                    "output_response": f"Erreur inattendue: {str(e)}"
                },
                status="FAILURE"
            )
            
            return resultat_dict
    
    # ---------- EXÉCUTION PYTEST ----------
    def executer_pytest(self, chemin_test: str = "") -> Dict[str, Any]:
        """
        Exécute Pytest sur un fichier ou dossier de tests.
        
        Args:
            chemin_test: Chemin relatif au sandbox (fichier .py ou dossier)
            
        Returns:
            Dictionnaire avec les résultats des tests
        """
        try:
            chemin_securise = self.securite.obtenir_chemin_securise(chemin_test) if chemin_test else self.securite.chemin_sandbox
            
            # LOG DÉBUT
            log_experiment(
                agent_name="JudgeAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.DEBUG,
                details={
                    "input_prompt": f"Exécution Pytest sur {chemin_test if chemin_test else 'sandbox'}",
                    "output_response": "Début des tests Pytest"
                },
                status="SUCCESS"
            )
            
            # Déterminer les arguments Pytest
            if os.path.isfile(chemin_securise) and chemin_securise.endswith('.py'):
                args_pytest = ["pytest", chemin_securise, "-v"]
            elif os.path.isdir(chemin_securise):
                args_pytest = ["pytest", chemin_securise, "-v"]
            else:
                args_pytest = ["pytest", self.securite.chemin_sandbox, "-v"]
            
            # Exécuter Pytest
            resultat = subprocess.run(
                args_pytest,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Analyser la sortie
            sortie = resultat.stdout
            
            # Extraire les statistiques (recherche dans la sortie)
            tests_reussis = 0
            tests_echoues = 0
            tests_ignores = 0
            
            for ligne in sortie.split('\n'):
                if "passed" in ligne and "failed" in ligne:
                    # Format typique: "3 passed, 1 failed in 0.12s"
                    parties = ligne.split()
                    for i, partie in enumerate(parties):
                        if partie.isdigit():
                            if i > 0 and "passed" in parties[i-1]:
                                tests_reussis = int(partie)
                            elif i > 0 and "failed" in parties[i-1]:
                                tests_echoues = int(partie)
                            elif i > 0 and "skipped" in parties[i-1]:
                                tests_ignores = int(partie)
                    break
            
            total_tests = tests_reussis + tests_echoues + tests_ignores
            succes_global = resultat.returncode == 0
            
            resultat_dict = {
                "succes": succes_global,
                "code_sortie": resultat.returncode,
                "tests_reussis": tests_reussis,
                "tests_echoues": tests_echoues,
                "tests_ignores": tests_ignores,
                "total_tests": total_tests,
                "sortie_complete": sortie[:1000],  # Limiter la taille
                "erreur": resultat.stderr[:500] if resultat.stderr else ""
            }
            
            # LOG RÉSULTAT
            log_experiment(
                agent_name="JudgeAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.DEBUG,
                details={
                    "input_prompt": f"Exécution Pytest sur {chemin_test if chemin_test else 'sandbox'}",
                    "output_response": f"Tests terminés: {tests_reussis}/{total_tests} réussis, code: {resultat.returncode}"
                },
                status="SUCCESS" if succes_global else "FAILURE"
            )
            
            return resultat_dict
            
        except subprocess.TimeoutExpired:
            resultat_dict = {
                "succes": False,
                "erreur": "Timeout Pytest (60 secondes)",
                "chemin_test": chemin_test
            }
            
            # LOG TIMEOUT
            log_experiment(
                agent_name="JudgeAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.DEBUG,
                details={
                    "input_prompt": f"Exécution Pytest sur {chemin_test if chemin_test else 'sandbox'}",
                    "output_response": "Timeout: tests trop longs (>60s)"
                },
                status="FAILURE"
            )
            
            return resultat_dict
            
        except Exception as e:
            resultat_dict = {
                "succes": False,
                "erreur": f"Erreur Pytest: {str(e)}",
                "chemin_test": chemin_test
            }
            
            # LOG EXCEPTION
            log_experiment(
                agent_name="JudgeAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.DEBUG,
                details={
                    "input_prompt": f"Exécution Pytest sur {chemin_test if chemin_test else 'sandbox'}",
                    "output_response": f"Erreur: {str(e)}"
                },
                status="FAILURE"
            )
            
            return resultat_dict
    
    # ---------- EXPLORATION FICHIERS ----------
    def lister_fichiers_python(self, repertoire: str = "") -> List[str]:
        """
        Liste tous les fichiers Python dans un répertoire.
        
        Args:
            repertoire: Chemin relatif au sandbox
            
        Returns:
            Liste des chemins relatifs des fichiers Python
        """
        try:
            chemin_repertoire = self.securite.obtenir_chemin_securise(repertoire) if repertoire else self.securite.chemin_sandbox
            
            if not os.path.exists(chemin_repertoire):
                # LOG DOSSIER INEXISTANT
                log_experiment(
                    agent_name="AuditorAgent",
                    model_used=TOOLSMITH_MODEL,
                    action=ActionType.ANALYSIS,
                    details={
                        "input_prompt": f"Liste fichiers Python dans {repertoire if repertoire else 'sandbox'}",
                        "output_response": "Dossier inexistant"
                    },
                    status="SUCCESS"
                )
                return []
            
            fichiers_python = []
            
            for racine, dossiers, fichiers in os.walk(chemin_repertoire):
                # Ignorer certains dossiers
                dossiers[:] = [d for d in dossiers if d not in [
                    '__pycache__', '.git', 'venv', '.venv',
                    'node_modules', '.idea', '.vscode', 'logs'
                ]]
                
                for fichier in fichiers:
                    if fichier.endswith('.py'):
                        chemin_complet = os.path.join(racine, fichier)
                        # Convertir en chemin relatif au sandbox
                        chemin_relatif = os.path.relpath(chemin_complet, self.securite.chemin_sandbox)
                        fichiers_python.append(chemin_relatif)
            
            fichiers_python.sort()
            
            # LOG SUCCÈS
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Liste fichiers Python dans {repertoire if repertoire else 'sandbox'}",
                    "output_response": f"{len(fichiers_python)} fichier(s) Python trouvé(s)"
                },
                status="SUCCESS"
            )
            
            return fichiers_python
            
        except Exception as e:
            # LOG ERREUR
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Liste fichiers Python dans {repertoire if repertoire else 'sandbox'}",
                    "output_response": f"Erreur: {str(e)}"
                },
                status="FAILURE"
            )
            raise
    
    def obtenir_info_fichier(self, chemin_fichier: str) -> Dict[str, Any]:
        """
        Obtient des informations détaillées sur un fichier.
        
        Args:
            chemin_fichier: Chemin relatif au sandbox
            
        Returns:
            Dictionnaire avec les informations du fichier
        """
        try:
            chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
            
            if not os.path.exists(chemin_securise):
                info = {
                    "erreur": f"Fichier non trouvé: {chemin_fichier}",
                    "existe": False
                }
                
                # LOG FICHIER INEXISTANT
                log_experiment(
                    agent_name="AuditorAgent",
                    model_used=TOOLSMITH_MODEL,
                    action=ActionType.ANALYSIS,
                    details={
                        "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                        "output_response": f"Fichier non trouvé: {chemin_fichier}"
                    },
                    status="SUCCESS"
                )
                
                return info
            
            info = {
                "existe": True,
                "chemin": chemin_fichier,
                "chemin_absolu": chemin_securise,
                "est_fichier": os.path.isfile(chemin_securise),
                "est_repertoire": os.path.isdir(chemin_securise),
                "nom": os.path.basename(chemin_fichier),
                "dossier_parent": os.path.dirname(chemin_fichier),
                "taille": os.path.getsize(chemin_securise) if os.path.isfile(chemin_securise) else 0,
                "extension": os.path.splitext(chemin_fichier)[1] if os.path.isfile(chemin_securise) else ""
            }
            
            # Pour les fichiers Python, lire quelques métriques
            if info["est_fichier"] and chemin_fichier.endswith('.py'):
                try:
                    contenu = self.lire_fichier(chemin_fichier)
                    lignes = contenu.split('\n')
                    info["lignes_code"] = len(lignes)
                    info["lignes_non_vides"] = len([l for l in lignes if l.strip()])
                    info["caracteres"] = len(contenu)
                except:
                    pass
            
            # LOG SUCCÈS
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                    "output_response": f"Informations obtenues: {info['nom']} - {info['taille']} octets"
                },
                status="SUCCESS"
            )
            
            return info
            
        except Exception as e:
            error_msg = f"Erreur inattendue: {str(e)}"
            info = {
                "erreur": error_msg
            }
            
            # LOG ERREUR
            log_experiment(
                agent_name="AuditorAgent",
                model_used=TOOLSMITH_MODEL,
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                    "output_response": error_msg
                },
                status="FAILURE"
            )
            
            return info


# Fonctions utilitaires pour compatibilité
def initialiser_outils(chemin_sandbox: str = "sandbox") -> OutilsCode:
    """Initialise les outils de code."""
    return OutilsCode(chemin_sandbox)