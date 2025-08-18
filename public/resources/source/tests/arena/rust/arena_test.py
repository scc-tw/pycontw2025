#!/usr/bin/env python3
"""
Unified Arena Testing and Build Management Tool

This script provides a modular interface for building, testing, and demonstrating
the glibc arena memory leak testing library across all Python environments.

This is the main entry point that coordinates between the modular components:
- arena_manager.py: Core management functionality  
- arena_builder.py: Build management
- arena_tester.py: Testing functionality
- arena_demo.py: Demonstration and validation
- arena_cli.py: Command-line interface

For backwards compatibility, running without arguments defaults to test mode.
"""

from pathlib import Path

# Import the CLI module which coordinates everything
from arena_cli import ArenaCLI

# For backwards compatibility, also import quick_test function
from arena_tester import ArenaTester

def quick_test():
    """Quick test function for interactive use."""
    tester = ArenaTester(Path(__file__).parent)
    return tester.quick_test()

def main():
    """Main entry point."""
    # Use the CLI to handle all commands
    cli = ArenaCLI(Path(__file__).parent)
    cli.run()

if __name__ == "__main__":
    main()
