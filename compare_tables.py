"""
Compare data between objectdownload_event and FILEDOWNLOAD tables.
"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, '..')

from synapse_wrapped.utils import get_data_from_snowflake

# Load Snowflake config from parent's secrets.toml
SECRETS_PATH = Path('..') / '.streamlit' / 'secrets.toml'
with open(SECRETS_PATH, 'rb') as f:
    secrets = tomllib.load(f)
    SNOWFLAKE_CONFIG = secrets['snowflake']

TEST_USER_ID = 3514384
YEAR = 2025

def compare_tables():
    # Query 1: objectdownload_event (synapse_wrapped uses this)
    query_event = f"""
    SELECT
        COUNT(DISTINCT file_handle_id) AS file_count,
        COUNT(DISTINCT project_id) AS project_count,
        COUNT(DISTINCT DATE(record_date)) AS active_days,
        MIN(record_date) AS first_activity,
        MAX(record_date) AS last_activity
    FROM synapse_data_warehouse.synapse_event.objectdownload_event
    WHERE user_id = {TEST_USER_ID}
        AND record_date BETWEEN '{YEAR}-01-01' AND '{YEAR}-12-31'
    """

    # Query 2: FILEDOWNLOAD (parent implementation uses this)
    query_filedownload = f"""
    SELECT
        COUNT(DISTINCT FILE_HANDLE_ID) AS file_count,
        COUNT(DISTINCT PROJECT_ID) AS project_count,
        COUNT(DISTINCT DATE(TIMESTAMP)) AS active_days,
        MIN(TIMESTAMP) AS first_activity,
        MAX(TIMESTAMP) AS last_activity
    FROM SYNAPSE_DATA_WAREHOUSE.SYNAPSE.FILEDOWNLOAD
    WHERE USER_ID = {TEST_USER_ID}
        AND RECORD_DATE >= '{YEAR}-01-01'
        AND RECORD_DATE < '{YEAR + 1}-01-01'
    """

    print("Comparing objectdownload_event vs FILEDOWNLOAD tables\n")
    print("="*60)

    try:
        print("\n1. Testing objectdownload_event table...")
        df_event = get_data_from_snowflake(query_event, SNOWFLAKE_CONFIG)
        print("✓ Query successful")
        print(df_event.to_string())

        print("\n2. Testing FILEDOWNLOAD table...")
        df_filedownload = get_data_from_snowflake(query_filedownload, SNOWFLAKE_CONFIG)
        print("✓ Query successful")
        print(df_filedownload.to_string())

        print("\n3. Comparison:")
        print("-" * 60)
        for col in ['FILE_COUNT', 'PROJECT_COUNT', 'ACTIVE_DAYS']:
            val1 = df_event.iloc[0][col]
            val2 = df_filedownload.iloc[0][col]
            diff = val2 - val1
            pct = (diff / val1 * 100) if val1 > 0 else 0
            match = "✓" if abs(pct) < 5 else "⚠"
            print(f"{match} {col:20s}: event={val1:8d} | filedownload={val2:8d} | diff={diff:+8d} ({pct:+.1f}%)")

        print("\n4. Schema comparison:")
        print("-" * 60)
        print("objectdownload_event table structure:")
        schema_event = get_data_from_snowflake("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM SYNAPSE_DATA_WAREHOUSE.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'SYNAPSE_EVENT'
              AND TABLE_NAME = 'OBJECTDOWNLOAD_EVENT'
            ORDER BY ORDINAL_POSITION
        """, SNOWFLAKE_CONFIG)
        print(schema_event.to_string())

        print("\nFILEDOWNLOAD table structure:")
        schema_filedownload = get_data_from_snowflake("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM SYNAPSE_DATA_WAREHOUSE.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'SYNAPSE'
              AND TABLE_NAME = 'FILEDOWNLOAD'
            ORDER BY ORDINAL_POSITION
        """, SNOWFLAKE_CONFIG)
        print(schema_filedownload.to_string())

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    compare_tables()
