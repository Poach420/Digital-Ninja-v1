# Fix Google OAuth - Error 400: redirect_uri_mismatch

## Problem
Google OAuth is failing because the redirect URI isn't registered in Google Cloud Console.

## Solution - Add Redirect URI to Google Console

### Step 1: Go to Google Cloud Console
1. Open: https://console.cloud.google.com/apis/credentials
2. Sign in with your Google account

### Step 2: Find Your OAuth Client
1. Look for OAuth 2.0 Client IDs section
2. Find the client with ID: `659055163058-7m8ij8ifqbrfug06c346cri4f5rr1nar`
3. Click on it to edit

### Step 3: Add Authorized Redirect URIs
Add BOTH of these URIs to "Authorized redirect URIs":
```
http://localhost:8000/api/auth/google/session
http://localhost:3000/auth/callback
```

### Step 4: Save
1. Click "SAVE" button at the bottom
2. Wait 5-10 seconds for changes to propagate

### Step 5: Test Again
1. Go to http://localhost:3000
2. Click "Sign in with Google"
3. Should work now!

## Alternative: Use Environment Variable
If you have a different redirect URI registered, update `.env`:
```
GOOGLE_REDIRECT_URI=<your-registered-uri>
```
