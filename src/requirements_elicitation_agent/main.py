"""
Main entry point for the Forge Requirements Assistant.

Can be run directly for CLI interaction or imported for programmatic use.
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from .graph import create_graph


def main():
    """Run the agent in CLI mode."""
    load_dotenv()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please set it in .env file or export it.")
        return
    
    print("=" * 60)
    print("Forge Requirements Assistant - CLI Mode")
    print("=" * 60)
    print("\nType 'exit' or 'quit' to end the session")
    print("Type 'show requirements' to see captured requirements\n")
    
    # Create graph
    graph = create_graph()
    config = {"configurable": {"thread_id": "cli-session"}}
    
    # Initialize
    print("Initializing...")
    for event in graph.stream({}, config, stream_mode="values"):
        if "messages" in event and event["messages"]:
            last_msg = event["messages"][-1]
            if isinstance(last_msg, AIMessage):
                print(f"\nAssistant: {last_msg.content}\n")
    
    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nThank you for using Forge Requirements Assistant!")
                break
            
            # Send to agent
            state = {"messages": [HumanMessage(content=user_input)]}
            
            print("\nAssistant: ", end="", flush=True)
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        print(last_msg.content)
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    main()
