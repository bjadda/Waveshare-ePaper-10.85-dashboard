#!/usr/bin/python3
# -*- coding:utf-8 -*-
import copy
import json
import os
import tempfile

CONFIG_FILENAME = 'dashboard_config.json'
CONFIG_VERSION = 1

WIDGET_KEYS = (
    'strava', 'bambu', 'roborock', 'antigravity',
    'claude', 'openai', 'spotify'
)

SLOT_WIDGETS = (
    'strava', 'sysload', 'bambu', 'crypto', 'roborock',
    'antigravity', 'ping', 'ai_usage', 'spotify', 'time_progress'
)

SLOT_KEYS = ('left_top', 'left_middle', 'left_bottom', 'right_middle')


def config_path(base_dir):
    return os.path.join(base_dir, CONFIG_FILENAME)


def bool_value(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ('1', 'true', 'yes', 'y', 'on'):
            return True
        if normalized in ('0', 'false', 'no', 'n', 'off'):
            return False
    return default


def float_value(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def int_value(value, default, minimum=None, maximum=None):
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = int(default)
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def list_value(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def clean_slot_widgets(value, fallback):
    requested = list_value(value)
    cleaned = []
    for widget_id in requested:
        if widget_id in SLOT_WIDGETS and widget_id not in cleaned:
            cleaned.append(widget_id)
    if cleaned:
        return cleaned
    return list(fallback)


def default_config(defaults):
    slots = {}
    for slot_name, slot in defaults.get('slots', {}).items():
        slots[slot_name] = {
            'widgets': list(slot.get('widgets', ())),
            'rotate': bool_value(slot.get('rotate'), False),
            'seconds': int_value(slot.get('seconds'), 300, minimum=30, maximum=86400)
        }

    return {
        'version': CONFIG_VERSION,
        'location': {
            'lat': float_value(defaults.get('location_lat'), 44.8240855),
            'lon': float_value(defaults.get('location_lon'), 20.4934273)
        },
        'widgets': {
            'strava': bool_value(defaults.get('widgets', {}).get('strava'), False),
            'bambu': bool_value(defaults.get('widgets', {}).get('bambu'), False),
            'roborock': bool_value(defaults.get('widgets', {}).get('roborock'), False),
            'antigravity': bool_value(defaults.get('widgets', {}).get('antigravity'), False),
            'claude': bool_value(defaults.get('widgets', {}).get('claude'), False),
            'openai': bool_value(defaults.get('widgets', {}).get('openai'), False),
            'spotify': bool_value(defaults.get('widgets', {}).get('spotify'), False)
        },
        'integrations': {
            'bambu': {
                'ip': str(defaults.get('printer', {}).get('IP', '')),
                'serial': str(defaults.get('printer', {}).get('SERIAL', '')),
                'access_code': str(defaults.get('printer', {}).get('ACCESS_CODE', ''))
            },
            'roborock': {
                'email': str(defaults.get('roborock', {}).get('EMAIL', ''))
            },
            'lastfm': {
                'api_key': str(defaults.get('lastfm', {}).get('API_KEY', '')),
                'username': str(defaults.get('lastfm', {}).get('USERNAME', ''))
            },
            'openai': {
                'label': str(defaults.get('openai', {}).get('LABEL', 'OPENAI / CODEX')),
                'project_ids': list_value(defaults.get('openai', {}).get('PROJECT_IDS', [])),
                'model_filters': list_value(defaults.get('openai', {}).get('MODEL_FILTERS', []))
            }
        },
        'slots': slots
    }


def merge_config(raw_config, defaults):
    config = default_config(defaults)
    if not isinstance(raw_config, dict):
        return config

    location = raw_config.get('location', {})
    if isinstance(location, dict):
        config['location']['lat'] = float_value(location.get('lat'), config['location']['lat'])
        config['location']['lon'] = float_value(location.get('lon'), config['location']['lon'])

    widgets = raw_config.get('widgets', {})
    if isinstance(widgets, dict):
        for key in WIDGET_KEYS:
            if key in widgets:
                config['widgets'][key] = bool_value(widgets.get(key), config['widgets'][key])

    integrations = raw_config.get('integrations', {})
    if isinstance(integrations, dict):
        bambu = integrations.get('bambu', {})
        if isinstance(bambu, dict):
            config['integrations']['bambu']['ip'] = str(bambu.get('ip', config['integrations']['bambu']['ip'])).strip()
            config['integrations']['bambu']['serial'] = str(bambu.get('serial', config['integrations']['bambu']['serial'])).strip()
            config['integrations']['bambu']['access_code'] = str(bambu.get('access_code', config['integrations']['bambu']['access_code'])).strip()

        roborock = integrations.get('roborock', {})
        if isinstance(roborock, dict):
            config['integrations']['roborock']['email'] = str(roborock.get('email', config['integrations']['roborock']['email'])).strip()

        lastfm = integrations.get('lastfm', {})
        if isinstance(lastfm, dict):
            config['integrations']['lastfm']['api_key'] = str(lastfm.get('api_key', config['integrations']['lastfm']['api_key'])).strip()
            config['integrations']['lastfm']['username'] = str(lastfm.get('username', config['integrations']['lastfm']['username'])).strip()

        openai = integrations.get('openai', {})
        if isinstance(openai, dict):
            config['integrations']['openai']['label'] = str(openai.get('label', config['integrations']['openai']['label'])).strip() or 'OPENAI / CODEX'
            config['integrations']['openai']['project_ids'] = list_value(openai.get('project_ids', config['integrations']['openai']['project_ids']))
            model_filters = list_value(openai.get('model_filters', config['integrations']['openai']['model_filters']))
            if model_filters:
                config['integrations']['openai']['model_filters'] = model_filters

    slots = raw_config.get('slots', {})
    if isinstance(slots, dict):
        for slot_name in SLOT_KEYS:
            incoming = slots.get(slot_name)
            if not isinstance(incoming, dict):
                continue
            fallback_widgets = config['slots'].get(slot_name, {}).get('widgets', [])
            config['slots'].setdefault(slot_name, {})
            config['slots'][slot_name]['widgets'] = clean_slot_widgets(incoming.get('widgets'), fallback_widgets)
            config['slots'][slot_name]['rotate'] = bool_value(incoming.get('rotate'), config['slots'][slot_name].get('rotate', False))
            config['slots'][slot_name]['seconds'] = int_value(incoming.get('seconds'), config['slots'][slot_name].get('seconds', 300), minimum=30, maximum=86400)

    config['version'] = CONFIG_VERSION
    return config


def load_config(base_dir, defaults):
    path = config_path(base_dir)
    if not os.path.exists(path):
        return default_config(defaults)

    try:
        with open(path, 'r', encoding='utf-8') as config_file:
            raw_config = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return default_config(defaults)

    return merge_config(raw_config, defaults)


def save_config(base_dir, config, defaults):
    merged = merge_config(config, defaults)
    path = config_path(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.dashboard_config.', suffix='.json', dir=base_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as config_file:
            json.dump(merged, config_file, indent=2)
            config_file.write('\n')
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return merged


def config_for_public_response(base_dir, defaults):
    return copy.deepcopy(load_config(base_dir, defaults))
