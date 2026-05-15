import requests

BASE_URL = "https://www.divera247.com/api/v2"
TIMEOUT = 10


def fetch_alarms(access_key):
    """Returns list of active alarms or raises on error."""
    import logging
    log = logging.getLogger(__name__)

    url = f"{BASE_URL}/pull/vehicle-status"
    resp = requests.get(url, params={"accesskey": access_key}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    log.debug("Divera Rohantwort: %s", data)

    if not isinstance(data, dict):
        raise ValueError(f"Unerwartetes API-Format (kein dict): {type(data).__name__}")
    if not data.get("success"):
        raise ValueError("Divera API: success=false")

    inner = data.get("data", {})
    if not isinstance(inner, dict):
        raise ValueError(f"data-Feld ist kein dict: {type(inner).__name__}")

    alarms_block = inner.get("alarms", {})
    if not isinstance(alarms_block, dict):
        raise ValueError(f"alarms-Feld ist kein dict: {type(alarms_block).__name__}")

    items = alarms_block.get("items", {})

    if isinstance(items, dict):
        alarms = list(items.values())
    elif isinstance(items, list):
        alarms = items
    else:
        alarms = []

    alarms = [a for a in alarms if isinstance(a, dict)]
    alarms.sort(key=lambda a: a.get("date", 0), reverse=True)
    return alarms


def get_latest_alarm_id(access_key):
    alarms = fetch_alarms(access_key)
    if not alarms:
        return None
    return alarms[0].get("id")
