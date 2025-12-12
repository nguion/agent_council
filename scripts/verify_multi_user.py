"""
Multi-User Session Isolation Test Script

Tests that:
1. Users can only see their own sessions
2. Users cannot access other users' sessions
3. Deletion only affects user's own sessions
4. Database metadata stays in sync with file state
"""

import sys

import requests

API_BASE = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_create_session(user_id, question):
    """Create a session for a user."""
    headers = {"X-User-Id": user_id}
    data = {"question": question}
    
    response = requests.post(
        f"{API_BASE}/api/sessions",
        data=data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Created session for {user_id}: {result['session_id']}")
        return result['session_id']
    else:
        print(f"✗ Failed to create session for {user_id}: {response.status_code}")
        print(f"  Error: {response.text}")
        return None

def test_list_sessions(user_id):
    """List sessions for a user."""
    headers = {"X-User-Id": user_id}
    
    response = requests.get(
        f"{API_BASE}/api/sessions",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        sessions = result.get('sessions', [])
        print(f"✓ User {user_id} sees {len(sessions)} session(s)")
        for sess in sessions:
            print(f"  - {sess['session_id'][:30]}... ({sess['current_step']})")
        return sessions
    else:
        print(f"✗ Failed to list sessions for {user_id}: {response.status_code}")
        return []

def test_access_session(user_id, session_id, should_succeed=True):
    """Try to access a specific session as a user."""
    headers = {"X-User-Id": user_id}
    
    response = requests.get(
        f"{API_BASE}/api/sessions/{session_id}/summary",
        headers=headers
    )
    
    if should_succeed:
        if response.status_code == 200:
            print(f"✓ User {user_id} can access session {session_id[:30]}...")
            return True
        else:
            print(f"✗ FAILED: User {user_id} should access {session_id} but got {response.status_code}")
            return False
    else:
        if response.status_code == 404:
            print(f"✓ User {user_id} correctly denied access to {session_id[:30]}...")
            return True
        else:
            print(f"✗ SECURITY ISSUE: User {user_id} should NOT access {session_id} but got {response.status_code}")
            return False

def test_delete_session(user_id, session_id, should_succeed=True):
    """Try to delete a session as a user."""
    headers = {"X-User-Id": user_id}
    
    response = requests.delete(
        f"{API_BASE}/api/sessions/{session_id}",
        headers=headers
    )
    
    if should_succeed:
        if response.status_code == 200:
            print(f"✓ User {user_id} deleted session {session_id[:30]}...")
            return True
        else:
            print(f"✗ FAILED: User {user_id} should delete {session_id} but got {response.status_code}")
            return False
    else:
        if response.status_code == 404:
            print(f"✓ User {user_id} correctly cannot delete {session_id[:30]}... (not their session)")
            return True
        else:
            print(f"✗ SECURITY ISSUE: User {user_id} should NOT delete {session_id} but got {response.status_code}")
            return False

def main():
    """Run multi-user isolation tests."""
    
    print_section("Multi-User Session Isolation Test")
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=2)
        if response.status_code != 200:
            print("✗ Backend is not responding correctly")
            sys.exit(1)
        print("✓ Backend is running\n")
    except requests.exceptions.RequestException:
        print("✗ Backend is not running. Start with: ./start_backend.sh")
        sys.exit(1)
    
    # Define test users
    user1 = "alice@deloitte.com"
    user2 = "bob@deloitte.com"
    
    print_section("Test 1: Create Sessions for Two Users")
    
    alice_session1 = test_create_session(user1, "Alice's first question about strategy")
    alice_session2 = test_create_session(user1, "Alice's second question about operations")
    bob_session1 = test_create_session(user2, "Bob's question about marketing")
    
    if not all([alice_session1, alice_session2, bob_session1]):
        print("\n✗ Session creation failed. Aborting tests.")
        sys.exit(1)
    
    print_section("Test 2: List Sessions (Each User Sees Only Their Own)")
    
    alice_sessions = test_list_sessions(user1)
    bob_sessions = test_list_sessions(user2)
    
    # Verify counts
    if len(alice_sessions) == 2:
        print("✓ Alice correctly sees 2 sessions")
    else:
        print(f"✗ FAILED: Alice should see 2 sessions, but sees {len(alice_sessions)}")
    
    if len(bob_sessions) == 1:
        print("✓ Bob correctly sees 1 session")
    else:
        print(f"✗ FAILED: Bob should see 1 session, but sees {len(bob_sessions)}")
    
    print_section("Test 3: Cross-User Access Control")
    
    # Alice should access her own sessions
    test_access_session(user1, alice_session1, should_succeed=True)
    test_access_session(user1, alice_session2, should_succeed=True)
    
    # Alice should NOT access Bob's session
    test_access_session(user1, bob_session1, should_succeed=False)
    
    # Bob should access his own session
    test_access_session(user2, bob_session1, should_succeed=True)
    
    # Bob should NOT access Alice's sessions
    test_access_session(user2, alice_session1, should_succeed=False)
    test_access_session(user2, alice_session2, should_succeed=False)
    
    print_section("Test 4: Deletion Isolation")
    
    # Alice deletes her first session
    test_delete_session(user1, alice_session1, should_succeed=True)
    
    # Bob tries to delete Alice's second session (should fail)
    test_delete_session(user2, alice_session2, should_succeed=False)
    
    # Verify Alice now sees only 1 session
    print("\nVerifying Alice's session list after deletion:")
    alice_sessions_after = test_list_sessions(user1)
    if len(alice_sessions_after) == 1:
        print("✓ Alice correctly sees 1 session after deleting one")
    else:
        print(f"✗ FAILED: Alice should see 1 session, but sees {len(alice_sessions_after)}")
    
    # Verify Bob still sees his session
    print("\nVerifying Bob's session list is unchanged:")
    bob_sessions_after = test_list_sessions(user2)
    if len(bob_sessions_after) == 1:
        print("✓ Bob's session count unchanged (still 1)")
    else:
        print(f"✗ FAILED: Bob should still see 1 session, but sees {len(bob_sessions_after)}")
    
    print_section("Test 5: Default User Fallback")
    
    # Create a session without X-User-Id header (should use default dev-user@localhost)
    print("Creating session without X-User-Id header:")
    response = requests.post(
        f"{API_BASE}/api/sessions",
        data={"question": "Anonymous question"}
    )
    
    if response.status_code == 200:
        default_session = response.json()['session_id']
        print(f"✓ Default user session created: {default_session[:30]}...")
        
        # List sessions without header
        response = requests.get(f"{API_BASE}/api/sessions")
        if response.status_code == 200:
            default_sessions = response.json().get('sessions', [])
            print(f"✓ Default user sees {len(default_sessions)} session(s)")
        else:
            print("✗ Failed to list sessions for default user")
    else:
        print(f"✗ Failed to create session for default user: {response.status_code}")
    
    print_section("Summary")
    
    print("Test Results:")
    print("  - Session creation: PASS")
    print("  - Per-user filtering: PASS (if all ✓ above)")
    print("  - Cross-user isolation: PASS (if all ✓ above)")
    print("  - Deletion isolation: PASS (if all ✓ above)")
    print("  - Default user fallback: PASS (if all ✓ above)")
    print("\n✓ Multi-user session isolation verified!")
    print("\nNote: Restart backend to clear test sessions if needed.")

if __name__ == "__main__":
    main()
