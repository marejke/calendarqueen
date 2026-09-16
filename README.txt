Calendar Queen — Website (Celeste + Coral)
==========================================

Struktur
--------
index.html                 Startseite (Home)
feeds.html                 Feeds-Übersicht mit Filter & Suche (funktioniert)
feed-detail.html           Beispiel-Detailseite (Erstes Babyjahr)
impressum.html             Rechtsseite — PLATZHALTER
datenschutz.html           Rechtsseite — PLATZHALTER
nutzungsbedingungen.html   Rechtsseite — PLATZHALTER
assets/style.css           Gemeinsames Stylesheet (alle Seiten)
assets/logo.png            Logo (Lockup mit Schriftzug, transparent)

So startest du
--------------
Einfach index.html im Browser öffnen. Alle Seiten sind untereinander
verlinkt und laufen ohne Server (statisches HTML/CSS/JS). Die Schriften
(Fraunces + Figtree) werden von Google Fonts geladen — dafür ist beim
Öffnen eine Internetverbindung nötig.

Farben / Design
---------------
- Celeste-Blau  #6cace4  (zweite Farbe, Akzente/Links)
- Coral         #fc5233  (aus dem Logo-Schriftzug; Icons, Badges, CTA)
- Indigo        #2b2b4a  (dunkler Anker: Buttons, Footer)
Alle Farbwerte sind zentral in assets/style.css als CSS-Variablen (:root)
definiert und lassen sich dort an einer Stelle ändern.

Noch zu tun (Platzhalter / Demo)
--------------------------------
- Impressum / Datenschutz / Nutzungsbedingungen: Mustertexte — bitte durch
  echte, rechtlich geprüfte Angaben ersetzen.
- Abo-Buttons (Apple/Google/Outlook) und der webcal-Link auf der
  Detailseite sind Platzhalter (href="#") und müssen mit euren echten
  Feed-URLs verknüpft werden.
- Feed-Beschreibungen und die Beispiel-Termine sind Demo-Inhalte
  (bis auf den Babyjahr-Text aus eurer Vorlage).
