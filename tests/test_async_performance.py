"""
Test script to verify async execution of graph nodes.
Simulates concurrent requests to ensure no blocking.
"""

import asyncio
import time
from graph import app_graph

async def simulate_request(user_id: str, message: str):
    """Simulate a single chat request."""
    start = time.time()
    
    initial_state = {
        "messages": [],
        "current_input": message,
        "channel": "test",
        "user_id": user_id,
        "iteration_count": 0
    }
    
    config = {
        "configurable": {"thread_id": f"user_{user_id}"},
        "recursion_limit": 25
    }
    
    try:
        result = await app_graph.ainvoke(initial_state, config=config)
        elapsed = time.time() - start
        print(f"✓ User {user_id}: Completed in {elapsed:.2f}s")
        return elapsed
    except Exception as e:
        print(f"✗ User {user_id}: Error - {e}")
        return None

async def test_concurrent_execution():
    """Test that multiple requests can run concurrently without blocking."""
    print("Testing concurrent execution (should complete in ~1-2s total, not 5s+)...")
    print("If this takes >3s, there's blocking I/O happening.\n")
    
    start = time.time()
    
    # Simulate 5 concurrent users
    tasks = [
        simulate_request("user1", "Olá, qual o horário?"),
        simulate_request("user2", "Preciso de ajuda"),
        simulate_request("user3", "Quais são os preços?"),
        simulate_request("user4", "Boa tarde"),
        simulate_request("user5", "Informações sobre produtos"),
    ]
    
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start
    successful = [r for r in results if r]
    
    if not successful:
        print("\n✗ CRITICAL: All requests failed!")
        print("Check that the database is running and nodes are working correctly.")
        return
    
    avg_time = sum(successful) / len(successful)
    
    print(f"\n{'='*50}")
    print(f"Successful requests: {len(successful)}/5")
    print(f"Total wall time: {total_time:.2f}s")
    print(f"Average request time: {avg_time:.2f}s")
    print(f"{'='*50}\n")
    
    if total_time < avg_time * 2:
        print("✓ PASS: Requests executed concurrently (non-blocking)")
    else:
        print("✗ FAIL: Requests appear to be blocking each other")
        print("  This suggests synchronous DB operations are blocking the event loop")

if __name__ == "__main__":
    asyncio.run(test_concurrent_execution())
