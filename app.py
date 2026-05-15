import logging
import os
import subprocess
import sys
import threading
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config as cfg_module
import divera
import shelly

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "divera-shelly-secret-2024"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

# In-memory state
state = {
    "last_alarm": None,
    "alarm_history": [],
    "poll_error": None,
    "lights_on": False,
    "lights_on_since": None,
}
_off_timer = None
_scheduler = None
# Gespeicherte Zustände vor dem Einsatz: [{"dev_id": ..., "saved_state": {...}}]
_alarm_restore_list: list = []


def _trigger_lights(alarm, cfg):
    global _off_timer, _alarm_restore_list
    selected = cfg.get("selected_lights", [])
    if not selected:
        log.warning("Einsatz erkannt, aber keine Lichter konfiguriert.")
        return

    devices = {d["id"]: d for d in cfg.get("shelly_devices", [])}
    restore_list = []

    for dev_id in selected:
        dev = devices.get(dev_id)
        if not dev:
            continue

        # Zustand vor dem Einsatz vollständig speichern
        saved_state = {"ison": False}
        try:
            saved_state = shelly.get_status(dev)
        except Exception:
            pass

        try:
            shelly.turn_on(dev)
            was_on = bool(saved_state.get("ison", False))
            restore_list.append({"dev_id": dev_id, "saved_state": saved_state})
            if was_on:
                log.info("Licht geändert: %s (war AN, Zustand gespeichert für Reset)", dev["name"])
            else:
                log.info("Licht AN: %s (war AUS, wird nach Timer ausgeschaltet)", dev["name"])
        except Exception as e:
            log.error("Fehler beim Einschalten von %s: %s", dev["name"], e)

    _alarm_restore_list = restore_list
    state["lights_on"] = True
    state["lights_on_since"] = datetime.now().strftime("%H:%M:%S")

    auto_off = cfg.get("auto_off_seconds", 0)
    if auto_off and auto_off > 0 and restore_list:
        if _off_timer:
            _off_timer.cancel()
        _off_timer = threading.Timer(auto_off, _restore_alarm_lights)
        _off_timer.daemon = True
        _off_timer.start()
        log.info("Restore in %ds für %d Gerät(e).", auto_off, len(restore_list))


def _restore_alarm_lights():
    """Stellt den Zustand vor dem Einsatz wieder her (aus→aus, an→Originalfarbe/-helligkeit)."""
    global _alarm_restore_list
    cfg = cfg_module.load()
    devices = {d["id"]: d for d in cfg.get("shelly_devices", [])}
    for entry in _alarm_restore_list:
        dev = devices.get(entry["dev_id"])
        if not dev:
            continue
        saved = entry["saved_state"]
        try:
            shelly.restore_state(dev, saved)
            was_on = saved.get("ison", False)
            log.info("Restore: %s → %s", dev["name"], "AN (Originalzustand)" if was_on else "AUS")
        except Exception as e:
            log.error("Fehler beim Restore von %s: %s", dev["name"], e)
    _alarm_restore_list = []
    state["lights_on"] = False


def _turn_off_all_lights():
    """Manuelles Ausschalten aller ausgewählten Lichter."""
    global _alarm_restore_list, _off_timer
    if _off_timer:
        _off_timer.cancel()
        _off_timer = None
    _alarm_restore_list = []
    cfg = cfg_module.load()
    devices = {d["id"]: d for d in cfg.get("shelly_devices", [])}
    for dev_id in cfg.get("selected_lights", []):
        dev = devices.get(dev_id)
        if not dev:
            continue
        try:
            shelly.turn_off(dev)
            log.info("Licht AUS (manuell): %s", dev["name"])
        except Exception as e:
            log.error("Fehler beim Ausschalten von %s: %s", dev["name"], e)
    state["lights_on"] = False


def poll_divera():
    cfg = cfg_module.load()
    key = cfg.get("divera_access_key", "").strip()
    if not key:
        return

    try:
        key_type = cfg.get("divera_key_type", "org")
        latest = divera.fetch_alarm(key, key_type)
        state["poll_error"] = None

        if not latest:
            return

        latest_id = latest.get("id")

        if latest_id and latest_id != cfg.get("last_alarm_id"):
            log.info("Neuer Einsatz: %s (ID %s)", latest.get("title", "?"), latest_id)
            state["last_alarm"] = latest
            state["alarm_history"].insert(0, {
                "id": latest_id,
                "title": latest.get("title", "—"),
                "text": latest.get("text", ""),
                "time": datetime.fromtimestamp(latest.get("date", 0)).strftime("%d.%m.%Y %H:%M:%S"),
            })
            state["alarm_history"] = state["alarm_history"][:20]

            cfg["last_alarm_id"] = latest_id
            cfg_module.save(cfg)

            _trigger_lights(latest, cfg)
        elif latest_id:
            # Einsatz bereits bekannt – nach Neustart State wiederherstellen ohne Lichter zu schalten
            if state["last_alarm"] is None:
                log.info("Bekannter Einsatz nach Neustart wiederhergestellt: %s (ID %s)", latest.get("title", "?"), latest_id)
                state["last_alarm"] = latest

    except Exception as e:
        state["poll_error"] = str(e)
        log.error("Fehler beim Abrufen von Divera: %s", e)


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    if request.method == "POST":
        cfg = cfg_module.load()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        stored_hash = cfg.get("password_hash", "")
        stored_user = cfg.get("username", "admin")
        if username == stored_user and stored_hash and check_password_hash(stored_hash, password):
            session["logged_in"] = True
            session["username"] = username
            log.info("Login erfolgreich: %s", username)
            return redirect(request.args.get("next") or url_for("index"))
        flash("Benutzername oder Passwort falsch.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    cfg = cfg_module.load()
    devices = cfg.get("shelly_devices", [])
    selected = set(cfg.get("selected_lights", []))
    return render_template(
        "index.html",
        cfg=cfg,
        devices=devices,
        selected=selected,
        state=state,
    )


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    cfg = cfg_module.load()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "password":
            new_user = request.form.get("new_username", "").strip()
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")
            if not new_user:
                flash("Benutzername darf nicht leer sein.", "danger")
            elif new_pw != confirm_pw:
                flash("Passwörter stimmen nicht überein.", "danger")
            elif len(new_pw) < 4:
                flash("Passwort muss mindestens 4 Zeichen lang sein.", "danger")
            else:
                cfg["username"] = new_user
                cfg["password_hash"] = generate_password_hash(new_pw)
                cfg_module.save(cfg)
                session["username"] = new_user
                flash("Zugangsdaten gespeichert.", "success")
        else:
            cfg["divera_access_key"] = request.form.get("access_key", "").strip()
            cfg["divera_key_type"] = request.form.get("key_type", "org")
            cfg["poll_interval"] = max(10, int(request.form.get("poll_interval", 30)))
            cfg["auto_off_seconds"] = max(0, int(request.form.get("auto_off_seconds", 0)))
            cfg_module.save(cfg)
            _restart_scheduler(cfg["poll_interval"])
            flash("Einstellungen gespeichert.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", cfg=cfg, state=state)


def _color_from_hex(hex_str):
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return {"red": r, "green": g, "blue": b, "white": 0}


@app.route("/devices", methods=["GET", "POST"])
@login_required
def devices():
    cfg = cfg_module.load()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        ip = request.form.get("ip", "").strip()
        model = request.form.get("model", "shelly1")
        channel = request.form.get("channel", 0)
        brightness = request.form.get("alarm_brightness", 100)
        color_hex = request.form.get("alarm_color_hex", "#ff0000")
        white = int(request.form.get("alarm_white", 0))
        color_temp = int(request.form.get("alarm_color_temp", 4000))
        if name and ip:
            alarm_color = _color_from_hex(color_hex)
            alarm_color["white"] = white
            cfg_module.add_device(cfg, name, ip, model, channel,
                                  alarm_brightness=brightness,
                                  alarm_color=alarm_color,
                                  alarm_color_temp=color_temp)
            flash(f"Gerät '{name}' hinzugefügt.", "success")
        else:
            flash("Name und IP sind Pflichtfelder.", "danger")
        return redirect(url_for("devices"))
    from shelly import MODELS
    return render_template("devices.html", cfg=cfg, state=state, shelly_models=MODELS)


@app.route("/devices/edit/<device_id>", methods=["POST"])
@login_required
def edit_device(device_id):
    cfg = cfg_module.load()
    brightness = int(request.form.get("alarm_brightness", 100))
    color_hex = request.form.get("alarm_color_hex", "#ff0000")
    white = int(request.form.get("alarm_white", 0))
    color_temp = int(request.form.get("alarm_color_temp", 4000))
    alarm_color = _color_from_hex(color_hex)
    alarm_color["white"] = white
    cfg_module.update_device(cfg, device_id,
                             alarm_brightness=brightness,
                             alarm_color=alarm_color,
                             alarm_color_temp=color_temp)
    flash("Einstellungen gespeichert.", "success")
    return redirect(url_for("devices"))


@app.route("/devices/delete/<device_id>")
@login_required
def delete_device(device_id):
    cfg = cfg_module.load()
    cfg_module.remove_device(cfg, device_id)
    flash("Gerät entfernt.", "success")
    return redirect(url_for("devices"))


@app.route("/devices/test/<device_id>")
@login_required
def test_device(device_id):
    cfg = cfg_module.load()
    dev = cfg_module.get_device(cfg, device_id)
    if not dev:
        return jsonify({"ok": False, "error": "Gerät nicht gefunden"})
    result = shelly.test_device(dev)
    return jsonify(result)


@app.route("/lights/select", methods=["POST"])
@login_required
def select_lights():
    cfg = cfg_module.load()
    cfg["selected_lights"] = request.form.getlist("lights")
    cfg_module.save(cfg)
    flash("Lichtauswahl gespeichert.", "success")
    return redirect(url_for("index"))


@app.route("/lights/on")
@login_required
def manual_on():
    cfg = cfg_module.load()
    _trigger_lights({"title": "Manuell", "text": ""}, cfg)
    flash("Lichter manuell eingeschaltet.", "success")
    return redirect(url_for("index"))


@app.route("/lights/off")
@login_required
def manual_off():
    _turn_off_all_lights()
    flash("Lichter ausgeschaltet.", "success")
    return redirect(url_for("index"))


@app.route("/api/divera-debug")
@login_required
def api_divera_debug():
    cfg = cfg_module.load()
    key = cfg.get("divera_access_key", "").strip()
    if not key:
        return jsonify({"ok": False, "error": "Kein API-Key konfiguriert."})
    key_type = cfg.get("divera_key_type", "org")
    endpoint = (
        "https://www.divera247.com/api/v2/pull/all"
        if key_type == "personal"
        else "https://www.divera247.com/api/last-alarm"
    )
    try:
        import requests as req
        resp = req.get(endpoint, params={"accesskey": key}, timeout=10)
        return jsonify({"ok": True, "status_code": resp.status_code, "data": resp.json(), "key_type": key_type})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/state")
@login_required
def api_state():
    cfg = cfg_module.load()
    return jsonify({
        "lights_on": state["lights_on"],
        "lights_on_since": state["lights_on_since"],
        "last_alarm": state["last_alarm"],
        "poll_error": state["poll_error"],
        "last_alarm_id": cfg.get("last_alarm_id"),
    })


# ─── Update ────────────────────────────────────────────────────────────────────

def _git(*args):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=os.path.dirname(__file__),
        capture_output=True, text=True
    )
    return result.stdout.strip(), result.returncode


@app.route("/update/check")
@login_required
def update_check():
    local, rc = _git("rev-parse", "HEAD")
    if rc != 0:
        return jsonify({"ok": False, "error": "Kein Git-Repository gefunden."})

    _, rc = _git("fetch", "origin", "--quiet")
    if rc != 0:
        return jsonify({"ok": False, "error": "Fetch fehlgeschlagen. Netzwerk prüfen."})

    remote, _ = _git("rev-parse", "origin/master")
    behind, _ = _git("rev-list", "--count", f"HEAD..origin/master")

    return jsonify({
        "ok": True,
        "local":   local[:7],
        "remote":  remote[:7],
        "up_to_date": local == remote,
        "commits_behind": int(behind or 0),
    })


@app.route("/update/apply", methods=["POST"])
@login_required
def update_apply():
    out, rc = _git("pull", "origin", "master")
    if rc != 0:
        return jsonify({"ok": False, "error": out or "git pull fehlgeschlagen."})

    log.info("Update eingespielt: %s — starte neu...", out)
    threading.Timer(1.5, _restart_process).start()
    return jsonify({"ok": True, "output": out})


def _restart_process():
    log.info("Server-Neustart nach Update...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ─── Scheduler ─────────────────────────────────────────────────────────────────

def _restart_scheduler(interval):
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(poll_divera, "interval", seconds=interval, id="divera_poll")
    _scheduler.start()
    log.info("Scheduler gestartet, Intervall: %ds", interval)


if __name__ == "__main__":
    cfg = cfg_module.load()
    if not cfg.get("password_hash"):
        cfg["username"] = "admin"
        cfg["password_hash"] = generate_password_hash("admin")
        cfg_module.save(cfg)
        log.info("Standardpasswort gesetzt: admin / admin — bitte in den Einstellungen ändern!")
    _restart_scheduler(cfg.get("poll_interval", 30))
    app.run(host="0.0.0.0", port=5000, debug=False)
