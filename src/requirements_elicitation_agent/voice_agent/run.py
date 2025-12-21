"""
Run the Voice Agent Server

Standalone script to start the voice-enabled requirements assistant.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.requirements_elicitation_agent.graph import create_graph
from src.requirements_elicitation_agent.voice_agent.server import create_voice_app


def main():
    import uvicorn
    
    # Create the agent graph
    print("🔥 Initializing Forge Requirements Assistant...")
    graph = create_graph()
    
    # Get static files directory
    static_dir = Path(__file__).parent / "web"
    
    # Create the app
    app = create_voice_app(graph, static_dir=static_dir)
    
    print("\n" + "=" * 60)
    print("🎤 Voice Agent Server Starting")
    print("=" * 60)
    print("\n📍 Open http://localhost:8000 in your browser")
    print("🎙️  Allow microphone access when prompted")
    print("🛑 Press Ctrl+C to stop\n")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
