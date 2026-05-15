import json
import os
import uuid

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "divera_access_key": "",
    "divera_key_type": "org",
    "poll_interval": 30,
    "shelly_devices": [],
    "selected_lights": [],
    "auto_off_seconds": 0,
    "last_alarm_id": None,
    "ha_url": "",
    "ha_token": "",
    "ha_selected_entities": [],
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


def add_device(cfg, name, ip, model, channel,
               alarm_brightness=100, alarm_color=None, alarm_color_temp=4000):
    from shelly import MODELS
    api_type = MODELS.get(model, ("relay",))[0]
    device = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "ip": ip.strip(),
        "model": model,
        "api_type": api_type,
        "type": api_type,   # Rückwärtskompatibilität
        "channel": int(channel),
        "alarm_brightness": int(alarm_brightness),
        "alarm_color": alarm_color or {"red": 255, "green": 0, "blue": 0, "white": 0},
        "alarm_color_temp": int(alarm_color_temp),
    }
    cfg["shelly_devices"].append(device)
    save(cfg)
    return device


def update_device(cfg, device_id, **fields):
    for dev in cfg["shelly_devices"]:
        if dev["id"] == device_id:
            dev.update(fields)
            break
    save(cfg)


def remove_device(cfg, device_id):
    cfg["shelly_devices"] = [d for d in cfg["shelly_devices"] if d["id"] != device_id]
    cfg["selected_lights"] = [i for i in cfg["selected_lights"] if i != device_id]
    save(cfg)


def get_device(cfg, device_id):
    return next((d for d in cfg["shelly_devices"] if d["id"] == device_id), None)
