import requests

TIMEOUT = 5

# Modell → (api_type, max_channels, label)
MODELS = {
    "shelly1":       ("relay",  1, "Shelly 1 / 1PM"),
    "shelly2":       ("relay",  2, "Shelly 2 / 2.5"),
    "shelly4pro":    ("relay",  4, "Shelly 4Pro"),
    "plug":          ("relay",  1, "Shelly Plug / Plug S"),
    "uni":           ("relay",  2, "Shelly UNI"),
    "dimmer":        ("dimmer", 1, "Shelly Dimmer 1 / 2"),
    "vintage":       ("dimmer", 1, "Shelly Vintage"),
    "duo":           ("duo",    1, "Shelly Duo"),
    "bulb":          ("color",  1, "Shelly Bulb"),
    "rgbw2_color":   ("color",  1, "Shelly RGBW2 (Farbmodus)"),
    "rgbw2_white":   ("white",  4, "Shelly RGBW2 (Weißkanal 0–3)"),
}

# API-Typ → HTTP-Endpunkt
_ENDPOINT = {
    "relay":  "relay",
    "dimmer": "light",
    "duo":    "light",
    "color":  "color",
    "white":  "white",
    "light":  "light",   # Rückwärtskompatibilität
}


def _base(device):
    api_type = device.get("api_type") or device.get("type", "relay")
    endpoint = _ENDPOINT.get(api_type, "relay")
    return f"http://{device['ip']}/{endpoint}/{device['channel']}"


def turn_on(device):
    api_type = device.get("api_type") or device.get("type", "relay")
    params = {"turn": "on"}

    if api_type == "color":
        c = device.get("alarm_color") or {}
        params["red"]   = c.get("red",   255)
        params["green"] = c.get("green",   0)
        params["blue"]  = c.get("blue",    0)
        params["white"] = c.get("white",   0)
        params["gain"]  = device.get("alarm_brightness", 100)

    elif api_type == "duo":
        params["brightness"] = device.get("alarm_brightness", 100)
        params["kelvin"]     = device.get("alarm_color_temp", 4000)

    elif api_type in ("dimmer", "light", "white"):
        params["brightness"] = device.get("alarm_brightness", 100)

    resp = requests.get(_base(device), params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def turn_off(device):
    resp = requests.get(_base(device), params={"turn": "off"}, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_status(device):
    resp = requests.get(_base(device), timeout=TIMEOUT)
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
