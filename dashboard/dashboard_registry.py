#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""Shared dashboard registry metadata.

This file is intentionally data-heavy: the runtime, configurator, preview, and
docs should agree on widget ids, region names, compatibility, and default
refresh intervals.
"""

BASE_SCREEN = {'width': 1360, 'height': 480}

REGION_TYPES = {
    'wide_card': 'Wide card',
    'large_panel': 'Large panel',
    'status_tile': 'Status tile',
    'header': 'Header',
}

DEFAULT_REGIONS = {
    'left_top': {
        'label': 'Left top',
        'description': 'Upper-left rotating widget card.',
        'type': 'wide_card',
        'x': 20,
        'y': 20,
        'w': 413,
        'h': 125,
        'dynamic': True,
    },
    'left_middle': {
        'label': 'Left middle',
        'description': 'Center-left rotating widget card.',
        'type': 'wide_card',
        'x': 20,
        'y': 170,
        'w': 413,
        'h': 145,
        'dynamic': True,
    },
    'left_bottom': {
        'label': 'Left bottom',
        'description': 'Lower-left rotating widget card.',
        'type': 'wide_card',
        'x': 20,
        'y': 340,
        'w': 413,
        'h': 130,
        'dynamic': True,
    },
    'weather': {
        'label': 'Weather',
        'description': 'Fixed weather, AQI, wind, and forecast region.',
        'type': 'large_panel',
        'x': 473,
        'y': 10,
        'w': 413,
        'h': 460,
        'dynamic': False,
    },
    'clock': {
        'label': 'Clock',
        'description': 'Fixed time and date header.',
        'type': 'header',
        'x': 936,
        'y': 10,
        'w': 404,
        'h': 210,
        'dynamic': False,
    },
    'right_middle': {
        'label': 'Right middle',
        'description': 'Large right-side rotating widget card.',
        'type': 'wide_card',
        'x': 936,
        'y': 240,
        'w': 404,
        'h': 130,
        'dynamic': True,
    },
    'gmail': {
        'label': 'Gmail',
        'description': 'Fixed unread-mail summary.',
        'type': 'status_tile',
        'x': 936,
        'y': 400,
        'w': 404,
        'h': 70,
        'dynamic': False,
    },
}

WIDGET_REGISTRY = {
    'weather': {
        'label': 'Weather',
        'description': 'Weather, AQI, wind, and forecast panel.',
        'icon': 'wifi',
        'bitmap': 'icon_partly-cloudy-day',
        'supports': ('large_panel',),
        'refresh_seconds': 600,
        'data_key': 'weather',
    },
    'clock': {
        'label': 'Clock',
        'description': 'Time and date header.',
        'icon': 'clock',
        'bitmap': 'icon_timer',
        'supports': ('header',),
        'refresh_seconds': 60,
        'data_key': 'clock',
    },
    'gmail': {
        'label': 'Gmail',
        'description': 'Unread inbox summary.',
        'icon': 'mail',
        'bitmap': 'icon_mail',
        'supports': ('status_tile',),
        'refresh_seconds': 300,
        'data_key': 'gmail',
    },
    'strava': {
        'label': 'Strava',
        'description': 'Activity totals and recent training stats.',
        'icon': 'activity',
        'bitmap': 'icon_strava',
        'supports': ('wide_card',),
        'toggle': 'strava',
        'refresh_seconds': 900,
        'data_key': 'strava',
    },
    'sysload': {
        'label': 'System load',
        'description': 'CPU, memory, and system trend.',
        'icon': 'cpu',
        'bitmap': 'icon_cpu',
        'supports': ('wide_card', 'status_tile'),
        'refresh_seconds': 30,
        'data_key': 'sysload',
    },
    'bambu': {
        'label': 'Bambu Lab',
        'description': '3D printer status, progress, and layer details.',
        'icon': 'printer',
        'bitmap': 'icon_3d',
        'supports': ('wide_card',),
        'toggle': 'bambu',
        'refresh_seconds': 15,
        'data_key': 'printer',
    },
    'crypto': {
        'label': 'Crypto prices',
        'description': 'BTC and ETH prices with short trend bars.',
        'icon': 'coins',
        'bitmap': 'icon_btc',
        'supports': ('wide_card',),
        'refresh_seconds': 600,
        'data_key': 'crypto',
    },
    'roborock': {
        'label': 'Roborock',
        'description': 'Vacuum status, battery, and cleaning area.',
        'icon': 'vacuum',
        'bitmap': 'icon_roborock',
        'supports': ('wide_card',),
        'toggle': 'roborock',
        'refresh_seconds': 60,
        'data_key': 'roborock',
    },
    'antigravity': {
        'label': 'Antigravity',
        'description': 'Antigravity usage limits and reset time.',
        'icon': 'code',
        'bitmap': 'icon_cpu',
        'supports': ('wide_card',),
        'toggle': 'antigravity',
        'refresh_seconds': 60,
        'data_key': 'antigravity',
    },
    'ping': {
        'label': 'Network ping',
        'description': 'Internet latency and recent quality bars.',
        'icon': 'wifi',
        'bitmap': 'icon_wifi',
        'supports': ('wide_card', 'status_tile'),
        'refresh_seconds': 20,
        'data_key': 'ping',
    },
    'claude': {
        'label': 'Claude Code',
        'description': 'Enable Claude usage collection for the AI usage widget.',
        'icon': 'gauge',
        'bitmap': 'icon_server',
        'supports': (),
        'toggle': 'claude',
        'refresh_seconds': 600,
        'data_key': 'claude',
    },
    'openai': {
        'label': 'OpenAI / Codex',
        'description': 'Enable OpenAI/Codex usage collection for the AI usage widget.',
        'icon': 'terminal',
        'bitmap': 'icon_server',
        'supports': (),
        'toggle': 'openai',
        'refresh_seconds': 600,
        'data_key': 'openai',
    },
    'ai_usage': {
        'label': 'AI usage',
        'description': 'Claude and OpenAI/Codex usage windows.',
        'icon': 'gauge',
        'bitmap': 'icon_server',
        'supports': ('wide_card',),
        'refresh_seconds': 600,
        'data_key': 'ai_usage',
    },
    'spotify': {
        'label': 'Spotify',
        'description': 'Now playing data via Last.fm.',
        'icon': 'music',
        'bitmap': 'icon_spotify',
        'supports': ('wide_card', 'large_panel'),
        'toggle': 'spotify',
        'refresh_seconds': 20,
        'data_key': 'spotify',
    },
    'time_progress': {
        'label': 'Time progress',
        'description': 'Day, month, and year progress bars.',
        'icon': 'clock',
        'bitmap': 'icon_timer',
        'supports': ('wide_card', 'status_tile'),
        'refresh_seconds': 60,
        'data_key': 'time_progress',
    },
    'calendar': {
        'label': 'Calendar',
        'description': 'Upcoming events from a local or remote ICS calendar.',
        'icon': 'calendar',
        'bitmap': 'icon_calendar',
        'supports': ('wide_card', 'large_panel'),
        'toggle': 'calendar',
        'refresh_seconds': 900,
        'data_key': 'calendar',
    },
    'homeassistant': {
        'label': 'Home Assistant',
        'description': 'Selected Home Assistant entity states.',
        'icon': 'home',
        'bitmap': 'icon_home',
        'supports': ('wide_card', 'status_tile'),
        'toggle': 'homeassistant',
        'refresh_seconds': 60,
        'data_key': 'homeassistant',
    },
    'github': {
        'label': 'GitHub / DevOps',
        'description': 'Repository PR, issue, and workflow summary.',
        'icon': 'github',
        'bitmap': 'icon_deploy',
        'supports': ('wide_card',),
        'toggle': 'github',
        'refresh_seconds': 300,
        'data_key': 'github',
    },
}

DEFAULT_WIDGETS = {
    widget_id: False
    for widget_id, widget in WIDGET_REGISTRY.items()
    if widget.get('toggle') == widget_id
}

DEFAULT_REFRESH = {
    widget_id: int(widget.get('refresh_seconds', 300))
    for widget_id, widget in WIDGET_REGISTRY.items()
}

DEFAULT_PROFILE_SLOTS = {
    'left_top': {
        'widgets': ('strava', 'sysload', 'calendar'),
        'rotate': False,
        'seconds': 300,
    },
    'left_middle': {
        'widgets': ('bambu', 'crypto', 'homeassistant'),
        'rotate': False,
        'seconds': 300,
    },
    'left_bottom': {
        'widgets': ('roborock', 'antigravity', 'ping'),
        'rotate': False,
        'seconds': 300,
    },
    'right_middle': {
        'widgets': ('ai_usage', 'spotify', 'time_progress', 'github'),
        'rotate': False,
        'seconds': 300,
    },
}

DEFAULT_PROFILES = {
    'home': {
        'label': 'Home',
        'description': 'The default mixed home dashboard.',
        'slots': DEFAULT_PROFILE_SLOTS,
    },
    'work': {
        'label': 'Work / IT',
        'description': 'Service, deploy, calendar, and usage focused layout.',
        'slots': {
            'left_top': {'widgets': ('github', 'calendar'), 'rotate': False, 'seconds': 300},
            'left_middle': {'widgets': ('homeassistant', 'sysload'), 'rotate': False, 'seconds': 300},
            'left_bottom': {'widgets': ('ping', 'crypto'), 'rotate': False, 'seconds': 300},
            'right_middle': {'widgets': ('ai_usage', 'time_progress'), 'rotate': True, 'seconds': 300},
        },
    },
    'focus': {
        'label': 'Focus',
        'description': 'Low-noise layout for time, calendar, and essentials.',
        'slots': {
            'left_top': {'widgets': ('calendar', 'time_progress'), 'rotate': False, 'seconds': 300},
            'left_middle': {'widgets': ('homeassistant', 'sysload'), 'rotate': False, 'seconds': 300},
            'left_bottom': {'widgets': ('ping', 'sysload'), 'rotate': False, 'seconds': 300},
            'right_middle': {'widgets': ('spotify', 'ai_usage'), 'rotate': True, 'seconds': 600},
        },
    },
}


def widget_ids():
    return tuple(WIDGET_REGISTRY.keys())


def dynamic_region_ids():
    return tuple(region_id for region_id, region in DEFAULT_REGIONS.items() if region.get('dynamic'))


def widget_supports_region(widget_id, region_id, regions=None):
    widget = WIDGET_REGISTRY.get(widget_id)
    region = (regions or DEFAULT_REGIONS).get(region_id)
    if not widget or not region:
        return False
    return region.get('type') in widget.get('supports', ())


def clean_widgets_for_region(region_id, widgets, fallback=(), regions=None):
    cleaned = []
    for widget_id in widgets or ():
        widget_id = str(widget_id).strip()
        if widget_id and widget_id not in cleaned and widget_supports_region(widget_id, region_id, regions=regions):
            cleaned.append(widget_id)
    if cleaned:
        return cleaned

    fallback_cleaned = []
    for widget_id in fallback or ():
        widget_id = str(widget_id).strip()
        if widget_id and widget_id not in fallback_cleaned and widget_supports_region(widget_id, region_id, regions=regions):
            fallback_cleaned.append(widget_id)
    return fallback_cleaned


def scaled_region_rect(region, width, height):
    sx = float(width) / float(BASE_SCREEN['width'])
    sy = float(height) / float(BASE_SCREEN['height'])
    x = int(round(region['x'] * sx))
    y = int(round(region['y'] * sy))
    w = int(round(region['w'] * sx))
    h = int(round(region['h'] * sy))
    return (x, y, x + w, y + h)


def runtime_region_rects(width, height, regions=None):
    return {
        region_id: scaled_region_rect(region, width, height)
        for region_id, region in (regions or DEFAULT_REGIONS).items()
    }


def metadata():
    return {
        'baseScreen': dict(BASE_SCREEN),
        'regionTypes': dict(REGION_TYPES),
        'regions': [dict({'id': region_id}, **region) for region_id, region in DEFAULT_REGIONS.items()],
        'dynamicRegions': [
            dict({'id': region_id}, **region)
            for region_id, region in DEFAULT_REGIONS.items()
            if region.get('dynamic')
        ],
        'widgets': [dict({'id': widget_id}, **widget) for widget_id, widget in WIDGET_REGISTRY.items()],
    }
