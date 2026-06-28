#!/usr/bin/python3
# -*- coding:utf-8 -*-
import argparse
import json
import os
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dashboard import dashboard_config, dashboard_defaults

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULTS = dashboard_defaults.dashboard_config_defaults()

WIDGET_META = [
    {
        'id': 'strava',
        'label': 'Strava',
        'description': 'Activity totals and recent training stats.',
        'icon': 'activity'
    },
    {
        'id': 'bambu',
        'label': 'Bambu Lab',
        'description': '3D printer status, progress, and layer details.',
        'icon': 'printer'
    },
    {
        'id': 'roborock',
        'label': 'Roborock',
        'description': 'Vacuum status, battery, and cleaning area.',
        'icon': 'vacuum'
    },
    {
        'id': 'antigravity',
        'label': 'Antigravity',
        'description': 'Antigravity usage limits and reset time.',
        'icon': 'code'
    },
    {
        'id': 'claude',
        'label': 'Claude Code',
        'description': 'Claude Code usage windows and remaining quota.',
        'icon': 'gauge'
    },
    {
        'id': 'openai',
        'label': 'OpenAI / Codex',
        'description': 'Codex usage and rate-limit status.',
        'icon': 'gauge'
    },
    {
        'id': 'spotify',
        'label': 'Spotify',
        'description': 'Now playing data via Last.fm.',
        'icon': 'music'
    }
]

SLOT_WIDGET_META = [
    {'id': 'strava', 'label': 'Strava', 'icon': 'activity'},
    {'id': 'sysload', 'label': 'System load', 'icon': 'cpu'},
    {'id': 'bambu', 'label': 'Bambu Lab', 'icon': 'printer'},
    {'id': 'crypto', 'label': 'Crypto prices', 'icon': 'coins'},
    {'id': 'roborock', 'label': 'Roborock', 'icon': 'vacuum'},
    {'id': 'antigravity', 'label': 'Antigravity', 'icon': 'code'},
    {'id': 'ping', 'label': 'Network ping', 'icon': 'wifi'},
    {'id': 'ai_usage', 'label': 'AI usage', 'icon': 'gauge'},
    {'id': 'spotify', 'label': 'Spotify', 'icon': 'music'},
    {'id': 'time_progress', 'label': 'Time progress', 'icon': 'clock'}
]

SLOT_META = [
    {'id': 'left_top', 'label': 'Left top', 'description': 'Upper-left widget region.'},
    {'id': 'left_middle', 'label': 'Left middle', 'description': 'Center-left widget region.'},
    {'id': 'left_bottom', 'label': 'Left bottom', 'description': 'Lower-left widget region.'},
    {'id': 'right_middle', 'label': 'Right middle', 'description': 'Large right-side widget region.'}
]

HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Waveshare Dashboard Configurator</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <svg class="svg-sprite" aria-hidden="true" focusable="false">
    <symbol id="icon-activity" viewBox="0 0 24 24"><path d="M3 13h4l2-7 4 14 3-7h5"/></symbol>
    <symbol id="icon-printer" viewBox="0 0 24 24"><path d="M7 8V3h10v5"/><path d="M7 17H5a2 2 0 0 1-2-2v-4a3 3 0 0 1 3-3h12a3 3 0 0 1 3 3v4a2 2 0 0 1-2 2h-2"/><path d="M7 14h10v7H7z"/></symbol>
    <symbol id="icon-vacuum" viewBox="0 0 24 24"><path d="M4 13a8 8 0 0 1 16 0v4H4z"/><path d="M7 17v3m10-3v3"/><path d="M9 11h.01M15 11h.01"/></symbol>
    <symbol id="icon-code" viewBox="0 0 24 24"><path d="m8 9-4 3 4 3"/><path d="m16 9 4 3-4 3"/><path d="m14 5-4 14"/></symbol>
    <symbol id="icon-gauge" viewBox="0 0 24 24"><path d="M4 14a8 8 0 0 1 16 0"/><path d="M12 14l4-5"/><path d="M7 18h10"/></symbol>
    <symbol id="icon-music" viewBox="0 0 24 24"><path d="M9 18V5l10-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="16" cy="16" r="3"/></symbol>
    <symbol id="icon-cpu" viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1"/><path d="M9 1v4m6-4v4M9 19v4m6-4v4M1 9h4m-4 6h4m14-6h4m-4 6h4"/></symbol>
    <symbol id="icon-coins" viewBox="0 0 24 24"><ellipse cx="9" cy="6" rx="6" ry="3"/><path d="M3 6v6c0 1.7 2.7 3 6 3s6-1.3 6-3V6"/><path d="M15 10c3.4.2 6 1.4 6 3s-2.7 3-6 3c-1.2 0-2.4-.2-3.3-.5"/><path d="M21 13v5c0 1.7-2.7 3-6 3-2.3 0-4.3-.6-5.3-1.5"/></symbol>
    <symbol id="icon-wifi" viewBox="0 0 24 24"><path d="M5 13a10 10 0 0 1 14 0"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M12 20h.01"/></symbol>
    <symbol id="icon-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
    <symbol id="icon-grid" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></symbol>
    <symbol id="icon-save" viewBox="0 0 24 24"><path d="M5 3h12l2 2v16H5z"/><path d="M8 3v6h8V3"/><path d="M8 21v-7h8v7"/></symbol>
    <symbol id="icon-rotate" viewBox="0 0 24 24"><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/></symbol>
    <symbol id="icon-plus" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></symbol>
    <symbol id="icon-trash" viewBox="0 0 24 24"><path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M7 7l1 14h8l1-14"/></symbol>
    <symbol id="icon-up" viewBox="0 0 24 24"><path d="m6 15 6-6 6 6"/></symbol>
    <symbol id="icon-down" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
    <symbol id="icon-eye" viewBox="0 0 24 24"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></symbol>
    <symbol id="icon-terminal" viewBox="0 0 24 24"><path d="m4 7 5 5-5 5"/><path d="M12 17h8"/></symbol>
    <symbol id="icon-github" viewBox="0 0 24 24"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.9a3.4 3.4 0 0 0-.9-2.6c3-.3 6.1-1.5 6.1-6.7a5.2 5.2 0 0 0-1.4-3.6 4.8 4.8 0 0 0-.1-3.6s-1.1-.3-3.7 1.4a12.8 12.8 0 0 0-6.8 0C6.6 2.3 5.5 2.6 5.5 2.6a4.8 4.8 0 0 0-.1 3.6A5.2 5.2 0 0 0 4 9.8c0 5.2 3.1 6.4 6.1 6.7a3 3 0 0 0-.8 1.9V22"/></symbol>
  </svg>

  <a class="skip-link" href="#settings">Skip to settings</a>

  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"><svg><use href="#icon-grid"></use></svg></span>
        <div>
          <p class="eyebrow">Waveshare 10.85 e-paper</p>
          <h1>Dashboard control panel</h1>
        </div>
      </div>
      <nav class="github-actions" aria-label="Project links">
        <a class="github-link" href="https://github.com/bjadda/Waveshare-ePaper-10.85-dashboard">
          <svg aria-hidden="true"><use href="#icon-github"></use></svg>
          Repository
        </a>
        <a class="github-link" href="https://github.com/bjadda/Waveshare-ePaper-10.85-dashboard/issues">
          <svg aria-hidden="true"><use href="#icon-github"></use></svg>
          Issues
        </a>
      </nav>
      <div class="status-stack">
        <span id="saveStatus" class="status-pill" role="status" aria-live="polite">Loading config</span>
        <span id="configPath" class="path-label"></span>
      </div>
    </header>

    <main class="app-grid">
      <aside class="preview-panel" aria-labelledby="previewTitle">
        <div class="panel-heading">
          <span aria-hidden="true"><svg><use href="#icon-grid"></use></svg></span>
          <div>
            <h2 id="previewTitle">Screen map</h2>
            <p>Physical screen regions.</p>
          </div>
        </div>
        <div id="screenPreview" class="screen-preview" aria-label="Dashboard screen region preview"></div>
        <div class="preview-footer">
          <button id="restartButton" class="secondary-button" type="button">
            <svg aria-hidden="true"><use href="#icon-rotate"></use></svg>
            Restart dashboard
          </button>
        </div>
      </aside>

      <form id="settings" class="settings" aria-labelledby="settingsTitle">
        <div class="settings-header">
          <div>
            <p class="eyebrow">Runtime settings</p>
            <h2 id="settingsTitle">Compose the dashboard</h2>
          </div>
          <div class="action-row">
            <button id="resetButton" class="secondary-button" type="button">Reset defaults</button>
            <button id="saveButton" class="primary-button" type="submit" disabled>
              <svg aria-hidden="true"><use href="#icon-save"></use></svg>
              Save changes
            </button>
          </div>
        </div>

        <section class="panel" aria-labelledby="widgetsTitle">
          <div class="panel-heading">
            <span aria-hidden="true"><svg><use href="#icon-gauge"></use></svg></span>
            <div>
              <h3 id="widgetsTitle">Widget switches</h3>
              <p>Live data sources and optional panels.</p>
            </div>
          </div>
          <div id="widgetToggles" class="toggle-grid"></div>
        </section>

        <section class="panel" aria-labelledby="slotsTitle">
          <div class="panel-heading">
            <span aria-hidden="true"><svg><use href="#icon-grid"></use></svg></span>
            <div>
              <h3 id="slotsTitle">Screen slots</h3>
              <p>Widget order and rotation by screen region.</p>
            </div>
          </div>
          <div id="slotEditors" class="slot-grid"></div>
        </section>

        <section class="panel" aria-labelledby="locationTitle">
          <div class="panel-heading">
            <span aria-hidden="true"><svg><use href="#icon-wifi"></use></svg></span>
            <div>
              <h3 id="locationTitle">Location</h3>
              <p>Coordinates for weather, air quality, and sunrise calculations.</p>
            </div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>Latitude</span>
              <input id="locationLat" type="number" step="0.000001" inputmode="decimal" autocomplete="off">
            </label>
            <label class="field">
              <span>Longitude</span>
              <input id="locationLon" type="number" step="0.000001" inputmode="decimal" autocomplete="off">
            </label>
          </div>
        </section>

        <section class="panel" aria-labelledby="integrationsTitle">
          <div class="panel-heading">
            <span aria-hidden="true"><svg><use href="#icon-terminal"></use></svg></span>
            <div>
              <h3 id="integrationsTitle">Integrations</h3>
              <p>Local credentials stored on this Pi.</p>
            </div>
          </div>
          <div class="integration-grid">
            <fieldset>
              <legend>Bambu Lab</legend>
              <label class="field"><span>Printer IP</span><input id="bambuIp" autocomplete="off"></label>
              <label class="field"><span>Serial number</span><input id="bambuSerial" autocomplete="off"></label>
              <label class="field secret-field">
                <span>Access code</span>
                <span class="secret-control">
                  <input id="bambuAccessCode" type="password" autocomplete="off">
                  <button class="icon-button reveal-button" type="button" data-target="bambuAccessCode" aria-label="Show Bambu access code" aria-pressed="false"><svg aria-hidden="true"><use href="#icon-eye"></use></svg></button>
                </span>
              </label>
            </fieldset>

            <fieldset>
              <legend>Roborock</legend>
              <label class="field"><span>Account email</span><input id="roborockEmail" type="email" autocomplete="email"></label>
            </fieldset>

            <fieldset>
              <legend>Last.fm</legend>
              <label class="field secret-field">
                <span>API key</span>
                <span class="secret-control">
                  <input id="lastfmApiKey" type="password" autocomplete="off">
                  <button class="icon-button reveal-button" type="button" data-target="lastfmApiKey" aria-label="Show Last.fm API key" aria-pressed="false"><svg aria-hidden="true"><use href="#icon-eye"></use></svg></button>
                </span>
              </label>
              <label class="field"><span>Username</span><input id="lastfmUsername" autocomplete="username"></label>
            </fieldset>

            <fieldset>
              <legend>OpenAI / Codex</legend>
              <label class="field"><span>Widget label</span><input id="openaiLabel" autocomplete="off"></label>
              <label class="field"><span>Project IDs</span><textarea id="openaiProjectIds" rows="3" spellcheck="false"></textarea></label>
              <label class="field"><span>Model filters</span><textarea id="openaiModelFilters" rows="3" spellcheck="false"></textarea></label>
            </fieldset>
          </div>
        </section>
      </form>
    </main>
  </div>

  <script src="/app.js"></script>
</body>
</html>
"""

CSS = r""":root {
  color-scheme: light;
  --paper: #eef2f0;
  --panel: #fffef9;
  --panel-strong: #f8faf8;
  --ink: #181c1f;
  --muted: #5f686f;
  --line: #c9d0cf;
  --line-strong: #879190;
  --cyan: #007d8f;
  --cyan-dark: #005766;
  --amber: #b86800;
  --green: #1d7b4f;
  --red: #b94040;
  --focus: #0f6fff;
  --shadow: 0 18px 50px rgba(24, 28, 31, 0.12);
}

* {
  box-sizing: border-box;
}

html {
  min-width: 320px;
}

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}

button,
input,
select,
textarea {
  font: inherit;
}

button,
input,
select,
textarea {
  border-radius: 6px;
}

svg {
  display: block;
  width: 1.1rem;
  height: 1.1rem;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.9;
}

.svg-sprite {
  display: none;
}

.skip-link {
  position: absolute;
  left: 16px;
  top: 12px;
  z-index: 20;
  transform: translateY(-140%);
  background: var(--ink);
  color: white;
  padding: 10px 12px;
  border-radius: 6px;
}

.skip-link:focus {
  transform: translateY(0);
}

:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 3px;
}

.shell {
  width: min(1440px, calc(100% - 32px));
  margin: 0 auto;
  padding: 22px 0 36px;
}

.topbar,
.settings-header,
.panel-heading,
.brand,
.github-actions,
.action-row,
.preview-footer,
.status-stack {
  display: flex;
  align-items: center;
}

.topbar {
  justify-content: space-between;
  gap: 20px;
  padding: 8px 0 20px;
}

.github-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.github-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 34px;
  padding: 6px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: var(--panel);
  color: var(--ink);
  font-weight: 800;
  text-decoration: none;
}

.github-link:hover {
  border-color: var(--cyan);
  color: var(--cyan-dark);
}

.brand {
  gap: 14px;
  min-width: 0;
}

.brand-mark,
.panel-heading > span {
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: var(--panel);
  color: var(--cyan-dark);
}

.brand-mark svg {
  width: 1.35rem;
  height: 1.35rem;
}

.eyebrow {
  margin: 0 0 2px;
  color: var(--cyan-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 0;
  font-size: 1.75rem;
  line-height: 1.12;
}

h2,
h3 {
  margin-bottom: 2px;
  line-height: 1.2;
}

h2 {
  font-size: 1.25rem;
}

h3 {
  font-size: 1.05rem;
}

.panel-heading p,
.preview-slot p,
.field span,
.path-label {
  color: var(--muted);
}

.panel-heading p,
.preview-slot p {
  margin-bottom: 0;
  font-size: 0.92rem;
}

.status-stack {
  align-items: flex-end;
  flex-direction: column;
  gap: 6px;
  min-width: 220px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 7px 12px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--panel);
  color: var(--muted);
  font-weight: 700;
}

.status-pill.is-dirty {
  border-color: var(--amber);
  color: var(--amber);
}

.status-pill.is-saved {
  border-color: var(--green);
  color: var(--green);
}

.status-pill.is-error {
  border-color: var(--red);
  color: var(--red);
}

.path-label {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 0.78rem;
  overflow-wrap: anywhere;
  text-align: right;
}

.app-grid {
  display: grid;
  grid-template-columns: minmax(300px, 420px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.preview-panel,
.panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

.preview-panel {
  position: sticky;
  top: 16px;
  padding: 16px;
  box-shadow: var(--shadow);
}

.panel {
  padding: 16px;
}

.panel + .panel {
  margin-top: 14px;
}

.panel-heading {
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.screen-preview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: repeat(3, minmax(88px, 1fr));
  gap: 8px;
  aspect-ratio: 10 / 7.46;
  min-height: 300px;
  padding: 10px;
  border: 2px solid var(--ink);
  border-radius: 6px;
  background:
    linear-gradient(#d5dddc 1px, transparent 1px),
    linear-gradient(90deg, #d5dddc 1px, transparent 1px),
    #fbfcfa;
  background-size: 18px 18px;
}

.preview-slot {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: rgba(255, 254, 249, 0.92);
  color: var(--ink);
  text-align: left;
  cursor: pointer;
}

.preview-slot:hover {
  border-color: var(--cyan);
}

.preview-slot[data-slot="right_middle"] {
  grid-column: 2;
  grid-row: 2 / 4;
}

.preview-slot[data-slot="left_top"] {
  grid-column: 1;
  grid-row: 1;
}

.preview-slot[data-slot="left_middle"] {
  grid-column: 1;
  grid-row: 2;
}

.preview-slot[data-slot="left_bottom"] {
  grid-column: 1;
  grid-row: 3;
}

.preview-slot[data-slot="weather"] {
  grid-column: 2;
  grid-row: 1;
  cursor: default;
}

.slot-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
}

.slot-name svg {
  color: var(--cyan-dark);
}

.slot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 3px 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--panel-strong);
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.chip svg {
  width: 0.9rem;
  height: 0.9rem;
}

.preview-footer,
.settings-header {
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.settings-header {
  margin-top: 0;
  margin-bottom: 14px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

.action-row {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.primary-button,
.secondary-button,
.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  font-weight: 800;
  cursor: pointer;
}

.primary-button {
  padding: 0 14px;
  background: var(--ink);
  color: white;
  border-color: var(--ink);
}

.secondary-button {
  padding: 0 12px;
  background: var(--panel-strong);
  color: var(--ink);
}

.primary-button:hover,
.secondary-button:hover,
.icon-button:hover {
  border-color: var(--cyan);
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.switch-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-height: 76px;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-strong);
}

.switch-row strong,
.slot-item strong {
  display: block;
  overflow-wrap: anywhere;
}

.switch-row small {
  display: block;
  color: var(--muted);
}

.switch-row input[type="checkbox"],
.rotate-row input[type="checkbox"] {
  appearance: none;
  position: relative;
  width: 48px;
  height: 28px;
  border: 2px solid var(--line-strong);
  border-radius: 999px;
  background: #dfe6e4;
  cursor: pointer;
}

.switch-row input[type="checkbox"]::after,
.rotate-row input[type="checkbox"]::after {
  content: "";
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transition: transform 0.18s ease;
}

.switch-row input[type="checkbox"]:checked,
.rotate-row input[type="checkbox"]:checked {
  border-color: var(--cyan-dark);
  background: var(--cyan);
}

.switch-row input[type="checkbox"]:checked::after,
.rotate-row input[type="checkbox"]:checked::after {
  transform: translateX(20px);
}

.slot-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.slot-editor {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-strong);
}

.slot-editor h4 {
  margin: 0 0 4px;
  font-size: 1rem;
}

.slot-editor > p {
  margin: 0 0 10px;
  color: var(--muted);
  font-size: 0.88rem;
}

.slot-list {
  display: grid;
  gap: 8px;
  margin: 0 0 10px;
  padding: 0;
  list-style: none;
}

.slot-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  min-width: 0;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}

.slot-actions {
  display: flex;
  gap: 4px;
}

.icon-button {
  width: 36px;
  min-height: 36px;
  padding: 0;
  background: white;
  color: var(--ink);
}

.slot-add {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
}

.rotate-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin-top: 12px;
}

.rotate-row label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
}

.seconds-field {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  color: var(--muted);
  font-size: 0.9rem;
}

.seconds-field input {
  width: 92px;
}

.form-grid,
.integration-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

fieldset {
  margin: 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel-strong);
}

legend {
  padding: 0 6px;
  font-weight: 900;
}

.field {
  display: grid;
  gap: 5px;
  min-width: 0;
  margin-bottom: 10px;
  font-weight: 750;
}

.field:last-child {
  margin-bottom: 0;
}

input,
select,
textarea {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line-strong);
  background: white;
  color: var(--ink);
  padding: 9px 10px;
}

textarea {
  resize: vertical;
}

.secret-control {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 6px;
}

@media (max-width: 1040px) {
  .app-grid {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
  }
}

@media (max-width: 760px) {
  .shell {
    width: min(100% - 20px, 1440px);
    padding-top: 12px;
  }

  .topbar,
  .settings-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .github-actions,
  .status-stack,
  .action-row,
  .preview-footer {
    align-items: stretch;
    width: 100%;
  }

  .path-label {
    text-align: left;
  }

  .screen-preview,
  .toggle-grid,
  .slot-grid,
  .form-grid,
  .integration-grid {
    grid-template-columns: 1fr;
  }

  .screen-preview {
    grid-template-rows: repeat(5, minmax(74px, auto));
    aspect-ratio: auto;
  }

  .preview-slot,
  .preview-slot[data-slot] {
    grid-column: auto;
    grid-row: auto;
  }

  .slot-add,
  .rotate-row {
    grid-template-columns: 1fr;
  }

  .seconds-field {
    justify-content: flex-start;
  }

  .primary-button,
  .secondary-button {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition: none !important;
  }
}
"""

JS = r"""const state = {
  config: null,
  defaults: null,
  meta: null,
  dirty: false
};

const els = {};

function icon(name) {
  return `<svg aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function listToText(values) {
  return Array.isArray(values) ? values.join("\n") : "";
}

function textToList(value) {
  return String(value || "")
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function setStatus(message, tone = "") {
  els.saveStatus.textContent = message;
  els.saveStatus.className = `status-pill ${tone}`.trim();
}

function setDirty(dirty = true) {
  state.dirty = dirty;
  els.saveButton.disabled = !dirty;
  if (dirty) {
    setStatus("Unsaved changes", "is-dirty");
  }
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function widgetById(id) {
  return state.meta.slotWidgets.find((widget) => widget.id === id) || {
    id,
    label: id,
    icon: "grid"
  };
}

function slotById(id) {
  return state.meta.slots.find((slot) => slot.id === id) || {
    id,
    label: id,
    description: ""
  };
}

function ensureConfigShape() {
  state.config.location ||= {};
  state.config.widgets ||= {};
  state.config.integrations ||= {};
  state.config.integrations.bambu ||= {};
  state.config.integrations.roborock ||= {};
  state.config.integrations.lastfm ||= {};
  state.config.integrations.openai ||= {};
  state.config.slots ||= {};

  for (const slot of state.meta.slots) {
    state.config.slots[slot.id] ||= { widgets: [], rotate: false, seconds: 300 };
    state.config.slots[slot.id].widgets ||= [];
  }
}

function renderWidgets() {
  els.widgetToggles.innerHTML = state.meta.widgets.map((widget) => {
    const checked = state.config.widgets[widget.id] ? "checked" : "";
    const id = `widget-${widget.id}`;
    return `
      <label class="switch-row" for="${id}">
        ${icon(widget.icon)}
        <span>
          <strong>${escapeHtml(widget.label)}</strong>
          <small>${escapeHtml(widget.description)}</small>
        </span>
        <input id="${id}" type="checkbox" data-widget="${escapeHtml(widget.id)}" ${checked}>
      </label>
    `;
  }).join("");
}

function renderPreview() {
  const fixedWeather = `
    <article class="preview-slot" data-slot="weather" aria-label="Weather region">
      <span class="slot-name">${icon("wifi")} Weather</span>
      <p>Fixed daily context area</p>
      <span class="slot-meta"><span class="chip">Always on</span></span>
    </article>
  `;

  const slots = state.meta.slots.map((slot) => {
    const config = state.config.slots[slot.id] || {};
    const selected = (config.widgets || []).map(widgetById);
    const label = selected.length ? selected.map((widget) => widget.label).join(", ") : "No widgets selected";
    const chips = selected.slice(0, 3).map((widget) => `<span class="chip">${icon(widget.icon)} ${escapeHtml(widget.label)}</span>`).join("");
    const extra = selected.length > 3 ? `<span class="chip">+${selected.length - 3} more</span>` : "";
    const rotate = config.rotate ? `<span class="chip">${icon("rotate")} ${Number(config.seconds || 300)}s</span>` : `<span class="chip">Priority</span>`;
    return `
      <button class="preview-slot" type="button" data-slot="${escapeHtml(slot.id)}" aria-label="Edit ${escapeHtml(slot.label)} slot: ${escapeHtml(label)}">
        <span>
          <span class="slot-name">${icon("grid")} ${escapeHtml(slot.label)}</span>
          <p>${escapeHtml(label)}</p>
        </span>
        <span class="slot-meta">${chips}${extra}${rotate}</span>
      </button>
    `;
  }).join("");

  els.screenPreview.innerHTML = fixedWeather + slots;
}

function renderSlots() {
  els.slotEditors.innerHTML = state.meta.slots.map((slot) => {
    const config = state.config.slots[slot.id] || { widgets: [], rotate: false, seconds: 300 };
    const selected = config.widgets || [];
    const selectedRows = selected.map((widgetId, index) => {
      const widget = widgetById(widgetId);
      return `
        <li class="slot-item">
          ${icon(widget.icon)}
          <strong>${escapeHtml(widget.label)}</strong>
          <span class="slot-actions">
            <button class="icon-button" type="button" data-slot="${escapeHtml(slot.id)}" data-index="${index}" data-action="up" aria-label="Move ${escapeHtml(widget.label)} up" title="Move up" ${index === 0 ? "disabled" : ""}>${icon("up")}</button>
            <button class="icon-button" type="button" data-slot="${escapeHtml(slot.id)}" data-index="${index}" data-action="down" aria-label="Move ${escapeHtml(widget.label)} down" title="Move down" ${index === selected.length - 1 ? "disabled" : ""}>${icon("down")}</button>
            <button class="icon-button" type="button" data-slot="${escapeHtml(slot.id)}" data-index="${index}" data-action="remove" aria-label="Remove ${escapeHtml(widget.label)}" title="Remove">${icon("trash")}</button>
          </span>
        </li>
      `;
    }).join("");

    const available = state.meta.slotWidgets
      .filter((widget) => !selected.includes(widget.id))
      .map((widget) => `<option value="${escapeHtml(widget.id)}">${escapeHtml(widget.label)}</option>`)
      .join("");

    const rotateId = `${slot.id}-rotate`;
    const secondsId = `${slot.id}-seconds`;
    const selectId = `${slot.id}-add`;
    return `
      <section class="slot-editor" id="slot-editor-${escapeHtml(slot.id)}" aria-labelledby="${escapeHtml(slot.id)}-title">
        <h4 id="${escapeHtml(slot.id)}-title">${escapeHtml(slot.label)}</h4>
        <p>${escapeHtml(slot.description)}</p>
        <ul class="slot-list" aria-label="${escapeHtml(slot.label)} widget priority">
          ${selectedRows || `<li class="slot-item"><span></span><strong>No widgets selected</strong><span></span></li>`}
        </ul>
        <div class="slot-add">
          <label class="field" for="${selectId}">
            <span>Add widget</span>
            <select id="${selectId}" data-slot="${escapeHtml(slot.id)}">${available || '<option value="">All widgets selected</option>'}</select>
          </label>
          <button class="secondary-button" type="button" data-slot="${escapeHtml(slot.id)}" data-action="add" ${available ? "" : "disabled"}>
            ${icon("plus")}
            Add
          </button>
        </div>
        <div class="rotate-row">
          <label for="${rotateId}">
            <input id="${rotateId}" type="checkbox" data-slot="${escapeHtml(slot.id)}" data-action="rotate" ${config.rotate ? "checked" : ""}>
            Rotate selected widgets
          </label>
          <label class="seconds-field" for="${secondsId}">
            Seconds
            <input id="${secondsId}" type="number" min="30" max="86400" step="30" value="${Number(config.seconds || 300)}" data-slot="${escapeHtml(slot.id)}" data-action="seconds">
          </label>
        </div>
      </section>
    `;
  }).join("");
}

function renderFields() {
  els.locationLat.value = state.config.location.lat ?? "";
  els.locationLon.value = state.config.location.lon ?? "";
  els.bambuIp.value = state.config.integrations.bambu.ip ?? "";
  els.bambuSerial.value = state.config.integrations.bambu.serial ?? "";
  els.bambuAccessCode.value = state.config.integrations.bambu.access_code ?? "";
  els.roborockEmail.value = state.config.integrations.roborock.email ?? "";
  els.lastfmApiKey.value = state.config.integrations.lastfm.api_key ?? "";
  els.lastfmUsername.value = state.config.integrations.lastfm.username ?? "";
  els.openaiLabel.value = state.config.integrations.openai.label ?? "OPENAI / CODEX";
  els.openaiProjectIds.value = listToText(state.config.integrations.openai.project_ids);
  els.openaiModelFilters.value = listToText(state.config.integrations.openai.model_filters);
}

function renderAll() {
  ensureConfigShape();
  renderWidgets();
  renderSlots();
  renderPreview();
  renderFields();
}

function updateConfigFromFields() {
  state.config.location.lat = Number(els.locationLat.value);
  state.config.location.lon = Number(els.locationLon.value);
  state.config.integrations.bambu.ip = els.bambuIp.value.trim();
  state.config.integrations.bambu.serial = els.bambuSerial.value.trim();
  state.config.integrations.bambu.access_code = els.bambuAccessCode.value.trim();
  state.config.integrations.roborock.email = els.roborockEmail.value.trim();
  state.config.integrations.lastfm.api_key = els.lastfmApiKey.value.trim();
  state.config.integrations.lastfm.username = els.lastfmUsername.value.trim();
  state.config.integrations.openai.label = els.openaiLabel.value.trim() || "OPENAI / CODEX";
  state.config.integrations.openai.project_ids = textToList(els.openaiProjectIds.value);
  state.config.integrations.openai.model_filters = textToList(els.openaiModelFilters.value);
}

async function loadConfig() {
  const response = await fetch("/api/config", { headers: { "Accept": "application/json" } });
  if (!response.ok) throw new Error(`Load failed: ${response.status}`);
  const payload = await response.json();
  state.config = payload.config;
  state.defaults = payload.defaults;
  state.meta = payload.meta;
  els.configPath.textContent = payload.path;
  els.restartButton.disabled = !payload.meta.canRestart;
  els.restartButton.title = payload.meta.canRestart ? "Restart the systemd dashboard service" : "Start this server with --allow-restart to enable service restarts";
  renderAll();
  setDirty(false);
  setStatus("Config loaded", "is-saved");
}

async function saveConfig(event) {
  event.preventDefault();
  updateConfigFromFields();
  setStatus("Saving...", "");
  els.saveButton.disabled = true;
  const response = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify(state.config)
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || `Save failed: ${response.status}`);
  }
  const payload = await response.json();
  state.config = payload.config;
  renderAll();
  setDirty(false);
  setStatus("Saved", "is-saved");
}

async function restartDashboard() {
  setStatus("Restarting service...", "");
  const response = await fetch("/api/restart", {
    method: "POST",
    headers: { "Accept": "application/json" }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Restart failed: ${response.status}`);
  }
  setStatus("Dashboard restarted", "is-saved");
}

function moveSlotItem(slotId, index, direction) {
  const widgets = state.config.slots[slotId].widgets;
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= widgets.length) return;
  [widgets[index], widgets[nextIndex]] = [widgets[nextIndex], widgets[index]];
  renderSlots();
  renderPreview();
  setDirty();
}

function removeSlotItem(slotId, index) {
  state.config.slots[slotId].widgets.splice(index, 1);
  renderSlots();
  renderPreview();
  setDirty();
}

function addSlotItem(slotId) {
  const select = document.getElementById(`${slotId}-add`);
  if (!select || !select.value) return;
  state.config.slots[slotId].widgets.push(select.value);
  renderSlots();
  renderPreview();
  setDirty();
}

function handleSlotClick(event) {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const action = button.dataset.action;
  const slotId = button.dataset.slot;
  if (!slotId || !state.config.slots[slotId]) return;

  if (action === "up") moveSlotItem(slotId, Number(button.dataset.index), -1);
  if (action === "down") moveSlotItem(slotId, Number(button.dataset.index), 1);
  if (action === "remove") removeSlotItem(slotId, Number(button.dataset.index));
  if (action === "add") addSlotItem(slotId);
}

function handleSlotInput(event) {
  const target = event.target;
  const slotId = target.dataset.slot;
  if (!slotId || !state.config.slots[slotId]) return;

  if (target.dataset.action === "rotate") {
    state.config.slots[slotId].rotate = target.checked;
    renderPreview();
    setDirty();
  }
  if (target.dataset.action === "seconds") {
    state.config.slots[slotId].seconds = Number(target.value || 300);
    renderPreview();
    setDirty();
  }
}

function bindEvents() {
  els.settings.addEventListener("submit", (event) => {
    saveConfig(event).catch((error) => setStatus(error.message, "is-error"));
  });

  els.settings.addEventListener("input", (event) => {
    if (event.target.matches("[data-widget]")) {
      state.config.widgets[event.target.dataset.widget] = event.target.checked;
    } else if (event.target.matches("input, textarea")) {
      updateConfigFromFields();
    }
    setDirty();
    renderPreview();
  });

  els.slotEditors.addEventListener("click", handleSlotClick);
  els.slotEditors.addEventListener("input", handleSlotInput);

  els.screenPreview.addEventListener("click", (event) => {
    const slotButton = event.target.closest("button[data-slot]");
    if (!slotButton) return;
    const target = document.getElementById(`slot-editor-${slotButton.dataset.slot}`);
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
    target?.querySelector("button, input, select")?.focus({ preventScroll: true });
  });

  els.resetButton.addEventListener("click", () => {
    state.config = clone(state.defaults);
    renderAll();
    setDirty();
  });

  els.restartButton.addEventListener("click", () => {
    restartDashboard().catch((error) => setStatus(error.message, "is-error"));
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest(".reveal-button");
    if (!button) return;
    const input = document.getElementById(button.dataset.target);
    if (!input) return;
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-pressed", show ? "true" : "false");
    button.setAttribute("aria-label", `${show ? "Hide" : "Show"} ${input.id}`);
  });
}

function cacheElements() {
  for (const id of [
    "saveStatus", "configPath", "screenPreview", "restartButton", "settings",
    "resetButton", "saveButton", "widgetToggles", "slotEditors",
    "locationLat", "locationLon", "bambuIp", "bambuSerial", "bambuAccessCode",
    "roborockEmail", "lastfmApiKey", "lastfmUsername", "openaiLabel",
    "openaiProjectIds", "openaiModelFilters"
  ]) {
    els[id] = document.getElementById(id);
  }
}

cacheElements();
bindEvents();
loadConfig().catch((error) => setStatus(error.message, "is-error"));
"""


def json_response(handler, status, payload):
    body = json.dumps(payload).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, status, content_type, text):
    body = text.encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', content_type)
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


def metadata(can_restart):
    return {
        'widgets': WIDGET_META,
        'slotWidgets': SLOT_WIDGET_META,
        'slots': SLOT_META,
        'canRestart': can_restart
    }


class ConfigHandler(BaseHTTPRequestHandler):
    allow_restart = False

    def log_message(self, fmt, *args):
        print('%s - %s' % (self.address_string(), fmt % args))

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path in ('/', '/index.html'):
            return text_response(self, 200, 'text/html; charset=utf-8', HTML)
        if path == '/app.css':
            return text_response(self, 200, 'text/css; charset=utf-8', CSS)
        if path == '/app.js':
            return text_response(self, 200, 'application/javascript; charset=utf-8', JS)
        if path == '/api/config':
            config = dashboard_config.config_for_public_response(BASE_DIR, DEFAULTS)
            defaults = dashboard_config.default_config(DEFAULTS)
            return json_response(self, 200, {
                'config': config,
                'defaults': defaults,
                'meta': metadata(self.allow_restart),
                'path': dashboard_config.config_path(BASE_DIR)
            })
        return json_response(self, 404, {'error': 'Not found'})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path == '/api/config':
            return self.save_config()
        if path == '/api/restart':
            return self.restart_dashboard()
        return json_response(self, 404, {'error': 'Not found'})

    def read_json_body(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 1024 * 128:
            raise ValueError('Request body is too large')
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode('utf-8'))

    def save_config(self):
        try:
            incoming = self.read_json_body()
            saved = dashboard_config.save_config(BASE_DIR, incoming, DEFAULTS)
            return json_response(self, 200, {
                'config': saved,
                'path': dashboard_config.config_path(BASE_DIR)
            })
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return json_response(self, 400, {'error': str(exc)})

    def restart_dashboard(self):
        if not self.allow_restart:
            return json_response(self, 403, {
                'error': 'Restart is disabled. Start config_server.py with --allow-restart.'
            })

        try:
            subprocess.run(
                ['sudo', 'systemctl', 'restart', 'epaper-dashboard'],
                check=True,
                timeout=20
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            return json_response(self, 500, {'error': str(exc)})

        return json_response(self, 200, {'ok': True})


def parse_args():
    parser = argparse.ArgumentParser(description='Run the Waveshare dashboard configurator.')
    parser.add_argument('--host', default='127.0.0.1', help='Host/interface to bind.')
    parser.add_argument('--port', default=8080, type=int, help='TCP port to listen on.')
    parser.add_argument(
        '--allow-restart',
        action='store_true',
        help='Allow the web UI to restart the epaper-dashboard systemd service.'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ConfigHandler.allow_restart = args.allow_restart
    server = ThreadingHTTPServer((args.host, args.port), ConfigHandler)
    print('Configurator listening on http://%s:%s' % (args.host, args.port))
    print('Editing %s' % dashboard_config.config_path(BASE_DIR))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping configurator')
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
