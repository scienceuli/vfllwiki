
# Wagtail CMS – Kurzüberblick

**Website:** [wagtail.org](https://wagtail.org) · **Doku:** [docs.wagtail.org](https://docs.wagtail.org/en/stable/) · **Code:** [github.com/wagtail/wagtail](https://github.com/wagtail/wagtail)

## Was ist Wagtail?

Wagtail ist ein freies Open-Source-Content-Management-System auf Basis von **Python** und **Django**. Es wurde von der britischen Agentur **Torchbox** entwickelt, die das Projekt bis heute trägt, und wird seit 2014 von einer großen Community (über 1000 Beitragende) weiterentwickelt. Lizenzgebühren fallen keine an.

Installation:

```bash
pip install wagtail
```

## Kernmerkmale

- **StreamField** – Inhalte werden aus frei kombinierbaren Blöcken (Text, Bild, Zitat, eigene Blocktypen …) zusammengesetzt. Redakteure gestalten Seiten flexibel, Entwickler definieren die Blöcke in Python.
- **Seitenmodelle in Python** – Seitentypen sind Django-Modelle; Datenbankschema und Admin-Oberfläche entstehen aus derselben Klassendefinition.
- **Alles, was Django kann** – Volle Django-Integration: eigene Apps, ORM, Templates, Middleware.
- **Headless oder klassisch** – Ausspielung über Django-Templates oder per API an Frontends wie React/Next.js.
- **Mehrsprachigkeit** – über das Zusatzpaket *Wagtail Localize*.
- **Multisite** – mehrere Websites aus einer Installation verwalten.
- **Redaktions-Features** – Workflows, Revisionen, Vorschau, Bild-/Dokumentenverwaltung mit Fokuspunkten, Personalisierung, seit 7.3 auch **Autosave**.
- **Barrierefreiheit & Nachhaltigkeit** – ausdrückliche Schwerpunkte des Projekts, inkl. eingebautem Accessibility-Checker.

## Aktueller Stand (Oktober 2026)

- **Wagtail 8.0** ist am **25. August 2026** erschienen. Neu ist u. a. eine **v3-REST-API (Preview)**, die auch Schreibzugriffe erlaubt und ein OpenAPI-Schema bereitstellt – gedacht für Automatisierung und KI-Agenten. Die API gilt noch als instabil.
- **KI-Ansatz:** „Ein CMS mit KI, kein KI-CMS“ – KI-Funktionen sind standardmäßig aus; das separate Paket **Wagtail AI** ist optional.
- Für Entwickler gibt es inzwischen offizielle **Agent Skills** (z. B. für Upgrades).

Die Vfll-Website nutzt noch Wagtail 3, ein Upgrade ist in Vorbereitung.

## Wer setzt Wagtail ein?

Laut wagtail.org u. a. NASA, Google, der britische NHS, Mozilla, MIT und Oxfam. Typische Einsatzfelder: öffentliche Verwaltung, Hochschulen und Forschung, Museen und Kultureinrichtungen, Non-Profits, Unternehmen.

## Stärken & Grenzen

| Stärken | Zu bedenken |
|---|---|
| Sauberes, entwicklerfreundliches Python/Django-Fundament | Setzt Python-/Django-Know-how voraus – kein „Klick-CMS“ |
| Sehr gute Redaktionsoberfläche (StreamField) | Kleineres Plugin-Ökosystem als z. B. WordPress |
| Kein Vendor-Lock-in, keine Lizenzkosten | Hosting/Betrieb in Eigenregie (Python-Stack, DB, Medien) |
| Headless und klassisch nutzbar | Neue v3-API noch nicht stabil |

## Einstieg

- [Get started](https://wagtail.org/get-started/) – lauffähige Seite in ca. 15 Minuten (Starter-Kit)
- [Tutorial](https://docs.wagtail.org/en/stable/getting_started/tutorial.html) – erste eigene Website
- [Benutzerhandbuch für Redakteure](https://guide.wagtail.org/)
- [Pakete/Erweiterungen](https://wagtail.org/packages/)

## Arbeiten mit Wagtail

Siehe [[Prozesse Wagtail]].


