# Contributing

Thanks for helping make this dashboard better. Useful contributions are small, specific, and easy to test on real hardware.

## Good First Contributions

- Add or improve a widget.
- Improve the local configurator labels, accessibility, or validation.
- Test the Waveshare 10.85-inch partial refresh behavior and report exact rectangles.
- Improve logs or error messages when an integration fails.
- Add examples for real dashboard layouts.
- Add compatible icons or font-gallery improvements; see `docs/ASSETS.md`.
- Clean up docs when setup steps are confusing.

## Before Opening An Issue

Please include:

- Raspberry Pi model and OS version.
- Display model and connection details.
- Whether the systemd service or foreground `python3 main.py` run failed.
- The widget or integration involved.
- The smallest config snippet that reproduces the issue, with secrets removed.
- Relevant logs from `journalctl -u epaper-dashboard -f` or `~/dashboard/dashboard.log`.

Do not paste tokens, API keys, OAuth callback URLs, local account emails, printer access codes, or full config files containing secrets.

## Development Setup

Clone your fork, then install dependencies:

```bash
git clone https://github.com/<your-user>/Waveshare-ePaper-10.85-dashboard.git
cd Waveshare-ePaper-10.85-dashboard
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

For manual config testing:

```bash
cp config/dashboard_config.example.json dashboard_config.json
python3 config_server.py --host 127.0.0.1 --port 8080
```

Most rendering changes should still be checked on the Pi, because desktop Python cannot prove SPI, GPIO, or e-paper refresh behavior.

## Checks Before A Pull Request

Run lightweight syntax checks:

```bash
python3 -m py_compile main.py config_server.py dashboard/*.py
```

On a Pi, also run:

```bash
python3 main.py
sudo systemctl restart epaper-dashboard
journalctl -u epaper-dashboard -f
```

For display-driver or partial-refresh changes, include:

- Rectangle coordinates and dimensions tested.
- Whether the update crossed the 680px controller split.
- Whether a full-screen source buffer was used.
- Photos or short notes about ghosting, crashes, and recovery.

## Pull Request Style

- Keep PRs focused on one behavior or cleanup.
- Prefer clear names over clever abstractions.
- Keep root files minimal. Put detailed references in `docs/`.
- Update `config/dashboard_config.example.json` when config shape changes.
- Update `README.md` only for the short path; put detailed setup in `docs/WIDGETS.md` and visual asset guidance in `docs/ASSETS.md`.
- Preserve local-only secret files in `.gitignore`.

## Logging First

If a failure is hard to reproduce, improve the log path before guessing. The best bug report usually has a short description, a config snippet with secrets removed, and the exact log line that shows where the dashboard got stuck.