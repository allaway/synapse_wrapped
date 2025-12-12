"""
Check if keyring is properly installed and configured for SSO token caching.
"""

try:
    import keyring
    print("✓ keyring is installed")
    
    # Check if we can access the keyring
    try:
        # Try to get a test value (this will fail, but shows keyring works)
        keyring.get_password("test", "test")
        print("✓ keyring is accessible")
    except Exception as e:
        print(f"⚠️  keyring access test: {e}")
    
    # Check Snowflake connector
    try:
        import snowflake.connector
        print("✓ snowflake-connector-python is installed")
        
        # Check if secure storage is available
        try:
            from snowflake.connector.auth import AuthByKeyPair
            print("✓ Snowflake connector supports secure storage")
        except:
            print("⚠️  Snowflake connector secure storage not available")
            
    except ImportError:
        print("❌ snowflake-connector-python not found")
        
except ImportError:
    print("❌ keyring is NOT installed")
    print("   Install it with: pip install 'snowflake-connector-python[secure-local-storage]'")

print("\nNote: With keyring installed, SSO tokens should be cached automatically.")
print("If you're still being asked to log in every time, it might be because:")
print("1. The token has expired (tokens typically last 4 hours)")
print("2. The keyring backend isn't configured properly on your system")
print("3. The session is being created in a way that bypasses the cache")

