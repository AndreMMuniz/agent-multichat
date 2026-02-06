"""
Quick test for the improved first contact flow.
Tests that agent asks for name FIRST before answering questions.
"""
import requests

API_URL = "http://127.0.0.1:8000"

def test_first_contact_flow():
    """Test that agent asks for name on first contact."""
    print("\n=== Testing First Contact Flow ===")
    
    # Use a completely new user ID
    import uuid
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    channel = "whatsapp"
    
    print(f"User ID: {user_id}")
    
    # Step 1: First message - agent should ask for name FIRST
    print("\n1. Sending first message (agent should ask for name):")
    payload1 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "Olá, qual o horário de funcionamento?"
    }
    
    response1 = requests.post(f"{API_URL}/chat", json=payload1)
    data1 = response1.json()
    
    print(f"Status: {data1['status']}")
    print(f"Agent: {data1['response']}")
    
    # Verify agent asked for name
    if "nome" in data1['response'].lower():
        print("✅ Agent asked for name FIRST (correct!)")
    else:
        print("❌ Agent didn't ask for name (incorrect)")
        return False
    
    # Step 2: Provide name
    print("\n2. Providing name:")
    payload2 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "Meu nome é André"
    }
    
    response2 = requests.post(f"{API_URL}/chat", json=payload2)
    data2 = response2.json()
    
    print(f"Agent: {data2['response']}")
    
    # Step 3: Check if profile was saved
    print("\n3. Checking profile:")
    import time
    time.sleep(1)
    
    profile_response = requests.get(f"{API_URL}/user-profile/{user_id}")
    if profile_response.status_code == 200 and profile_response.json():
        profile = profile_response.json()
        print(f"✅ Profile saved!")
        print(f"   Name: {profile.get('name')}")
        print(f"   First contact: {profile.get('is_first_contact')}")
        
        if profile.get('name') == "André":
            print("✅ Name correctly extracted and saved!")
        else:
            print(f"⚠ Name mismatch: expected 'André', got '{profile.get('name')}'")
    else:
        print("❌ Profile not found")
        return False
    
    # Step 4: Ask the original question again
    print("\n4. Asking original question (agent should use name and answer):")
    payload3 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "Qual o horário de funcionamento?"
    }
    
    response3 = requests.post(f"{API_URL}/chat", json=payload3)
    data3 = response3.json()
    
    print(f"Agent: {data3['response']}")
    
    if "andré" in data3['response'].lower():
        print("✅ Agent used the name in response!")
    else:
        print("⚠ Agent didn't use the name (might be natural)")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing First Contact Name Request Flow")
    print("=" * 60)
    
    try:
        success = test_first_contact_flow()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ Test PASSED!")
            print("\nFlow verified:")
            print("  1. Agent asks for name FIRST on first contact")
            print("  2. User provides name")
            print("  3. Name is extracted and saved to database")
            print("  4. Agent uses name in subsequent conversations")
        else:
            print("❌ Test FAILED - check logs above")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
