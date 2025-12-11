# Package Structure

```
synapse_wrapped/
├── synapse_wrapped/          # Main package
│   ├── __init__.py          # Package exports
│   ├── queries.py           # SQL queries for user-specific data
│   ├── visualizations.py    # HTML card generation functions
│   ├── generator.py         # Main wrapped generation logic
│   ├── utils.py             # Snowflake connection utilities
│   └── cli.py               # Command-line interface
├── example_repository/       # Reference implementation
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup configuration
├── pyproject.toml           # Modern Python packaging config
├── README.md                # Main documentation
├── QUICKSTART.md            # Quick start guide
├── example_usage.py         # Usage examples
└── .gitignore               # Git ignore rules
```

## Key Components

### `queries.py`
Contains SQL queries scoped to individual users (not projects):
- `query_user_files_downloaded()` - Files downloaded by user
- `query_user_top_projects()` - Top 5 accessed projects
- `query_user_all_projects()` - All projects for word cloud
- `query_user_active_days()` - Days active on Synapse
- `query_user_creations()` - Projects/files/tables created
- `query_user_collaboration_network()` - Network of collaborators
- `query_user_top_collaborators()` - Top 5 collaborators

### `visualizations.py`
HTML card generation functions:
- `create_files_downloaded_card()` - Files downloaded metric
- `create_top_projects_card()` - Top 5 projects list
- `create_projects_wordcloud_card()` - Word cloud visualization
- `create_active_days_card()` - Days active metric
- `create_creations_card()` - Content creation breakdown
- `create_network_card()` - Collaboration network graph
- `create_top_collaborators_card()` - Top 5 collaborators list

### `generator.py`
Main generation logic:
- `generate_wrapped()` - Generate for single user
- `generate_wrapped_batch()` - Batch generation for multiple users
- `get_html_template()` - HTML template with styling

### `utils.py`
Utility functions:
- `connect_to_snowflake()` - Snowflake connection handler
- `get_data_from_snowflake()` - Query execution wrapper

### `cli.py`
Command-line interface for easy usage without Python scripts.

## Data Flow

1. User provides username/email
2. Query user ID from username
3. Execute queries for all metrics (files, projects, collaborations, etc.)
4. Generate HTML cards for each metric
5. Combine into single HTML file with embedded assets
6. Save to disk

## Output Format

Self-contained HTML files with:
- Embedded CSS styling
- Base64-encoded images (word clouds, network graphs)
- Optional audio support
- Responsive design
- Email-ready format

