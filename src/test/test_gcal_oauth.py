from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# test_gcal_oauth.py está em: src/test/test_gcal_oauth.py
# então SRC_DIR = src/
SRC_DIR = Path(__file__).resolve().parents[1]

CLIENT_SECRET = SRC_DIR / "plugins" / "plugin_yeast_bank" / "utils" / "client_secret.apps.googleusercontent.com.json"

print(f"Testando OAuth Google Calendar usando: {CLIENT_SECRET}")

if not CLIENT_SECRET.exists():
    raise SystemExit(f"Arquivo não encontrado: {CLIENT_SECRET}")

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)

creds = flow.run_local_server(port=0)
print("OK: token gerado. Refresh token existe?", bool(creds.refresh_token))