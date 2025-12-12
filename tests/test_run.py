"""
Test script to verify Synapse Wrapped setup.

This script will:
1. Test Snowflake connection
2. Test query execution
3. Generate a sample wrapped (if you provide a username)
"""

import json
import sys
from pathlib import Path

from synapse_wrapped.utils import get_data_from_snowflake
from synapse_wrapped.queries import get_user_id_from_username


def test_snowflake_connection(config_path=None):
    """Test Snowflake connection."""
    print("Testing Snowflake connection...")
    
    # Try to load config
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        print(f"✓ Loaded config from {config_path}")
    else:
        # Try to use streamlit secrets
        try:
            import streamlit as st
            config = None  # Will use streamlit secrets
            print("✓ Using Streamlit secrets")
        except:
            print("❌ No config file found and Streamlit not available")
            print("   Please create snowflake_config.json or set up .streamlit/secrets.toml")
            return False
    
    # Test with a simple query
    try:
        test_query = "SELECT 1 as test_value"
        result = get_data_from_snowflake(test_query, config)
        if not result.empty and 'test_value' in result.columns:
            print(f"✓ Snowflake connection successful! (Test query returned: {result.iloc[0]['test_value']})")
        else:
            print(f"✓ Snowflake connection successful! (Query executed)")
        return True
    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_user_lookup(username, config_path=None):
    """Test looking up a user."""
    print(f"\nTesting user lookup for: {username}")
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = None
    
    try:
        query = get_user_id_from_username(username)
        result = get_data_from_snowflake(query, config)
        
        if not result.empty:
            user_id = result.iloc[0]['user_id']
            user_name = result.iloc[0].get('user_name', username)
            print(f"✓ Found user: {user_name} (ID: {user_id})")
            return True
        else:
            print(f"❌ User '{username}' not found in Synapse")
            return False
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Synapse Wrapped - Setup Test")
    print("=" * 60)
    
    # Check for config file
    config_path = "snowflake_config.json"
    if not Path(config_path).exists():
        print(f"\n⚠️  Config file '{config_path}' not found.")
        print("   You can:")
        print("   1. Create snowflake_config.json (see snowflake_config.json.example)")
        print("   2. Set up .streamlit/secrets.toml (see .streamlit/secrets.toml.example)")
        print("\n   Continuing with Streamlit secrets if available...\n")
        config_path = None
    
    # Test connection
    if not test_snowflake_connection(config_path):
        print("\n❌ Setup incomplete. Please configure Snowflake connection.")
        sys.exit(1)
    
    # Test user lookup if username provided
    if len(sys.argv) > 1:
        username = sys.argv[1]
        test_user_lookup(username, config_path)
        print(f"\n✓ Ready to generate wrapped for {username}!")
        print(f"\n   Run: python -m synapse_wrapped.cli --username {username} --year 2024")
    else:
        print("\n✓ Setup complete! Ready to generate wrapped.")
        print("\n   Usage examples:")
        print("   - Single user: python -m synapse_wrapped.cli --username user@example.com --year 2024")
        print("   - Batch: python -m synapse_wrapped.cli --batch usernames.txt --year 2024")
    
    print("\n" + "=" * 60)

