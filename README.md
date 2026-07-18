# Calendar Queen 🗓️

**calendarqueen.de** – Kuratierte Kalender-Feeds für dein Leben.

## Repository-Struktur

```
calendarqueen/
├── index.html              # Startseite
├── feeds.html              # Feed-Übersicht
├── feed-babyjahr.html      # Feed-Detailseite (Beispiel)
├── impressum.html
├── datenschutz.html
├── nutzungsbedingungen.html
├── css/style.css
├── js/main.js
├── assets/logo.png
├── feeds/                  # ICS-Kalender-Feeds
│   ├── mondphasen.ics
│   ├── berlin-events.ics
│   ├── krauter-berlin.ics
│   └── ...
├── scripts/
│   └── update_feeds.py     # Feed-Update-Agent
└── .github/
    └── workflows/
        └── daily-feed-update.yml
```

## Feed-Update-Agent einrichten

Der Agent läuft täglich um 7:00 Uhr (Berlin) und erstellt automatisch einen Pull Request mit aktualisierten Feeds.

### 1. GitHub Secret setzen

Im GitHub-Repo unter **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Wert |
|------|------|
| `ANTHROPIC_API_KEY` | Dein Anthropic API Key (https://console.anthropic.com) |

### 2. GitHub Actions aktivieren

Actions sind nach dem ersten Push automatisch aktiv. Workflow-Datei: `.github/workflows/daily-feed-update.yml`

### 3. Workflow manuell testen

Unter **Actions → Daily Feed Update → Run workflow** → optional einen Feed-Namen eingeben (z.B. `mondphasen`) oder leer lassen für alle Feeds.

### 4. Pull Requests prüfen und mergen

Der Agent erstellt täglich (wenn Änderungen vorhanden) einen PR mit dem Titel `📅 Feed-Update YYYY-MM-DD`. Einfach prüfen und mergen.

## Hosting auf GitHub Pages

### GitHub Pages aktivieren

1. **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, Folder: `/ (root)`
4. **Save**

Die Seite ist dann erreichbar unter: `https://marejke.github.io/calendarqueen/`

### Eigene Domain (calendarqueen.de)

1. Bei deinem DNS-Anbieter: `CNAME calendarqueen.de → marejke.github.io`
2. Unter **Settings → Pages → Custom domain**: `calendarqueen.de` eintragen
3. "Enforce HTTPS" aktivieren

## Feed-URLs für Nutzer

Feeds sind als Kalender-Abonnements abrufbar:

```
https://calendarqueen.de/feeds/mondphasen.ics
https://calendarqueen.de/feeds/berlin-events.ics
# etc.
```

Für Webcal-Links (direkt in iOS/macOS Kalender öffnen):
```
webcal://calendarqueen.de/feeds/mondphasen.ics
```

## Lokale Entwicklung

```bash
# Einfacher HTTP-Server
python3 -m http.server 8000
# Dann: http://localhost:8000
```

## Vor dem Go-Live

- [ ] `impressum.html`: Platzhalter `[...]` mit echten Betreiberdaten ersetzen
- [ ] `datenschutz.html`: Hosting-Anbieter eintragen
- [ ] Domain calendarqueen.de bei GitHub Pages eintragen
- [ ] `ANTHROPIC_API_KEY` Secret bei GitHub setzen
- [ ] Feed-URLs in allen HTML-Dateien prüfen (sollten relativ sein)
- [ ] Einen manuellen Workflow-Run testen

## Technologie

- Reines HTML/CSS/JS – kein Framework, kein Build-Step
- ICS-Feeds (RFC 5545) für maximale Kalender-Kompatibilität  
- GitHub Actions für automatische Feed-Updates
- Claude API (Sonnet 4.6) als Prüf- und Update-Agent
- GitHub Pages für kostenfreies Hosting

## Accessibility

Die Website erfüllt WCAG 2.1 AA und die EU-Richtlinie 2016/2102:
- Skip-Link, ARIA-Labels, Semantic HTML
- Keyboard-Navigation vollständig
- Screenreader-kompatibel
- `forced-colors` für Windows High Contrast
- `prefers-reduced-motion` berücksichtigt
