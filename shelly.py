import requests

TIMEOUT = 5

# Typ → API-Endpunkt
_ENDPOINTS = {
    "relay": "relay",
    "light": "light",
    "color": "color",
    "white": "white",
}


def _base_url(device):
    endpoint = _ENDPOINTS.get(device["type"], "relay")
    return f"http://{device['ip']}/{endpoint}/{device['channel']}"


def turn_on(device):
    params = {"turn": "on"}
    t = device["type"]

    if t == "color":
        c = device.get("alarm_color", {})
        params["red"]   = c.get("red",   255)
        params["green"] = c.get("green",   0)
        params["blue"]  = c.get("blue",    0)
        params["white"] = c.get("white",   0)
        params["gain"]  = device.get("alarm_brightness", 100)

    elif t in ("light", "white"):
        params["brightness"] = device.get("alarm_brightness", 100)

    resp = requests.get(_base_url(device), params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def turn_off(device):
    resp = requests.get(_base_url(device), params={"turn": "off"}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_status(device):
    resp = requests.get(_base_url(device), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def test_device(device):
    try:
        status = get_status(device)
        return {"ok": True, "status": status}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Gerät nicht erreichbar"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
