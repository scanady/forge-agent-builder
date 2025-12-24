import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Set dummy API key for testing
os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing"
