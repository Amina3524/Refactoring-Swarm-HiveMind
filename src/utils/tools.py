import os
import subprocess
import sys
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from src.utils.logger import log_experiment, ActionType

def lire_fichier(chemin_fichier: str) -> str:
    """
    Lit le contenu d'un fichier (à partir de son chemin) et le retourne sous forme de chaîne 
    ou un message d'erreur.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        if not os.path.isfile(chemin_fichier):
            resultat = f"Erreur: Le chemin '{chemin_fichier}' ne correspond pas à un fichier."
            
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,  

                details={
                    "input_prompt": f"Lecture du fichier {chemin_fichier}",
                    "output_response": resultat,  # OBLIGATOIRE
                    "file_analyzed": chemin_fichier,
                    "tool_used": "lire_fichier"
                },
                status="FAILURE"  # ❌ CORRECTION: "FAILURE" pas "ERROR"
            )
            return resultat
            
        if not os.path.exists(chemin_fichier):
            resultat = f"Erreur: Le chemin '{chemin_fichier}' n'existe pas."
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Lecture du fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_analyzed": chemin_fichier,
                    "tool_used": "lire_fichier"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat

        with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
            contenu = fichier.read()
        
        # LOG SUCCÈS
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier {chemin_fichier}",
                "output_response": f"Fichier lu avec succès: {len(contenu)} caractères",
                "file_analyzed": chemin_fichier,
                "tool_used": "lire_fichier",
                "content_length": len(contenu)
            },
            status="SUCCESS"
        )
        
        return contenu
        
    except PermissionError:
        resultat = f"Erreur: Permission refusée lors de la lecture du fichier '{chemin_fichier}'."
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "lire_fichier",
                "error_type": "PermissionError"
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat
        
    except UnicodeDecodeError:
        resultat = f"Erreur: Impossible de décoder le fichier '{chemin_fichier}'. Ce n'est peut-être pas un fichier texte."
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "lire_fichier",
                "error_type": "UnicodeDecodeError"
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat
        
    except Exception as e:
        resultat = f"Erreur: Une erreur inattendue s'est produite lors de la lecture du fichier '{chemin_fichier}': {str(e)}"
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Lecture du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "lire_fichier",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat

def ecrire_fichier(chemin_fichier: str, contenu: str) -> str:
    """
    Écrit un contenu dans un fichier.
    S'assure que l'écriture se fait uniquement dans le répertoire 'sandbox'.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        # Vérifier si on écrit dans 'sandbox'
        sandbox_dir = os.path.normpath('sandbox')
        sandbox_absolu = os.path.abspath(sandbox_dir)
        cible_absolu = os.path.abspath(chemin_fichier)

        if not cible_absolu.startswith(sandbox_absolu):
            resultat = f"Erreur: L'écriture n'est autorisée que dans le répertoire 'sandbox'."
            # LOG ERREUR SÉCURITÉ
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.FIX,  # ❌ CORRECTION: ActionType.FIX 
                details={
                    "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_modified": chemin_fichier,
                    "tool_used": "ecrire_fichier",
                    "security_breach": True
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat
        
        os.makedirs(os.path.dirname(chemin_fichier), exist_ok=True)
        
        # Si le fichier existe déjà, créer une sauvegarde
        chemin_sauvegarde = None
        if os.path.exists(chemin_fichier):
            chemin_sauvegarde = f"{chemin_fichier}.bak"
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier_original:
                with open(chemin_sauvegarde, 'w', encoding='utf-8') as fichier_sauvegarde:
                    fichier_sauvegarde.write(fichier_original.read())

        with open(chemin_fichier, 'w', encoding='utf-8') as fichier:
            fichier.write(contenu)

        # Vérifier que l'écriture a réussi
        if os.path.exists(chemin_fichier):
            with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                contenu_ecrit = fichier.read()
                if contenu_ecrit == contenu:
                    resultat = f"Succès: Contenu écrit dans '{chemin_fichier}'."
                    # LOG SUCCÈS
                    log_experiment(
                        agent_name="Toolsmith_Agent",
                        model_used="python_tool",
                        action=ActionType.FIX,  # ❌ CORRECTION
                        details={
                            "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                            "output_response": resultat,
                            "file_modified": chemin_fichier,
                            "tool_used": "ecrire_fichier",
                            "content_length": len(contenu),
                            "backup_created": chemin_sauvegarde is not None
                        },
                        status="SUCCESS"
                    )
                    return resultat
                else:
                    # Restaurer depuis la sauvegarde si l'écriture a échoué
                    if chemin_sauvegarde and os.path.exists(chemin_sauvegarde):
                        with open(chemin_sauvegarde, 'r', encoding='utf-8') as fichier_sauvegarde:
                            with open(chemin_fichier, 'w', encoding='utf-8') as fichier_original:
                                fichier_original.write(fichier_sauvegarde.read())
                    resultat = f"Erreur: Échec de vérification. Le contenu dans '{chemin_fichier}' ne correspond pas au contenu attendu."
                    log_experiment(
                        agent_name="Toolsmith_Agent",
                        model_used="python_tool",
                        action=ActionType.FIX,  # ❌ CORRECTION
                        details={
                            "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                            "output_response": resultat,
                            "file_modified": chemin_fichier,
                            "tool_used": "ecrire_fichier",
                            "verification_failed": True
                        },
                        status="FAILURE"  # ❌ CORRECTION
                    )
                    return resultat
        else:
            resultat = f"Erreur: Fichier non créé: {chemin_fichier}"
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.FIX,  # ❌ CORRECTION
                details={
                    "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_modified": chemin_fichier,
                    "tool_used": "ecrire_fichier"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat
            
    except Exception as e:
        resultat = f"Erreur: Une erreur inattendue s'est produite lors de l'écriture dans le fichier '{chemin_fichier}': {str(e)}"
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.FIX,  # ❌ CORRECTION
            details={
                "input_prompt": f"Écriture dans le fichier {chemin_fichier}",
                "output_response": resultat,
                "file_modified": chemin_fichier,
                "tool_used": "ecrire_fichier",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat

def executer_pylint(chemin_fichier: str) -> str:
    """
    Exécute pylint sur un fichier Python donné et retourne les résultats.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)

        if not os.path.exists(chemin_fichier):
            resultat = f"Erreur: Le fichier '{chemin_fichier}' n'existe pas."
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_analyzed": chemin_fichier,
                    "tool_used": "executer_pylint"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat
        
        if not os.path.isfile(chemin_fichier):
            resultat = f"Erreur: Le chemin '{chemin_fichier}' ne correspond pas à un fichier."
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_analyzed": chemin_fichier,
                    "tool_used": "executer_pylint"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat
            
        if not chemin_fichier.endswith('.py'):
            resultat = f"Erreur: Le fichier '{chemin_fichier}' n'est pas un fichier Python (.py requis)."
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                    "output_response": resultat,
                    "file_analyzed": chemin_fichier,
                    "tool_used": "executer_pylint"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return resultat

        print(f"[DEBUG] Exécution de pylint sur: {chemin_fichier}")
        
        # Exécuter pylint avec format texte
        resultat_subprocess = subprocess.run(
            ['pylint', '--output-format=text', chemin_fichier],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(chemin_fichier).parent) or '.',
            shell=False
        )
        
        # Construire la sortie complète
        parties_sortie = []
        
        if resultat_subprocess.stdout:
            parties_sortie.append(f"RAPPORT D'ANALYSE PYLINT:\n{'='*50}")
            parties_sortie.append(resultat_subprocess.stdout)
        
        if resultat_subprocess.stderr:
            parties_sortie.append(f"\nERREURS PYLINT:\n{'='*50}")
            parties_sortie.append(resultat_subprocess.stderr)
        
        parties_sortie.append(f"\n{'='*50}")
        
        if resultat_subprocess.returncode == 0:
            parties_sortie.append("RÉSUMÉ PYLINT: Aucun problème détecté !")
            status_final = "SUCCESS"
        else:
            lignes = resultat_subprocess.stdout.split('\n') if resultat_subprocess.stdout else []
            erreurs = sum(1 for ligne in lignes if ': E' in ligne)
            avertissements = sum(1 for ligne in lignes if ': W' in ligne)
            refactorisations = sum(1 for ligne in lignes if ': R' in ligne)
            conventions = sum(1 for ligne in lignes if ': C' in ligne)
            
            resume = f"RÉSUMÉ PYLINT: {erreurs} erreur(s), {avertissements} avertissement(s), "
            resume += f"{conventions} problème(s) de convention, {refactorisations} suggestion(s) de refactorisation."
            parties_sortie.append(resume)
            status_final = "SUCCESS"
        
        resultat_final = "\n".join(parties_sortie)
        
        # LOG SUCCÈS
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                "output_response": f"Analyse terminée. Code de sortie: {resultat_subprocess.returncode}",
                "file_analyzed": chemin_fichier,
                "tool_used": "executer_pylint",
                "pylint_exit_code": resultat_subprocess.returncode,
                "errors_found": erreurs if 'erreurs' in locals() else 0,
                "warnings_found": avertissements if 'avertissements' in locals() else 0
            },
            status=status_final
        )
        
        return resultat_final
        
    except subprocess.TimeoutExpired:
        resultat = f"Erreur: Timeout de pylint après 30 secondes pour le fichier '{chemin_fichier}'."
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "executer_pylint",
                "timeout": True
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat
        
    except FileNotFoundError:
        resultat = "Erreur: Commande 'pylint' introuvable."
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "executer_pylint",
                "pylint_not_found": True
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat
        
    except Exception as e:
        resultat = f"Erreur: Erreur inattendue lors de l'exécution de pylint: {str(e)}"
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Analyse pylint du fichier {chemin_fichier}",
                "output_response": resultat,
                "file_analyzed": chemin_fichier,
                "tool_used": "executer_pylint",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat

def executer_pytest(chemin_test: str) -> str:
    """
    Exécute pytest sur un fichier de test Python donné et retourne les résultats.
    """
    try:
        chemin_test = os.path.normpath(chemin_test)

        print(f"[DEBUG] Exécution de pytest sur : {chemin_test}")

        if os.path.isfile(chemin_test) and chemin_test.endswith('.py'):
            pytest_args = ['pytest', chemin_test, '-v', '--tb=short']
        elif os.path.isdir(chemin_test):
            pytest_args = ['pytest', chemin_test, '-v', '--tb=short']
        else:
            pytest_args = ['pytest', chemin_test, '-v', '--tb=short']
            
        resultat_subprocess = subprocess.run(
            pytest_args,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False
        )
        
        parties_sortie = []

        if resultat_subprocess.stdout:
            parties_sortie.append(f"RAPPORT D'EXÉCUTION PYTEST:\n{'='*50}")
            lignes = resultat_subprocess.stdout.split('\n')
            debut_idx = 0
            for i, ligne in enumerate(lignes):
                if ligne.startswith('============================= test session starts ============================='):
                    debut_idx = i
                    break

            if debut_idx < len(lignes):
                parties_sortie.append('\n'.join(lignes[debut_idx:]))    

        if resultat_subprocess.stderr:
            parties_sortie.append(f"\nERREURS PYTEST:\n{'='*50}")
            parties_sortie.append(resultat_subprocess.stderr)

        parties_sortie.append(f"\n{'='*50}")   
        signification_code_sortie = {
            0: "Tous les tests ont réussi.",
            1: "Des tests ont échoué.",
            2: "Un problème est survenu lors de l'exécution des tests.",
            3: "Une erreur fatale est survenue lors de l'exécution de pytest.",
            4: "Pytest a été interrompu par l'utilisateur.",
            5: "Aucun test n'a été collecté."
        }
        resume = signification_code_sortie.get(resultat_subprocess.returncode, "Code de sortie inconnu de pytest.")
        parties_sortie.append(f"RÉSUMÉ PYTEST: {resume}")

        if resultat_subprocess.stdout:
            for ligne in reversed(resultat_subprocess.stdout.split('\n')):
                if "passed" in ligne.lower() and "failed" in ligne.lower():
                    parties_sortie.append(f"STATISTIQUES PYTEST: {ligne.strip()}")
                    break
                    
        resultat_final = "\n".join(parties_sortie)
        
        
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.DEBUG,  # ActionType.DEBUG 
            details={
                "input_prompt": f"Exécution pytest sur {chemin_test}",
                "output_response": f"Tests exécutés: code de sortie {resultat_subprocess.returncode}",
                "test_path": chemin_test,
                "tool_used": "executer_pytest",
                "pytest_exit_code": resultat_subprocess.returncode
            },
            status="SUCCESS" if resultat_subprocess.returncode in [0, 1] else "FAILURE"  # ❌ CORRECTION
        )
        
        return resultat_final
        
    except Exception as e:
        resultat = f"Erreur: {str(e)}"
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.DEBUG,
            details={
                "input_prompt": f"Exécution pytest sur {chemin_test}",
                "output_response": resultat,
                "test_path": chemin_test,
                "tool_used": "executer_pytest",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return resultat

def lister_fichiers_python(repertoire: str) -> List[str]:
    """
    Liste tous les fichiers Python (.py) dans un répertoire donné.
    """
    try:
        repertoire = os.path.normpath(repertoire)

        if not os.path.exists(repertoire):
            resultat = []
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Liste fichiers Python dans {repertoire}",
                    "output_response": "Répertoire inexistant, liste vide retournée",
                    "directory": repertoire,
                    "tool_used": "lister_fichiers_python"
                },
                status="SUCCESS"
            )
            return resultat
            
        fichiers_python = []
        for racine, repertoires, fichiers in os.walk(repertoire):
            # Ignorer certains répertoires
            repertoires[:] = [d for d in repertoires if d not in [
                '__pycache__', '.git', 'venv', '.venv',
                'node_modules', '.idea', '.vscode', 'logs'
            ]]
            for fichier in fichiers:
                if fichier.endswith('.py'):
                    chemin_complet = os.path.join(racine, fichier)
                    fichiers_python.append(chemin_complet)
        
        fichiers_python.sort()
        
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Liste fichiers Python dans {repertoire}",
                "output_response": f"{len(fichiers_python)} fichier(s) trouvé(s)",
                "directory": repertoire,
                "tool_used": "lister_fichiers_python",
                "files_found": len(fichiers_python),
                "files_sample": fichiers_python[:10]  # Limiter à 10 fichiers pour éviter les logs trop longs
            },
            status="SUCCESS"
        )
        
        return fichiers_python
        
    except Exception as e:
        error_msg = f"Erreur: {str(e)}"
        print(error_msg, file=sys.stderr)
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Liste fichiers Python dans {repertoire}",
                "output_response": error_msg,
                "directory": repertoire,
                "tool_used": "lister_fichiers_python",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return []

def obtenir_info_fichier(chemin_fichier: str) -> Dict[str, Any]:
    """
    Obtient des informations détaillées sur un fichier.
    """
    try:
        chemin_fichier = os.path.normpath(chemin_fichier)
        
        if not os.path.exists(chemin_fichier):
            info = {
                "erreur": f"Le fichier '{chemin_fichier}' n'existe pas.",
                "existe": False
            }
            log_experiment(
                agent_name="Toolsmith_Agent",
                model_used="python_tool",
                action=ActionType.ANALYSIS,
                details={
                    "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                    "output_response": info["erreur"],
                    "file_analyzed": chemin_fichier,
                    "tool_used": "obtenir_info_fichier",
                    "error_type": "file_not_found"
                },
                status="FAILURE"  # ❌ CORRECTION
            )
            return info
        
        info = {
            "chemin": chemin_fichier,
            "chemin_absolu": os.path.abspath(chemin_fichier),
            "existe": True,
            "est_fichier": os.path.isfile(chemin_fichier),
            "est_repertoire": os.path.isdir(chemin_fichier),
            "taille": os.path.getsize(chemin_fichier) if os.path.isfile(chemin_fichier) else 0,
            "date_modification": datetime.fromtimestamp(os.path.getmtime(chemin_fichier)).isoformat(),
            "date_creation": datetime.fromtimestamp(os.path.getctime(chemin_fichier)).isoformat(),
            "extension": os.path.splitext(chemin_fichier)[1] if os.path.isfile(chemin_fichier) else "",
            "nom": os.path.basename(chemin_fichier),
            "repertoire_parent": os.path.dirname(chemin_fichier)
        }
        
        if info["est_fichier"] and chemin_fichier.endswith('.py'):
            contenu = lire_fichier(chemin_fichier)
            if "Erreur:" not in contenu:
                info["lignes"] = len(contenu.split('\n'))
                info["caracteres"] = len(contenu)
        
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                "output_response": f"Informations obtenues pour {chemin_fichier}",
                "file_analyzed": chemin_fichier,
                "tool_used": "obtenir_info_fichier",
                "file_size": info.get("taille", 0),
                "is_python_file": chemin_fichier.endswith('.py'),
                "file_info_summary": f"{info['nom']} - {info['taille']} bytes"
            },
            status="SUCCESS"
        )
        
        return info
        
    except Exception as e:
        error_msg = f"Erreur inattendue: {str(e)}"
        info = {
            "erreur": error_msg
        }
        log_experiment(
            agent_name="Toolsmith_Agent",
            model_used="python_tool",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Obtenir info fichier {chemin_fichier}",
                "output_response": error_msg,
                "file_analyzed": chemin_fichier,
                "tool_used": "obtenir_info_fichier",
                "error_type": type(e).__name__
            },
            status="FAILURE"  # ❌ CORRECTION
        )
        return info