"""Constants for Whisper API STT."""

DOMAIN = "whisper_api_stt"

CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_URL = "server_url"
CONF_PROMPT = "prompt"
CONF_TEMPERATURE = "temperature"

# --- Form defaults ---
# Pre-filled in the config/options flow UI; edit here only to change what
# a fresh install starts with. Actual per-install values live in the
# config entry (set via the UI), not here.
DEFAULT_API_KEY = ""
DEFAULT_LANGUAGE = "en-US"
DEFAULT_MODEL = "whisper-1"
DEFAULT_URL = "http://192.168.0.55:5045/v1/audio/transcriptions"
DEFAULT_PROMPT = None
DEFAULT_TEMPERATURE = 0.0
