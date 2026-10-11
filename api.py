import json
import math
import re
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
    # A small margin keeps rounded coordinates inside the 100 m boundary.
    max_dist = max(0.0, min(config.MAX_DISTANCE_METERS, 100.0) - 0.01)
    distance = max_dist * math.sqrt(random.random())
    bearing = 2 * math.pi * random.random()
    angular = distance / 6371000.0
    lat1, lon1 = math.radians(center_lat), math.radians(center_lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(angular) + math.cos(lat1) * math.sin(angular) * math.cos(bearing))
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular) * math.cos(lat1), math.cos(angular) - math.sin(lat1) * math.sin(lat2))
    return {
        "latitude": round(math.degrees(lat2), 8),
        "longitude": round(math.degrees(lon2), 8),
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
            headers["X-Tenant-Id"] = config.TENANT_ID

        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=20, context=self.ssl_context) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw) if raw else {}
                if result.get("success") is False:
                    raise ValueError(result.get("message") or "API rejected request")
                return result
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
        
        selected = self._request("POST", "/auth/select-tenant", token=token,
                                 data={"tenant_id": config.TENANT_ID})
        selected_data = selected.get("data") or {}
        return selected_data.get("token") or selected_data.get("access_token") or selected.get("token") or selected.get("access_token") or token

    def get_status(self, token: str) -> Dict[str, Any]:
        return self._request("GET", "/attendance/status", token=token)

    def attendance_payload(self, token, loc, check_in):
        binding_response = self._request("GET", "/attendance/device", token=token)
        bindings = binding_response.get("devices") or [binding_response.get("device") or {}]
        records = self._request("GET", "/devices", token=token).get("data", [])
        matches = {}
        for binding in bindings:
            if binding.get("status") != "approved":
                continue
            parts = re.split(r"[•*…]+", binding.get("device_uid_masked") or "")
            if len(parts) != 2 or not all(parts):
                continue
            for record in records:
                match = re.fullmatch(r"mobile-([^-]+)-(.+)", record.get("device_name") or "")
                if match and match[1] == binding.get("platform"):
                    uid = match[2]
                    if uid.lower().startswith(parts[0].lower()) and uid.lower().endswith(parts[1].lower()):
                        matches[uid] = binding.get("device_name") or record.get("name") or match[1]
        if len(matches) != 1:
            raise ValueError("Cannot uniquely resolve approved attendance device UID from device list")
        uid, name = next(iter(matches.items()))
        if config.ATTENDANCE_DEVICE_UID and uid.upper() != config.ATTENDANCE_DEVICE_UID.upper():
            raise ValueError("Approved device does not match configured attendance UID")
        payload = {
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "accuracy": round(random.uniform(3.0, 20.0), 2), "address": "",
            "device_id": uid, "image": None, "is_remote": False, "note": "",
        }
        if check_in:
            payload.update(device_name=name, rule_id=config.ATTENDANCE_RULE_ID)
        return payload

    def check_in(self, token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        loc = generate_random_location()
        payload = self.attendance_payload(token, loc, True)
        res = self._request("POST", "/attendance/check-in", token=token, data=payload)
        return res, loc

    def check_out(self, token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        loc = generate_random_location()
        payload = self.attendance_payload(token, loc, False)
        res = self._request("POST", "/attendance/check-out", token=token, data=payload)
        return res, loc
