# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Synapse Wrapped is a Python package that generates Spotify Wrapped-style visualizations for Synapse.org users. It queries the Synapse Data Warehouse in Snowflake to collect user activity metrics (downloads, projects accessed, collaborations, content created) and generates self-contained HTML reports.

**Two Distinct Components:**
1. **`synapse_wrapped/` package**: Main Python package for generating user-specific wrapped visualizations
2. **`example_repository/` directory**: Reference implementation of a different Streamlit dashboard (NF Open Science Initiative funder-facing analytics)

## Architecture

### Data Flow
1. **User Identification**: Convert username/email to Synapse user ID via `get_user_id_from_username()`
2. **Data Collection**: Execute SQL queries in `queries.py` against Snowflake tables:
   - `synapse_data_warehouse.synapse_event.objectdownload_event` - Download events
   - `synapse_data_warehouse.synapse.node_latest` - Entity metadata
   - `synapse_data_warehouse.synapse.file_latest` - File metadata
   - `synapse_data_warehouse.synapse.userprofile_latest` - User profiles
3. **Visualization Generation**: `visualizations.py` creates HTML cards with embedded visualizations (Plotly charts, word clouds, network graphs)
4. **HTML Assembly**: `generator.py` combines cards into single HTML file with embedded CSS and base64-encoded images
5. **Output**: Self-contained HTML files ready to share via email or web hosting

### Key Design Patterns
- **Session Caching**: `utils.py` maintains global `_session_cache` to reuse Snowflake connections (SSO tokens last ~4 hours)
- **User-Scoped Queries**: All queries filter by `user_id` (unlike example_repository which filters by project)
- **String Interpolation**: Queries use f-strings for parameter injection (note: not parameterized, assumes trusted input)
- **Embedded Assets**: Visualizations encoded as base64 data URLs in HTML for portability

### Package Structure
```
synapse_wrapped/
├── __init__.py          # Exports generate_wrapped, generate_wrapped_batch
├── queries.py           # SQL query functions (user-scoped)
├── visualizations.py    # HTML card generation with Plotly/matplotlib/wordcloud
├── generator.py         # Main generation logic and HTML template
├── utils.py             # Snowflake connection with session caching
└── cli.py               # Command-line interface (argparse)
```

## Development Commands

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install as editable package (for development)
pip install -e .
```

### Running the Package

**Command Line Interface:**
```bash
# Single user
python -m synapse_wrapped.cli --username user@example.com --year 2024

# Batch processing
python -m synapse_wrapped.cli --batch usernames.txt --year 2024 --output-dir wrapped_output

# With custom timezone
python -m synapse_wrapped.cli --username user@example.com --year 2024 --timezone America/New_York

# Disable audio
python -m synapse_wrapped.cli --username user@example.com --year 2024 --no-audio
```

**Python API:**
```python
from synapse_wrapped import generate_wrapped, generate_wrapped_batch

# Single user
output_path = generate_wrapped(
    username="user@example.com",
    year=2024,
    output_path="my_wrapped_2024.html",
    snowflake_config=snowflake_config,  # Optional if using .streamlit/secrets.toml
    include_audio=True,
    timezone="America/Chicago"
)

# Batch processing
output_files = generate_wrapped_batch(
    usernames=["user1@example.com", "user2@example.com"],
    year=2024,
    output_dir="wrapped_output",
    snowflake_config=snowflake_config
)
```

### Testing Connection
```bash
# Test Snowflake connection and authentication
python test_run.py

# Debug query execution
python debug_queries.py

# Check keyring/SSO token storage
python check_keyring.py
```

### Building Package
```bash
# Build distribution packages
pip install build
python -m build

# Install from local build
pip install dist/synapse_wrapped-0.1.0-py3-none-any.whl
```

## Authentication Setup

### Snowflake SSO (Recommended for Development)

Create `.streamlit/secrets.toml`:
```toml
[snowflake]
user = "your_email@sagebase.org"
authenticator = "externalbrowser"
account = "mqxxxxx-vxxxxxx"  # Format: orgname-accountname (hyphen, not dot)
warehouse = "COMPUTE_XSMALL"
```

**Important**:
- On first run, browser opens for SSO authentication
- SSO tokens cached via keyring package (~4 hours validity)
- After SSO login in Snowflake web UI, change role from "PUBLIC" to "DATA_ANALYTICS" to access data warehouse

### Username/Password Authentication

For scripts or non-interactive environments:
```python
snowflake_config = {
    "user": "username",
    "password": "password",
    "account": "account-identifier",
    "warehouse": "COMPUTE_XSMALL"
}

generate_wrapped(username="...", snowflake_config=snowflake_config)
```

Or create `snowflake_config.json`:
```bash
python -m synapse_wrapped.cli --username user@example.com --config snowflake_config.json
```

## Development Workflow

### Adding New Metrics
1. **Add Query**: Create query function in `queries.py` that takes `user_id`, `start_date`, `end_date`
2. **Create Visualization**: Add card generation function in `visualizations.py` that accepts DataFrame and returns HTML string
3. **Integrate in Generator**: Update `generate_wrapped()` in `generator.py` to:
   - Execute new query
   - Generate visualization card
   - Add card to HTML template
4. **Test**: Run with test user to verify output

### Query Development Best Practices
- Test queries in Snowflake's Snowsight SQL Worksheet first
- Use consistent parameters: `user_id` (int), `start_date` and `end_date` (ISO format strings)
- Handle NULL values with `COALESCE()` for names and annotations
- Use `JSON_EXTRACT_PATH_TEXT()` for parsing JSON annotations
- Add `DISTINCT` where appropriate to avoid duplicate counts
- Consider query performance - add `LIMIT` clauses for large result sets

### Visualization Best Practices
- Return HTML strings that fit within `.wrapped-card` divs
- Use base64 encoding for images: `img src="data:image/png;base64,{encoded_data}"`
- Handle empty DataFrames gracefully with fallback messages
- Include metric labels and units for clarity
- Use consistent color schemes across visualizations

## Key Features

### Metrics Collected
- **Files Downloaded**: Count and total size
- **Top 5 Projects**: Most accessed projects with file counts
- **Project Word Cloud**: Visual representation of all accessed projects
- **Days Active**: Number of distinct days with activity
- **Content Created**: Breakdown by type (projects, files, tables)
- **Collaboration Network**: Graph of users with overlapping downloads
- **Top 5 Collaborators**: Users with most shared file downloads
- **Activity Patterns**: Hourly breakdown, night owl/early bird detection
- **Notable Moments**: First download, busiest day, largest file

### Timezone Support
- Activity patterns calculated in user's local timezone (default: America/Chicago)
- Uses Snowflake's `CONVERT_TIMEZONE()` function
- Specify via `--timezone` CLI flag or `timezone` parameter

### Output Characteristics
- Self-contained HTML (no external dependencies)
- Embedded CSS with gradient styling
- Base64-encoded images and visualizations
- Optional background audio
- Responsive design for mobile/desktop
- Email-ready format (can be sent as attachment)

## Example Repository

The `example_repository/` directory contains a separate Streamlit application for the NF Open Science Initiative. This is a **different project** with:
- Funder-facing dashboard ([app.py](example_repository/app.py))
- Internal DCC compliance dashboard ([internal-app.py](example_repository/internal-app.py))
- Project-scoped queries (not user-scoped)
- Different data model and visualizations

Refer to the [example_repository documentation](example_repository/) for details on that application.

## Troubleshooting

### "No Snowflake config provided"
- Ensure `.streamlit/secrets.toml` exists with correct format
- Or pass `snowflake_config` dict to generation functions

### "User not found"
- Verify username/email exists in `synapse.userprofile_latest` table
- Check for typos in username

### SSO Browser Not Opening
- Ensure `authenticator = "externalbrowser"` in config
- Run from terminal (not IDE) to allow browser launch
- Check firewall/security settings

### "Access denied" or "Insufficient privileges"
- Log into Snowflake web UI
- Switch role from "PUBLIC" to "DATA_ANALYTICS"
- Verify access to `synapse_data_warehouse` database

### No Data in Output
- Check that user had activity during specified year
- Verify date range covers expected activity period
- Confirm data exists in Snowflake tables
