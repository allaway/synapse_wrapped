"""Generate wrapped report using synapse_wrapped package"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, '..')

from synapse_wrapped import generate_wrapped

# Load Snowflake config from parent's secrets.toml
SECRETS_PATH = Path('..') / '.streamlit' / 'secrets.toml'
with open(SECRETS_PATH, 'rb') as f:
    secrets = tomllib.load(f)
    SNOWFLAKE_CONFIG = secrets['snowflake']

print("Generating wrapped report for james.moon...")
output_path = generate_wrapped(
    username="james.moon",
    year=2025,
    output_path="james_moon_wrapped_2025_from_package.html",
    snowflake_config=SNOWFLAKE_CONFIG,
    include_audio=False,  # Optional: disable audio for faster testing
    timezone="America/Chicago"
)

print(f"✓ Report generated: {output_path}")
