import json
import os
import uuid

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "divera_access_key": "",
    "poll_interval": 30,
    "shelly_devices": [],
    "selected_lights": [],
    "auto_off_seconds": 0,
    "last_alarm_id": None,
}


def load():
    if not os.path.exists(CONFIG_FILE):
        save(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in DEFAULT_CONFIG.items():
        data.setdefault(k, v)
    return data


def save(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def add_device(cfg, name, ip, device_type, channel):
    device = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "ip": ip.strip(),
        "type": device_type,
        "channel": int(channel),
    }
    cfg["shelly_devices"].append(device)
    save(cfg)
    return device


def remove_device(cfg, device_id):
    cfg["shelly_devices"] = [d for d in cfg["shelly_devices"] if d["id"] != device_id]
    cfg["selected_lights"] = [i for i in cfg["selected_lights"] if i != device_id]
    save(cfg)


def get_device(cfg, device_id):
    return next((d for d in cfg["shelly_devices"] if d["id"] == device_id), None)
