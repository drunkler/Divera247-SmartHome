import requests

BASE_URL = "https://www.divera247.com/api/v2"
TIMEOUT = 10


def fetch_alarms(access_key):
    """Returns list of active alarms or raises on error."""
    url = f"{BASE_URL}/pull/vehicle-status"
    resp = requests.get(url, params={"accesskey": access_key}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise ValueError("Divera API: success=false")
    alarms_raw = data.get("data", {}).get("alarms", {}).get("items", {})
    alarms = list(alarms_raw.values()) if isinstance(alarms_raw, dict) else []
    alarms.sort(key=lambda a: a.get("date", 0), reverse=True)
    return alarms


def get_latest_alarm_id(access_key):
    alarms = fetch_alarms(access_key)
    if not alarms:
        return None
    return alarms[0].get("id")
