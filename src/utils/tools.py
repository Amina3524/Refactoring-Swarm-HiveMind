import os
import subprocess
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

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
        chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
        
        if not os.path.isfile(chemin_securise):
            raise FileNotFoundError(f"Fichier non trouvé: {chemin_fichier}")
        
        # Essayer différents encodages
        encodages = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        for encodage in encodages:
            try:
                with open(chemin_securise, 'r', encoding=encodage) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError(f"Impossible de décoder le fichier: {chemin_fichier}")
    
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
        
        resultat = {
            "succes": contenu_verifie == contenu,
            "chemin": chemin_fichier,
            "chemin_absolu": chemin_securise,
            "taille": len(contenu),
            "sauvegarde_creee": chemin_sauvegarde is not None,
            "chemin_sauvegarde": chemin_sauvegarde,
            "message": "Écriture réussie" if contenu_verifie == contenu else "Écriture vérifiée mais contenu différent"
        }
        
        return resultat
    
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
        chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
        
        if not os.path.exists(chemin_securise):
            raise FileNotFoundError(f"Fichier non trouvé: {chemin_fichier}")
        
        if not chemin_securise.endswith('.py'):
            raise ValueError(f"Ce n'est pas un fichier Python: {chemin_fichier}")
        
        try:
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
                    
                    return {
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
                except json.JSONDecodeError:
                    return {
                        "succes": False,
                        "erreur": "Impossible de parser la sortie JSON de Pylint",
                        "sortie_brute": resultat.stdout[:500]
                    }
            else:
                return {
                    "succes": False,
                    "erreur": f"Pylint a échoué avec le code {resultat.returncode}",
                    "code_sortie": resultat.returncode,
                    "erreur_brute": resultat.stderr[:500]
                }
                
        except subprocess.TimeoutExpired:
            return {
                "succes": False,
                "erreur": "Timeout Pylint (30 secondes)",
                "chemin_fichier": chemin_fichier
            }
        except FileNotFoundError:
            return {
                "succes": False,
                "erreur": "Pylint n'est pas installé ou non trouvé dans PATH"
            }
    
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
            
            return {
                "succes": resultat.returncode == 0,
                "code_sortie": resultat.returncode,
                "tests_reussis": tests_reussis,
                "tests_echoues": tests_echoues,
                "tests_ignores": tests_ignores,
                "total_tests": total_tests,
                "sortie_complete": sortie[:1000],  # Limiter la taille
                "erreur": resultat.stderr[:500] if resultat.stderr else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "succes": False,
                "erreur": "Timeout Pytest (60 secondes)",
                "chemin_test": chemin_test
            }
        except Exception as e:
            return {
                "succes": False,
                "erreur": f"Erreur Pytest: {str(e)}",
                "chemin_test": chemin_test
            }
    
    # ---------- EXPLORATION FICHIERS ----------
    def lister_fichiers_python(self, repertoire: str = "") -> List[str]:
        """
        Liste tous les fichiers Python dans un répertoire.
        
        Args:
            repertoire: Chemin relatif au sandbox
            
        Returns:
            Liste des chemins relatifs des fichiers Python
        """
        chemin_repertoire = self.securite.obtenir_chemin_securise(repertoire) if repertoire else self.securite.chemin_sandbox
        
        if not os.path.exists(chemin_repertoire):
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
        
        return sorted(fichiers_python)
    
    def obtenir_info_fichier(self, chemin_fichier: str) -> Dict[str, Any]:
        """
        Obtient des informations détaillées sur un fichier.
        
        Args:
            chemin_fichier: Chemin relatif au sandbox
            
        Returns:
            Dictionnaire avec les informations du fichier
        """
        chemin_securise = self.securite.obtenir_chemin_securise(chemin_fichier)
        
        if not os.path.exists(chemin_securise):
            return {
                "erreur": f"Fichier non trouvé: {chemin_fichier}",
                "existe": False
            }
        
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
        
        return info
    
    # ---------- UTILITAIRE ----------
    def creer_structure_dossiers(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une structure de dossiers et fichiers dans le sandbox.
        
        Args:
            structure: Dictionnaire décrivant la structure
            
        Returns:
            Statut de la création
        """
        resultats = {"dossiers_crees": [], "fichiers_crees": [], "erreurs": []}
        
        # Créer les dossiers
        for dossier in structure.get("dossiers", []):
            try:
                chemin_dossier = self.securite.obtenir_chemin_securise(dossier)
                os.makedirs(chemin_dossier, exist_ok=True)
                resultats["dossiers_crees"].append(dossier)
            except Exception as e:
                resultats["erreurs"].append(f"Erreur création dossier {dossier}: {str(e)}")
        
        # Créer les fichiers
        for fichier_info in structure.get("fichiers", []):
            try:
                chemin_fichier = fichier_info["chemin"]
                contenu = fichier_info.get("contenu", "")
                self.ecrire_fichier(chemin_fichier, contenu, sauvegarde=False)
                resultats["fichiers_crees"].append(chemin_fichier)
            except Exception as e:
                resultats["erreurs"].append(f"Erreur création fichier {fichier_info.get('chemin')}: {str(e)}")
        
        resultats["succes"] = len(resultats["erreurs"]) == 0
        return resultats


# Fonctions utilitaires pour compatibilité
def initialiser_outils(chemin_sandbox: str = "sandbox") -> OutilsCode:
    """Initialise les outils de code."""
    return OutilsCode(chemin_sandbox)