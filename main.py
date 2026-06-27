#!/usr/bin/python3
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import threading
import requests
import io
import gc
import socket
import resource
import signal
import json
import asyncio
import pickle
import subprocess
import urllib.parse
from collections import deque
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import dashboard_widgets
from logging.handlers import RotatingFileHandler

# --- GMAIL IMPORTS ---
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- SYSTEM LIMITS ---
try:
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))
except Exception as e:
    print(f"Failed to set rlimit: {e}")

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
LIB_DIR = os.path.join(BASE_DIR, 'lib')
FONT_DIR = os.path.join(BASE_DIR, 'fnt')
ICON_DIR = os.path.join(BASE_DIR, 'icons')
LOG_FILE = os.path.join(BASE_DIR, 'dashboard.log')

# ######################
# --- WIDGET TOGGLES ---
# ######################
ENABLE_STRAVA = False
ENABLE_BAMBU = False
ENABLE_ROBOROCK = False
ENABLE_ANTIGRAVITY = False
ENABLE_CLAUDE = False
ENABLE_OPENAI = False
ENABLE_SPOTIFY = False

# --- DYNAMIC WIDGET SLOTS ---
# Each slot keeps today's first-available fallback behavior by default.
# Set rotate=True per slot to cycle through every currently available widget.
WIDGET_SLOTS = {
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


def widget_slot_can_show(widget_id):
    for slot in WIDGET_SLOTS.values():
        widgets = slot.get('widgets', ())
        if widget_id in widgets and (slot.get('rotate', False) or widgets[0] == widget_id):
            return True
    return False
# --- API ENDPOINTS ---
API_ENDPOINTS = {
    'weather': 'https://api.open-meteo.com/v1/forecast',
    'aqi': 'https://air-quality-api.open-meteo.com/v1/air-quality',
    'strava_token': 'https://www.strava.com/oauth/token',
    'strava_auth': 'https://www.strava.com/oauth/authorize',
    'strava_activities': 'https://www.strava.com/api/v3/athlete/activities',
    'btc': 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart',
    'eth': 'https://api.coingecko.com/api/v3/coins/ethereum/market_chart',
    'lastfm': 'http://ws.audioscrobbler.com/2.0/'
}

# --- CONFIGURATION ---
# Change to your GEO location
LOCATION_LAT = 44.8240855
LOCATION_LON = 20.4934273

PRINTER_CONF = {
    'IP': '192.168....',
    'SERIAL': '',
    'ACCESS_CODE': ''
}

ROBOROCK_CONF = {
    'EMAIL': 'email...'
}

LASTFM_CONF = {
    'API_KEY': '',
    'USERNAME': ''
}

STRAVA_CONF = {
    'TOKEN_FILE': os.path.join(BASE_DIR, 'strava_token.json')
}

OPENAI_CONF = {
    'LABEL': 'OPENAI / CODEX',
    'PROJECT_IDS': [],
    'MODEL_FILTERS': ['gpt-5-codex', 'gpt-5.3-codex', 'codex-mini-latest']
}

# --- FILES & SCOPES ---
GMAIL_TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
ROBOROCK_TOKEN_FILE = os.path.join(BASE_DIR, 'roborock_session.pkl')
ROBOROCK_STATS_FILE = os.path.join(BASE_DIR, 'roborock_stats.json')
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

if os.path.exists(LIB_DIR):
    sys.path.append(LIB_DIR)

try:
    from waveshare_epd import epd10in85
    import bambulabs_api as bl
    from roborock.web_api import RoborockApiClient
    from roborock.devices.device_manager import create_device_manager, UserParams
except ImportError:
    pass

# --- LOGGING ---
logging.getLogger("bambulabs_api").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("roborock").setLevel(logging.CRITICAL)
logging.getLogger("aiomqtt").setLevel(logging.CRITICAL)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1 * 1024 * 1024, backupCount=1)
file_handler.setFormatter(formatter)

logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(file_handler)

icon_cache = {}
global_printer = None


class HardwareTimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise HardwareTimeoutError("Hardware Busy-Wait Timeout")


# --- ROBUST NETWORK MANAGER ---
class NetworkManager:
    def __init__(self):
        self.session = None
        self.create_session()

    def create_session(self):
        if self.session:
            try:
                self.session.close()
            except:
                pass
        gc.collect()
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5, pool_maxsize=10,
            max_retries=requests.adapters.Retry(total=1, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def get_json(self, url, headers=None, data=None, method='GET', timeout=10):
        try:
            if self.session is None: self.create_session()
            if method == 'POST':
                resp = self.session.post(url, headers=headers, data=data, timeout=timeout)
            else:
                resp = self.session.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.create_session()
            return None

    def get_image(self, url, timeout=15):
        try:
            if self.session is None: self.create_session()
            resp = self.session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            self.create_session()
            return None


net = NetworkManager()


# --- GLOBAL DATA STORE ---
class DataStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.weather = {}
        self.aqi = 0
        self.strava = {
            'rides': 0, 'total_distance': 0,
            'rides_curr': 0, 'distance_curr': 0,
            'rides_prev': 0, 'distance_prev': 0,
            'bike_total': 0, 'hike_total': 0
        }
        self.printer = {'status': 'OFFLINE'}
        self.gmail_unread = 0
        self.spotify = {'status': 'PAUSED', 'text': '', 'cover': None}
        self.claude = {'error': False, 'five_hour': {}, 'seven_day': {}}
        self.openai = {'error': False, 'window_24h': {}, 'window_7d': {}, 'models': []}
        self.antigravity = {'error': False, 'models': []}
        self.roborock = {
            'status': 'OFFLINE', 'battery': 0, 'is_cleaning': False,
            'current_area': 0.0, 'ref_area': 0.0, 'pct': 0.0, 'last_date': '-'
        }
        self.sysload = {'cpu': 0, 'ram_free': 0, 'history': deque(maxlen=30)}
        self.crypto = {'btc': 0, 'eth': 0, 'btc_hist': [], 'eth_hist': []}
        self.ping = {'current': 0, 'history': deque(maxlen=50)}

        self.last_update = {
            'weather': 0, 'strava': 0, 'printer': 0, 'gmail': 0,
            'spotify': 0, 'crypto': 0, 'sysload': 0, 'ping': 0,
            'claude': 0, 'openai': 0, 'antigravity': 0
        }


data_store = DataStore()


# --- HELPERS ---
def ping_printer(ip):
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except:
        return False


def get_cached_icon(name, size, is_white=False):
    key = f"{name}_{size[0]}x{size[1]}_{'white' if is_white else 'black'}"
    if key not in icon_cache:
        path = os.path.join(ICON_DIR, f"{name}.bmp")
        if os.path.exists(path):
            try:
                with Image.open(path) as f_img:
                    img = f_img.convert("L").resize(size)
                    img = ImageOps.invert(img)
                    icon_cache[key] = img.convert("1")
            except:
                return None
        else:
            icon_cache[key] = None
    return icon_cache.get(key)


def time_until(iso_str):
    if not iso_str: return "N/A"
    try:
        # Handling the explicit +00:00 timezone format
        target = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = target - now
        if diff.total_seconds() < 0: return "Resetting..."
        hours, rem = divmod(diff.total_seconds(), 3600)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{int(days)}d {int(hours)}h"
        else:
            minutes = rem // 60
            return f"{int(hours)}h {int(minutes)}m"
    except Exception:
        return "N/A"


def compact_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "0"

    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        scaled = f"{number / 1_000_000_000:.1f}".rstrip('0').rstrip('.')
        return f"{scaled}B"
    if abs_number >= 1_000_000:
        scaled = f"{number / 1_000_000:.1f}".rstrip('0').rstrip('.')
        return f"{scaled}M"
    if abs_number >= 1_000:
        scaled = f"{number / 1_000:.1f}".rstrip('0').rstrip('.')
        return f"{scaled}K"
    return str(int(number))


def format_model_label(model_name):
    if not model_name:
        return "Unknown"
    known_labels = {
        'gpt-5-codex': 'GPT-5 Codex',
        'gpt-5.3-codex': 'GPT-5.3 Codex',
        'codex-mini-latest': 'Codex Mini'
    }
    return known_labels.get(model_name, model_name.replace('-', ' ')[:20])


def format_window_label(seconds):
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "Window"
    if seconds >= 3600:
        hours = seconds // 3600
        return f"{hours}h Window"
    if seconds >= 60:
        minutes = seconds // 60
        return f"{minutes}m Window"
    return f"{seconds}s Window"


# --- AUTH & FETCH THREADS ---

def auth_claude():
    global ENABLE_CLAUDE
    if not ENABLE_CLAUDE: return
    try:
        import claude
        success = claude.interactive_auth()
        if not success:
            ENABLE_CLAUDE = False
            print("Claude widget is disabled.")
    except ImportError:
        print("claude.py not found. Claude widget disabled.")
        ENABLE_CLAUDE = False


def auth_antigravity():
    global ENABLE_ANTIGRAVITY
    if not ENABLE_ANTIGRAVITY: return
    try:
        import antigravity
        success = antigravity.interactive_auth()
        if not success:
            ENABLE_ANTIGRAVITY = False
            print("Antigravity widget is disabled.")
    except ImportError:
        print("antigravity.py not found. Antigravity widget disabled.")
        ENABLE_ANTIGRAVITY = False


def auth_openai():
    global ENABLE_OPENAI
    if not ENABLE_OPENAI: return
    try:
        import openai_codex
        success = openai_codex.interactive_auth({
            'label': OPENAI_CONF.get('LABEL', 'OPENAI / CODEX'),
            'project_ids': OPENAI_CONF.get('PROJECT_IDS', []),
            'model_filters': OPENAI_CONF.get('MODEL_FILTERS', [])
        })
        if not success:
            ENABLE_OPENAI = False
            print("OpenAI / Codex widget is disabled.")
    except ImportError:
        print("openai_codex.py not found. OpenAI / Codex widget disabled.")
        ENABLE_OPENAI = False


def auth_strava():
    global ENABLE_STRAVA
    if not ENABLE_STRAVA: return

    if os.path.exists(STRAVA_CONF['TOKEN_FILE']):
        return

    print("\n--- STRAVA CONFIGURATION REQUIRED ---")
    c_id = input("Enter Strava Client ID (or press Enter to disable): ").strip()
    if not c_id:
        print("Strava is disabled. Fallback widget (System Load) will be used.\n")
        ENABLE_STRAVA = False
        return

    c_secret = input("Enter Strava Client Secret: ").strip()

    auth_url = (
        f"{API_ENDPOINTS['strava_auth']}?"
        f"client_id={c_id}&"
        f"response_type=code&"
        f"redirect_uri=http://localhost&"
        f"approval_prompt=force&"
        f"scope=activity:read_all"
    )

    print("\n[!] To get a token with the correct permissions, open this link in your browser:\n")
    print(f"--> {auth_url} <--\n")
    print("Click 'Authorize'. You will be redirected to an empty/error page (localhost).")
    print("Look at the address bar. Copy the 'code' parameter.")

    code_input = input("Enter the 'code' from the URL (or paste the full URL): ").strip()

    if not code_input:
        print("Authorization cancelled. Strava is disabled.\n")
        ENABLE_STRAVA = False
        return

    if 'code=' in code_input:
        try:
            parsed = urllib.parse.urlparse(code_input)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get('code', [code_input])[0]
        except:
            code = code_input.split('code=')[1].split('&')[0]
    else:
        code = code_input

    print("Fetching Access Token...")
    data = {'client_id': c_id, 'client_secret': c_secret, 'code': code, 'grant_type': 'authorization_code'}

    try:
        resp = requests.post(API_ENDPOINTS['strava_token'], data=data)
        resp.raise_for_status()
        token_data = resp.json()
        token_data['client_id'] = c_id
        token_data['client_secret'] = c_secret

        with open(STRAVA_CONF['TOKEN_FILE'], 'w') as f:
            json.dump(token_data, f, indent=4)
        print("Strava Authorization Successful!\n")
    except Exception as e:
        print(f"Failed to fetch Strava tokens: {e}")
        ENABLE_STRAVA = False


def fetch_strava_data():
    if not os.path.exists(STRAVA_CONF['TOKEN_FILE']): return None
    with open(STRAVA_CONF['TOKEN_FILE'], 'r') as f:
        token_data = json.load(f)

    c_id = token_data.get('client_id')
    c_secret = token_data.get('client_secret')

    if time.time() > token_data.get('expires_at', 0):
        data = {'client_id': c_id, 'client_secret': c_secret, 'grant_type': 'refresh_token',
                'refresh_token': token_data.get('refresh_token')}
        new_token = net.get_json(API_ENDPOINTS['strava_token'], data=data, method='POST')
        if new_token and 'access_token' in new_token:
            new_token['client_id'] = c_id
            new_token['client_secret'] = c_secret
            token_data = new_token
            with open(STRAVA_CONF['TOKEN_FILE'], 'w') as f:
                json.dump(token_data, f, indent=4)
        else:
            return None

    access_token = token_data['access_token']

    now_year = datetime.now().year
    start_curr_ts = datetime(now_year, 1, 1).timestamp()
    start_prev_ts = datetime(now_year - 1, 1, 1).timestamp()
    end_prev_ts = datetime(now_year - 1, 12, 31, 23, 59, 59).timestamp()

    page = 1
    total_rides, total_dist = 0, 0
    rides_curr, dist_curr = 0, 0
    rides_prev, dist_prev = 0, 0
    bike_total, hike_total = 0, 0

    headers = {"Authorization": f"Bearer {access_token}"}

    while True:
        url = f"{API_ENDPOINTS['strava_activities']}?page={page}&per_page=100"
        activities = net.get_json(url, headers=headers)
        if not activities: break

        for act in activities:
            t = act.get('type')
            d = act.get('distance', 0)
            act_time = datetime.strptime(act['start_date'], "%Y-%m-%dT%H:%M:%SZ").timestamp()

            if t in ['Ride', 'VirtualRide', 'EBikeRide', 'GravelRide', 'MountainBikeRide']:
                total_rides += 1
                total_dist += d
                bike_total += d
                if act_time >= start_curr_ts:
                    rides_curr += 1
                    dist_curr += d
                elif start_prev_ts <= act_time <= end_prev_ts:
                    rides_prev += 1
                    dist_prev += d
            elif t in ['Hike', 'Walk']:
                hike_total += d

        if len(activities) < 100: break
        page += 1

    return {
        "rides": total_rides,
        "total_distance": round(total_dist / 1000, 1),
        "rides_curr": rides_curr,
        "distance_curr": round(dist_curr / 1000, 1),
        "rides_prev": rides_prev,
        "distance_prev": round(dist_prev / 1000, 1),
        "bike_total": round(bike_total / 1000, 1),
        "hike_total": round(hike_total / 1000, 1)
    }


def auth_roborock(email):
    global ENABLE_ROBOROCK
    if not ENABLE_ROBOROCK: return None

    if os.path.exists(ROBOROCK_TOKEN_FILE):
        try:
            with open(ROBOROCK_TOKEN_FILE, "rb") as f:
                return pickle.load(f)
        except:
            pass

    print("\n--- ROBOROCK AUTHORIZATION REQUIRED ---")

    async def _do_auth():
        web_api = RoborockApiClient(username=email)
        await web_api.request_code()
        code = input(f"Enter 6-digit Roborock auth code sent to {email} (or press Enter to disable): ").strip()
        if not code: return None
        user_data = await web_api.code_login(code)
        with open(ROBOROCK_TOKEN_FILE, "wb") as f: pickle.dump(user_data, f)
        print("Roborock Authorization Successful!\n")
        return user_data

    if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        user_data = asyncio.run(_do_auth())
        if not user_data:
            print("Roborock is disabled. Fallback widget (Ping) will be used.\n")
            ENABLE_ROBOROCK = False
        return user_data
    except Exception as e:
        print(f"Failed to auth Roborock: {e}")
        ENABLE_ROBOROCK = False
        return None


def roborock_update_thread(user_data, email):
    if not ENABLE_ROBOROCK or not user_data: return

    async def _loop():
        ref_area, last_date = 0.0, "-"
        if os.path.exists(ROBOROCK_STATS_FILE):
            try:
                with open(ROBOROCK_STATS_FILE, "r") as f:
                    stats = json.load(f)
                    ref_area, last_date = stats.get("ref_area", 0.0), stats.get("last_date", "-")
            except:
                pass

        user_params = UserParams(username=email, user_data=user_data)
        device_manager = await create_device_manager(user_params)

        short_states = {
            5: "Clean", 6: "Return", 8: "Charge", 10: "Pause",
            17: "Spot", 18: "Room", 22: "Empty", 23: "Wash",
            26: "ToWash", 29: "Map"
        }

        while True:
            try:
                devices = await device_manager.get_devices()
                if devices and devices[0].v1_properties:
                    device = devices[0]
                    status_trait = device.v1_properties.status
                    await status_trait.refresh()
                    current_area = (status_trait.clean_area / 1000000) if status_trait.clean_area else 0

                    is_cleaning = status_trait.state in [5, 6, 10, 17, 18, 22, 23, 26, 29]
                    status_str = short_states.get(status_trait.state, f"S:{status_trait.state}")

                    if not is_cleaning and current_area > 0 and current_area != ref_area:
                        ref_area = current_area
                        last_date = datetime.now().strftime("%d %b %H:%M")
                        with open(ROBOROCK_STATS_FILE, "w") as f: json.dump(
                            {"ref_area": ref_area, "last_date": last_date}, f)

                    pct = (current_area / ref_area) * 100 if is_cleaning and ref_area > 0 else 0.0

                    with data_store.lock:
                        data_store.roborock = {
                            'status': status_str, 'battery': status_trait.battery,
                            'is_cleaning': is_cleaning, 'current_area': current_area,
                            'ref_area': ref_area, 'pct': pct, 'last_date': last_date
                        }
            except Exception as e:
                logging.error(f"Roborock error: {e}")
            await asyncio.sleep(60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_loop())


def update_data_thread():
    global global_printer

    if ENABLE_BAMBU:
        try:
            global_printer = bl.Printer(PRINTER_CONF['IP'], PRINTER_CONF['ACCESS_CODE'], PRINTER_CONF['SERIAL'])
        except Exception as e:
            logging.error(f"Bambu init error: {e}")
            global_printer = None

    is_connected = False

    while True:
        now = time.time()

        if now - data_store.last_update['weather'] > 600:
            weather_url = f"{API_ENDPOINTS['weather']}?latitude={LOCATION_LAT}&longitude={LOCATION_LON}&current=temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,weather_code,is_day,uv_index&hourly=temperature_2m,precipitation_probability,weather_code,cloud_cover&timezone=auto&forecast_days=2"
            aqi_url = f"{API_ENDPOINTS['aqi']}?latitude={LOCATION_LAT}&longitude={LOCATION_LON}&current=european_aqi&timezone=auto"
            w_data = net.get_json(weather_url)
            a_data = net.get_json(aqi_url)
            with data_store.lock:
                if w_data: data_store.weather = w_data
                if a_data and 'current' in a_data: data_store.aqi = a_data['current'].get('european_aqi', 0)
            data_store.last_update['weather'] = now

        if ENABLE_STRAVA:
            if now - data_store.last_update['strava'] > 900:
                s_data = fetch_strava_data()
                if s_data:
                    with data_store.lock: data_store.strava = s_data
                data_store.last_update['strava'] = now
        if (not ENABLE_STRAVA) or widget_slot_can_show('sysload'):
            if now - data_store.last_update['sysload'] > 30:
                try:
                    with open('/proc/loadavg', 'r') as f:
                        cpu = float(f.read().split()[0]) * 10
                    with open('/proc/meminfo', 'r') as f:
                        lines = f.readlines()
                        free = int(lines[1].split()[1]) // 1024
                    with data_store.lock:
                        data_store.sysload['cpu'] = min(int(cpu), 100)
                        data_store.sysload['ram_free'] = free
                        data_store.sysload['history'].append(min(int(cpu), 100))
                except:
                    pass
                data_store.last_update['sysload'] = now

        if ENABLE_BAMBU:
            update_interval = 5 if is_connected else 15
            if now - data_store.last_update['printer'] > update_interval:
                is_alive = ping_printer(PRINTER_CONF['IP'])
                if is_alive:
                    try:
                        if not is_connected and global_printer:
                            global_printer.connect()
                            time.sleep(1)
                            is_connected = True
                        if global_printer:
                            status = global_printer.get_state()
                            if status and status != "UNKNOWN":
                                with data_store.lock:
                                    data_store.printer = {
                                        'status': status,
                                        'percentage': global_printer.get_percentage(),
                                        'remaining_time': global_printer.get_time(),
                                        'layers': f"{global_printer.current_layer_num()}/{global_printer.total_layer_num()}"
                                    }
                    except Exception as e:
                        is_connected = False
                        with data_store.lock:
                            data_store.printer['status'] = 'OFFLINE'
                        try:
                            if global_printer: global_printer.disconnect()
                        except:
                            pass
                else:
                    if is_connected:
                        is_connected = False
                        try:
                            global_printer.disconnect()
                        except:
                            pass
                    with data_store.lock:
                        data_store.printer['status'] = 'OFFLINE'
                data_store.last_update['printer'] = now
        if (not ENABLE_BAMBU) or widget_slot_can_show('crypto'):
            if now - data_store.last_update['crypto'] > 600:
                btc_url = f"{API_ENDPOINTS['btc']}?vs_currency=usd&days=7"
                eth_url = f"{API_ENDPOINTS['eth']}?vs_currency=usd&days=7"
                btc_data = net.get_json(btc_url)
                eth_data = net.get_json(eth_url)
                with data_store.lock:
                    if btc_data:
                        prices = [p[1] for p in btc_data.get('prices', [])]
                        if prices:
                            data_store.crypto['btc'] = int(prices[-1])
                            data_store.crypto['btc_hist'] = prices[::len(prices) // 50][:50]
                    if eth_data:
                        prices = [p[1] for p in eth_data.get('prices', [])]
                        if prices:
                            data_store.crypto['eth'] = int(prices[-1])
                            data_store.crypto['eth_hist'] = prices[::len(prices) // 50][:50]
                data_store.last_update['crypto'] = now

        if (not ENABLE_ROBOROCK and not ENABLE_ANTIGRAVITY) or widget_slot_can_show('ping'):
            if now - data_store.last_update['ping'] > 20:
                try:
                    out = subprocess.check_output(['ping', '-c', '1', '-W', '1', '8.8.8.8']).decode('utf-8')
                    ms = float(out.split('time=')[1].split(' ms')[0])
                except:
                    ms = 0
                with data_store.lock:
                    data_store.ping['current'] = int(ms)
                    data_store.ping['history'].append(int(ms))
                data_store.last_update['ping'] = now

        if now - data_store.last_update['gmail'] > 300:
            try:
                creds = None
                if os.path.exists(GMAIL_TOKEN_PATH):
                    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, GMAIL_SCOPES)
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        with open(GMAIL_TOKEN_PATH, 'w') as t: t.write(creds.to_json())
                if creds and creds.valid:
                    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
                    label_info = service.users().labels().get(userId='me', id='INBOX').execute()
                    with data_store.lock: data_store.gmail_unread = label_info.get('messagesUnread', 0)
            except:
                pass
            data_store.last_update['gmail'] = now

        # Claude Data Fetching (Run external script every 10 min)
        if ENABLE_CLAUDE and now - data_store.last_update['claude'] > 600:
            try:
                subprocess.run([sys.executable, os.path.join(BASE_DIR, 'claude.py')], capture_output=True, timeout=30)
                usage_path = os.path.join(BASE_DIR, 'usage.json')
                if os.path.exists(usage_path):
                    with open(usage_path, 'r') as f:
                        usage_data = json.load(f)
                    with data_store.lock:
                        data_store.claude = usage_data
                        if "error" in usage_data and "five_hour" not in usage_data:
                            data_store.claude['error'] = True
                        else:
                            data_store.claude['error'] = False
                else:
                    with data_store.lock:
                        data_store.claude['error'] = True
            except Exception as e:
                logging.error(f"Claude update error: {e}")
                with data_store.lock:
                    data_store.claude['error'] = True
            data_store.last_update['claude'] = now

        if ENABLE_OPENAI and now - data_store.last_update['openai'] > 600:
            try:
                subprocess.run([sys.executable, os.path.join(BASE_DIR, 'openai_codex.py')], capture_output=True, timeout=30)
                openai_usage_path = os.path.join(BASE_DIR, 'openai_usage.json')
                if os.path.exists(openai_usage_path):
                    with open(openai_usage_path, 'r', encoding='utf-8') as f:
                        openai_data = json.load(f)
                    with data_store.lock:
                        data_store.openai = openai_data
                        if "error" in openai_data and "window_24h" not in openai_data:
                            data_store.openai['error'] = True
                        else:
                            data_store.openai['error'] = False
                else:
                    with data_store.lock:
                        data_store.openai['error'] = True
            except Exception as e:
                logging.error(f"OpenAI / Codex update error: {e}")
                with data_store.lock:
                    data_store.openai['error'] = True
            data_store.last_update['openai'] = now

        if ENABLE_ANTIGRAVITY and now - data_store.last_update['antigravity'] > 60:
            try:
                subprocess.run([sys.executable, os.path.join(BASE_DIR, 'antigravity.py')], capture_output=True, timeout=30)
                limits_path = os.path.join(BASE_DIR, 'limits.json')
                if os.path.exists(limits_path):
                    with open(limits_path, 'r', encoding='utf-8') as f:
                        limits_data = json.load(f)
                    with data_store.lock:
                        data_store.antigravity = limits_data
                        if "error" in limits_data:
                            data_store.antigravity['error'] = True
                        else:
                            data_store.antigravity['error'] = False
                else:
                    with data_store.lock:
                        data_store.antigravity['error'] = True
            except Exception as e:
                logging.error(f"Antigravity update error: {e}")
                with data_store.lock:
                    data_store.antigravity['error'] = True
            data_store.last_update['antigravity'] = now

        if ENABLE_SPOTIFY and now - data_store.last_update['spotify'] > 20:
            url = f"{API_ENDPOINTS['lastfm']}?method=user.getrecenttracks&user={LASTFM_CONF['USERNAME']}&api_key={LASTFM_CONF['API_KEY']}&format=json&limit=2&rnd={int(now)}"
            s_data = net.get_json(url, timeout=5)
            if s_data:
                try:
                    tracks = s_data.get('recenttracks', {}).get('track', [])
                    if isinstance(tracks, dict): tracks = [tracks]
                    if tracks:
                        current_track = tracks[0]
                        is_playing = current_track.get('@attr', {}).get('nowplaying') == 'true'
                        if is_playing:
                            track_name = current_track.get('name', 'Unknown')
                            artist = current_track.get('artist', {}).get('#text', 'Unknown')
                            img_url = ""
                            for img in current_track.get('image', []):
                                if img.get('size') == 'extralarge': img_url = img.get('#text', '')
                            cover_dithered = None
                            if img_url:
                                img_bytes = net.get_image(img_url)
                                if img_bytes:
                                    img_pil = Image.open(io.BytesIO(img_bytes)).convert("L").resize((120, 120))
                                    enhancer = ImageEnhance.Contrast(img_pil)
                                    img_pil = enhancer.enhance(3.0)
                                    cover_dithered = img_pil.convert("1", dither=Image.NONE)
                            with data_store.lock:
                                data_store.spotify = {'status': 'PLAYING', 'text': f"{artist} - {track_name}",
                                                      'cover': cover_dithered}
                        else:
                            with data_store.lock:
                                data_store.spotify = {'status': 'PAUSED', 'text': '', 'cover': None}
                except:
                    pass
            data_store.last_update['spotify'] = now

        gc.collect()
        time.sleep(1)


# --- GRAPHICS FUNCTIONS ---
def draw_icon(draw, x, y, name, size=(40, 40), is_white=False):
    icon = get_cached_icon(name, size, is_white)
    if icon:
        draw.bitmap((x, y), icon, fill=255 if is_white else 0)
    else:
        draw.rectangle((x, y, x + size[0], y + size[1]), outline=255 if is_white else 0)


def draw_sparkline(draw, x, y, data, max_items=50, width=400, height=60, color=0, style="bar"):
    if not data: return
    max_val = max(data) if max(data) > 0 else 1
    step = width / max(max_items - 1, 1)

    if style == "line":
        points = []
        for i, val in enumerate(data):
            px = x + i * step
            py = y + height - (val / max_val) * height
            points.append((px, py))
        if len(points) > 1: draw.line(points, fill=color, width=2)
    elif style == "bar":
        bar_w = max(int(step) - 1, 1)
        for i, val in enumerate(data):
            bh = int((val / max_val) * height)
            bx = x + i * step
            by = y + height - bh
            draw.rectangle((bx, by, bx + bar_w, y + height), fill=color)


def get_weather_icon(code, is_day=1):
    if code == 0:
        return "icon_sun" if is_day else "icon_moon"
    elif code in [1, 2]:
        return "icon_partly-cloudy-day"
    elif code == 3:
        return "icon_clouds"
    elif code in [45, 48]:
        return "icon_wind"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "icon_rain"
    elif code in [71, 73, 75, 85, 86]:
        return "icon_snow"
    elif code in [95, 96, 99]:
        return "icon_lightning"
    return "icon_sun"


def snapshot_data_store():
    if not data_store.lock.acquire(timeout=2.0):
        return None

    try:
        sysload = data_store.sysload.copy()
        sysload['history'] = list(sysload.get('history', []))
        ping = data_store.ping.copy()
        ping['history'] = list(ping.get('history', []))

        return {
            'weather': data_store.weather.copy(),
            'aqi': data_store.aqi,
            'strava': data_store.strava.copy(),
            'printer': data_store.printer.copy(),
            'roborock': data_store.roborock.copy(),
            'gmail_unread': data_store.gmail_unread,
            'spotify': data_store.spotify.copy(),
            'claude': data_store.claude.copy(),
            'openai': data_store.openai.copy(),
            'antigravity': data_store.antigravity.copy(),
            'sysload': sysload,
            'crypto': data_store.crypto.copy(),
            'ping': ping,
            'now': datetime.now()
        }
    finally:
        data_store.lock.release()


def is_widget_available(widget_id):
    if widget_id == 'strava':
        return ENABLE_STRAVA
    if widget_id == 'bambu':
        return ENABLE_BAMBU
    if widget_id == 'roborock':
        return ENABLE_ROBOROCK
    if widget_id == 'antigravity':
        return ENABLE_ANTIGRAVITY
    if widget_id == 'ai_usage':
        return ENABLE_CLAUDE or ENABLE_OPENAI
    if widget_id == 'spotify':
        return ENABLE_SPOTIFY
    return widget_id in ('sysload', 'crypto', 'ping', 'time_progress')


def choose_slot_widget(slot_name, now_ts=None):
    slot = WIDGET_SLOTS.get(slot_name, {})
    widgets = slot.get('widgets', ())
    available = [widget_id for widget_id in widgets if is_widget_available(widget_id)]
    if not available:
        return None

    if not slot.get('rotate', False):
        return available[0]

    try:
        seconds = max(1, int(slot.get('seconds', 300)))
    except (TypeError, ValueError):
        seconds = 300

    if now_ts is None:
        now_ts = time.time()
    return available[int(now_ts // seconds) % len(available)]


def get_widget_slot_rects(epd):
    col_w = epd.width // 3
    col1_x = 20
    col2_x = col_w + 20
    col3_x = col_w * 2 + 30
    return {
        'left_top': (col1_x, 20, col_w - 20, 145),
        'left_middle': (col1_x, 170, col_w - 20, 315),
        'left_bottom': (col1_x, 340, col_w - 20, 470),
        'weather': (col2_x, 10, col_w * 2 - 20, 470),
        'clock': (col3_x, 10, epd.width - 20, 220),
        'right_middle': (col3_x, 240, epd.width - 20, 370),
        'gmail': (col3_x, 400, epd.width - 20, 470)
    }


def render_screen(epd, fonts):
    Himage = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(Himage)

    state = snapshot_data_store()
    if state is None:
        return Himage

    col_w = epd.width // 3
    col1_x = 20
    col2_x = col_w + 20
    col3_x = col_w * 2 + 30
    slot_rects = get_widget_slot_rects(epd)
    now_ts = time.time()

    dashboard_widgets.configure(
        draw_icon, draw_sparkline, get_weather_icon, time_until,
        compact_number, format_model_label, format_window_label,
        OPENAI_CONF, ENABLE_CLAUDE, ENABLE_OPENAI
    )

    dashboard_widgets.draw_slot(choose_slot_widget('left_top', now_ts), Himage, draw, fonts, state, col1_x, 20, clear_rect=slot_rects['left_top'])
    draw.line((col1_x, 150, col_w - 20, 150), fill=0, width=2)

    dashboard_widgets.draw_slot(choose_slot_widget('left_middle', now_ts), Himage, draw, fonts, state, col1_x, 170, clear_rect=slot_rects['left_middle'])
    draw.line((col1_x, 320, col_w - 20, 320), fill=0, width=2)

    dashboard_widgets.draw_slot(choose_slot_widget('left_bottom', now_ts), Himage, draw, fonts, state, col1_x, 340, clear_rect=slot_rects['left_bottom'])
    draw.line((col_w, 10, col_w, 470), fill=0, width=2)

    dashboard_widgets.draw_weather_panel(draw, fonts, state, col2_x, col_w)
    draw.line((col_w * 2, 10, col_w * 2, 470), fill=0, width=2)

    dashboard_widgets.draw_time_header(draw, fonts, state, col3_x)
    draw.line((col3_x, 220, epd.width - 20, 220), fill=0, width=2)

    dashboard_widgets.draw_slot(choose_slot_widget('right_middle', now_ts), Himage, draw, fonts, state, col3_x, 240,
                                clear_rect=slot_rects['right_middle'])
    draw.line((col3_x, 380, epd.width - 20, 380), fill=0, width=2)

    dashboard_widgets.draw_gmail_widget(draw, fonts, state, col3_x, 400)

    return Himage

# --- MAIN LOOP ---
def main():
    auth_strava()
    auth_claude()
    auth_openai()
    auth_antigravity()
    roborock_user_data = auth_roborock(ROBOROCK_CONF['EMAIL'])

    signal.signal(signal.SIGALRM, timeout_handler)
    epd = None

    try:
        epd = epd10in85.EPD()
        epd.init()
        epd.Clear()
        time.sleep(1)
        epd.init_Part()

        def load_font(name, size):
            return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

        fonts = {
            '20': load_font('Aldrich-Regular.ttc', 20),
            '24': load_font('Aldrich-Regular.ttc', 24),
            '28': load_font('Aldrich-Regular.ttc', 28),
            '32': load_font('Aldrich-Regular.ttc', 32),
            '35': load_font('Aldrich-Regular.ttc', 35),
            '40': load_font('Aldrich-Regular.ttc', 40),
            '60': load_font('Aldrich-Regular.ttc', 60),
            '80': load_font('Aldrich-Regular.ttc', 80),
            'clock': load_font('advanced_led_board-7.ttc', 180),
        }

        t_data = threading.Thread(target=update_data_thread)
        t_data.daemon = True
        t_data.start()

        if ENABLE_ROBOROCK:
            t_robo = threading.Thread(target=roborock_update_thread, args=(roborock_user_data, ROBOROCK_CONF['EMAIL']))
            t_robo.daemon = True
            t_robo.start()

        refresh_counter = 0

        while True:
            start_time = time.time()
            try:
                signal.alarm(20)
                image = render_screen(epd, fonts)
                buf = epd.getbuffer(image)

                if refresh_counter >= 600:
                    logging.info("Full Refresh cycle")
                    epd.init()
                    epd.display(buf)
                    time.sleep(2)
                    epd.init_Part()
                    refresh_counter = 0
                else:
                    logging.info("Partial Refresh")
                    epd.display_Partial(buf, 0, 0, epd.width, epd.height)
                    refresh_counter += 1

                signal.alarm(0)
                del image
                del buf
                if refresh_counter % 10 == 0: gc.collect()

            except HardwareTimeoutError:
                logging.critical("HARDWARE HANG DETECTED!")
                signal.alarm(0)
                logging.shutdown()
                os.execv(sys.executable, ['python'] + sys.argv)
            except OSError as e:
                signal.alarm(0)
                if e.errno == 24:
                    os.execv(sys.executable, ['python'] + sys.argv)
            except Exception as e:
                signal.alarm(0)
                logging.error(f"Unexpected error in main: {e}")

            elapsed = time.time() - start_time
            sleep_time = max(5, 60 - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        try:
            signal.alarm(0)
            epd10in85.epdconfig.module_exit(cleanup=True)
        except:
            pass
        exit()


if __name__ == '__main__':
    main()
