import requests

TIMEOUT = 5


def _url(device, action):
    endpoint = "light" if device["type"] == "light" else "relay"
    return f"http://{device['ip']}/{endpoint}/{device['channel']}?turn={action}"


def turn_on(device):
    url = _url(device, "on")
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def turn_off(device):
    url = _url(device, "off")
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_status(device):
    endpoint = "light" if device["type"] == "light" else "relay"
    url = f"http://{device['ip']}/{endpoint}/{device['channel']}"
    resp = requests.get(url, timeout=TIMEOUT)
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
