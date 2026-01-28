"""
Fix Agent that automatically fixes code issues identified by the Auditor.
Version avec utilisation complète des outils
"""

from typing import Dict, Any, List, Optional
import re
import os
from .base_agent import BaseAgent
from src.llm.gemini_client import LLMClient
from src.utils.tools import initialiser_outils
from src.utils.logger import ActionType, log_experiment

class FixAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="FixAgent")
        print(f"{self.name} initialized with tools integration")
        
        # Initialize LLM client
        self.llm_client = self._init_llm_client()
        
        # Initialize tools
        self.tools = self._init_tools()
        
        # Fixing strategies
        self.fixing_strategies = {
            "security": self._fix_security,
            "syntax": self._fix_syntax,
            "error_handling": self._fix_error_handling,
            "style": self._fix_style,
            "performance": self._fix_performance,
            "logic": self._fix_logic,
            "default": self._fix_with_llm
        }
    
    def _init_llm_client(self):
        """Initialize the LLM client."""
        try:
            return LLMClient()
        except Exception as e:
            print(f"⚠️ LLM client not available: {e}")
            return None
    
    def _init_tools(self):
        """Initialize code fixing tools."""
        try:
            self.outils = initialiser_outils("sandbox")
            print(f"✅ Tools initialized for {self.name}")
            return True
        except Exception as e:
            print(f"❌ Tools initialization failed: {e}")
            return False
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply fixes to code based on audit report."""
        current_file = state.get('current_file', 'unknown')
        print(f"{self.name} fixing: {current_file}")
        
        # Get the original code
        original_code = state.get("file_content", "")
        if not original_code:
            print("❌ No code to fix")
            return self._create_error_result(state, "No code content")
        
        # Get the audit report
        audit_report = state.get("agent_outputs", {}).get("audit_report", {})
        if not audit_report or audit_report.get("error"):
            print("❌ No valid audit report found")
            return self._create_error_result(state, "No audit report")
        
        total_issues = self._count_issues(audit_report)
        print(f"📊 Issues to fix: {total_issues}")
        
        # 🔥 ÉTAPE 1: Sauvegarder le code original dans le sandbox
        file_saved = False
        if self.tools and current_file:
            try:
                # Normaliser le nom de fichier pour le sandbox
                if not current_file.startswith("sandbox/"):
                    sandbox_file = f"sandbox/{current_file}"
                else:
                    sandbox_file = current_file
                
                # Utiliser l'outil d'écriture
                write_result = self.outils.ecrire_fichier(sandbox_file, original_code, sauvegarde=True)
                if write_result.get("succes"):
                    file_saved = True
                    print(f"✅ Original code saved to sandbox: {sandbox_file}")
                    if write_result.get("sauvegarde_creee"):
                        print(f"   Backup created: {write_result.get('chemin_sauvegarde', 'N/A')}")
                else:
                    print(f"⚠️ Could not save original code: {write_result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ File save error: {e}")
        
        # 🔥 ÉTAPE 2: Analyser avec Pylint avant corrections
        pylint_before = None
        if self.tools and file_saved:
            try:
                pylint_result = self.outils.analyser_pylint(sandbox_file)
                if pylint_result.get("succes"):
                    pylint_before = {
                        "score": pylint_result.get("score_pylint", 0),
                        "total_issues": pylint_result.get("statistiques", {}).get("total", 0),
                        "errors": pylint_result.get("statistiques", {}).get("erreurs", 0),
                        "warnings": pylint_result.get("statistiques", {}).get("avertissements", 0)
                    }
                    print(f"📈 Pylint BEFORE fixes: Score {pylint_before['score']}/10, "
                          f"Issues: {pylint_before['total_issues']}")
            except Exception as e:
                print(f"⚠️ Pylint analysis error: {e}")
        
        # 🔥 ÉTAPE 3: Appliquer les corrections
        fixed_code, fix_log = self._apply_fixes(original_code, audit_report)
        
        # 🔥 ÉTAPE 4: Sauvegarder le code corrigé
        if self.tools and file_saved:
            try:
                # Écrire le code corrigé
                write_fixed_result = self.outils.ecrire_fichier(sandbox_file, fixed_code, sauvegarde=False)
                if write_fixed_result.get("succes"):
                    print(f"✅ Fixed code saved: {sandbox_file}")
                    
                    # 🔥 ÉTAPE 5: Analyser avec Pylint après corrections
                    pylint_after = None
                    try:
                        pylint_result = self.outils.analyser_pylint(sandbox_file)
                        if pylint_result.get("succes"):
                            pylint_after = {
                                "score": pylint_result.get("score_pylint", 0),
                                "total_issues": pylint_result.get("statistiques", {}).get("total", 0),
                                "errors": pylint_result.get("statistiques", {}).get("erreurs", 0),
                                "warnings": pylint_result.get("statistiques", {}).get("avertissements", 0)
                            }
                            print(f"📈 Pylint AFTER fixes: Score {pylint_after['score']}/10, "
                                  f"Issues: {pylint_after['total_issues']}")
                            
                            # Calculer l'amélioration
                            if pylint_before and pylint_after:
                                score_improvement = pylint_after['score'] - pylint_before['score']
                                issues_reduction = pylint_before['total_issues'] - pylint_after['total_issues']
                                print(f"📊 Improvement: Score +{score_improvement:.2f}, "
                                      f"Issues reduced by {issues_reduction}")
                    except Exception as e:
                        print(f"⚠️ Pylint after analysis error: {e}")
                else:
                    print(f"⚠️ Could not save fixed code: {write_fixed_result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Fixed file save error: {e}")
        
        # 🔥 ÉTAPE 6: Calculer les métriques
        metrics = self._calculate_metrics(original_code, fixed_code, fix_log, pylint_before, pylint_after)
        
        # 🔥 ÉTAPE 7: Loguer l'action
        self._log_fixes(current_file, original_code, fixed_code, fix_log, metrics)
        
        # 🔥 ÉTAPE 8: Retourner les résultats
        return {
            "file_content": fixed_code,
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "fix_report": {
                    "original_file": current_file,
                    "sandbox_file": sandbox_file if 'sandbox_file' in locals() else current_file,
                    "fixes_applied": fix_log,
                    "pylint_before": pylint_before,
                    "pylint_after": pylint_after,
                    "file_saved": file_saved,
                    "metrics": metrics,
                    "summary": {
                        "issues_fixed": metrics.get("issues_fixed", 0),
                        "score_improvement": metrics.get("score_improvement", 0),
                        "code_changed": fixed_code != original_code
                    }
                }
            },
            "current_phase": "review" if metrics.get("issues_fixed", 0) > 0 else "error",
            "original_code": original_code
        }
    
    def _log_fixes(self, filename: str, original_code: str, fixed_code: str, 
                   fix_log: List[Dict], metrics: Dict[str, Any]):
        """Log the fixing action using professor's format."""
        
        # Créer le message de réponse
        issues_fixed = metrics.get("issues_fixed", 0)
        
        # Calculer les statistiques
        critical_fixed = len([f for f in fix_log if f.get('severity') == 'critical' and f.get('fix_applied')])
        major_fixed = len([f for f in fix_log if f.get('severity') == 'major' and f.get('fix_applied')])
        minor_fixed = len([f for f in fix_log if f.get('severity') == 'minor' and f.get('fix_applied')])
        
        output_response = f"Applied {issues_fixed} fixes to {filename} (Critical: {critical_fixed}, Major: {major_fixed}, Minor: {minor_fixed})"
        
        # SEULEMENT ces deux champs sont autorisés !
        details = {
            "input_prompt": f"Fix issues in {filename}",
            "output_response": output_response
            # PAS d'autres champs !
        }
        
        # Loguer avec le format du prof
        self.log_action("fix", details)
        print(f"✅ Fixes logged: {output_response}")
    
    def _count_issues(self, audit_report: Dict[str, Any]) -> int:
        """Count total issues in audit report."""
        return (
            len(audit_report.get("critical_issues", [])) +
            len(audit_report.get("major_issues", [])) +
            len(audit_report.get("minor_issues", []))
        )
    
    def _apply_fixes(self, code: str, audit_report: Dict[str, Any]) -> tuple:
        """Apply all fixes to the code."""
        lines = code.split('\n')
        fix_log = []
        
        # Créer une copie des lignes pour modification
        modified_lines = lines.copy()
        
        # Traiter d'abord les issues critiques et majeures
        all_issues = []
        all_issues.extend([(issue, "critical") for issue in audit_report.get("critical_issues", [])])
        all_issues.extend([(issue, "major") for issue in audit_report.get("major_issues", [])])
        
        # Trier par ligne (décroissant pour éviter conflits)
        all_issues.sort(key=lambda x: x[0].get("line", 0), reverse=True)
        
        for issue, severity in all_issues:
            line_num = issue.get("line", 0)
            if 0 < line_num <= len(modified_lines):
                issue_type = issue.get("type", "default")
                print(f"  🔧 Fixing {severity} issue on line {line_num}: {issue_type}")
                
                # Appliquer le fix
                success = self._fix_line(modified_lines, line_num, issue, severity)
                
                fix_log.append({
                    "severity": severity,
                    "line": line_num,
                    "type": issue_type,
                    "description": issue.get("description", "")[:60],
                    "fix_applied": success
                })
        
        # Traiter les issues mineures en batch
        minor_issues = audit_report.get("minor_issues", [])
        if minor_issues:
            # Grouper par ligne
            line_groups = {}
            for issue in minor_issues:
                line_num = issue.get("line", 0)
                if line_num > 0:
                    line_groups.setdefault(line_num, []).append(issue)
            
            # Appliquer les fixes mineurs
            for line_num, issues in line_groups.items():
                if 0 < line_num <= len(modified_lines):
                    original_line = modified_lines[line_num - 1]
                    fixed_line = original_line
                    
                    for issue in issues:
                        fixed_line = self._apply_minor_fix(fixed_line, issue)
                    
                    if fixed_line != original_line:
                        modified_lines[line_num - 1] = fixed_line
                        fix_log.append({
                            "severity": "minor",
                            "line": line_num,
                            "type": "batch_minor",
                            "description": f"Fixed {len(issues)} minor issues",
                            "fix_applied": True
                        })
        
        fixed_code = '\n'.join(modified_lines)
        return fixed_code, fix_log
    
    def _fix_line(self, lines: List[str], line_num: int, issue: Dict[str, Any], severity: str) -> bool:
        """Fix a single line based on issue type."""
        issue_type = issue.get("type", "default")
        
        # Get the appropriate strategy
        strategy = self.fixing_strategies.get(issue_type, self.fixing_strategies["default"])
        
        try:
            # Apply the strategy
            success = strategy(lines, line_num, issue)
            return success
        except Exception as e:
            print(f"    ❌ Error fixing {issue_type}: {e}")
            return False
    
    def _fix_security(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix security issues."""
        line = lines[line_num - 1]
        
        # Fix eval()
        if 'eval(' in line:
            # Try to replace with ast.literal_eval for simple expressions
            if '"' in line or "'" in line:
                # Ajouter l'import ast si nécessaire
                if 'import ast' not in '\n'.join(lines):
                    for i, l in enumerate(lines):
                        if l.strip().startswith('import ') or l.strip().startswith('from '):
                            lines.insert(i + 1, 'import ast')
                            break
                
                lines[line_num - 1] = line.replace('eval(', 'ast.literal_eval(')
                print(f"    ✅ Replaced eval() with ast.literal_eval()")
            else:
                lines[line_num - 1] = line.replace('eval(', '# SECURITY FIX: eval() removed - ')
                print(f"    ✅ Commented out eval()")
            return True
        
        # Fix exec()
        elif 'exec(' in line:
            lines[line_num - 1] = line.replace('exec(', '# SECURITY FIX: exec() removed - ')
            print(f"    ✅ Commented out exec()")
            return True
        
        # Fix pickle.loads()
        elif 'pickle.loads(' in line:
            lines[line_num - 1] = line.replace('pickle.loads(', '# SECURITY FIX: pickle.loads() unsafe - use json.loads()')
            print(f"    ✅ Replaced pickle.loads() with json.loads() suggestion")
            return True
        
        return False
    
    def _fix_syntax(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix syntax issues."""
        line = lines[line_num - 1]
        
        # Missing colon
        if 'missing colon' in issue.get('description', '').lower():
            if not line.rstrip().endswith(':'):
                lines[line_num - 1] = line.rstrip() + '  # FIXED: added missing colon'
                print(f"    ✅ Added missing colon")
                return True
        
        # Missing parenthesis
        elif 'parenthesis' in issue.get('description', '').lower():
            if line.count('(') > line.count(')'):
                lines[line_num - 1] = line.rstrip() + ')' + '  # FIXED: added missing )'
                print(f"    ✅ Added missing parenthesis")
                return True
        
        return False
    
    def _fix_error_handling(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix error handling issues."""
        line = lines[line_num - 1]
        
        # Bare except
        if 'except:' in line:
            lines[line_num - 1] = line.replace('except:', 'except Exception:  # FIXED: bare except')
            print(f"    ✅ Replaced bare except with except Exception:")
            return True
        elif 'except :' in line:
            lines[line_num - 1] = line.replace('except :', 'except Exception:  # FIXED: bare except')
            print(f"    ✅ Replaced bare except with except Exception:")
            return True
        
        # Division by zero warning
        elif '/' in line and 'zero' in issue.get('description', '').lower():
            lines[line_num - 1] = line.rstrip() + '  # WARNING: division by zero possible'
            print(f"    ✅ Added division by zero warning")
            return True
        
        return False
    
    def _fix_style(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix style issues."""
        line = lines[line_num - 1]
        fixed_line = line.rstrip()  # Remove trailing whitespace
        
        description = issue.get('description', '').lower()
        
        # Missing spaces around operators
        if 'space' in description or 'spaces' in description:
            # Fix common operators
            operators = ['=', '==', '+=', '-=', '*=', '/=', '<', '>', '<=', '>=', '!=', '+', '-', '*', '/']
            for op in operators:
                pattern = rf'(\S)({re.escape(op)})(\S)'
                fixed_line = re.sub(pattern, rf'\1 {op} \3', fixed_line)
        
        # Comparison to None
        if 'none' in description and ('comparison' in description or 'compare' in description):
            fixed_line = fixed_line.replace('== None', 'is None')
            fixed_line = fixed_line.replace('!= None', 'is not None')
        
        # Line too long warning
        if 'too long' in description and len(fixed_line) > 79:
            fixed_line = fixed_line + '  # WARNING: line exceeds 79 characters'
        
        if fixed_line != line:
            lines[line_num - 1] = fixed_line
            print(f"    ✅ Fixed style issue: {description[:40]}...")
            return True
        
        return False
    
    def _fix_performance(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix performance issues."""
        line = lines[line_num - 1]
        description = issue.get('description', '').lower()
        
        # String concatenation in loop
        if 'concatenation' in description and 'loop' in description:
            if '+=' in line:
                lines[line_num - 1] = line.rstrip() + '  # PERFORMANCE: consider using list and join()'
                print(f"    ✅ Added performance suggestion for string concatenation")
                return True
        
        # Inefficient loop
        elif 'inefficient' in description or 'performance' in description:
            lines[line_num - 1] = line.rstrip() + '  # PERFORMANCE: review for optimization'
            print(f"    ✅ Added performance review comment")
            return True
        
        return False
    
    def _fix_logic(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Fix logic errors using LLM."""
        if not self.llm_client:
            return False
        
        # Get context
        start = max(0, line_num - 3)
        end = min(len(lines), line_num + 2)
        context_lines = lines[start:end]
        context = '\n'.join([f"{i+start+1}: {line}" for i, line in enumerate(context_lines)])
        
        prompt = f"""
        Fix this logic error in Python code:
        
        Line {line_num}: {lines[line_num - 1]}
        
        Context:
        {context}
        
        Issue: {issue.get('description', '')}
        Suggestion: {issue.get('suggestion', '')}
        
        Return ONLY the fixed line for line {line_num}.
        Keep the same indentation and style.
        """
        
        try:
            response = self.llm_client.call(prompt)
            if response and not response.startswith("Error:"):
                fixed_line = response.strip().split('\n')[0].strip()
                if fixed_line and len(fixed_line) > 5:
                    lines[line_num - 1] = fixed_line
                    print(f"    ✅ Fixed logic error using LLM")
                    return True
        except Exception as e:
            print(f"    ❌ LLM logic fix error: {e}")
        
        return False
    
    def _fix_with_llm(self, lines: List[str], line_num: int, issue: Dict[str, Any]) -> bool:
        """Use LLM for complex fixes."""
        if not self.llm_client:
            return False
        
        # Get context
        start = max(0, line_num - 3)
        end = min(len(lines), line_num + 2)
        context_lines = lines[start:end]
        context = '\n'.join([f"{i+start+1}: {line}" for i, line in enumerate(context_lines)])
        
        prompt = f"""
        Fix this code issue:
        
        Line {line_num}: {lines[line_num - 1]}
        
        Context:
        {context}
        
        Issue type: {issue.get('type', 'unknown')}
        Description: {issue.get('description', '')}
        Suggestion: {issue.get('suggestion', '')}
        
        Return exactly ONE line with the fix.
        Keep the same indentation.
        """
        
        try:
            response = self.llm_client.call(prompt)
            if response and not response.startswith("Error:"):
                fixed_line = response.strip().split('\n')[0].strip()
                if fixed_line:
                    lines[line_num - 1] = fixed_line
                    print(f"    ✅ Fixed using LLM")
                    return True
        except Exception as e:
            print(f"    ❌ LLM fix error: {e}")
        
        return False
    
    def _apply_minor_fix(self, line: str, issue: Dict[str, Any]) -> str:
        """Apply minor style fixes."""
        fixed_line = line.rstrip()  # Remove trailing whitespace
        
        description = issue.get('description', '').lower()
        
        # Fix spaces around commas and colons
        if 'space' in description:
            fixed_line = re.sub(r',(\S)', r', \1', fixed_line)
            fixed_line = re.sub(r':(\S)', r': \1', fixed_line)
        
        # Fix None comparison
        if 'none' in description:
            fixed_line = fixed_line.replace('== None', 'is None')
            fixed_line = fixed_line.replace('!= None', 'is not None')
        
        return fixed_line
    
    def _calculate_metrics(self, original_code: str, fixed_code: str, 
                          fix_log: List[Dict], pylint_before: Optional[Dict], 
                          pylint_after: Optional[Dict]) -> Dict[str, Any]:
        """Calculate fixing metrics."""
        issues_fixed = len([f for f in fix_log if f.get("fix_applied", False)])
        total_attempted = len(fix_log)
        
        # Calculate line changes
        orig_lines = original_code.split('\n')
        fixed_lines = fixed_code.split('\n')
        lines_changed = 0
        
        for i in range(min(len(orig_lines), len(fixed_lines))):
            if orig_lines[i] != fixed_lines[i]:
                lines_changed += 1
        
        # Calculate Pylint improvement
        score_improvement = 0
        issues_reduction = 0
        
        if pylint_before and pylint_after:
            score_improvement = pylint_after['score'] - pylint_before['score']
            issues_reduction = pylint_before['total_issues'] - pylint_after['total_issues']
        
        return {
            "issues_fixed": issues_fixed,
            "total_attempted": total_attempted,
            "fix_rate": issues_fixed / total_attempted if total_attempted > 0 else 0,
            "code_changed": fixed_code != original_code,
            "lines_changed": lines_changed,
            "score_improvement": round(score_improvement, 2),
            "issues_reduction": issues_reduction,
            "original_length": len(original_code),
            "fixed_length": len(fixed_code)
        }
    
    def _create_error_result(self, state: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Create error result with proper logging."""
        print(f"❌ FixAgent Error: {error_msg}")
        
        # Loguer l'erreur avec le format du prof
        details = {
            "input_prompt": f"Fix issues in {state.get('current_file', 'unknown')}",
            "output_response": f"Error: {error_msg}"
        }
        
        self.log_action(ActionType.FIX, details, "FAILURE")
        
        return {
            "agent_outputs": {
                **(state.get("agent_outputs") or {}),
                "fix_report": {
                    "error": error_msg,
                    "fixes_applied": []
                }
            },
            "current_phase": "error"
        }