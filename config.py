import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Try to load .env file if python-dotenv is installed or parse manually
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))

# Application Settings
BASE_URL = os.getenv("BASE_URL", "https://unicore.systems/api/mobile")
UNICORE_LOGIN = os.getenv("UNICORE_LOGIN", "")
UNICORE_PASSWORD = os.getenv("UNICORE_PASSWORD", "")

# Timezone & Schedule
TIMEZONE_STR = os.getenv("TIMEZONE", "Asia/Ulaanbaatar")
try:
    MONGOLIA_TZ = ZoneInfo(TIMEZONE_STR)
except Exception:
    MONGOLIA_TZ = ZoneInfo("Asia/Ulaanbaatar")

CHECKIN_START_TIME = os.getenv("CHECKIN_START_TIME", "07:30")   # 07:30 AM
CHECKIN_END_TIME = os.getenv("CHECKIN_END_TIME", "07:45")       # 07:50 AM
CHECKOUT_START_TIME = os.getenv("CHECKOUT_START_TIME", "16:15") # 04:10 PM
CHECKOUT_END_TIME = os.getenv("CHECKOUT_END_TIME", "16:30")     # 04:30 PM

SKIP_WEEKENDS = os.getenv("SKIP_WEEKENDS", "true").lower() in ("true", "1", "yes")

# Location Settings (Default: Tselmeg Digital International School)
CENTER_LATITUDE = float(os.getenv("CENTER_LATITUDE", "47.89679317"))
CENTER_LONGITUDE = float(os.getenv("CENTER_LONGITUDE", "106.88973599"))
MAX_DISTANCE_METERS = float(os.getenv("MAX_DISTANCE_METERS", "100.0"))
LOCATION_NAME = os.getenv("LOCATION_NAME", "Tselmeg Digital International School")

# Webhook notifications (Optional)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Mobile attendance API settings
TENANT_ID = os.getenv("TENANT_ID", "tenant_65")
ATTENDANCE_ACCURACY = float(os.getenv("ATTENDANCE_ACCURACY", "12.0"))
ATTENDANCE_RULE_ID = int(os.getenv("ATTENDANCE_RULE_ID", "5"))

ATTENDANCE_DEVICE_UID = os.getenv("ATTENDANCE_DEVICE_UID", "")
