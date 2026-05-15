import logging

import requests

BASE_URL = "https://www.divera247.com/api"
TIMEOUT = 10
log = logging.getLogger(__name__)


def fetch_last_alarm(access_key):
    """Organisations-Key: /api/last-alarm"""
    url = f"{BASE_URL}/last-alarm"
    resp = requests.get(url, params={"accesskey": access_key}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    log.debug("Divera /last-alarm Antwort: %s", data)

    if not isinstance(data, dict):
        raise ValueError(f"Unerwartetes API-Format: {type(data).__name__}")

    if not data.get("success"):
        return None

    alarm = data.get("data")
    if not isinstance(alarm, dict) or not alarm.get("id"):
        return None

    return alarm


def fetch_last_alarm_personal(access_key):
    """Persönlicher Key: /api/v2/pull/all — neuesten Einsatz aus alarm.items."""
    url = f"{BASE_URL}/v2/pull/all"
    resp = requests.get(url, params={"accesskey": access_key}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    log.debug("Divera /v2/pull/all Antwort (gekürzt): success=%s", data.get("success"))

    if not isinstance(data, dict) or not data.get("success"):
        return None

    items = data.get("data", {}).get("alarm", {}).get("items", {})
    if not isinstance(items, dict) or not items:
        return None

    alarms = [a for a in items.values() if isinstance(a, dict) and a.get("id")]
    if not alarms:
        return None

    # Neuesten Einsatz nach date-Timestamp
    alarms.sort(key=lambda a: a.get("date", 0), reverse=True)
    return alarms[0]


def fetch_alarm(access_key, key_type="org"):
    """Wählt automatisch die richtige Fetch-Funktion je nach Key-Typ."""
    if key_type == "personal":
        return fetch_last_alarm_personal(access_key)
    return fetch_last_alarm(access_key)


# Rückwärtskompatibilität
def fetch_alarms(access_key):
    alarm = fetch_last_alarm(access_key)
    return [alarm] if alarm else []
