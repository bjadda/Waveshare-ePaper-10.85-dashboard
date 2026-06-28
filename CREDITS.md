# Credits and Project Changes

This file records project ownership and the main changes in this branch. It is attribution, not a project license.

## Credits

- Original repository owner: [bjadda](https://github.com/bjadda).

## What This Dashboard Adds

- Patched 10.85-inch e-paper partial refresh handling for safer rectangular updates.
- Modular widget rendering in `dashboard_widgets.py`.
- JSON-backed runtime configuration in `dashboard_config.json`.
- Accessible local web configurator in `config_server.py`.
- Dynamic widget slots with priority fallback or timed rotation per screen region.
- OpenAI/Codex, Claude Code, Antigravity, Strava, Bambu Lab, Roborock, Spotify/Last.fm, Gmail, weather, system load, crypto, and network widgets.

## Maintenance Notes

- Do not commit local secrets or runtime state. Use `dashboard_config.example.json` as the shareable reference.
- Keep new Python package dependencies in `requirements.txt`.
- Keep Raspberry Pi OS packages in `install.sh` because GPIO/SPI packages are better installed through apt on the Pi.
