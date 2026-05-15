# Divera247 → SmartHome Schnittstelle

Verbindet **Divera 247** (Einsatzleitsystem für Feuerwehr & Rettungsdienste) mit **Shelly**-Geräten. Wenn ein neuer Einsatz eingeht, werden automatisch ausgewählte Lichter eingeschaltet.

## Features

- Automatisches Polling der Divera 247 API auf neue Einsätze
- Weboberfläche zur Verwaltung von Shelly-Geräten (Hinzufügen, Testen, Löschen)
- Auswahl welche Lichter bei einem Einsatz angehen
- Optionaler Auto-Off-Timer (Lichter nach X Sekunden automatisch ausschalten)
- Manuelle Steuerung (Ein/Aus) über die Weboberfläche
- Einsatz-Verlauf der aktuellen Sitzung

## Unterstützte Geräte

**Shelly Generation 1** (HTTP-API):
- Shelly 1, 1PM
- Shelly 2, 2.5
- Shelly Plug, Plug S
- Shelly RGBW2, Bulb, Duo

## Voraussetzungen

- Python 3.10 oder neuer → [python.org/downloads](https://www.python.org/downloads/)
  - Bei der Installation **"Add Python to PATH"** ankreuzen!
- Shelly-Gerät im gleichen lokalen Netzwerk
- Divera 247 API-Zugangscode

## Installation & Start

### Windows

Doppelklick auf `start.bat` — die Anwendung richtet beim ersten Start automatisch eine virtuelle Python-Umgebung ein und öffnet `http://localhost:5000` im Browser.

### Manuell (Windows/Linux/macOS)

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Server starten
python app.py
```

Dann im Browser: [http://localhost:5000](http://localhost:5000)

## Konfiguration

1. **Divera API-Key eintragen**: Einstellungen → Access-Key  
   *(In Divera 247: Verwaltung → Schnittstellen → API)*

2. **Shelly-Geräte hinzufügen**: Geräte → IP-Adresse, Name, Typ und Kanal eintragen

3. **Lichter auswählen**: Im Dashboard Häkchen bei den Geräten setzen, die bei einem Einsatz angehen sollen

4. **Speichern** — fertig!

## Projektstruktur

```
├── app.py          # Flask-Server, Polling-Loop, Routen
├── config.py       # Konfigurationsverwaltung (config.json)
├── divera.py       # Divera 247 API-Client
├── shelly.py       # Shelly Gen1 HTTP-Steuerung
├── templates/      # HTML-Oberfläche (Bootstrap 5)
└── start.bat       # Windows-Starter
```

## API-Endpunkte (intern)

| Endpunkt | Beschreibung |
|---|---|
| `GET /` | Dashboard |
| `GET /devices` | Geräteverwaltung |
| `GET /settings` | Einstellungen |
| `GET /lights/on` | Alle ausgewählten Lichter einschalten |
| `GET /lights/off` | Alle Lichter ausschalten |
| `GET /api/state` | Aktueller Status als JSON |
| `GET /devices/test/<id>` | Einzelnes Gerät testen |

## Lizenz

MIT
