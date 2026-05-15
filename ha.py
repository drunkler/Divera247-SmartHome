import logging
import requests

TIMEOUT = 10
log = logging.getLogger(__name__)

ALARM_DOMAINS = ("light", "switch")


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_entities(ha_url, ha_token, domains=ALARM_DOMAINS):
    url = f"{ha_url.rstrip('/')}/api/states"
    resp = requests.get(url, headers=_headers(ha_token), timeout=TIMEOUT)
    resp.raise_for_status()
    entities = []
    for s in resp.json():
        domain = s["entity_id"].split(".")[0]
        if domain in domains:
            entities.append({
                "entity_id": s["entity_id"],
                "name": s["attributes"].get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "domain": domain,
            })
    entities.sort(key=lambda e: (e["domain"], e["name"].lower()))
    return entities


def get_state(ha_url, ha_token, entity_id):
    url = f"{ha_url.rstrip('/')}/api/states/{entity_id}"
    resp = requests.get(url, headers=_headers(ha_token), timeout=TIMEOUT)
    resp.raise_for_status()
    s = resp.json()
    return {"state": s["state"], "attributes": s.get("attributes", {})}


def turn_on(ha_url, ha_token, entity_id, **service_data):
    domain = entity_id.split(".")[0]
    url = f"{ha_url.rstrip('/')}/api/services/{domain}/turn_on"
    resp = requests.post(url, headers=_headers(ha_token),
                         json={"entity_id": entity_id, **service_data}, timeout=TIMEOUT)
    resp.raise_for_status()


def turn_off(ha_url, ha_token, entity_id):
    domain = entity_id.split(".")[0]
    url = f"{ha_url.rstrip('/')}/api/services/{domain}/turn_off"
    resp = requests.post(url, headers=_headers(ha_token),
                         json={"entity_id": entity_id}, timeout=TIMEOUT)
    resp.raise_for_status()


def restore_state(ha_url, ha_token, entity_id, saved):
    if saved["state"] == "off":
        turn_off(ha_url, ha_token, entity_id)
        return
    attrs = saved.get("attributes", {})
    domain = entity_id.split(".")[0]
    service_data = {}
    if domain == "light":
        if "brightness" in attrs:
            service_data["brightness"] = attrs["brightness"]
        if "rgb_color" in attrs:
            service_data["rgb_color"] = attrs["rgb_color"]
        elif "color_temp" in attrs:
            service_data["color_temp"] = attrs["color_temp"]
    turn_on(ha_url, ha_token, entity_id, **service_data)
