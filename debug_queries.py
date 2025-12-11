"""
Debug script to check what data is being returned from queries.
"""

from datetime import datetime
from synapse_wrapped.queries import *
from synapse_wrapped.utils import get_data_from_snowflake

year = 2025
start_date = f"{year}-01-01"
end_date = f"{year}-12-31"
user_id = 3342573  # allawayr

print("=" * 60)
print(f"Debugging queries for user {user_id} in {year}")
print("=" * 60)

# Test each query
queries_to_test = [
    ("Files Downloaded", query_user_files_downloaded(user_id, start_date, end_date)),
    ("Top Projects", query_user_top_projects(user_id, start_date, end_date, limit=5)),
    ("All Projects", query_user_all_projects(user_id, start_date, end_date)),
    ("Active Days", query_user_active_days(user_id, start_date, end_date)),
    ("Creations", query_user_creations(user_id, start_date, end_date)),
    ("Collaboration Network", query_user_collaboration_network(user_id, start_date, end_date)),
    ("Top Collaborators", query_user_top_collaborators(user_id, start_date, end_date, limit=5)),
]

for name, query in queries_to_test:
    print(f"\n{name}:")
    print("-" * 40)
    try:
        df = get_data_from_snowflake(query)
        print(f"Rows returned: {len(df)}")
        if not df.empty:
            print(f"Columns: {list(df.columns)}")
            print(f"First few rows:")
            print(df.head())
        else:
            print("⚠️  Empty result!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Note: If you see empty results, it might be because:")
print("1. The user has no activity in 2025 (year just started)")
print("2. The date range needs adjustment")
print("3. There's an issue with the query")
print("=" * 60)

