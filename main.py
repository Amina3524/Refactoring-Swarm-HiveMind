"""
Main entry point for The Refactoring Swarm
This file will be called by the correction bot with: python main.py --target_dir "./sandbox/dataset"
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import log_experiment, ActionType
from src.workflow.orchestrator import RefactoringOrchestrator

# Load environment variables
load_dotenv()


def validate_environment():
    """Validate that the environment is properly configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERROR: GOOGLE_API_KEY not found in .env file")
        print("Please create a .env file with your Gemini API key")
        sys.exit(1)
    return True


def main():
    """Main execution function."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="The Refactoring Swarm - Automated Code Refactoring System"
    )
    parser.add_argument(
        "--target_dir",
        type=str,
        required=True,
        help="Directory containing Python files to refactor"
    )
    parser.add_argument(
        "--clean_logs",
        action="store_true",
        help="Clear old logs before starting"
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum iterations per file (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    validate_environment()
    
    # Clean logs if requested
    log_file = Path("logs/experiment_data.json")
    if args.clean_logs and log_file.exists():
        log_file.unlink()
        print("🧹 Cleared old logs")
    
    # Validate target directory
    target_path = Path(args.target_dir)
    if not target_path.exists():
        print(f"❌ ERROR: Directory not found: {args.target_dir}")
        sys.exit(1)
    
    # Log system startup
    log_experiment(
        agent_name="System",
        model_used="system",
        action=ActionType.ANALYSIS,
        details={
            "input_prompt": "System startup",
            "output_response": f"Target directory: {args.target_dir}, Max iterations: {args.max_iterations}"
        },
        status="INFO"
    )
    
    print("=" * 60)
    print("🤖 THE REFACTORING SWARM")
    print("=" * 60)
    print(f"📁 Target: {args.target_dir}")
    print(f"🔄 Max iterations: {args.max_iterations}")
    print(f"📊 Logs: {log_file}")
    print("=" * 60)
    
    try:
        # Create and execute orchestrator
        orchestrator = RefactoringOrchestrator(max_iterations=args.max_iterations)
        result = orchestrator.execute(str(target_path))
        
        # Report results
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS")
        print("=" * 60)
        print(f"✅ Files processed: {result.get('files_processed', 0)}")
        print(f"✅ Files successful: {result.get('files_successful', 0)}")
        print(f"❌ Files failed: {result.get('files_failed', 0)}")
        
        if result.get("success"):
            print("\n🎉 MISSION_COMPLETE")
            sys.exit(0)
        else:
            print(f"\n❌ MISSION_FAILED: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ SYSTEM_ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Log the error
        log_experiment(
            agent_name="System",
            model_used="system",
            action=ActionType.DEBUG,
            details={
                "input_prompt": "System error occurred",
                "output_response": str(e)
            },
            status="FAILURE"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()