# For Roz 2.0 🌹

A mobile-friendly Streamlit mini-world with:
- Shared NGL-style message wall, replies, and reactions (Supabase-backed)
- Private room password gate (SHA-256 hash stored in Streamlit Secrets)
- Random “CLICK HERE 😜” surprises
- Random questions by vibe
- Message-in-a-bottle demo
- Clickable rose garden
- Midnight mood and thought corner

## Important privacy/security notes
- Streamlit Community Cloud apps are generally reachable by anyone with the URL. The room password gate protects the app's UI, but this is not a substitute for proper user accounts/rate limiting, and a person with the app's backend credentials could access the database.
- The app uses the Supabase service-role key server-side. Never commit it to GitHub or put it in client-side code.
- Shared messages are stored online in Supabase and persist across devices. Do not share highly sensitive information.
- This starter build has a single shared room ID (`main`). Anyone who knows the room password can enter that room.
- The message-in-a-bottle and local UI state are demo/session features; they are not persistent, secure, cross-device scheduled delivery.
- Reaction inserts need the included `roz_reactions` table. Reaction display/counting is not implemented in this starter build.
- For real production privacy, add per-user authentication, server-side rate limiting, room membership and password verification in a backend service.

## Deploy on Streamlit Community Cloud
1. Create a new GitHub repository, e.g. `for-roz-2`.
2. Upload `app.py`, `requirements.txt`, `supabase_schema.sql`, `README.md`, and `.gitignore` to the repository root.
3. Create a free project at https://supabase.com/.
4. In Supabase → SQL Editor, run the complete contents of `supabase_schema.sql`.
5. In Supabase Project Settings → API, copy the **Project URL** and the **service_role** secret key.
6. Generate a hash for a room password you and Roz agree on. Run locally:
   ```bash
   python -c "import hashlib; print(hashlib.sha256(b'CHOOSE-A-LONG-ROOM-PASSWORD').hexdigest())"
   ```
   Replace the example with your own password. Don't use your GitHub password or any reused password.
7. In Streamlit Community Cloud → app → Settings → Secrets, add:
   ```toml
   SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
   SUPABASE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_KEY"
   ROOM_PASSWORD_HASH = "PASTE_THE_SHA256_HASH_HERE"
   ```
   Keep these values out of GitHub.
8. Deploy `app.py`. The app is not deployed by creating this ZIP; you must connect the repository and configure the secrets.

## Deploy on Render (alternative)
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Add `SUPABASE_URL`, `SUPABASE_KEY`, and `ROOM_PASSWORD_HASH` as environment variables in Render.
- Note: Render free web services may sleep when idle and may have free-tier limitations.

## Files
- `app.py` — Streamlit app
- `requirements.txt` — dependencies
- `supabase_schema.sql` — shared message database tables
- `.gitignore` — excludes local secrets and virtual environments
