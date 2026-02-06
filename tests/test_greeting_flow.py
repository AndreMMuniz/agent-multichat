"""
Test script for the known user greeting flow.
"""
import requests
import uuid
import time

API_URL = "http://127.0.0.1:8000"

def test_greeting_flow():
    print("\n=== Testing Known User Greeting Flow ===")
    
    # Setup: Create a user and profile first
    user_id = f"test_greet_{uuid.uuid4().hex[:8]}"
    channel = "whatsapp"
    name = "Mariana"
    
    print(f"User ID: {user_id}")
    
    # 1. Establish profile
    print("\n1. Establishing profile...")
    # First msg
    requests.post(f"{API_URL}/chat", json={
        "channel": channel,
        "user_identifier": user_id,
        "content": "Olá"
    })
    # Provide name
    requests.post(f"{API_URL}/chat", json={
        "channel": channel,
        "user_identifier": user_id,
        "content": f"Meu nome é {name}"
    })
    
    time.sleep(1) # Wait for persist
    
    # Verify profile
    prof = requests.get(f"{API_URL}/user-profile/{user_id}").json()
    if not prof or prof.get('name') != name:
        print("❌ Failed to setup profile. Aborting.")
        return False
        
    print(f"✓ Profile ready for {name}")
    
    # 2. Test Greeting (The specific request)
    print("\n2. Testing 'Oi voltei' (Should trigger special greeting):")
    resp = requests.post(f"{API_URL}/chat", json={
        "channel": channel,
        "user_identifier": user_id,
        "content": "Oi voltei"
    }).json()
    
    print(f"Agent: {resp['response']}")
    
    expected_phrase = f"Oi {name}, que bom tê-lo de volta! Como posso ajudar?"
    if resp['response'] == expected_phrase:
        print("✅ Success! Agent gave the specific welcoming response.")
    else:
        print(f"❌ Failed. Expected: '{expected_phrase}'")
        print(f"   Got: '{resp['response']}'")
        return False

    # 3. Test Specific Question (Should NOT trigger generic greeting)
    print("\n3. Testing specific question (Should get normal answer):")
    resp = requests.post(f"{API_URL}/chat", json={
        "channel": channel,
        "user_identifier": user_id,
        "content": "Qual o status do meu pedido?"
    }).json()
    
    print(f"Agent: {resp['response']}")
    
    if "que bom tê-lo de volta" not in resp['response']:
        print("✅ Success! Agent gave a contextual answer.")
    else:
        print("❌ Failed. Agent gave generic greeting for a specific question.")
        return False
        
    return True

if __name__ == "__main__":
    try:
        if test_greeting_flow():
            print("\n✅ All greeting tests passed!")
        else:
            print("\n❌ Greeting tests failed.")
    except Exception as e:
        print(f"Error: {e}")
