import argparse
import sys
import os
import io
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType

# Forcer l'encodage UTF-8 pour éviter les problèmes sur Windows
if sys.platform == "win32":
    # Forcer stdout et stderr à utiliser UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    parser.add_argument("--clean_logs", action="store_true", 
                       help="Clear old logs before starting")
    args = parser.parse_args()

    if args.clean_logs and os.path.exists("logs/experiment_data.json"):
        os.remove("logs/experiment_data.json")
        print("Cleared old logs")

    if not os.path.exists(args.target_dir):
        print(f"Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    print(f"DEMARRAGE SUR : {args.target_dir}")
    
    try:
        log_experiment(
            agent_name="System",
            model_used="system",  
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": "System startup",
                "output_response": f"Target directory: {args.target_dir}"
            },
            status="INFO"
        )
    except Exception as e:
        print(f"Warning: Could not log experiment: {e}")
    
    print("MISSION_COMPLETE")

    try:
        # Importer ici pour éviter les problèmes circulaires d'import
        from src.workflow.orchestrator import RefactoringOrchestrator
        
        orchestrator = RefactoringOrchestrator()
        result = orchestrator.execute(args.target_dir)
    
        if result.get("success"):
            files_processed = result.get('files_processed', 0)
            print(f"MISSION_COMPLETE - Processed {files_processed} files")
            sys.exit(0)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"MISSION_FAILED: {error_msg}")
            sys.exit(1)
        
    except ImportError as e:
        print(f"IMPORT_ERROR: {e}")
        print("Make sure all dependencies are installed and modules are in the correct location.")
        sys.exit(1)
    except Exception as e:
        print(f"SYSTEM_ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()