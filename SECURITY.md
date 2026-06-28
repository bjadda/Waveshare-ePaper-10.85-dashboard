# Security Policy

This project is designed for a personal Raspberry Pi on a trusted local network. It is not hardened as an internet-facing application.

## Supported Branch

Security fixes are accepted for the `main` branch.

## Reporting A Vulnerability

Please do not open a public issue with exploit details, tokens, API keys, OAuth callback URLs, local emails, printer access codes, or private logs.

Use GitHub private vulnerability reporting if it is available for this repository. If it is not available, open a minimal public issue that says security contact is needed, without technical details or secrets.

Helpful private report details:

- Affected file or feature.
- Steps to reproduce.
- Expected impact.
- Whether the issue requires local network access, Pi shell access, or a malicious config.
- Relevant logs with secrets removed.

## Local Secrets

The dashboard may create local runtime files such as:

- `dashboard_config.json`
- `config.env`
- `*_creds.json`
- `*_token.json`
- `credentials.json`
- `token.json`
- `strava_token.json`
- `roborock_session.pkl`
- `openai_usage.json`
- `usage.json`
- `limits.json`
- `*.log`
- Home Assistant and GitHub tokens saved inside `dashboard_config.json`

These files are ignored by git and should stay local to the Pi. Review logs before sharing them, because provider errors can include account identifiers or request details. The configurator debug bundle redacts obvious token and key fields, but still review it before attaching it to an issue.

## Web Configurator

`config_server.py` has no login system. Run it only on a trusted LAN, preferably only while configuring the dashboard. Its debug bundle endpoint is intended for local troubleshooting and should not be exposed publicly.

Safer default:

```bash
python3 config_server.py --host 127.0.0.1 --port 8080
```

Convenient LAN mode:

```bash
python3 config_server.py --host 0.0.0.0 --port 8080
```

Use LAN mode only when the network is trusted. Do not expose the configurator through port forwarding or a public reverse proxy.

## OAuth And API Integrations

Some widgets use OAuth tokens or provider API keys. Keep these points in mind:

- First-run auth flows may print URLs containing short-lived authorization codes.
- Saved token files should be treated like passwords.
- The OpenAI/Codex widget can reuse local Codex CLI auth or an OpenAI Admin API key.
- The Antigravity helper includes public native-client OAuth identifiers. Those are not local secrets, but saved refresh tokens are.
- If a token is accidentally shared, revoke it with the provider and delete the local token file before re-authenticating.

## Hardware Safety

The e-paper display should not be refreshed aggressively. Keep the normal one-minute render cadence unless you are intentionally testing hardware behavior. For partial-refresh driver changes, document the rectangle size, coordinates, controller split behavior, and any ghosting or recovery steps.
