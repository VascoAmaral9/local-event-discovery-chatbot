"""Interactive CLI for chatting with the event recommendation agent."""
import asyncio
import sys
from pathlib import Path
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents import get_agent
from src.database import init_db


async def main():
    """Run interactive chat session."""
    print("=" * 60)
    print("🤖 Event Recommendation Chatbot")
    print("=" * 60)
    print("\nInitializing...")
    
    # Initialize database
    init_db()
    
    # Get agent
    agent = get_agent()
    
    # Create a session ID for this conversation
    session_id = str(uuid.uuid4())
    
    print("✅ Agent ready!\n")
    
    print("Ask me about local events! Type 'exit' or 'quit' to end.\n")
    print("Examples:")
    print("  - What events are happening this week?")
    print("  - Show me music events")
    print("  - What's happening in Lisbon?")
    print("  - Tell me about upcoming events\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye! Have fun at the events!")
                break
            
            # Get agent response with session ID
            print("\n🤖 Agent: ", end="", flush=True)
            response = await agent.chat(user_input, session_id=session_id)
            response_text = agent.print_response(response)
            print(response_text)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
