# Divera247 → SmartHome Schnittstelle

Verbindet **Divera 247** (Einsatzleitsystem für Feuerwehr & Rettungsdienste) mit **Shelly**-Geräten. Wenn ein neuer Einsatz eingeht, werden automatisch ausgewählte Lichter eingeschaltet.

> **Hinweis:** Dieses Projekt ist ein unabhängiges Community-Projekt und steht in keiner Verbindung zu Divera GmbH oder Shelly (Allterco Robotics). Alle verwendeten Markennamen sind Eigentum ihrer jeweiligen Inhaber. Die Nutzung der Divera-API erfolgt ausschließlich über den offiziellen, öffentlich dokumentierten Zugangscode des eigenen Accounts.

## Features

- Automatisches Polling der Divera 247 API auf neue Einsätze
- Weboberfläche zur Verwaltung von Shelly-Geräten (Hinzufügen, Testen, Löschen, Bearbeiten)
- Auswahl welche Geräte bei einem Einsatz gesteuert werden
- **Zustandsspeicherung**: Vor dem Einsatz wird Farbe, Helligkeit und Farbtemperatur jedes Geräts gespeichert und danach wiederhergestellt
- Optionaler Auto-Off-Timer — Geräte die vorher **aus** waren werden ausgeschaltet, Geräte die **an** waren kehren zu ihrem Originalzustand zurück
- Manuelle Steuerung (Ein/Aus) über die Weboberfläche
- Einsatz-Verlauf der aktuellen Sitzung
- **Login-Schutz**: Passwortgeschützte Weboberfläche, Zugangsdaten in den Einstellungen änderbar
- **In-App-Updates**: Per Knopfdruck auf neue Version prüfen und aktualisieren (inkl. automatischem Serverneustart)

## Unterstützte Geräte

**Shelly Generation 1** (lokale HTTP-API):

| Modell | Typ | Steuerung |
|---|---|---|
| Shelly 1 / 1PM | Relay | Ein/Aus |
| Shelly 2 / 2.5 | Relay (2 Kanäle) | Ein/Aus |
| Shelly 4Pro | Relay (4 Kanäle) | Ein/Aus |
| Shelly Plug / Plug S | Relay | Ein/Aus |
| Shelly UNI | Relay (2 Kanäle) | Ein/Aus |
| Shelly Dimmer 1 / 2 | Dimmer | Ein/Aus + Helligkeit |
| Shelly Vintage | Dimmer | Ein/Aus + Helligkeit |
| Shelly Duo | Weißlicht | Ein/Aus + Helligkeit + Farbtemperatur (3000–6500 K) |
| Shelly Bulb | RGB | Ein/Aus + Farbe (RGBW) + Helligkeit |
| Shelly RGBW2 (Farbmodus) | RGB | Ein/Aus + Farbe (RGBW) + Helligkeit |
| Shelly RGBW2 (Weißkanal) | White (4 Kanäle) | Ein/Aus + Helligkeit |

## Voraussetzungen

- Python 3.10 oder neuer → [python.org/downloads](https://www.python.org/downloads/)
  - Bei der Installation **"Add Python to PATH"** ankreuzen!
- Git → [git-scm.com](https://git-scm.com/) (für die Update-Funktion)
- Shelly-Gerät im gleichen lokalen Netzwerk
- Divera 247 API-Zugangscode

## Installation & Start

### Windows

```bat
git clone https://github.com/drunkler/Divera247-SmartHome.git
cd Divera247-SmartHome
```

Dann `start.bat` doppelklicken — richtet automatisch eine virtuelle Python-Umgebung ein, installiert alle Abhängigkeiten und öffnet `http://localhost:5000` im Browser.

### Linux (empfohlen für Dauerbetrieb, z.B. Raspberry Pi)

```bash
git clone https://github.com/drunkler/Divera247-SmartHome.git
cd Divera247-SmartHome
sudo bash install.sh
```

Das Skript erledigt automatisch:
- Python 3 & Git installieren (apt / dnf / pacman)
- Virtuelle Python-Umgebung anlegen & Pakete installieren
- Systemd-Service einrichten (Autostart beim Booten)
- Port 5000 in der Firewall freigeben (ufw / firewalld)
- Service direkt starten

Nützliche Befehle danach:

```bash
sudo systemctl status divera-shelly    # Status prüfen
sudo systemctl restart divera-shelly   # Neustart
sudo journalctl -u divera-shelly -f    # Live-Log
```

### Windows

```bat
git clone https://github.com/drunkler/Divera247-SmartHome.git
cd Divera247-SmartHome
```

Dann `start.bat` doppelklicken — richtet automatisch eine virtuelle Python-Umgebung ein, installiert alle Abhängigkeiten und öffnet `http://localhost:5000` im Browser.

### Manuell (alle Plattformen)

```bash
git clone https://github.com/drunkler/Divera247-SmartHome.git
cd Divera247-SmartHome
pip install -r requirements.txt
python app.py
```

Dann im Browser: [http://localhost:5000](http://localhost:5000)

## Konfiguration

### Erster Start

Beim ersten Start wird automatisch ein Standard-Login angelegt:

| | |
|---|---|
| Benutzername | `admin` |
| Passwort | `admin` |

**Bitte sofort unter Einstellungen → Zugangsdaten ändern!**

### Einrichtung

1. **Divera API-Key eintragen**: Einstellungen → Access-Key  
   *(In Divera 247: **Verwaltung → Einstellungen → Schnittstellen → API** — dies ist der Organisations-Key, nicht der persönliche Account-Key)*

2. **Shelly-Geräte hinzufügen**: Geräte → Modell, IP-Adresse, Kanal und gewünschte Alarm-Einstellungen (Farbe, Helligkeit, Farbtemperatur) eintragen

3. **Lichter auswählen**: Im Dashboard Häkchen bei den Geräten setzen, die bei einem Einsatz gesteuert werden sollen

4. **Optional — Auto-Off**: In den Einstellungen eine Zeit in Sekunden eintragen, nach der der Originalzustand wiederhergestellt wird (`0` = dauerhaft an)

### Zustandswiederherstellung

Wenn der Auto-Off-Timer aktiv ist, wird beim Einsatz der aktuelle Zustand jedes Geräts gespeichert:

- Gerät war **aus** → wird nach dem Timer ausgeschaltet
- Gerät war **an** → kehrt nach dem Timer zu Originalfarbe, -helligkeit und -farbtemperatur zurück

## Updates

Unter **Einstellungen → Software-Update** kann direkt in der Oberfläche nach neuen Versionen gesucht und aktualisiert werden. Der Server startet nach dem Update automatisch neu.

## Projektstruktur

```
├── app.py          # Flask-Server, Routen, Polling-Loop, Update-Logik
├── config.py       # Konfigurationsverwaltung (config.json)
├── divera.py       # Divera 247 API-Client
├── shelly.py       # Shelly Gen1 HTTP-Steuerung (alle Typen)
├── templates/      # HTML-Oberfläche (Bootstrap 5)
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── devices.html
│   └── settings.html
├── start.bat       # Windows-Starter mit Auto-Setup
└── requirements.txt
```

## Interne API-Endpunkte

| Endpunkt | Beschreibung |
|---|---|
| `GET /` | Dashboard |
| `GET /devices` | Geräteverwaltung |
| `GET /settings` | Einstellungen |
| `GET /login` · `GET /logout` | Authentifizierung |
| `GET /lights/on` | Alle ausgewählten Lichter einschalten |
| `GET /lights/off` | Alle Lichter ausschalten |
| `POST /lights/select` | Lichtauswahl speichern |
| `GET /api/state` | Aktueller Status als JSON |
| `GET /devices/test/<id>` | Einzelnes Gerät testen |
| `POST /devices/edit/<id>` | Gerät bearbeiten |
| `GET /update/check` | Auf neue Version prüfen |
| `POST /update/apply` | Update einspielen + Neustart |

## Lizenz

MIT — siehe [LICENSE](LICENSE)

## Haftungsausschluss

Dieses Projekt ist **nicht offiziell** und steht in keiner Verbindung zu:
- **Divera GmbH** (Hersteller von Divera 247)
- **Allterco Robotics** (Hersteller von Shelly)

Die Nutzung erfolgt auf eigene Verantwortung. Dieses Projekt verwendet ausschließlich öffentlich dokumentierte, offizielle APIs über den eigenen Account-Zugangscode. Es werden keine Sicherheitsmechanismen umgangen.
