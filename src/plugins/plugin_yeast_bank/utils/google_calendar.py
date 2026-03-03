import os
import re
import json
import secrets
import hashlib
import base64

from typing import Any, Dict, Tuple, List, Optional
from flask import current_app, session, url_for, request, session
from jinja2 import Environment, BaseLoader, select_autoescape
from requests_oauthlib import OAuth2Session


# Google libs are optional at runtime (dev environments may not have them).
try:
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    from googleapiclient.discovery import build
except Exception:  # pragma: no cover
    Flow = None
    Credentials = None
    GoogleRequest = None
    build = None


DEFAULT_CONFIG: Dict[str, Any] = {
    "timezone": "America/Sao_Paulo",

    # For creating calendars and events we need the broader scope.
    # If you change scopes in an existing installation, you must re-authorize (delete gcal_token.json).
    "scopes": ["https://www.googleapis.com/auth/calendar"],

    # Calendar destination preferences
    "calendar_mode": "yeastbank",  # primary | yeastbank | by_id
    "default_calendar_name": "YeastBank",
    "default_calendar_id": "",  # cached id after first resolve
    "auto_create_calendar": True,

    # Legacy UI support (static list; UI will prefer /gcal/calendars when authorized)
    "calendars": [
        {"id": "primary", "name": "Principal"},
        {"id": "__YEASTBANK__", "name": "YeastBank (auto)"}
    ],

    "event_summary_templates": {
        "starter": "Starter — {strain_name}",
        "viability": "Viabilidade estimada — {strain_name}",
        "review": "Revisão — {strain_name}"
    },
    "default_template_name": "starter_event.html"
}


_ALLOWED_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]{1,80}$")

def _pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")
    return verifier, challenge


def _instance_dir() -> str:
    root = current_app.instance_path
    p = os.path.join(root, "plugin_yeast_bank")
    os.makedirs(p, exist_ok=True)
    return p


def config_paths() -> Tuple[str, str]:
    # (instance_path, packaged_default_path)
    inst = os.path.join(_instance_dir(), "config_google_calendar.json")
    pkg = os.path.join(os.path.dirname(__file__), "config_google_calendar.json")
    return inst, pkg


def read_config() -> Dict[str, Any]:
    inst, pkg = config_paths()

    # If instance config exists, prefer it.
    path = inst if os.path.exists(inst) else pkg

    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw = (f.read() or "").strip()
                if not raw:
                    return DEFAULT_CONFIG.copy()
                cfg = json.loads(raw)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg if isinstance(cfg, dict) else {})
                return merged
    except Exception:
        pass

    return DEFAULT_CONFIG.copy()


def write_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    inst, _ = config_paths()
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg if isinstance(cfg, dict) else {})
    with open(inst, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    return merged


def templates_dir() -> str:
    p = os.path.join(_instance_dir(), "gcal_templates")
    os.makedirs(p, exist_ok=True)
    return p


def list_templates() -> List[str]:
    d = templates_dir()
    names: List[str] = []
    for fn in sorted(os.listdir(d)):
        if fn.lower().endswith(".html") and _ALLOWED_NAME_RE.match(fn):
            names.append(fn)
    return names


def _safe_template_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Nome do template é obrigatório")
    if not _ALLOWED_NAME_RE.match(name):
        raise ValueError("Nome inválido (use letras/números/._-)")
    if not name.lower().endswith(".html"):
        raise ValueError("O template deve terminar com .html")
    return name


def load_template(name: str) -> str:
    name = _safe_template_name(name)
    path = os.path.join(templates_dir(), name)
    if not os.path.exists(path):
        raise FileNotFoundError("Template não encontrado")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_template(name: str, html: str) -> str:
    name = _safe_template_name(name)
    path = os.path.join(templates_dir(), name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html or "")
    return name


def render_html(template_html: str, ctx: Dict[str, Any]) -> str:
    env = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(["html", "xml"])
    )
    tpl = env.from_string(template_html or "")
    return tpl.render(**(ctx or {}))


def token_path() -> str:
    return os.path.join(_instance_dir(), "gcal_token.json")


def _client_secret_path() -> str:
    # kept in utils/ per request
    return os.path.join(os.path.dirname(__file__), "client_secret.apps.googleusercontent.com.json")


def google_supported() -> bool:
    return Flow is not None and Credentials is not None and build is not None


def get_credentials() -> Optional["Credentials"]:
    if not google_supported():
        return None

    cfg = read_config()
    scopes = cfg.get("scopes") or DEFAULT_CONFIG["scopes"]

    tp = token_path()
    creds = None
    if os.path.exists(tp):
        try:
            creds = Credentials.from_authorized_user_file(tp, scopes=scopes)
        except Exception:
            creds = None

    # refresh if needed
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            with open(tp, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception:
            return None

    if creds and creds.valid:
        return creds
    return None


def build_service(creds: "Credentials"):
    if not google_supported():
        raise RuntimeError("Google libs não disponíveis")
    return build("calendar", "v3", credentials=creds)



def list_calendars(service) -> List[Dict[str, Any]]:
    """Return a simplified list of calendars the user can write to."""
    items: List[Dict[str, Any]] = []
    page_token = None
    while True:
        resp = service.calendarList().list(pageToken=page_token).execute()
        for it in resp.get("items", []):
            cal_id = it.get("id")
            summary = it.get("summary")
            if not cal_id or not summary:
                continue
            items.append({
                "id": cal_id,
                "summary": summary,
                "primary": bool(it.get("primary")),
                "accessRole": it.get("accessRole"),
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def find_calendar_id_by_name(service, name: str) -> Optional[str]:
    target = (name or "").strip().lower()
    if not target:
        return None
    for c in list_calendars(service):
        if (c.get("summary") or "").strip().lower() == target:
            return c.get("id")
    return None


def ensure_calendar(service, name: str) -> str:
    """Ensure a calendar exists (by summary name). Create if missing."""
    name = (name or "").strip()
    if not name:
        raise ValueError("calendar name is empty")

    found = find_calendar_id_by_name(service, name)
    if found:
        return found

    created = service.calendars().insert(body={"summary": name}).execute()
    cal_id = created.get("id")
    if not cal_id:
        raise RuntimeError("Falha ao criar agenda (sem id).")
    return cal_id
def start_oauth(next_path: str = "/yeast_bank/calendar"):
    if not google_supported():
        return None, "Google API libs não instaladas (google-auth-oauthlib / google-api-python-client)."

    cfg = read_config()
    scopes = cfg.get("scopes") or DEFAULT_CONFIG["scopes"]

    secret_path = _client_secret_path()
    if not os.path.exists(secret_path):
        return None, "client_secret.apps.googleusercontent.com.json não encontrado em plugins/plugin_yeast_bank/utils/"

    redirect_uri = url_for("yeast_bank.gcal_callback", _external=True)

    flow = Flow.from_client_secrets_file(
        secret_path,
        scopes=scopes,
        redirect_uri=redirect_uri
    )
    
    verifier, challenge = _pkce_pair()
    session["gcal_code_verifier"] = verifier

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=challenge,
        code_challenge_method="S256",
    )
    session["gcal_state"] = state
    session["gcal_next"] = next_path or "/yeast_bank/calendar"
    return authorization_url, None


def finish_oauth() -> Tuple[bool, str]:
    if not google_supported():
        return False, "Google API libs não instaladas."

    state = session.get("gcal_state")
    if not state:
        return False, "Sessão OAuth expirada. Tente novamente."

    code_verifier = session.get("gcal_code_verifier")
    if not code_verifier:
        return False, "Sessão OAuth sem code_verifier (PKCE). Tente novamente."

    cfg = read_config()
    scopes = cfg.get("scopes") or DEFAULT_CONFIG["scopes"]

    flow = Flow.from_client_secrets_file(
        _client_secret_path(),
        scopes=scopes,
        state=state,
        redirect_uri=url_for("yeast_bank.gcal_callback", _external=True),
    )

    try:
        # ✅ ESSENCIAL: enviar code_verifier
        flow.fetch_token(
            authorization_response=request.url,
            code_verifier=code_verifier,
        )

        creds = flow.credentials
        with open(token_path(), "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        # limpeza da sessão
        session.pop("gcal_code_verifier", None)
        # opcional: session.pop("gcal_state", None)

        return True, "OK"

    except Exception as e:
        return False, f"Falha no OAuth: {e}"
