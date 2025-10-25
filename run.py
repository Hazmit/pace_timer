#!/usr/bin/env python3
"""
Run script for Pace Timer application
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
from pace_timer import main

if __name__ == "__main__":
    main()

