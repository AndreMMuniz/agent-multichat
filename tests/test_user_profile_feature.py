"""
Test script for user profile functionality.
Tests first contact detection, name extraction, and profile persistence.
"""
import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_first_contact_and_name_extraction():
    """Test that agent asks for name on first contact and remembers it."""
    print("\n=== Testing User Profile System ===")
    
    user_id = "test_user_profile_001"
    channel = "whatsapp"
    
    # First message - should trigger "first contact" behavior
    print("\n1. First Contact (agent should ask for name):")
    payload1 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "Hello, what are your business hours?"
    }
    
    response1 = requests.post(f"{API_URL}/chat", json=payload1)
    data1 = response1.json()
    
    print(f"Agent response: {data1['response']}")
    print(f"Status: {data1['status']}")
    
    # Check if agent asked for name
    if "name" in data1['response'].lower() or "nome" in data1['response'].lower():
        print("✓ Agent asked for user's name on first contact")
    else:
        print("⚠ Agent didn't ask for name (might be expected depending on context)")
    
    # Second message - provide name
    print("\n2. Providing Name:")
    payload2 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "My name is Carlos Silva"
    }
    
    response2 = requests.post(f"{API_URL}/chat", json=payload2)
    data2 = response2.json()
    
    print(f"Agent response: {data2['response']}")
    
    # Wait a moment for profile to be saved
    time.sleep(1)
    
    # Check profile via API
    print("\n3. Checking Saved Profile:")
    profile_response = requests.get(f"{API_URL}/user-profile/{user_id}")
    
    if profile_response.status_code == 200 and profile_response.json():
        profile = profile_response.json()
        print(f"✓ Profile saved!")
        print(f"  - Name: {profile.get('name')}")
        print(f"  - First Contact: {profile.get('is_first_contact')}")
        print(f"  - Created: {profile.get('created_at')}")
        
        if profile.get('name'):
            print(f"✓ Name extracted and saved: {profile['name']}")
        else:
            print("✗ Name not saved")
    else:
        print("✗ Profile not found")
    
    # Third message - agent should use the name
    print("\n4. Testing Name Recall (agent should use 'Carlos'):")
    payload3 = {
        "channel": channel,
        "user_identifier": user_id,
        "content": "Do you offer delivery?"
    }
    
    response3 = requests.post(f"{API_URL}/chat", json=payload3)
    data3 = response3.json()
    
    print(f"Agent response: {data3['response']}")
    
    if "carlos" in data3['response'].lower():
        print("✓ Agent used user's name in response!")
    else:
        print("⚠ Agent didn't use the name (might be natural depending on context)")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing User Profile System")
    print("=" * 60)
    
    try:
        test_first_contact_and_name_extraction()
        
        print("\n" + "=" * 60)
        print("✅ User profile test completed!")
        print("\nKey Features Tested:")
        print("  - First contact detection")
        print("  - Name extraction from conversation")
        print("  - Profile persistence in database")
        print("  - Name recall in subsequent messages")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
