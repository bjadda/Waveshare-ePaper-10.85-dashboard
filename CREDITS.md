# Credits and Project Changes

This project combines vendor display code, bundled local libraries, and dashboard-specific application work. This file is attribution, not a project license.

## Credits

- Waveshare: e-paper hardware driver code under `lib/waveshare_epd/`, including the MIT-style permission notice in those source files.
- Bambu Lab API package authors: bundled local package under `lib/bambulabs_api/`.
- Raspberry Pi, Waveshare, Open-Meteo, Strava, Last.fm, Roborock, Anthropic Claude, and OpenAI/Codex ecosystems: services and hardware this dashboard integrates with.
- GitHub Copilot assisted with the Raspberry Pi installer flow in [PR #2](https://github.com/bjadda/Waveshare-ePaper-10.85-dashboard/pull/2).

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
