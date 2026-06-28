# Credits and Project Changes

This file records project ownership and the main changes in this repo. It is attribution, not a project license.

## Credits

- Original repository owner: [czuryk](https://github.com/czuryk), via [`czuryk/Waveshare-ePaper-10.85-dashboard`](https://github.com/czuryk/Waveshare-ePaper-10.85-dashboard).

## What This Dashboard Adds

- Patched 10.85-inch e-paper partial refresh handling for safer rectangular updates.
- Modular widget rendering in `dashboard/dashboard_widgets.py`.
- JSON-backed runtime configuration in `dashboard_config.json`.
- Accessible local web configurator in `config_server.py`.
- Dashboard profiles, named screen regions, widget fit rules, and dynamic slots with priority fallback or timed rotation.
- OpenAI/Codex, Claude Code, Antigravity, Strava, Bambu Lab, Roborock, Spotify/Last.fm, Gmail, weather, calendar, Home Assistant, GitHub/DevOps, system load, crypto, and network widgets.

## Maintenance Notes

- Do not commit local secrets or runtime state. Use `config/dashboard_config.example.json` as the shareable reference.
- Keep new Python package dependencies in `requirements.txt`.
- Keep Raspberry Pi OS packages in `install.sh` because GPIO/SPI packages are better installed through apt on the Pi.
