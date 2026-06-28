#!/usr/bin/python3
# -*- coding:utf-8 -*-

from dashboard import dashboard_registry

DEFAULT_LOCATION_LAT = 44.8240855
DEFAULT_LOCATION_LON = 20.4934273

DEFAULT_WIDGETS = dict(dashboard_registry.DEFAULT_WIDGETS)
DEFAULT_WIDGET_SLOTS = dashboard_registry.DEFAULT_PROFILE_SLOTS
DEFAULT_PROFILES = dashboard_registry.DEFAULT_PROFILES
DEFAULT_REGIONS = dashboard_registry.DEFAULT_REGIONS
DEFAULT_REFRESH = dashboard_registry.DEFAULT_REFRESH

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

DEFAULT_CALENDAR_CONF = {
    'URLS': [],
    'ICS_PATH': '',
    'LOOKAHEAD_DAYS': 14,
    'MAX_EVENTS': 3
}

DEFAULT_HOMEASSISTANT_CONF = {
    'BASE_URL': '',
    'TOKEN': '',
    'ENTITIES': []
}

DEFAULT_GITHUB_CONF = {
    'TOKEN': '',
    'REPOSITORIES': [],
    'LABEL': 'GITHUB / DEVOPS'
}


def _copy_slots(slots):
    return {
        slot_name: {
            'widgets': tuple(slot.get('widgets', ())),
            'rotate': bool(slot.get('rotate', False)),
            'seconds': int(slot.get('seconds', 300))
        }
        for slot_name, slot in slots.items()
    }


def _copy_profiles(profiles):
    return {
        profile_id: {
            'label': str(profile.get('label', profile_id.title())),
            'description': str(profile.get('description', '')),
            'slots': _copy_slots(profile.get('slots', {}))
        }
        for profile_id, profile in profiles.items()
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
        'calendar': dict(DEFAULT_CALENDAR_CONF),
        'homeassistant': {
            'BASE_URL': DEFAULT_HOMEASSISTANT_CONF['BASE_URL'],
            'TOKEN': DEFAULT_HOMEASSISTANT_CONF['TOKEN'],
            'ENTITIES': list(DEFAULT_HOMEASSISTANT_CONF['ENTITIES'])
        },
        'github': {
            'TOKEN': DEFAULT_GITHUB_CONF['TOKEN'],
            'REPOSITORIES': list(DEFAULT_GITHUB_CONF['REPOSITORIES']),
            'LABEL': DEFAULT_GITHUB_CONF['LABEL']
        },
        'slots': _copy_slots(DEFAULT_WIDGET_SLOTS),
        'active_profile': 'home',
        'profiles': _copy_profiles(DEFAULT_PROFILES),
        'regions': copy_regions(DEFAULT_REGIONS),
        'refresh': dict(DEFAULT_REFRESH)
    }


def copy_regions(regions):
    return {
        region_id: dict(region)
        for region_id, region in regions.items()
    }
