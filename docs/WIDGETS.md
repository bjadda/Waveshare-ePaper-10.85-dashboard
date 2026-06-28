# Widget Setup

Use the web configurator for normal setup:

```bash
cd ~/dashboard
python3 config_server.py --host 0.0.0.0 --port 8080
```

Open `http://<pi-ip>:8080` on the same trusted network, save, then restart:

```bash
sudo systemctl restart epaper-dashboard
```

Manual setup starts from `config/dashboard_config.example.json`.

## Profiles And Fit Rules

Profiles are complete dashboard views. The active profile owns the dynamic slot choices, while the top-level `slots` block mirrors that active profile for older tooling.

Named regions carry a shape type such as `wide_card`, `large_panel`, `status_tile`, or `header`. Widgets declare which region types they support in `dashboard/dashboard_registry.py`, and the configurator filters the add-widget menus so a widget is not offered in a region it cannot fit.

## Dynamic Slots

Each screen region has a slot in `dashboard_config.json`. A slot can use the first available widget as a priority fallback, or rotate through multiple widgets on a timer.

```json
"right_middle": {
  "widgets": ["ai_usage", "spotify", "time_progress"],
  "rotate": true,
  "seconds": 300
}
```

This rotates the right-middle region every five minutes while the rest of the screen stays stable. If a widget is disabled, the next available widget in that region becomes the fallback.

## AI Usage Widgets

### Claude Code

1. Enable the Claude widget.
2. Run `python3 main.py` in a terminal for first-run auth.
3. Open the printed authorization URL in a browser.
4. Copy the full localhost callback URL back into the terminal.
5. The token is saved to `claude_creds.json`.

Logs: `claude_monitor.log` and `usage.json`.

### OpenAI / Codex

1. Enable the OpenAI / Codex widget.
2. Preferred: sign in with the local Codex CLI so the widget can reuse `~/.codex/auth.json`.
3. Optional fallback: provide an OpenAI Admin API key when prompted.
4. Run `python3 main.py` once in a terminal to complete setup.

Logs: `openai_monitor.log` and `openai_usage.json`.

### Antigravity

1. Enable the Antigravity widget.
2. Run `python3 main.py` in a terminal for first-run auth.
3. Open the printed authorization URL in a browser.
4. Copy the full localhost callback URL back into the terminal.
5. The token is saved to `antigravity_creds.json`.

Logs: `limits.log` and `limits.json`.

## Calendar, Home, And DevOps Widgets

### Calendar

The calendar widget reads one or more ICS URLs or a local ICS file. Configure it with the web UI, or set `integrations.calendar.urls`, `integrations.calendar.path`, and `integrations.calendar.max_events` manually.

### Home Assistant

Use a Home Assistant base URL, a long-lived access token, and a small list of entity IDs. Each entity line in the configurator can use `entity_id | label | unit`.

### GitHub / DevOps

Add repositories as `owner/repo`. A token is optional for public repositories but recommended to avoid low anonymous rate limits. The widget summarizes open PRs, non-PR issues, and the latest workflow status.

## Home And Device Widgets

### Strava

1. Create a Strava API application.
2. Run `python3 main.py` in a terminal.
3. Enter the client ID and client secret when prompted.
4. Open the printed authorization URL.
5. Paste the returned `code=...` value back into the terminal.

Token file: `strava_token.json`.

### Roborock

1. Add the Roborock account email in the configurator.
2. Run `python3 main.py`.
3. Enter the one-time password sent by Roborock.

Session file: `roborock_session.pkl`.

### Bambu Lab

You do not need to enable LAN mode for the current local data path.

1. On the printer, open Settings, then Network.
2. Note the printer IP address, serial number, and access code.
3. Add those values in the configurator.

For reliability, reserve the printer IP address on your router.

### Spotify Via Last.fm

The dashboard reads current playback through Last.fm.

1. Connect Spotify to Last.fm.
2. Create a Last.fm API key.
3. Add the API key and Last.fm username in the configurator.

A paid Last.fm account is not required.

### Gmail

1. Create a Google Cloud project.
2. Enable the Gmail API.
3. Create OAuth credentials for a desktop application.
4. Save the credentials file as needed by your setup.
5. Run `python3 main.py` once to complete the browser auth flow.

Token file: `token.json`.

## Troubleshooting

Start with logs:

```bash
journalctl -u epaper-dashboard -f
tail -f ~/dashboard/dashboard.log
```

If a widget shows fallback text on the display, check that widget's token or usage file first. The configurator can also download a redacted debug bundle with config shape, file status, and recent logs. If the display stops refreshing, restart the service and check whether the last log line mentions a full refresh, partial refresh, or hardware hang.
