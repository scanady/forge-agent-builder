import sys
import os

def test_debug_env():
    print(f"Executable: {sys.executable}")
    print(f"Path: {sys.path}")
    print(f"CWD: {os.getcwd()}")
    try:
        import forge_requirements_builder
        print(f"Package found: {forge_requirements_builder}")
    except ImportError as e:
        print(f"Package not found: {e}")
    
    assert True
