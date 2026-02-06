from graph import app_graph

async def verify_history():
    config = {"configurable": {"thread_id": "thread_1"}}
    
    print("--- State History ---")
    try:
        # Get history
        history = list(app_graph.get_state_history(config))
        if not history:
            print("No history found for thread_1 (Expected if never run).")
        
        for state_snapshot in history:
            print(f"--- Step: {state_snapshot.next} ---")
            print(f"Draft length: {len(state_snapshot.values.get('draft', ''))}")
            print(f"Iteration: {state_snapshot.values.get('iteration_count', 0)}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error reading history: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_history())
