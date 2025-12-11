"""
Utility functions for Synapse Wrapped.
"""

from snowflake.snowpark import Session
from typing import Dict, Optional
import pandas as pd

# Global session cache to reuse connections
_session_cache = {}


def connect_to_snowflake(snowflake_config: Optional[Dict] = None, cache_key: Optional[str] = None):
    """
    Establishes a connection to Snowflake with session caching.
    
    Args:
        snowflake_config: Optional dict with Snowflake config.
                         If None, tries to use streamlit secrets (if available).
        cache_key: Optional key to cache the session. If None, uses config hash.
    
    Returns:
        Session: A Snowflake session object.
    """
    # Create cache key
    if cache_key is None:
        if snowflake_config is None:
            cache_key = "streamlit_secrets"
        else:
            # Create a simple hash from config values
            cache_key = str(sorted(snowflake_config.items()))
    
    # Return cached session if available and still valid
    if cache_key in _session_cache:
        try:
            session = _session_cache[cache_key]
            # Test if session is still valid
            session.sql("SELECT 1").collect()
            return session
        except:
            # Session expired, remove from cache
            del _session_cache[cache_key]
    
    # Create new session
    if snowflake_config is None:
        try:
            # Try to use streamlit secrets if available
            import streamlit as st
            config = dict(st.secrets.snowflake)
        except (ImportError, AttributeError, KeyError):
            raise ValueError(
                "No Snowflake config provided and streamlit secrets not available. "
                "Please provide snowflake_config parameter."
            )
    else:
        config = dict(snowflake_config)  # Make a copy
    
    # Ensure we're using the cached token from keyring
    # The keyring package should automatically cache and reuse the SSO token
    # when authenticator="externalbrowser" is set. The token is cached per
    # (account, user) combination and typically lasts 4 hours.
    # 
    # Note: If you're still being prompted every time, it might be because:
    # 1. The token expired (tokens last ~4 hours)
    # 2. The keyring backend needs configuration
    # 3. The account/user combination changed
    session = Session.builder.configs(config).create()
    
    # Cache the session
    _session_cache[cache_key] = session
    
    return session


def get_data_from_snowflake(query: str, snowflake_config: Optional[Dict] = None):
    """
    Retrieve data from Snowflake based on the provided SQL query.
    Uses cached sessions to avoid repeated authentication.
    
    Args:
        query: SQL query string
        snowflake_config: Optional Snowflake connection config dict
    
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    session = connect_to_snowflake(snowflake_config)
    df = session.sql(query).to_pandas()
    return df


def close_all_sessions():
    """
    Close all cached Snowflake sessions.
    Useful for cleanup or when you want to force re-authentication.
    """
    global _session_cache
    for session in _session_cache.values():
        try:
            session.close()
        except:
            pass
    _session_cache.clear()

