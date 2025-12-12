"""
Validate all queries in synapse_wrapped package.
Tests execution, data return, and basic sanity checks.
"""

import sys
from datetime import datetime
import tomllib
from pathlib import Path

sys.path.insert(0, '..')  # Access parent's .streamlit/secrets.toml

from synapse_wrapped.queries import *
from synapse_wrapped.utils import get_data_from_snowflake, connect_to_snowflake

# Load Snowflake config from parent's secrets.toml
SECRETS_PATH = Path('..') / '.streamlit' / 'secrets.toml'
with open(SECRETS_PATH, 'rb') as f:
    secrets = tomllib.load(f)
    SNOWFLAKE_CONFIG = secrets['snowflake']

TEST_USER_ID = 3514384  # james.moon
TEST_USERNAME = "james.moon"
TEST_YEAR = 2025
START_DATE = f"{TEST_YEAR}-01-01"
END_DATE = f"{TEST_YEAR}-12-31"

def validate_query(query_name, query_func, *args):
    """Execute query and validate results."""
    print(f"\n{'='*60}")
    print(f"Testing: {query_name}")
    print(f"{'='*60}")

    try:
        # Get query SQL
        query_sql = query_func(*args)
        print(f"Query SQL (first 200 chars):\n{query_sql[:200]}...")

        # Execute query
        start_time = datetime.now()
        df = get_data_from_snowflake(query_sql, SNOWFLAKE_CONFIG)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Validate results
        print(f"✓ Query executed successfully in {elapsed:.2f}s")
        print(f"  Rows returned: {len(df)}")
        if not df.empty:
            print(f"  Columns: {', '.join(df.columns.tolist())}")
            print(f"  Sample data:\n{df.head(3).to_string()}")
        else:
            print(f"  ⚠ WARNING: No data returned")

        return {
            'status': 'success',
            'rows': len(df),
            'elapsed_seconds': elapsed,
            'columns': df.columns.tolist() if not df.empty else [],
            'error': None
        }
    except Exception as e:
        print(f"✗ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'rows': 0,
            'elapsed_seconds': 0,
            'columns': [],
            'error': str(e)
        }

def main():
    results = {}

    # Test authentication
    print("Testing Snowflake connection...")
    try:
        session = connect_to_snowflake(SNOWFLAKE_CONFIG)
        print("✓ Connected to Snowflake\n")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # Test user lookup
    results['get_user_id_from_username'] = validate_query(
        "get_user_id_from_username",
        get_user_id_from_username,
        TEST_USERNAME
    )

    # Test download queries
    results['query_user_files_downloaded'] = validate_query(
        "query_user_files_downloaded",
        query_user_files_downloaded,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_top_projects'] = validate_query(
        "query_user_top_projects",
        query_user_top_projects,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_all_projects'] = validate_query(
        "query_user_all_projects",
        query_user_all_projects,
        TEST_USER_ID, START_DATE, END_DATE
    )

    # Test activity queries
    results['query_user_active_days'] = validate_query(
        "query_user_active_days",
        query_user_active_days,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_activity_by_date'] = validate_query(
        "query_user_activity_by_date",
        query_user_activity_by_date,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_activity_by_month'] = validate_query(
        "query_user_activity_by_month",
        query_user_activity_by_month,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_activity_by_hour'] = validate_query(
        "query_user_activity_by_hour",
        query_user_activity_by_hour,
        TEST_USER_ID, START_DATE, END_DATE, 'America/Chicago'
    )

    # Test collaboration queries
    results['query_user_collaboration_network'] = validate_query(
        "query_user_collaboration_network",
        query_user_collaboration_network,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_top_collaborators'] = validate_query(
        "query_user_top_collaborators",
        query_user_top_collaborators,
        TEST_USER_ID, START_DATE, END_DATE
    )

    # Test creation queries
    results['query_user_creations'] = validate_query(
        "query_user_creations",
        query_user_creations,
        TEST_USER_ID, START_DATE, END_DATE
    )

    # Test notable moments
    results['query_user_first_download'] = validate_query(
        "query_user_first_download",
        query_user_first_download,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_busiest_day'] = validate_query(
        "query_user_busiest_day",
        query_user_busiest_day,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_user_largest_download'] = validate_query(
        "query_user_largest_download",
        query_user_largest_download,
        TEST_USER_ID, START_DATE, END_DATE
    )

    # Test file size queries
    results['query_user_average_file_size'] = validate_query(
        "query_user_average_file_size",
        query_user_average_file_size,
        TEST_USER_ID, START_DATE, END_DATE
    )

    results['query_platform_average_file_size'] = validate_query(
        "query_platform_average_file_size",
        query_platform_average_file_size,
        START_DATE, END_DATE
    )

    # Print summary
    print(f"\n\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")

    successful = sum(1 for r in results.values() if r['status'] == 'success')
    failed = sum(1 for r in results.values() if r['status'] == 'error')

    print(f"Total queries tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed queries:")
        for name, result in results.items():
            if result['status'] == 'error':
                print(f"  - {name}: {result['error']}")

    # Save results to JSON
    import json
    with open('query_validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Full results saved to query_validation_results.json")

if __name__ == '__main__':
    main()
