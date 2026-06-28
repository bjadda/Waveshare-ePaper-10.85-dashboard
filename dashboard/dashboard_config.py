#!/usr/bin/python3
# -*- coding:utf-8 -*-
import copy
import json
import os
import re
import tempfile

from dashboard import dashboard_registry

CONFIG_FILENAME = 'dashboard_config.json'
CONFIG_VERSION = 2

PROFILE_ID_RE = re.compile(r'[^a-z0-9_-]+')

WIDGET_KEYS = tuple(dashboard_registry.DEFAULT_WIDGETS.keys())
SLOT_WIDGETS = dashboard_registry.widget_ids()
SLOT_KEYS = dashboard_registry.dynamic_region_ids()


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


def entity_list_value(value):
    if isinstance(value, str):
        return [{'entity_id': item} for item in list_value(value)]
    if not isinstance(value, (list, tuple)):
        return []

    entities = []
    for item in value:
        if isinstance(item, str):
            entity_id = item.strip()
            if entity_id:
                entities.append({'entity_id': entity_id, 'label': entity_id, 'unit': ''})
            continue
        if isinstance(item, dict):
            entity_id = str(item.get('entity_id') or item.get('id') or '').strip()
            topic = str(item.get('topic') or '').strip()
            if not entity_id and not topic:
                continue
            entities.append({
                'entity_id': entity_id,
                'topic': topic,
                'label': str(item.get('label') or entity_id or topic).strip(),
                'unit': str(item.get('unit') or '').strip(),
                'field': str(item.get('field') or 'state').strip() or 'state'
            })
    return entities


def profile_id_value(value, default='home'):
    cleaned = PROFILE_ID_RE.sub('-', str(value or '').strip().lower()).strip('-_')
    return cleaned or default


def clean_slot_widgets(value, fallback, region_id=None, regions=None):
    requested = list_value(value)
    if region_id:
        return dashboard_registry.clean_widgets_for_region(
            region_id, requested, fallback=fallback, regions=regions
        )

    cleaned = []
    for widget_id in requested:
        if widget_id in SLOT_WIDGETS and widget_id not in cleaned:
            cleaned.append(widget_id)
    if cleaned:
        return cleaned
    return list(fallback)


def clean_slot(region_id, incoming, fallback, regions=None):
    incoming = incoming if isinstance(incoming, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}
    fallback_widgets = fallback.get('widgets', [])
    return {
        'widgets': clean_slot_widgets(
            incoming.get('widgets'), fallback_widgets, region_id=region_id, regions=regions
        ),
        'rotate': bool_value(incoming.get('rotate'), bool_value(fallback.get('rotate'), False)),
        'seconds': int_value(incoming.get('seconds'), fallback.get('seconds', 300), minimum=30, maximum=86400)
    }


def normalize_regions(raw_regions, defaults):
    regions = {region_id: dict(region) for region_id, region in defaults.items()}
    if not isinstance(raw_regions, dict):
        return regions

    for region_id, incoming in raw_regions.items():
        if region_id not in regions or not isinstance(incoming, dict):
            continue
        region = regions[region_id]
        for key in ('label', 'description', 'type'):
            if key in incoming:
                region[key] = str(incoming.get(key) or region.get(key, '')).strip() or region.get(key, '')
        for key in ('x', 'y', 'w', 'h'):
            if key in incoming:
                region[key] = int_value(incoming.get(key), region[key], minimum=0)
        if 'dynamic' in incoming:
            region['dynamic'] = bool_value(incoming.get('dynamic'), region.get('dynamic', False))
    return regions


def normalize_profile(profile_id, raw_profile, fallback_slots, regions):
    raw_profile = raw_profile if isinstance(raw_profile, dict) else {}
    slots = {}
    raw_slots = raw_profile.get('slots', {})
    if not isinstance(raw_slots, dict):
        raw_slots = {}

    for slot_name in SLOT_KEYS:
        slots[slot_name] = clean_slot(
            slot_name,
            raw_slots.get(slot_name),
            fallback_slots.get(slot_name, {}),
            regions=regions
        )

    return {
        'label': str(raw_profile.get('label') or profile_id.replace('-', ' ').title()).strip(),
        'description': str(raw_profile.get('description') or '').strip(),
        'slots': slots
    }


def normalize_profiles(raw_profiles, fallback_profiles, active_profile, regions):
    profiles = {}
    for profile_id, profile in fallback_profiles.items():
        profile_id = profile_id_value(profile_id)
        profiles[profile_id] = normalize_profile(
            profile_id,
            profile,
            profile.get('slots', {}),
            regions
        )

    if isinstance(raw_profiles, dict):
        for raw_id, raw_profile in raw_profiles.items():
            profile_id = profile_id_value(raw_id)
            fallback = profiles.get(profile_id, profiles.get('home', {}))
            profiles[profile_id] = normalize_profile(
                profile_id,
                raw_profile,
                fallback.get('slots', {}),
                regions
            )

    if active_profile not in profiles:
        active_profile = 'home' if 'home' in profiles else next(iter(profiles), 'home')
    return profiles, active_profile


def default_config(defaults):
    regions = normalize_regions({}, defaults.get('regions', dashboard_registry.DEFAULT_REGIONS))
    active_profile = profile_id_value(defaults.get('active_profile', 'home'))
    profiles, active_profile = normalize_profiles(
        defaults.get('profiles', {}),
        defaults.get('profiles', {}),
        active_profile,
        regions
    )
    slots = copy.deepcopy(profiles[active_profile]['slots'])

    return {
        'version': CONFIG_VERSION,
        'active_profile': active_profile,
        'location': {
            'lat': float_value(defaults.get('location_lat'), 44.8240855),
            'lon': float_value(defaults.get('location_lon'), 20.4934273)
        },
        'widgets': {
            key: bool_value(defaults.get('widgets', {}).get(key), False)
            for key in WIDGET_KEYS
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
            },
            'calendar': {
                'label': str(defaults.get('calendar', {}).get('LABEL', 'CALENDAR')),
                'urls': list_value(defaults.get('calendar', {}).get('URLS', [])),
                'path': str(defaults.get('calendar', {}).get('ICS_PATH', '')).strip(),
                'lookahead_days': int_value(defaults.get('calendar', {}).get('LOOKAHEAD_DAYS', 14), 14, minimum=1, maximum=365),
                'max_events': int_value(defaults.get('calendar', {}).get('MAX_EVENTS', 3), 3, minimum=1, maximum=10)
            },
            'homeassistant': {
                'base_url': str(defaults.get('homeassistant', {}).get('BASE_URL', '')).strip(),
                'token': str(defaults.get('homeassistant', {}).get('TOKEN', '')).strip(),
                'entities': entity_list_value(defaults.get('homeassistant', {}).get('ENTITIES', []))
            },
            'github': {
                'label': str(defaults.get('github', {}).get('LABEL', 'GITHUB / DEVOPS')),
                'token': str(defaults.get('github', {}).get('TOKEN', '')).strip(),
                'repositories': list_value(defaults.get('github', {}).get('REPOSITORIES', []))
            }
        },
        'regions': regions,
        'profiles': profiles,
        'slots': slots,
        'refresh': {
            widget_id: int_value(defaults.get('refresh', {}).get(widget_id), refresh, minimum=5, maximum=86400)
            for widget_id, refresh in dashboard_registry.DEFAULT_REFRESH.items()
        }
    }


def merge_config(raw_config, defaults):
    config = default_config(defaults)
    if not isinstance(raw_config, dict):
        return config

    regions = normalize_regions(raw_config.get('regions'), config['regions'])
    config['regions'] = regions

    active_profile = profile_id_value(raw_config.get('active_profile'), config['active_profile'])

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

        calendar = integrations.get('calendar', {})
        if isinstance(calendar, dict):
            urls = calendar.get('urls', calendar.get('ics_urls', calendar.get('url', [])))
            config['integrations']['calendar']['label'] = str(calendar.get('label', config['integrations']['calendar']['label'])).strip() or 'CALENDAR'
            config['integrations']['calendar']['urls'] = list_value(urls)
            config['integrations']['calendar']['path'] = str(calendar.get('path', calendar.get('ics_path', config['integrations']['calendar']['path']))).strip()
            config['integrations']['calendar']['lookahead_days'] = int_value(calendar.get('lookahead_days'), config['integrations']['calendar']['lookahead_days'], minimum=1, maximum=365)
            config['integrations']['calendar']['max_events'] = int_value(calendar.get('max_events'), config['integrations']['calendar']['max_events'], minimum=1, maximum=10)

        homeassistant = integrations.get('homeassistant', {})
        if isinstance(homeassistant, dict):
            config['integrations']['homeassistant']['base_url'] = str(homeassistant.get('base_url', config['integrations']['homeassistant']['base_url'])).strip().rstrip('/')
            config['integrations']['homeassistant']['token'] = str(homeassistant.get('token', config['integrations']['homeassistant']['token'])).strip()
            config['integrations']['homeassistant']['entities'] = entity_list_value(homeassistant.get('entities', config['integrations']['homeassistant']['entities']))

        github = integrations.get('github', integrations.get('devops', {}))
        if isinstance(github, dict):
            config['integrations']['github']['label'] = str(github.get('label', config['integrations']['github']['label'])).strip() or 'GITHUB / DEVOPS'
            config['integrations']['github']['token'] = str(github.get('token', config['integrations']['github']['token'])).strip()
            config['integrations']['github']['repositories'] = list_value(github.get('repositories', github.get('repos', config['integrations']['github']['repositories'])))

    profiles, active_profile = normalize_profiles(
        raw_config.get('profiles'),
        config['profiles'],
        active_profile,
        regions
    )
    config['profiles'] = profiles
    config['active_profile'] = active_profile

    # Backward compatibility: top-level slots are treated as the active profile mirror.
    slots = raw_config.get('slots', {})
    if isinstance(slots, dict):
        active_slots = copy.deepcopy(config['profiles'][active_profile]['slots'])
        for slot_name in SLOT_KEYS:
            incoming = slots.get(slot_name)
            if not isinstance(incoming, dict):
                continue
            active_slots[slot_name] = clean_slot(slot_name, incoming, active_slots.get(slot_name, {}), regions=regions)
        config['profiles'][active_profile]['slots'] = active_slots

    config['slots'] = copy.deepcopy(config['profiles'][active_profile]['slots'])

    refresh = raw_config.get('refresh', raw_config.get('widget_refresh', {}))
    if isinstance(refresh, dict):
        for widget_id in dashboard_registry.DEFAULT_REFRESH:
            if widget_id in refresh:
                config['refresh'][widget_id] = int_value(refresh.get(widget_id), config['refresh'][widget_id], minimum=5, maximum=86400)

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
