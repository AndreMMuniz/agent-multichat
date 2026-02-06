"""
Test script to trace graph execution.
Invokes app_graph directly and prints state updates.
"""
import asyncio
from graph import app_graph
from state import ChatState
import uuid

async def test_graph():
    print("=== Testing Graph Execution Flow ===")
    
    # Mock input
    user_id = f"test_graph_{uuid.uuid4().hex[:4]}"
    print(f"User ID: {user_id}")
    
    initial_state = {
        "messages": [],
        "current_input": "Eu gosto de programar em Python",
        "channel": "whatsapp",
        "user_id": user_id,
        "iteration_count": 0
    }
    
    config = {
        "configurable": {"thread_id": f"test_{user_id}"},
        "recursion_limit": 25
    }
    
    print("Invoking graph...")
    try:
        # Stream the graph execution to see steps
        async for event in app_graph.astream(initial_state, config=config):
            for key, value in event.items():
                print(f"\n[Node Completed]: {key}")
                if key == "summarize_conversation":
                    print(f"  > Summary Generated: {value.get('should_summarize')}")
                    if value.get('conversation_summary'):
                        print(f"  > Summary Content: {value.get('conversation_summary')[:50]}...")
                elif key == "save_user_context":
                    print("  > Context Saved")
                    
        print("\n=== Graph Execution Completed ===")
        
    except Exception as e:
        print(f"\n❌ Graph Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph())
