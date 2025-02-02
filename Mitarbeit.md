---
tags:
- Howto
---

# Mitarbeit

Folgende technische Konfigurationen sind notwendig, damit Sie an der Wissensdatenbank mitarbeiten können.

## Initialisierung

Arbeitsschritte:
1. Erstellen Sie einen Account auf <https://github.com/>
2. Werden Sie Mitglied bei <https://github.com/scienceuli/> (optional)
3. Installieren Sie <https://obsidian.md/>
4. Installieren Sie <https://git-scm.com/>
5. Verwenden Sie Ihren bestehenden SSH-Schlüssel oder erstellen Sie ein neues SSH-Schlüsselpaar <https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent>
6. Forken Sie das *vfllwiki* Repository (optional)
7. Klonen Sie das *vfllwiki* Repository

```bash
git clone git@github.com:scienceuli/vfllwiki.git
```

8. Öffnen Sie den Ordner mit Obsidian.

Beachten Sie dabei die [[Richtlinie - Obsidian]].

## Synchronisierung

Der Obsidian Vault und das Git Repository werden mit dem Obisidian Git Plugin synchronisiert.

## Publizierung

Die Inhalte, die auf GitHub unter <https://github.com/scienceuli/vfllwiki> vorhanden sind, werden in Zukunft automatisch von [[Vercel]] unter <https://wikivfll.de> publiziert.

Damit man die Inhalte auf GitHub stellen kann, benötigt man:
* einen GitHub-Account
* Zugriff auf die Github-Account <https://github.com/Mint-System>
* einen [[Git#Client|Git Client]]

## Tags

Siehe [[Tags]] für Details.

## Metadaten

Alle Wiki-Einträge können im Frontmatter Metadaten enthalten. Folgende Metadaten sind definiert:

* `tags`: Auswahl aus der Liste von [[Tags]].
* `responsible`: Person oder Rolle Verantwortlich für den Prozess.
* `responsibilities`: Bereiche in der Verwantwortung der Person.
* `title`: Alternativer Name für den Artikel.