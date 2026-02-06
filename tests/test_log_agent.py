import asyncio
from graph import app_graph

async def test_log_agent():
    # Sample log simulating a Coolify/SSH error
    sample_log = """
    2026-02-02 14:00:01 ERROR: Connection failed.
    Permission denied (publickey).
    fatal: Could not read from remote repository.
    Please make sure you have the correct access rights and the repository exists.
    [Coolify] Verify your private key settings.
    """
    
    print("--- Testing Log Analysis Agent ---")
    inputs = {
        "raw_log": sample_log,
        "error_summary": "",
        "diagnosis": "",
        "fix_action": "",
        "is_technical": False,
        "iteration_count": 0,
        "is_safe": False,
        "security_review": ""
    }
    
    try:
        final_state = await app_graph.ainvoke(inputs)
        
        print("\n=== RESULT ===")
        print(f"Error: {final_state.get('error_summary')}")
        print(f"Diagnosis: {final_state.get('diagnosis')}")
        print(f"Fix: {final_state.get('fix_action')}")
        print(f"Safe: {final_state.get('is_safe')}")
        print(f"Review: {final_state.get('security_review')}")
        print("==============")
        
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_log_agent())
