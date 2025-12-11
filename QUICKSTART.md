# Quick Start Guide

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd synapse_wrapped

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -r requirements.txt
# Or install in development mode:
pip install -e .
```

## Basic Usage

### 1. Configure Snowflake Connection

Create a JSON config file `snowflake_config.json`:
```json
{
    "user": "your_username",
    "password": "your_password",
    "account": "your-account",
    "warehouse": "COMPUTE_XSMALL"
}
```

Or use Streamlit secrets (see README.md for details).

### 2. Generate Wrapped for a Single User

**Using Python:**
```python
from synapse_wrapped import generate_wrapped
import json

# Load config
with open('snowflake_config.json') as f:
    config = json.load(f)

# Generate wrapped
generate_wrapped(
    username="user@example.com",
    year=2024,
    snowflake_config=config
)
```

**Using CLI:**
```bash
python -m synapse_wrapped.cli \
    --username user@example.com \
    --year 2024 \
    --config snowflake_config.json \
    --output my_wrapped.html
```

### 3. Batch Generation

**Using Python:**
```python
from synapse_wrapped import generate_wrapped_batch
import json

with open('snowflake_config.json') as f:
    config = json.load(f)

usernames = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

generate_wrapped_batch(
    usernames=usernames,
    year=2024,
    output_dir="wrapped_output",
    snowflake_config=config
)
```

**Using CLI:**
```bash
# Create usernames.txt with one username per line
echo "user1@example.com" > usernames.txt
echo "user2@example.com" >> usernames.txt

# Generate for all users
python -m synapse_wrapped.cli \
    --batch usernames.txt \
    --year 2024 \
    --config snowflake_config.json \
    --output wrapped_output
```

## Output

The generated HTML files are:
- Self-contained (all assets embedded)
- Email-ready (can be attached and opened)
- Responsive (works on mobile and desktop)
- Beautiful (gradient styling, animations)

## Sharing

1. **Via Email**: Attach the HTML file directly
2. **Via Web**: Upload to a web server
3. **Local Viewing**: Open the HTML file in any web browser

## Troubleshooting

### "User not found"
- Verify the username/email is correct
- Check that the user exists in Synapse

### "No Snowflake config"
- Ensure you've provided `snowflake_config` parameter
- Or set up Streamlit secrets (see README.md)

### Empty visualizations
- User may not have activity in the specified year
- Check date range (defaults to full year)

## Next Steps

- See `README.md` for detailed documentation
- Check `example_usage.py` for more examples
- Customize visualizations in `synapse_wrapped/visualizations.py`

