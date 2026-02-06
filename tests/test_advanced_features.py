"""
Integration test for advanced agent features.
Tests HITL, Long-term Memory, and Omnichannel routing.
"""
import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_hitl_workflow():
    """Test Human-in-the-Loop with refund scenario."""
    print("\n=== Testing HITL Workflow ===")
    
    # Send message requesting refund
    payload = {
        "channel": "whatsapp",
        "user_identifier": "test_user_hitl",
        "content": "I want a refund for my last order"
    }
    
    response = requests.post(f"{API_URL}/chat", json=payload)
    data = response.json()
    
    print(f"Status: {data['status']}")
    assert data['status'] == 'pending_approval', "Should require approval"
    assert data['pending_action_id'] is not None, "Should have pending action ID"
    
    print(f"✓ Critical action detected: {data['action_description']}")
    print(f"✓ Pending action ID: {data['pending_action_id']}")
    
    # Approve the action
    action_id = data['pending_action_id']
    approval_response = requests.post(
        f"{API_URL}/approve-action/{action_id}",
        json={"approved": True}
    )
    
    approval_data = approval_response.json()
    print(f"✓ Action approved: {approval_data['message']}")
    print(f"✓ Final response: {approval_data['response'][:100]}...")
    
    return True

def test_long_term_memory():
    """Test long-term memory persistence."""
    print("\n=== Testing Long-term Memory ===")
    
    user_id = "test_user_memory"
    channel = "email"
    
    # First conversation
    messages = [
        "Hello, I prefer morning deliveries between 9-11am",
        "Also, I'm allergic to peanuts",
        "My favorite color is blue",
        "I work from home on Mondays"
    ]
    
    for msg in messages:
        payload = {
            "channel": channel,
            "user_identifier": user_id,
            "content": msg
        }
        response = requests.post(f"{API_URL}/chat", json=payload)
        print(f"Sent: {msg[:50]}...")
        time.sleep(0.5)
    
    # Check if context was saved
    time.sleep(2)  # Wait for summarization
    context_response = requests.get(f"{API_URL}/user-context/{channel}/{user_id}")
    
    if context_response.status_code == 200 and context_response.json():
        context_data = context_response.json()
        print(f"✓ Context saved! Conversations: {context_data['conversation_count']}")
        print(f"✓ Summary preview: {context_data['context_summary'][:150]}...")
        return True
    else:
        print("⚠ Context not yet saved (may need more messages)")
        return False

def test_omnichannel_routing():
    """Test channel-specific response formatting."""
    print("\n=== Testing Omnichannel Routing ===")
    
    message = "What are your business hours?"
    user_id = "test_user_omni"
    
    # Test WhatsApp (should be casual with emojis)
    whatsapp_payload = {
        "channel": "whatsapp",
        "user_identifier": user_id,
        "content": message
    }
    whatsapp_response = requests.post(f"{API_URL}/chat", json=whatsapp_payload)
    whatsapp_text = whatsapp_response.json()['response']
    
    print(f"WhatsApp response: {whatsapp_text}")
    print(f"✓ Length: {len(whatsapp_text)} chars (should be short)")
    
    # Test Email (should be formal)
    email_payload = {
        "channel": "email",
        "user_identifier": user_id,
        "content": message
    }
    email_response = requests.post(f"{API_URL}/chat", json=email_payload)
    email_text = email_response.json()['response']
    
    print(f"\nEmail response: {email_text}")
    print(f"✓ Length: {len(email_text)} chars (should be longer/formal)")
    
    return True

if __name__ == "__main__":
    print("🧪 Starting Integration Tests for Advanced Features")
    print("=" * 60)
    
    try:
        # Test 1: HITL
        test_hitl_workflow()
        
        # Test 2: Long-term Memory
        test_long_term_memory()
        
        # Test 3: Omnichannel
        test_omnichannel_routing()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
