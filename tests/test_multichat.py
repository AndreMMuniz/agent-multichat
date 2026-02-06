import asyncio
import os
from graph import app_graph
from database import SessionLocal, engine, Base
from models import Conversation, Message

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

async def test_chat():
    print("--- Testing Multichat Agent ---")
    
    # Test Data
    user_id = "test_user_001"
    channel = "whatsapp"
    input_text = "Hello, I would like to know the status of my order #12345. It is delayed!"
    
    print(f"Input -> User: {user_id} | Channel: {channel}")
    print(f"Message: '{input_text}'")
    
    initial_state = {
        "messages": [],
        "current_input": input_text,
        "channel": channel,
        "user_id": user_id,
        "iteration_count": 0
    }
    
    print("\nProcessing...")
    try:
        # Run Graph
        result = await app_graph.ainvoke(initial_state)
        
        print("\n--- Agent Result ---")
        print(f"Intent Detected: {result.get('intent')}")
        print(f"Response: {result.get('response')}")
        print(f"Conversation ID: {result.get('conversation_id')}")
        
        # Verify DB Persistence
        print("\n--- Database Verification ---")
        db = SessionLocal()
        msgs = db.query(Message).filter(Message.conversation_id == result['conversation_id']).all()
        print(f"Found {len(msgs)} messages in conversation {result['conversation_id']}:")
        for m in msgs:
            print(f" - [{m.sender}]: {m.content[:50]}...")
            
        db.close()
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat())
