#!/usr/bin/python3
# -*- coding:utf-8 -*-

DEFAULT_LOCATION_LAT = 44.8240855
DEFAULT_LOCATION_LON = 20.4934273

DEFAULT_WIDGETS = {
    'strava': False,
    'bambu': False,
    'roborock': False,
    'antigravity': False,
    'claude': False,
    'openai': False,
    'spotify': False
}

DEFAULT_WIDGET_SLOTS = {
    'left_top': {
        'widgets': ('strava', 'sysload'),
        'rotate': False,
        'seconds': 300
    },
    'left_middle': {
        'widgets': ('bambu', 'crypto'),
        'rotate': False,
        'seconds': 300
    },
    'left_bottom': {
        'widgets': ('roborock', 'antigravity', 'ping'),
        'rotate': False,
        'seconds': 300
    },
    'right_middle': {
        'widgets': ('ai_usage', 'spotify', 'time_progress'),
        'rotate': False,
        'seconds': 300
    }
}

DEFAULT_PRINTER_CONF = {
    'IP': '192.168....',
    'SERIAL': '',
    'ACCESS_CODE': ''
}

DEFAULT_ROBOROCK_CONF = {
    'EMAIL': 'email...'
}

DEFAULT_LASTFM_CONF = {
    'API_KEY': '',
    'USERNAME': ''
}

DEFAULT_OPENAI_CONF = {
    'LABEL': 'OPENAI / CODEX',
    'PROJECT_IDS': [],
    'MODEL_FILTERS': ['gpt-5-codex', 'gpt-5.3-codex', 'codex-mini-latest']
}


def dashboard_config_defaults():
    return {
        'location_lat': DEFAULT_LOCATION_LAT,
        'location_lon': DEFAULT_LOCATION_LON,
        'widgets': dict(DEFAULT_WIDGETS),
        'printer': dict(DEFAULT_PRINTER_CONF),
        'roborock': dict(DEFAULT_ROBOROCK_CONF),
        'lastfm': dict(DEFAULT_LASTFM_CONF),
        'openai': {
            'LABEL': DEFAULT_OPENAI_CONF['LABEL'],
            'PROJECT_IDS': list(DEFAULT_OPENAI_CONF['PROJECT_IDS']),
            'MODEL_FILTERS': list(DEFAULT_OPENAI_CONF['MODEL_FILTERS'])
        },
        'slots': {
            slot_name: {
                'widgets': tuple(slot['widgets']),
                'rotate': slot['rotate'],
                'seconds': slot['seconds']
            }
            for slot_name, slot in DEFAULT_WIDGET_SLOTS.items()
        }
    }
