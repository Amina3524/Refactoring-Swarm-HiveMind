"""
Auto-generated tests for test_messy_code.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the module
import test_messy_code


def test_import():
    """Test that the module can be imported."""
    assert test_messy_code is not None


def test_no_syntax_errors():
    """Test that there are no syntax errors."""
    # If we got here, syntax is OK
    assert True
