#!/usr/bin/env bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

section() {
  echo -e "\n${GREEN}==> $1${NC}"
}

warn() {
  echo -e "${YELLOW}Warning:${NC} $1"
}

error() {
  echo -e "${RED}Error:${NC} $1"
}

prompt_value() {
  local prompt="$1"
  local default="$2"
  local value
  read -r -p "$prompt [$default]: " value
  if [ -z "$value" ]; then
    value="$default"
  fi
  printf '%s' "$value"
}

prompt_yes_no() {
  local prompt="$1"
  local default="$2"
  local reply
  while true; do
    read -r -p "$prompt [$default]: " reply
    reply="${reply:-$default}"
    case "${reply,,}" in
      y|yes) printf 'True'; return 0 ;;
      n|no) printf 'False'; return 0 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

validate_float() {
  local value="$1"
  [[ "$value" =~ ^-?[0-9]+([.][0-9]+)?$ ]]
}

REPO_URL="https://github.com/bjadda/Waveshare-ePaper-10.85-dashboard.git"
INSTALL_DIR="$HOME/dashboard"
MAIN_FILE="$INSTALL_DIR/main.py"
CONFIG_FILE="$INSTALL_DIR/dashboard_config.json"
SERVICE_TEMPLATE="$INSTALL_DIR/epaper-dashboard.service"
SERVICE_FILE="/etc/systemd/system/epaper-dashboard.service"
DASH_USER="$(id -un)"
DASH_USER_ESC="$(printf '%s' "$DASH_USER" | sed 's/[\\/&]/\\&/g')"

section "Checking environment"
if ! command -v python3 >/dev/null 2>&1; then
  error "python3 is required but not found. Please install Python 3 first."
  exit 1
fi

IS_RPI=false
if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
  IS_RPI=true
elif [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
  IS_RPI=true
fi

if [ "$IS_RPI" = false ]; then
  warn "This does not appear to be a Raspberry Pi. Installer will continue anyway."
fi

section "Cloning/updating repository"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Repository already exists at $INSTALL_DIR"
  if ! git -C "$INSTALL_DIR" pull --ff-only; then
    warn "Could not fast-forward pull in $INSTALL_DIR. Continuing with existing files."
  fi
elif [ -d "$INSTALL_DIR" ] && [ -n "$(ls -A "$INSTALL_DIR")" ]; then
  error "$INSTALL_DIR exists and is not empty, but is not a git repository."
  exit 1
else
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

section "Enabling SPI"
if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_spi 0 || warn "Failed to enable SPI automatically. Please verify with raspi-config."
else
  warn "raspi-config not found. Please ensure SPI is enabled manually."
fi

section "Installing system dependencies"
sudo apt update
sudo apt install -y python3-pip python3-pil python3-numpy git tmux

section "Installing Python dependencies"
if ! pip3 install requests Pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib aiomqtt roborock; then
  warn "Standard pip install failed (likely due to PEP 668 on newer OS versions); retrying with --break-system-packages"
  pip3 install --break-system-packages requests Pillow google-api-python-client google-auth-httplib2 google-auth-oauthlib aiomqtt roborock
fi

section "Collecting configuration"
if [ ! -f "$MAIN_FILE" ]; then
  error "Expected file not found: $MAIN_FILE"
  exit 1
fi

CURRENT_CONFIG="$(CONFIG_FILE="$CONFIG_FILE" python3 - <<'PY'
import json
import os
import pathlib
import shlex

path = pathlib.Path(os.environ["CONFIG_FILE"])
try:
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
except (OSError, json.JSONDecodeError):
    config = {}

location = config.get("location", {}) if isinstance(config.get("location"), dict) else {}
widgets = config.get("widgets", {}) if isinstance(config.get("widgets"), dict) else {}

def yn(name):
    return "y" if widgets.get(name, False) else "n"

values = {
    "CURRENT_LAT": location.get("lat", "44.8240855"),
    "CURRENT_LON": location.get("lon", "20.4934273"),
    "DEF_STRAVA": yn("strava"),
    "DEF_BAMBU": yn("bambu"),
    "DEF_ROBOROCK": yn("roborock"),
    "DEF_ANTIGRAVITY": yn("antigravity"),
    "DEF_CLAUDE": yn("claude"),
    "DEF_OPENAI": yn("openai"),
    "DEF_SPOTIFY": yn("spotify")
}

for key, value in values.items():
    print(f"{key}={shlex.quote(str(value))}")
PY
)"
eval "$CURRENT_CONFIG"

echo "Set your location for weather and sunrise/sunset calculations."
GPS_LAT="$(prompt_value 'GPS latitude' "${CURRENT_LAT:-44.8240855}")"
GPS_LON="$(prompt_value 'GPS longitude' "${CURRENT_LON:-20.4934273}")"
if ! validate_float "$GPS_LAT" || ! validate_float "$GPS_LON"; then
  error "Latitude/longitude must be numeric values (example: 44.8240855, 20.4934273)."
  exit 1
fi

echo -e "\nEnable optional widgets (y/n):"
ENABLE_STRAVA="$(prompt_yes_no 'Strava (activity stats)' "$DEF_STRAVA")"
ENABLE_BAMBU="$(prompt_yes_no 'Bambu Lab (3D printer status)' "$DEF_BAMBU")"
ENABLE_ROBOROCK="$(prompt_yes_no 'Roborock (vacuum status)' "$DEF_ROBOROCK")"
ENABLE_ANTIGRAVITY="$(prompt_yes_no 'Antigravity (usage limits)' "$DEF_ANTIGRAVITY")"
ENABLE_CLAUDE="$(prompt_yes_no 'Claude (usage limits)' "$DEF_CLAUDE")"
ENABLE_OPENAI="$(prompt_yes_no 'OpenAI/Codex (usage limits)' "$DEF_OPENAI")"
ENABLE_SPOTIFY="$(prompt_yes_no 'Spotify via Last.fm (now playing)' "$DEF_SPOTIFY")"

BAMBU_IP=""
BAMBU_SERIAL=""
BAMBU_ACCESS_CODE=""
ROBOROCK_EMAIL=""
LASTFM_API_KEY=""
LASTFM_USERNAME=""

if [ "$ENABLE_BAMBU" = "True" ]; then
  BAMBU_IP="$(prompt_value 'Bambu printer IP address' '192.168.1.100')"
  BAMBU_SERIAL="$(prompt_value 'Bambu printer Serial Number' '')"
  BAMBU_ACCESS_CODE="$(prompt_value 'Bambu printer Access Code' '')"
fi

if [ "$ENABLE_ROBOROCK" = "True" ]; then
  ROBOROCK_EMAIL="$(prompt_value 'Roborock account email' '')"
fi

if [ "$ENABLE_SPOTIFY" = "True" ]; then
  LASTFM_API_KEY="$(prompt_value 'Last.fm API Key' '')"
  LASTFM_USERNAME="$(prompt_value 'Last.fm Username' '')"
fi

section "Writing config.env"
cat > "$INSTALL_DIR/config.env" <<CFG
LOCATION_LAT=$GPS_LAT
LOCATION_LON=$GPS_LON
ENABLE_STRAVA=$ENABLE_STRAVA
ENABLE_BAMBU=$ENABLE_BAMBU
ENABLE_ROBOROCK=$ENABLE_ROBOROCK
ENABLE_ANTIGRAVITY=$ENABLE_ANTIGRAVITY
ENABLE_CLAUDE=$ENABLE_CLAUDE
ENABLE_OPENAI=$ENABLE_OPENAI
ENABLE_SPOTIFY=$ENABLE_SPOTIFY
BAMBU_IP=$BAMBU_IP
BAMBU_SERIAL=$BAMBU_SERIAL
BAMBU_ACCESS_CODE=$BAMBU_ACCESS_CODE
ROBOROCK_EMAIL=$ROBOROCK_EMAIL
LASTFM_API_KEY=$LASTFM_API_KEY
LASTFM_USERNAME=$LASTFM_USERNAME
CFG

section "Writing dashboard_config.json"
export CONFIG_FILE GPS_LAT GPS_LON ENABLE_STRAVA ENABLE_BAMBU ENABLE_ROBOROCK ENABLE_ANTIGRAVITY ENABLE_CLAUDE ENABLE_OPENAI ENABLE_SPOTIFY
export BAMBU_IP BAMBU_SERIAL BAMBU_ACCESS_CODE ROBOROCK_EMAIL LASTFM_API_KEY LASTFM_USERNAME
python3 - <<'PY'
import json
import os
import pathlib

path = pathlib.Path(os.environ["CONFIG_FILE"])
try:
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
except (OSError, json.JSONDecodeError):
    config = {}

def enabled(name):
    return os.environ.get(name) == "True"

def value(name):
    return os.environ.get(name, "").strip()

config["version"] = 1
config["location"] = {
    "lat": float(os.environ["GPS_LAT"]),
    "lon": float(os.environ["GPS_LON"])
}
config["widgets"] = {
    "strava": enabled("ENABLE_STRAVA"),
    "bambu": enabled("ENABLE_BAMBU"),
    "roborock": enabled("ENABLE_ROBOROCK"),
    "antigravity": enabled("ENABLE_ANTIGRAVITY"),
    "claude": enabled("ENABLE_CLAUDE"),
    "openai": enabled("ENABLE_OPENAI"),
    "spotify": enabled("ENABLE_SPOTIFY")
}

integrations = config.setdefault("integrations", {})
bambu = integrations.setdefault("bambu", {})
if enabled("ENABLE_BAMBU") or any(value(name) for name in ("BAMBU_IP", "BAMBU_SERIAL", "BAMBU_ACCESS_CODE")):
    bambu["ip"] = value("BAMBU_IP")
    bambu["serial"] = value("BAMBU_SERIAL")
    bambu["access_code"] = value("BAMBU_ACCESS_CODE")

roborock = integrations.setdefault("roborock", {})
if enabled("ENABLE_ROBOROCK") or value("ROBOROCK_EMAIL"):
    roborock["email"] = value("ROBOROCK_EMAIL")

lastfm = integrations.setdefault("lastfm", {})
if enabled("ENABLE_SPOTIFY") or any(value(name) for name in ("LASTFM_API_KEY", "LASTFM_USERNAME")):
    lastfm["api_key"] = value("LASTFM_API_KEY")
    lastfm["username"] = value("LASTFM_USERNAME")

openai = integrations.setdefault("openai", {})
openai.setdefault("label", "OPENAI / CODEX")
openai.setdefault("project_ids", [])
openai.setdefault("model_filters", ["gpt-5-codex", "gpt-5.3-codex", "codex-mini-latest"])

path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
PY

section "Installing systemd service"
if [ ! -f "$SERVICE_TEMPLATE" ]; then
  error "Service template $SERVICE_TEMPLATE not found."
  exit 1
fi

sed "s/%i/$DASH_USER_ESC/g" "$SERVICE_TEMPLATE" | sudo tee "$SERVICE_FILE" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable epaper-dashboard
sudo systemctl start epaper-dashboard

section "Installation complete"
echo "Configured location: $GPS_LAT, $GPS_LON"
echo "Widget toggles: STRAVA=$ENABLE_STRAVA BAMBU=$ENABLE_BAMBU ROBOROCK=$ENABLE_ROBOROCK ANTIGRAVITY=$ENABLE_ANTIGRAVITY CLAUDE=$ENABLE_CLAUDE OPENAI=$ENABLE_OPENAI SPOTIFY=$ENABLE_SPOTIFY"
if [ "$ENABLE_BAMBU" = "True" ]; then
  echo "Bambu configured for IP: $BAMBU_IP"
fi
if [ "$ENABLE_ROBOROCK" = "True" ]; then
  echo "Roborock configured for email: $ROBOROCK_EMAIL"
fi
if [ "$ENABLE_SPOTIFY" = "True" ]; then
  echo "Last.fm configured for user: $LASTFM_USERNAME"
fi

echo ""
echo "Service commands:"
echo "  sudo systemctl status epaper-dashboard"
echo "  sudo systemctl restart epaper-dashboard"
echo "  sudo systemctl stop epaper-dashboard"
echo "  journalctl -u epaper-dashboard -f"
echo ""
echo "Configurator:"
echo "  python3 ~/dashboard/config_server.py --host 0.0.0.0 --port 8080"
echo "  python3 ~/dashboard/config_server.py --host 0.0.0.0 --port 8080 --allow-restart"
echo ""
echo "OAuth reminder: for each enabled OAuth widget (Strava, Claude, OpenAI/Codex), run once as user '$DASH_USER':"
echo "  sudo -u $DASH_USER python3 ~/dashboard/main.py"
echo "Complete each prompt, then restart service: sudo systemctl restart epaper-dashboard"
