# Getting Started with Synapse Wrapped

## ✅ Step 1: Install Dependencies (Already Done!)

The virtual environment and all dependencies have been installed.

## 🔐 Step 2: Configure Snowflake SSO

Edit `.streamlit/secrets.toml` with your Snowflake credentials:

```toml
[snowflake]
user = "your_email@sagebase.org"           # Your Sage email
authenticator = "externalbrowser"          # SSO login
account = "your-account-identifier"        # Your Snowflake account
warehouse = "COMPUTE_XSMALL"               # Warehouse name
```

### Finding Your Account Identifier

1. Log into Snowflake web UI
2. Go to your account settings
3. Look for the account identifier (format: `mqxxxxx-vxxxxxx` or `orgname-accountname`)
4. **Important**: If you see `orgname.accountname`, change the dot to a hyphen: `orgname-accountname`

### Example

```toml
[snowflake]
user = "robert.allaway@sagebase.org"
authenticator = "externalbrowser"
account = "mqxxxxx-vxxxxxx"
warehouse = "COMPUTE_XSMALL"
```

## 🧪 Step 3: Test Connection

Run the test script:

```bash
source venv/bin/activate
python test_run.py
```

**Note**: On first run, it will open your browser for SSO authentication. This is normal!

## 🚀 Step 4: Generate Your First Wrapped

### Single User

```bash
source venv/bin/activate
python -m synapse_wrapped.cli --username your_email@sagebase.org --year 2024
```

Or using Python:

```python
from synapse_wrapped import generate_wrapped

generate_wrapped(
    username="your_email@sagebase.org",
    year=2024
)
```

### Batch Processing

Create a file `usernames.txt` with one username per line:

```
user1@sagebase.org
user2@sagebase.org
user3@sagebase.org
```

Then run:

```bash
python -m synapse_wrapped.cli --batch usernames.txt --year 2024 --output wrapped_output
```

## 📋 Important Notes

1. **Role Access**: Make sure you're logged into Snowflake web UI and have changed your role from "PUBLIC" to "DATA_ANALYTICS" to access the Synapse data warehouse.

2. **SSO Authentication**: When you run queries, your browser will open for authentication. This is expected behavior with SSO.

3. **Security**: The `.streamlit/secrets.toml` file is in `.gitignore` - never commit it!

4. **Output**: Generated HTML files are self-contained and can be:
   - Opened directly in a browser
   - Attached to emails
   - Hosted on a web server

## 🆘 Troubleshooting

### "No Snowflake config provided"
- Make sure `.streamlit/secrets.toml` exists and has the correct format
- Check that the file path is correct

### "User not found"
- Verify the username/email is correct
- Check that the user exists in Synapse

### Browser doesn't open for SSO
- Make sure `authenticator = "externalbrowser"` is set
- Try running from a terminal (not an IDE) so the browser can open

### "Access denied" or "Insufficient privileges"
- Log into Snowflake web UI
- Change your role to "DATA_ANALYTICS"
- Make sure you have access to the Synapse data warehouse

## 📚 Next Steps

- See `README.md` for detailed documentation
- See `QUICKSTART.md` for quick reference
- See `example_usage.py` for code examples

