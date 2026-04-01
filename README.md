# Random MTG Creature

Eine Browser-App, die eine zufällige Magic: The Gathering Kreaturenkarte anzeigt — inklusive Vorschau und Druck auf einem 58mm-Thermodrucker.

## Features

- **Zufällige Kreatur** per Mana Value (umgewandelte Manakosten) abrufen
- **Editionsfilter**: Alle Editionen, Standard, Pioneer, Modern, Pauper oder Premodern
- **Un-Sets**: Ohne, mit oder ausschließlich Un-Set-Karten
- **Kartenbild** (Original von Scryfall) und **Thermodrucker-Vorschau** nebeneinander
- **Thermodruck**: Direkt auf einen 58mm-ESC/POS-Thermodrucker drucken (384 Dots/Zeile, Floyd-Steinberg-Dithering)

## Voraussetzungen

- Ein moderner Webbrowser
- Python 3 (für den Print-Server, nur zum Drucken nötig)
- Ein 58mm-Thermodrucker an `/dev/usb/lp1` (nur zum Drucken nötig)

## Starten

### Nur die Web-App

Die Datei `index.html` direkt im Browser öffnen — es wird kein Server und kein Build-Step benötigt.

### Mit Thermodrucker

```bash
./start.sh
```

Das Skript startet den Print-Server (`print-server.py`) mit Root-Rechten und öffnet die App im Browser. Der Print-Server läuft auf `http://127.0.0.1:8432` und wird beim Beenden des Skripts (z.B. Strg+C) automatisch gestoppt.

## Benutzung

1. **Mana Value** eingeben (0–20)
2. Optional: Edition und Un-Set-Filter wählen
3. **Go!** klicken — es erscheinen das Kartenbild und die Thermodrucker-Vorschau
4. **Drucken** klicken, um die Karte auf dem Thermodrucker auszugeben (Print-Server muss laufen)

## Projektstruktur

| Datei | Beschreibung |
|---|---|
| `index.html` | Komplette App (HTML + CSS + JS in einer Datei) |
| `print-server.py` | Lokaler HTTP-Server, der PNG-Daten als ESC/POS an den Drucker sendet |
| `start.sh` | Startet Print-Server und öffnet die App im Browser |

## API

Die App nutzt die [Scryfall API](https://scryfall.com/docs/api) — öffentlich, kein API-Key nötig.
