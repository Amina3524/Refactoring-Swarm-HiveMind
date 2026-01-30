"""Main entry point for The Refactoring Swarm
This file will be called by the correction bot with: python main.py --target_dir "./sandbox/dataset"
"""

import argparse
import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from src.workflow.orchestrator import RefactoringOrchestrator

# Load environment variables
load_dotenv()


def validate_environment():
    """Validate that the environment is properly configured."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env file")
        print("Please create a .env file with your Gemini API key")
        sys.exit(1)
    return True


def clean_logs():
    """Clean the experiment logs file."""
    log_file = Path("logs/experiment_data.json")
    if log_file.exists():
        # Create a backup before cleaning
        backup_file = Path(f"logs/experiment_data_backup_{os.getpid()}.json")
        try:
            with open(log_file, 'r') as f:
                existing_data = f.read()
                if existing_data.strip():
                    with open(backup_file, 'w') as backup:
                        backup.write(existing_data)
                    print(f"Backup created: {backup_file}")
        except:
            pass
        
        # Create empty logs array
        with open(log_file, 'w') as f:
            json.dump([], f, indent=4)
        print("Logs cleaned successfully")
    else:
        # Create empty logs file if it doesn't exist
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump([], f, indent=4)
        print("Empty logs file created")


def print_banner():
    """Print the application banner."""
    # Version ASCII uniquement - compatible Windows
    banner = """
========================================================================
               THE REFACTORING SWARM                      
         Automated Code Refactoring System                
========================================================================
    """
    print(banner)


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
        "--max_iterations",
        type=int,
        default=10,
        help="Maximum iterations per file (default: 10)"
    )
    parser.add_argument(
        "--clean_logs",
        action="store_true",
        help="Clean the experiment logs before starting"
    )
    
    args = parser.parse_args()
    
    # Clean logs if requested
    if args.clean_logs:
        clean_logs()
    
    # Validate environment
    validate_environment()
    
    # Validate target directory
    target_path = Path(args.target_dir)
    if not target_path.exists():
        print(f"ERROR: Directory not found: {args.target_dir}")
        sys.exit(1)
    
    # Show banner and configuration
    print_banner()
    print("=" * 60)
    print(f"Target directory: {args.target_dir}")
    print(f"Max iterations per file: {args.max_iterations}")
    print(f"Logs will be saved to: logs/experiment_data.json")
    if args.clean_logs:
        print(f"Logs were cleaned before execution")
    print("=" * 60)
    
    try:
        # Create and execute orchestrator
        orchestrator = RefactoringOrchestrator(max_iterations=args.max_iterations)
        result = orchestrator.execute(str(target_path))
        
        # Report results
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)
        print(f"Files processed: {result.get('files_processed', 0)}")
        print(f"Files successful: {result.get('files_successful', 0)}")
        print(f"Files failed: {result.get('files_failed', 0)}")
        
        if result.get("success") or result.get("files_successful", 0) > 0:
            print("\n" + "=" * 60)
            print("MISSION COMPLETE")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("MISSION FAILED")
            print("=" * 60)
            if result.get('error'):
                print(f"Error: {result.get('error')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\nSYSTEM ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()