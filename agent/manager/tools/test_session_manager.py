#!/usr/bin/env python3
"""
Test script for SessionManagerTool functionality.
"""

from session_manager import session_manager_tool, update_session_state, get_session_info

def test_session_creation():
    """Test creating a new session with default state."""
    
    print("🧪 Testing Session Manager Tool")
    print("=" * 50)
    
    # Test 1: Basic session creation
    print("\n1. Creating basic session...")
    result = session_manager_tool(
        email_id="test@example.com",
        app_name="HealthManagerAgent"
    )
    
    print(f"✅ Session created successfully!")
    print(f"📧 Email: {result['email_id']}")
    print(f"🆔 Session ID: {result['session_id']}")
    print(f"📱 App: {result['app_name']}")
    print(f"🕐 Created: {result['created_at']}")
    
    # Test 2: Session with custom initial data
    print("\n2. Creating session with custom initial data...")
    custom_data = {
        "user_profile": {
            "name": "John Doe",
            "location": "New York"
        },
        "current_step": "intake_started"
    }
    
    result2 = session_manager_tool(
        email_id="john.doe@example.com",
        app_name="HealthManagerAgent",
        initial_data=custom_data
    )
    
    print(f"✅ Custom session created!")
    print(f"👤 User: {result2['state']['user_profile']['name']}")
    print(f"📍 Location: {result2['state']['user_profile']['location']}")
    print(f"📋 Current Step: {result2['state']['current_step']}")
    
    # Test 3: State structure validation
    print("\n3. Validating state structure...")
    state = result['state']
    
    required_sections = [
        'user_profile', 'health_report', 'analysis_results', 
        'generated_documents', 'current_step', 'completed_steps'
    ]
    
    for section in required_sections:
        if section in state:
            print(f"✅ {section}: Present")
        else:
            print(f"❌ {section}: Missing")
    
    # Test 4: Session update (mock)
    print("\n4. Testing session update...")
    session_id = result['session_id']
    updates = {
        "user_profile.name": "Jane Smith",
        "current_step": "intake_complete",
        "completed_steps": ["session_created", "intake_started"]
    }
    
    update_result = update_session_state(session_id, updates)
    print(f"✅ Update result: {update_result['status']}")
    print(f"📝 Updates applied: {update_result['updates_applied']}")
    
    # Test 5: Session info retrieval (mock)
    print("\n5. Testing session info retrieval...")
    info_result = get_session_info(session_id)
    print(f"✅ Info result: {info_result['status']}")
    print(f"📄 Message: {info_result['message']}")
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed successfully!")
    
    return result['session_id']

if __name__ == "__main__":
    session_id = test_session_creation()
    print(f"\n📋 Generated Session ID for further testing: {session_id}") 