#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --- Configuration ---
SCRIPT_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = SCRIPT_DIR / "openai_creds.json"
USAGE_FILE = SCRIPT_DIR / "openai_usage.json"
LOG_FILE = SCRIPT_DIR / "openai_monitor.log"

CODEX_HOME = Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
CODEX_AUTH_FILE = CODEX_HOME / "auth.json"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
CODEX_TOKEN_URL = "https://auth.openai.com/oauth/token"
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"

OPENAI_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL_FILTERS = ["gpt-5-codex", "gpt-5.3-codex", "codex-mini-latest"]
DEFAULT_LABEL = "OPENAI / CODEX"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def current_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def unix_to_iso(timestamp_value) -> str | None:
    try:
        return datetime.fromtimestamp(int(timestamp_value), timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload, indent=2))


def write_secure_json(path: Path, payload: dict):
    write_json(path, payload)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def load_codex_auth() -> dict | None:
    return load_json(CODEX_AUTH_FILE)


def save_codex_auth(auth: dict):
    CODEX_HOME.mkdir(parents=True, exist_ok=True)
    write_secure_json(CODEX_AUTH_FILE, auth)


def sanitize_dashboard_credentials(raw: dict | None) -> dict | None:
    if not raw:
        return None

    admin_api_key = str(raw.get("admin_api_key", "")).strip()
    if not admin_api_key:
        return None

    project_ids = raw.get("project_ids", [])
    if isinstance(project_ids, str):
        project_ids = parse_csv(project_ids)
    else:
        project_ids = [str(item).strip() for item in project_ids if str(item).strip()]

    model_filters = raw.get("model_filters", [])
    if isinstance(model_filters, str):
        model_filters = parse_csv(model_filters)
    else:
        model_filters = [str(item).strip() for item in model_filters if str(item).strip()]

    label = str(raw.get("label", DEFAULT_LABEL)).strip() or DEFAULT_LABEL

    return {
        "admin_api_key": admin_api_key,
        "project_ids": project_ids,
        "model_filters": model_filters or DEFAULT_MODEL_FILTERS.copy(),
        "label": label,
    }


def load_dashboard_credentials() -> dict | None:
    stored = load_json(CREDENTIALS_FILE) or {}

    env_key = os.getenv("OPENAI_ADMIN_API_KEY", "").strip()
    if env_key:
        stored["admin_api_key"] = env_key

    env_projects = parse_csv(os.getenv("OPENAI_PROJECT_IDS"))
    if env_projects:
        stored["project_ids"] = env_projects

    env_models = parse_csv(os.getenv("OPENAI_MODEL_FILTERS"))
    if env_models:
        stored["model_filters"] = env_models

    env_label = os.getenv("OPENAI_DASHBOARD_LABEL", "").strip()
    if env_label:
        stored["label"] = env_label

    return sanitize_dashboard_credentials(stored)


def save_dashboard_credentials(creds: dict):
    write_secure_json(CREDENTIALS_FILE, creds)


def interactive_auth(defaults: dict | None = None) -> bool:
    if load_codex_auth() or load_dashboard_credentials():
        return True

    defaults = defaults or {}
    default_models = defaults.get("model_filters", DEFAULT_MODEL_FILTERS)
    default_projects = defaults.get("project_ids", [])
    default_label = defaults.get("label", DEFAULT_LABEL)

    print("\n" + "=" * 60)
    print("  OPENAI / CODEX AUTHORIZATION REQUIRED")
    print("=" * 60)
    print("\nPreferred setup: sign in with the Codex CLI (`codex`) so the widget can reuse ~/.codex/auth.json.")
    print("Fallback setup: provide an OpenAI Admin API key for organization usage totals.\n")

    api_key = input("OpenAI Admin API Key (or press Enter to skip and disable): ").strip()
    if not api_key:
        print("Authorization skipped. Enable Codex CLI login first if you want plan/rate-limit data.\n")
        return False

    default_projects_text = ", ".join(default_projects)
    projects_prompt = "Optional project IDs, comma separated"
    if default_projects_text:
        projects_prompt += f" [{default_projects_text}]"
    projects_value = input(f"{projects_prompt}: ").strip()

    default_models_text = ", ".join(default_models)
    models_value = input(f"Codex model filters [{default_models_text}]: ").strip()

    label_value = input(f"Widget label [{default_label}]: ").strip()

    creds = sanitize_dashboard_credentials({
        "admin_api_key": api_key,
        "project_ids": parse_csv(projects_value) if projects_value else default_projects,
        "model_filters": parse_csv(models_value) if models_value else default_models,
        "label": label_value or default_label,
    })

    if not creds:
        print("Failed to save OpenAI / Codex credentials. Widget is disabled.\n")
        return False

    save_dashboard_credentials(creds)
    print("OpenAI / Codex Authorization Successful!\n")
    return True


def decode_jwt_payload(token: str) -> dict:
    if not token or token.count(".") < 2:
        return {}
    try:
        _, payload_b64, _ = token.split(".", 2)
        padding = "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        return json.loads(payload_bytes)
    except Exception:
        return {}


def get_codex_plan_type(auth: dict) -> str | None:
    claims = decode_jwt_payload((auth.get("tokens") or {}).get("id_token", ""))
    auth_claims = claims.get("https://api.openai.com/auth", {})
    if isinstance(auth_claims, dict):
        plan_type = auth_claims.get("chatgpt_plan_type")
        if plan_type:
            return str(plan_type)
    for key in ("https://api.openai.com/auth.chatgpt_plan_type", "chatgpt_plan_type"):
        if claims.get(key):
            return str(claims[key])
    return None


def get_codex_account_id(auth: dict) -> str | None:
    tokens = auth.get("tokens") or {}
    if tokens.get("account_id"):
        return str(tokens["account_id"])

    claims = decode_jwt_payload(tokens.get("id_token", ""))
    auth_claims = claims.get("https://api.openai.com/auth", {})
    if isinstance(auth_claims, dict) and auth_claims.get("chatgpt_account_id"):
        return str(auth_claims["chatgpt_account_id"])
    for key in ("https://api.openai.com/auth.chatgpt_account_id", "chatgpt_account_id"):
        if claims.get(key):
            return str(claims[key])
    return None


def codex_access_token_expired(auth: dict, skew_seconds: int = 300) -> bool:
    access_token = (auth.get("tokens") or {}).get("access_token")
    if not access_token:
        return True

    claims = decode_jwt_payload(access_token)
    expires_at = claims.get("exp")
    if not expires_at:
        return False

    try:
        return time.time() >= int(expires_at) - skew_seconds
    except (TypeError, ValueError):
        return False


def refresh_codex_auth(auth: dict) -> dict | None:
    refresh_token = (auth.get("tokens") or {}).get("refresh_token")
    if not refresh_token:
        log.error("No Codex refresh token found.")
        return None

    payload = {
        "client_id": CODEX_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        resp = requests.post(CODEX_TOKEN_URL, json=payload, timeout=20)
        if resp.status_code != 200:
            log.error(f"Codex token refresh failed: {resp.status_code} {resp.text}")
            return None

        refreshed = resp.json()
        updated_auth = dict(auth)
        updated_tokens = dict(updated_auth.get("tokens") or {})
        for key in ("access_token", "refresh_token", "id_token"):
            if refreshed.get(key):
                updated_tokens[key] = refreshed[key]
        updated_auth["tokens"] = updated_tokens
        updated_auth["last_refresh"] = current_iso()
        save_codex_auth(updated_auth)
        return updated_auth
    except requests.RequestException as e:
        log.error(f"Network error refreshing Codex auth: {e}")
        return None


def fetch_codex_usage(access_token: str, account_id: str | None = None) -> dict | None:
    headers = {
        "Authorization": "Bearer " + access_token,
        "Accept": "application/json",
        "User-Agent": "codex-dashboard/1.0",
    }
    if account_id:
        headers["ChatGPT-Account-ID"] = account_id

    try:
        resp = requests.get(CODEX_USAGE_URL, headers=headers, timeout=20)
        if resp.status_code in [401, 403, 429]:
            log.warning(f"Codex usage request returned {resp.status_code}: {resp.text[:200]}")
            return None
        if resp.status_code != 200:
            log.error(f"Codex usage request failed: {resp.status_code} {resp.text[:200]}")
            return None
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Network error fetching Codex usage: {e}")
        return None


def normalize_rate_window(window: dict | None) -> dict:
    window = window or {}
    used_percent = window.get("used_percent")
    try:
        used_percent = float(used_percent)
    except (TypeError, ValueError):
        used_percent = 0.0

    return {
        "used_percent": round(used_percent, 1),
        "limit_window_seconds": int(window.get("limit_window_seconds") or 0),
        "reset_after_seconds": int(window.get("reset_after_seconds") or 0),
        "reset_at": unix_to_iso(window.get("reset_at")),
    }


def build_codex_status_output(auth: dict) -> dict | None:
    if str(auth.get("auth_mode", "")).lower() != "chatgpt":
        return None

    if codex_access_token_expired(auth):
        auth = refresh_codex_auth(auth) or auth

    access_token = (auth.get("tokens") or {}).get("access_token")
    if not access_token:
        raise RuntimeError("No Codex access token available")

    account_id = get_codex_account_id(auth)
    usage = fetch_codex_usage(access_token, account_id=account_id)
    if usage is None:
        refreshed_auth = refresh_codex_auth(auth)
        if refreshed_auth:
            access_token = (refreshed_auth.get("tokens") or {}).get("access_token")
            account_id = get_codex_account_id(refreshed_auth)
            usage = fetch_codex_usage(access_token, account_id=account_id)
            auth = refreshed_auth

    if usage is None:
        raise RuntimeError("Failed to fetch Codex ChatGPT usage endpoint")

    credits = usage.get("credits") or {}
    reset_credits = usage.get("rate_limit_reset_credits") or {}

    return {
        "updated_at": current_iso(),
        "label": DEFAULT_LABEL,
        "mode": "codex_chatgpt",
        "plan_type": get_codex_plan_type(auth) or "unknown",
        "primary_window": normalize_rate_window((usage.get("rate_limit") or {}).get("primary_window")),
        "secondary_window": normalize_rate_window((usage.get("rate_limit") or {}).get("secondary_window")),
        "credits": {
            "has_credits": bool(credits.get("has_credits")),
            "unlimited": bool(credits.get("unlimited")),
            "balance": str(credits.get("balance", "")),
            "available_count": int(reset_credits.get("available_count") or 0),
        },
    }


def make_openai_admin_request(endpoint: str, api_key: str, params: dict | None = None) -> dict | None:
    headers = {
        "Authorization": "Bearer " + api_key,
        "Accept": "application/json",
    }
    try:
        resp = requests.get(f"{OPENAI_API_BASE_URL}{endpoint}", headers=headers, params=params, timeout=20)
        if resp.status_code in [401, 403, 429]:
            log.warning(f"OpenAI admin request returned {resp.status_code}: {resp.text[:200]}")
            return None
        if resp.status_code != 200:
            log.error(f"OpenAI admin request failed: {resp.status_code} {resp.text[:200]}")
            return None
        return resp.json()
    except requests.RequestException as e:
        log.error(f"Network error fetching OpenAI organization usage: {e}")
        return None


def empty_usage_summary() -> dict:
    return {
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "input_audio_tokens": 0,
        "output_audio_tokens": 0,
    }


def apply_usage_result(target: dict, result: dict):
    target["requests"] += int(result.get("num_model_requests") or 0)
    target["input_tokens"] += int(result.get("input_tokens") or 0)
    target["output_tokens"] += int(result.get("output_tokens") or 0)
    target["cached_tokens"] += int(result.get("input_cached_tokens") or 0)
    target["input_audio_tokens"] += int(result.get("input_audio_tokens") or 0)
    target["output_audio_tokens"] += int(result.get("output_audio_tokens") or 0)


def summarize_usage_buckets(raw: dict) -> tuple[dict, dict[str, dict]]:
    total = empty_usage_summary()
    per_model: dict[str, dict] = {}

    for bucket in raw.get("data", []):
        for result in bucket.get("results", []):
            if result.get("object") != "organization.usage.completions.result":
                continue

            apply_usage_result(total, result)

            model_name = result.get("model") or "unknown"
            model_summary = per_model.setdefault(model_name, empty_usage_summary())
            apply_usage_result(model_summary, result)

    return total, per_model


def merge_model_windows(models_24h: dict[str, dict], models_7d: dict[str, dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for window_key, source in (("24h", models_24h), ("7d", models_7d)):
        for model_name, usage in source.items():
            entry = merged.setdefault(model_name, {
                "model": model_name,
                "requests_24h": 0,
                "input_tokens_24h": 0,
                "output_tokens_24h": 0,
                "cached_tokens_24h": 0,
                "requests_7d": 0,
                "input_tokens_7d": 0,
                "output_tokens_7d": 0,
                "cached_tokens_7d": 0,
            })
            entry[f"requests_{window_key}"] = usage.get("requests", 0)
            entry[f"input_tokens_{window_key}"] = usage.get("input_tokens", 0)
            entry[f"output_tokens_{window_key}"] = usage.get("output_tokens", 0)
            entry[f"cached_tokens_{window_key}"] = usage.get("cached_tokens", 0)

    return sorted(
        merged.values(),
        key=lambda item: (
            item.get("requests_7d", 0),
            item.get("requests_24h", 0),
            item.get("input_tokens_7d", 0) + item.get("output_tokens_7d", 0),
        ),
        reverse=True,
    )


def fetch_admin_usage_window(creds: dict, start_time: int, end_time: int, bucket_width: str, limit: int) -> dict | None:
    params = {
        "start_time": start_time,
        "end_time": end_time,
        "bucket_width": bucket_width,
        "limit": limit,
        "group_by": ["model"],
    }

    if creds.get("project_ids"):
        params["project_ids"] = creds["project_ids"]
    if creds.get("model_filters"):
        params["models"] = creds["model_filters"]

    return make_openai_admin_request("/organization/usage/completions", creds["admin_api_key"], params=params)


def build_admin_usage_output(creds: dict) -> dict:
    now = int(time.time())
    usage_24h_raw = fetch_admin_usage_window(creds, now - 24 * 3600, now, "1h", 24)
    usage_7d_raw = fetch_admin_usage_window(creds, now - 7 * 24 * 3600, now, "1d", 7)

    if usage_24h_raw is None or usage_7d_raw is None:
        raise RuntimeError("Failed to fetch OpenAI organization usage")

    summary_24h, models_24h = summarize_usage_buckets(usage_24h_raw)
    summary_7d, models_7d = summarize_usage_buckets(usage_7d_raw)

    return {
        "updated_at": current_iso(),
        "label": creds.get("label", DEFAULT_LABEL),
        "mode": "organization_admin",
        "scope": {
            "project_ids": creds.get("project_ids", []),
            "model_filters": creds.get("model_filters", DEFAULT_MODEL_FILTERS),
        },
        "window_24h": summary_24h,
        "window_7d": summary_7d,
        "models": merge_model_windows(models_24h, models_7d),
    }


def save_usage(payload: dict):
    write_json(USAGE_FILE, payload)


def write_error(error_code: str, detail: str):
    save_usage({
        "updated_at": current_iso(),
        "error": error_code,
        "detail": detail,
    })


def fetch_and_save_usage():
    codex_auth = load_codex_auth()
    if codex_auth:
        auth_mode = str(codex_auth.get("auth_mode", "")).lower()
        if auth_mode == "chatgpt":
            try:
                save_usage(build_codex_status_output(codex_auth))
                return
            except Exception as e:
                log.warning(f"Codex ChatGPT usage path failed, falling back if possible: {e}")
        elif auth_mode == "apikey" and not load_dashboard_credentials():
            save_usage({
                "updated_at": current_iso(),
                "label": DEFAULT_LABEL,
                "mode": "codex_api_key",
                "status": "Codex is signed in with API key mode. Configure an OpenAI Admin API key for organization usage totals or sign in with ChatGPT for plan/rate-limit data.",
            })
            return

    dashboard_creds = load_dashboard_credentials()
    if dashboard_creds:
        save_usage(build_admin_usage_output(dashboard_creds))
        return

    raise RuntimeError("No Codex ChatGPT auth or OpenAI admin credentials configured")


def main():
    if not load_codex_auth() and not load_dashboard_credentials():
        log.error("No credentials. Sign in with Codex CLI or configure an OpenAI Admin API key first.")
        sys.exit(1)

    try:
        fetch_and_save_usage()
    except Exception as e:
        log.error(f"OpenAI / Codex usage fetch failed: {e}")
        write_error("fetch_failed", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
