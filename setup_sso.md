# Setting Up SSO Login for Synapse Wrapped

## Quick Setup

1. **Create the `.streamlit` directory** (if it doesn't exist):
   ```bash
   mkdir -p .streamlit
   ```

2. **Create `secrets.toml` file**:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

3. **Edit `.streamlit/secrets.toml`** with your information:
   ```toml
   [snowflake]
   user = "your_email@sagebase.org"
   authenticator = "externalbrowser"
   account = "your-account-identifier"
   warehouse = "COMPUTE_XSMALL"
   ```

4. **Find your Snowflake account identifier**:
   - Log into Snowflake
   - Go to your account settings
   - The account identifier format is usually: `orgname-accountname` or `mqxxxxx-vxxxxxx`
   - **Note**: If you see `orgname.accountname`, change the dot to a hyphen

5. **Test the connection**:
   ```bash
   source venv/bin/activate
   python test_run.py
   ```

## Important Notes

- **SSO Login**: When you run a query, it will open your browser for authentication
- **Role**: Make sure you're logged into Snowflake web UI and have changed your role from "PUBLIC" to "DATA_ANALYTICS" to access the Synapse data warehouse
- **Security**: The `secrets.toml` file is already in `.gitignore` - never commit it!

## Example secrets.toml

```toml
[snowflake]
user = "robert.allaway@sagebase.org"
authenticator = "externalbrowser"
account = "mqxxxxx-vxxxxxx"
warehouse = "COMPUTE_XSMALL"
```

