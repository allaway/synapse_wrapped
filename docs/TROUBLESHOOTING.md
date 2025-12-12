# Troubleshooting Guide

## SSO Authentication Issues

### Problem: Repeated Login Prompts / Login Loop

If you're being asked to log in repeatedly or getting stuck in a login loop:

1. **Check keyring installation**: The package should cache your SSO token
   ```bash
   pip install 'snowflake-connector-python[secure-local-storage]'
   ```

2. **Clear cached sessions**: If sessions are corrupted, clear them
   ```python
   from synapse_wrapped.utils import close_all_sessions
   close_all_sessions()
   ```

3. **Check your secrets.toml**: Make sure it has the correct format:
   ```toml
   [snowflake]
   user = "your_email@sagebase.org"
   authenticator = "externalbrowser"
   account = "your-account"
   warehouse = "COMPUTE_XSMALL"
   ```

4. **Verify role access**: Log into Snowflake web UI and ensure your role is set to "DATA_ANALYTICS"

### Problem: Browser Doesn't Open for SSO

- Make sure you're running from a terminal (not an IDE) so the browser can open
- Check that `authenticator = "externalbrowser"` is set in secrets.toml
- Try manually opening the URL that's printed in the terminal

### Problem: "User not found"

The username lookup is case-insensitive and searches both `user_name` and `email` fields. Try:
- Username (e.g., `allawayr`)
- Email (e.g., `robert.allaway@sagebase.org`)
- Different variations of your email

### Problem: Session Timeout

Sessions are cached but may expire. If you get timeout errors:
1. The code will automatically create a new session
2. You may need to authenticate again in the browser
3. Sessions are cached per Python process, so restarting the script will require re-authentication

## Performance Issues

### Slow Query Execution

- Queries are executed sequentially
- Large date ranges may take longer
- Network visualizations are limited to top 20 collaborators for performance

### Memory Issues

- Word clouds and network graphs are generated as images (not interactive)
- If you have many projects, the word cloud generation may take time

## Common Errors

### "No Snowflake config provided"
- Make sure `.streamlit/secrets.toml` exists
- Check the file format matches the example

### "Access denied" or "Insufficient privileges"
- Log into Snowflake web UI
- Change your role to "DATA_ANALYTICS"
- Verify you have access to `synapse_data_warehouse`

### Empty Results
- User may not have activity in the specified year
- Check the date range (defaults to full year)
- Verify the user exists in Synapse

## Getting Help

1. Check the error message carefully
2. Verify your Snowflake connection with `python test_run.py`
3. Check that your role is set correctly in Snowflake web UI
4. Review the logs for specific query errors

