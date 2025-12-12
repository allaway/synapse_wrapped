# SSO Token Caching Information

## How It Works

With `keyring` installed, the Snowflake connector automatically caches your SSO token when using `authenticator = "externalbrowser"`. The token is stored securely in your system's keyring and reused for subsequent connections.

## Token Lifetime

- **SSO tokens typically last 4 hours**
- After expiration, you'll need to authenticate again
- The token is cached per (account, user) combination

## Why You Might Still Be Prompted

1. **Token Expired**: If it's been more than 4 hours since your last login, the token has expired
2. **First Run**: The first time you run the script, there's no cached token, so you must authenticate
3. **Account/User Changed**: If you change the account or user in your config, it's treated as a new combination
4. **Keyring Backend Issues**: On some systems, the keyring backend might need additional configuration

## Checking Your Token Status

The keyring stores tokens with a key like:
```
snowflake_<account>_<user>_id_token
```

You can check if a token exists (though you can't read it directly for security):
```python
import keyring
# This will show if a token exists (but won't show the actual token)
try:
    token = keyring.get_password("snowflake", f"{account}_{user}_id_token")
    if token:
        print("Token is cached")
    else:
        print("No token cached")
except:
    print("Could not check token status")
```

## Expected Behavior

- **First run**: Browser opens, you authenticate → token is cached
- **Subsequent runs (within 4 hours)**: No browser prompt, uses cached token
- **After 4 hours**: Browser opens again, new token is cached

## If You're Still Being Prompted Every Time

1. **Check keyring is working**: Run `python check_keyring.py`
2. **Verify your config**: Make sure account and user are consistent
3. **Check token expiration**: If it's been more than 4 hours, re-authentication is expected
4. **Try clearing and re-authenticating**: Sometimes clearing the keyring and starting fresh helps

## Force Re-authentication

If you want to force a new authentication (e.g., if you suspect the token is corrupted):

```python
import keyring
# Clear the token (replace with your actual account and user)
account = "mqzfhld-vp00034"
user = "robert.allaway@sagebase.org"
keyring.delete_password("snowflake", f"{account}_{user}_id_token")
```

Then run your script again - it will prompt for authentication and cache a new token.

