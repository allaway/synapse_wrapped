# Synapse Wrapped

Generate Spotify Wrapped-style visualizations for Synapse.org users using data from Snowflake.

## Features

- **Files Downloaded**: Total count and size of files downloaded
- **Top 5 Projects**: Most accessed projects with file counts
- **Projects Explored**: Word cloud visualization of all accessed projects
- **Days Active**: Number of days spent on Synapse during the year
- **Content Created**: Breakdown of projects, files, and tables created
- **Collaboration Network**: Network visualization of users who interacted with the same projects/files
- **Top 5 Collaborators**: Users with the most shared project/file interactions

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd synapse_wrapped
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

You need to configure Snowflake connection. You can do this in two ways:

### Option 1: Using Streamlit Secrets (for Streamlit apps)

Create a `.streamlit/secrets.toml` file:
```toml
[snowflake]
user = "your_username"
password = "your_password"
account = "your-account"
warehouse = "COMPUTE_XSMALL"
```

### Option 2: Using Config Dictionary (for scripts)

Pass a dictionary with Snowflake configuration:
```python
snowflake_config = {
    "user": "your_username",
    "password": "your_password",
    "account": "your-account",
    "warehouse": "COMPUTE_XSMALL"
}
```

## Usage

### Single User

```python
from synapse_wrapped import generate_wrapped

# Generate wrapped for a single user
output_path = generate_wrapped(
    username="user@example.com",
    year=2024,
    output_path="my_wrapped_2024.html",
    snowflake_config=snowflake_config  # Optional if using streamlit secrets
)
```

### Batch Generation

```python
from synapse_wrapped import generate_wrapped_batch

# Generate wrapped for multiple users
usernames = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

output_files = generate_wrapped_batch(
    usernames=usernames,
    year=2024,
    output_dir="wrapped_output",
    snowflake_config=snowflake_config  # Optional if using streamlit secrets
)
```

### Command Line Interface

You can also use the CLI script:

```bash
# Single user
python -m synapse_wrapped.cli --username user@example.com --year 2024

# Batch processing from file
python -m synapse_wrapped.cli --batch usernames.txt --year 2024 --output-dir wrapped_output
```

Create a `usernames.txt` file with one username per line:
```
user1@example.com
user2@example.com
user3@example.com
```

## Output

The generated HTML files are self-contained and can be:
- Opened directly in a web browser
- Shared via email (as HTML attachment)
- Hosted on a web server

Each HTML file includes:
- Beautiful gradient styling
- Interactive visualizations
- Word cloud of project names
- Network graph of collaborators
- Responsive design for mobile and desktop

## Data Sources

The package queries the following Snowflake tables:
- `synapse_data_warehouse.synapse_event.objectdownload_event` - Download events
- `synapse_data_warehouse.synapse.node_latest` - Entity metadata
- `synapse_data_warehouse.synapse.file_latest` - File metadata
- `synapse_data_warehouse.synapse.userprofile_latest` - User profiles

## Requirements

- Python 3.8+
- Access to Synapse Data Warehouse in Snowflake
- Appropriate Snowflake permissions to query the data warehouse

## Notes

- The visualization focuses on a specific user's activity across **all** Synapse projects (unlike the example repository which is scoped to specific projects)
- Data is collected for the specified year (defaults to current year)
- Network visualizations are limited to top 20 collaborators for performance
- Word clouds include all project names accessed by the user

## License

See LICENSE file for details.

