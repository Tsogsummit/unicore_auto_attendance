import json
import math
import random
import urllib.request
import urllib.error
import ssl
from typing import Dict, Any, Tuple
import config

def generate_random_location() -> Dict[str, Any]:
    """
    Generates a realistic random GPS coordinate within config.MAX_DISTANCE_METERS radius
    matching the exact trigonometric formula used in the Flutter mobile app.
    """
    center_lat = config.CENTER_LATITUDE
    center_lon = config.CENTER_LONGITUDE
    max_dist = config.MAX_DISTANCE_METERS
    earth_radius = 6371000.0  # Earth radius in meters

    # Random distance and bearing
    distance = max_dist * math.sqrt(random.random())
    bearing = 2 * math.pi * random.random()
    center_lat_rad = math.radians(center_lat)

    delta_lat = (distance * math.cos(bearing)) / earth_radius
    delta_lon = (distance * math.sin(bearing)) / (earth_radius * math.cos(center_lat_rad))

    lat = center_lat + math.degrees(delta_lat)
    lon = center_lon + math.degrees(delta_lon)

    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "location_name": config.LOCATION_NAME,
        "_distance_meters": round(distance, 1)
    }


def notify(message: str):
    """Sends optional Telegram or Discord notifications."""
    print(f"[NOTIFY] {message}")
    
    # Discord Webhook
    if config.DISCORD_WEBHOOK_URL:
        try:
            req = urllib.request.Request(
                config.DISCORD_WEBHOOK_URL,
                data=json.dumps({"content": message}).encode('utf-8'),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[NOTIFY ERROR] Discord webhook failed: {e}")

    # Telegram Bot
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = json.dumps({
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": message
            }).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"[NOTIFY ERROR] Telegram send failed: {e}")


class UnicoreApi:
    def __init__(self, base_url: str = config.BASE_URL):
        self.base_url = base_url.rstrip("/")
        # Setup SSL context
        self.ssl_context = ssl.create_default_context()

    def _request(self, method: str, path: str, token: str = None, data: dict = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "UnicoreAutoAttendance/1.0 (Android; Linux x86_64)",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=20, context=self.ssl_context) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            err_text = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_text)
                msg = parsed.get("message") or parsed.get("error") or err_text
            except Exception:
                msg = err_text or f"HTTP {e.code}"
            raise Exception(f"HTTP {e.code}: {msg}")
        except Exception as e:
            raise Exception(f"Network request failed: {e}")

    def login(self, login: str = None, password: str = None) -> str:
        login_str = login or config.UNICORE_LOGIN
        password_str = password or config.UNICORE_PASSWORD

        if not login_str or not password_str:
            raise ValueError("UNICORE_LOGIN and UNICORE_PASSWORD must be configured in .env or arguments.")

        res = self._request("POST", "/auth/login", data={"login": login_str, "password": password_str})
        
        # Token extraction supporting multiple API response formats
        token = (
            res.get("token") or 
            res.get("access_token") or 
            (res.get("data") and isinstance(res["data"], dict) and (res["data"].get("token") or res["data"].get("access_token")))
        )
        if not token:
            raise ValueError(f"Failed to find authorization token in login response: {res}")
        
        return token

    def get_status(self, token: str) -> Dict[str, Any]:
        return self._request("GET", "/attendance/status", token=token)

    def check_in(self, token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        loc = generate_random_location()
        payload = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "location_name": loc["location_name"]
        }
        res = self._request("POST", "/attendance/check-in", token=token, data=payload)
        return res, loc

    def check_out(self, token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        loc = generate_random_location()
        payload = {
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "location_name": loc["location_name"]
        }
        res = self._request("POST", "/attendance/check-out", token=token, data=payload)
        return res, loc
