#!/usr/bin/env python3
"""
Test runner for mspec app generator tests

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --verbose    # Run with verbose output
"""

import sys
import unittest
from pathlib import Path

# Add the repository root to the Python path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

if __name__ == "__main__":
    # Determine verbosity
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    verbosity = 2 if verbose else 1
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = repo_root / "tests"
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)