"""
Test script to verify SSO token caching works correctly.
"""

import keyring
from synapse_wrapped.utils import get_data_from_snowflake

print("=" * 60)
print("SSO Token Cache Test")
print("=" * 60)

# Test 1: Check if keyring is working
print("\n1. Testing keyring...")
try:
    # Try to set and get a test value
    keyring.set_password("test", "test_key", "test_value")
    value = keyring.get_password("test", "test_key")
    if value == "test_value":
        print("   ✓ keyring is working")
        keyring.delete_password("test", "test_key")
    else:
        print("   ❌ keyring test failed")
except Exception as e:
    print(f"   ❌ keyring error: {e}")

# Test 2: Run a query (this should cache the token if it's not already cached)
print("\n2. Running a test query (this will authenticate if needed)...")
try:
    result = get_data_from_snowflake("SELECT 1 as test")
    print(f"   ✓ Query successful: {result.iloc[0]['test']}")
except Exception as e:
    print(f"   ❌ Query failed: {e}")
    print("   (This is expected if you need to authenticate)")

# Test 3: Check for cached tokens (Snowflake uses various key formats)
print("\n3. Checking for cached tokens...")
account = "mqzfhld-vp00034"
user = "robert.allaway@sagebase.org"

# Try different possible key formats
possible_keys = [
    f"snowflake_{account}_{user}_id_token",
    f"snowflake_{account.replace('-', '_')}_{user}_id_token",
    f"snowflake_id_token_{account}_{user}",
]

found_token = False
for key in possible_keys:
    try:
        token = keyring.get_password("snowflake", key)
        if token:
            print(f"   ✓ Found token with key: {key}")
            found_token = True
            break
    except:
        pass

if not found_token:
    print("   ⚠️  No cached token found (this is normal for first run)")
    print("   The token should be cached after successful authentication")

# Test 4: Run another query to see if it uses cached token
print("\n4. Running second query (should use cached token if available)...")
try:
    result = get_data_from_snowflake("SELECT 2 as test")
    print(f"   ✓ Query successful: {result.iloc[0]['test']}")
    print("   (If no browser opened, the cached token was used!)")
except Exception as e:
    print(f"   ❌ Query failed: {e}")

print("\n" + "=" * 60)
print("Note: SSO tokens typically last 4 hours.")
print("If you're prompted every time, the token may be expiring quickly")
print("or the keyring backend may need configuration.")
print("=" * 60)

