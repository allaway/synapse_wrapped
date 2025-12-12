"""
Example usage of Synapse Wrapped.

This script demonstrates how to generate wrapped visualizations
for single users and batches of users.
"""

from synapse_wrapped import generate_wrapped, generate_wrapped_batch

# Example 1: Generate wrapped for a single user
# Note: You'll need to provide your Snowflake configuration
snowflake_config = {
    "user": "your_username",
    "password": "your_password",
    "account": "your-account",
    "warehouse": "COMPUTE_XSMALL"
}

# Single user example
try:
    output_path = generate_wrapped(
        username="user@example.com",
        year=2024,
        output_path="example_wrapped_2024.html",
        snowflake_config=snowflake_config,
        include_audio=True
    )
    print(f"Generated wrapped: {output_path}")
except Exception as e:
    print(f"Error: {e}")

# Example 2: Batch generation
usernames = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

try:
    output_files = generate_wrapped_batch(
        usernames=usernames,
        year=2024,
        output_dir="wrapped_output",
        snowflake_config=snowflake_config,
        include_audio=True
    )
    print(f"Generated {len(output_files)} wrapped visualizations")
except Exception as e:
    print(f"Error: {e}")

