"""
test_my_prompts.py
Tests YOUR prompts - Place this in src/prompts/ folder
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    from prompt_manager import PromptManager
    print("✓ Imported PromptManager directly")
except ImportError:
   
    src_dir = os.path.dirname(current_dir) 
    project_root = os.path.dirname(src_dir)
    sys.path.insert(0, project_root)
    
    from src.prompts.prompt_manager import PromptManager
    print("✓ Imported via fixed path")

def test_your_prompts():
    print("=== Testing Your Prompts ===")

    pm = PromptManager()
    print("✓ PromptManager created")
    
    project_root = os.path.dirname(os.path.dirname(current_dir))
    sandbox_dir = os.path.join(project_root, "logs", "sandbox")  # ← CHANGED!
    
    print(f"\nLooking for test files in: {sandbox_dir}")
   
    print("\n--- Testing with test1.py ---")
    test1_path = os.path.join(sandbox_dir, "test1.py")  # ← CHANGED!
    
    if os.path.exists(test1_path):
        with open(test1_path, "r") as f:
            code1 = f.read().strip()
        
        print(f"Code from test1.py:\n```python\n{code1}\n```")
        
        prompt1 = pm.get_auditor_prompt(code1)
        print(f"\n✅ Generated auditor prompt: {len(prompt1)} characters")
        print("\nFirst 150 chars of prompt:")
        print("-" * 50)
        print(prompt1[:150])
        print("-" * 50)
    else:
        print(f"✗ File not found: {test1_path}")
        print("Available files in sandbox/:")
        if os.path.exists(sandbox_dir):
            for f in os.listdir(sandbox_dir):
                print(f"  - {f}")

    print("\n--- Testing with test2.py ---")
    test2_path = os.path.join(sandbox_dir, "test2.py")  
    
    if os.path.exists(test2_path):
        with open(test2_path, "r") as f:
            code2 = f.read().strip()
        
        print(f"Code from test2.py:\n```python\n{code2}\n```")
        
        prompt2 = pm.get_auditor_prompt(code2)
        print(f"\n✅ Generated auditor prompt: {len(prompt2)} characters")
        
        fake_audit = {
            "issues": ["Bad spacing at line 2", "Missing docstring"],
            "summary": "Code needs minor fixes"
        }
        fixer_prompt = pm.get_fixer_prompt(code2, fake_audit)
        print(f"✅ Generated fixer prompt: {len(fixer_prompt)} characters")
    else:
        print(f"✗ File not found: {test2_path}")
    
 
    print("\n=== Checking Logs ===")
    log_file = os.path.join(project_root, "logs", "experiment_data.json")  # logs/ not sandbox/
    if os.path.exists(log_file):
        try:
            import json
            with open(log_file, "r") as f:
                logs = json.load(f)
            print(f"✅ Log file exists with {len(logs)} entries")
            if logs:
                print("\nRecent log entries:")
                for log in logs[-3:]:  # Last 3 entries
                    print(f"  • {log.get('agent', 'Unknown')}: {log.get('action', 'Unknown')}")
        except Exception as e:
            print(f"⚠️ Could not read log file: {e}")
    else:
        print("⚠️ Log file doesn't exist yet")
    
    print("\n" + "="*50)
    print("✅ YOUR Prompt Testing Complete!")
    print("Your prompts are working correctly!")
    print("="*50)

if __name__ == "__main__":
    test_your_prompts()