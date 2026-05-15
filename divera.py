import logging

import requests

BASE_URL = "https://www.divera247.com/api"
TIMEOUT = 10
log = logging.getLogger(__name__)


def fetch_last_alarm(access_key):
    """
    Ruft den letzten Einsatz über /api/last-alarm ab.
    Gibt das Alarm-Dict zurück oder None wenn kein Einsatz vorhanden.
    """
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


# Rückwärtskompatibilität – wird intern nicht mehr genutzt
def fetch_alarms(access_key):
    alarm = fetch_last_alarm(access_key)
    return [alarm] if alarm else []
