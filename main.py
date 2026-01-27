import argparse
import sys
import os
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.workflow.orchestrator import RefactoringOrchestrator

load_dotenv()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_dir", type=str, required=True)
    parser.add_argument("--clean_logs", action="store_true", 
                       help="Clear old logs before starting")
    args = parser.parse_args()

    if args.clean_logs and os.path.exists("logs/experiment_data.json"):
        os.remove("logs/experiment_data.json")
        print(" Cleared old logs")

    if not os.path.exists(args.target_dir):
        print(f"Dossier {args.target_dir} introuvable.")
        sys.exit(1)

    print(f"DEMARRAGE SUR : {args.target_dir}")
    log_experiment(
    agent_name="System",
    model_used="system",  
    action=ActionType.ANALYSIS,     # Or use ActionType.ANALYSIS if you import it
    details={             # Changed from string to dict
        "input_prompt": "System startup",
        "output_response": f"Target directory: {args.target_dir}"
    },
    status="INFO"         # Added this
    )
    print("MISSION_COMPLETE")

    try:
       orchestrator = RefactoringOrchestrator()
       result = orchestrator.execute(args.target_dir)
    
       if result.get("success"):
          print(f"MISSION_COMPLETE - Processed {result.get('files_processed', 0)} files")
       else:
          print(f"MISSION_FAILED: {result.get('error', 'Unknown error')}")
          sys.exit(1)
        
    except Exception as e:
        print(f"SYSTEM_ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()