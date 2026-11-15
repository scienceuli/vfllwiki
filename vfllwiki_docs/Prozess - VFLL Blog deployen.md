# Prozess - VFLL Blog deployen

Der VFLL-Blog (WordPress, https://lektorenverband.de) läuft seit Oktober 2026 als Docker-Container auf dem Server **gauss** (Netcup, Debian 13, ARM). Daneben läuft eine Staging-Kopie unter https://staging.blog.vfll.de. Deployt wird mit [[Ansible]] aus dem Repo https://github.com/scienceuli/Ansible-Build.

| | Produktion | Staging |
|---|---|---|
| Inventory-Host | `gauss_blog` | `gauss_blog_staging` |
| Domain | https://lektorenverband.de (`www.lektorenverband.de` → 301) | https://staging.blog.vfll.de (Basic Auth, User `vfll`) |
| Container | `wordpress01`, `gauss-mysql01` | `wordpress-staging01`, `gauss-staging-mysql01` |
| Docker-Volumes | `wordpress_data01`, `mysql_data01` | `wordpress_staging_data01`, `mysql_staging_data01` |
| Konfiguration | `inventories/host_vars/gauss_blog/` | `inventories/host_vars/gauss_blog_staging/` |
| restic-Backup | ja | nein |

Der Docker-Host selbst ist der Inventory-Host `gauss`: nginx (`nginx01`), certbot, Basic Auth und die restic-Backups, konfiguriert in `inventories/host_vars/gauss/vars.yml`.

## Was wird  deployt?

Anders als z.B. beim [[Prozess - VFLLCMS deployen|VFLLCMS]] wird hier kein eigener Code gebaut:

- **Image:** das offizielle `wordpress:php8.3-apache`. Das Tag legt nur den **PHP-Zweig** fest. Bei jedem Deploy wird das Image neu gepullt; ist ein neuerer Build da (PHP-Sicherheitsupdates), wird der Container neu erstellt – ein paar Sekunden Ausfall.
- **WordPress-Core, Plugins, Uploads** liegen im Volume (`/var/www/html`) und werden **im WordPress-Admin** aktualisiert, nicht über Ansible. Ein Deploy fasst sie nicht an.
- **Child-Theme `twentytwelve-child`** (VFLL-Header, Logo, Farben, Mobil-Anpassungen): Die Masterkopie liegt im Repo unter `playbooks/vfll_wordpress/themes/twentytwelve-child/`. Jeder Deploy kopiert sie ins Volume. Das Parent-Theme Twenty Twelve aktualisiert sich wie der Core selbst.
- **Datenbank:** `mysql:8.4` im Container `gauss-mysql01`.

## Grundregeln

- Einmalig vorher: Repo, `inventories/`, `ansible.cfg` und `.vault-pass` einrichten, siehe [[Prozess - Ansible-Build einrichten]].
- Alle Befehle **im Repo-Root** `Ansible-Build` ausführen (dort liegen `ansible.cfg` und `.vault-pass`).
- Immer mit `-l` auf **eine Instanz** einschränken (`gauss_blog` oder `gauss_blog_staging`). nginx/certbot laufen getrennt über `playbooks/proxy.yml -l gauss`.
- **Zuerst Staging, dann Produktion.**
- `task play` ist ein Wrapper für `ansible-playbook`. Ohne aktivierte venv geht stattdessen `uv run ansible-playbook ...`.

## Normalfall: Container aktualisieren (neues Image, geänderte Konfiguration)

1. **Staging:**
   ```
   task play -i inventories playbooks/wordpress.yml -l gauss_blog_staging
   ```
2. https://staging.blog.vfll.de prüfen (Startseite, ein Beitrag, Login).
3. **Produktion:**
   ```
   task play -i inventories playbooks/wordpress.yml -l gauss_blog
   ```

Vorher sehen, ob etwas geändert würde (ändert nichts):
```
task play -i inventories playbooks/wordpress.yml -l gauss_blog --check --diff
```
`changed` bei „Start wordpress container wordpress01“ heißt: neues Image, der Container wird neu erstellt.

## Theme ändern

Das Child-Theme **nur im Repo ändern** – nicht im Theme-Editor von WordPress und nicht per FTP, der nächste Deploy würde das überschreiben.

1. Dateien in `playbooks/vfll_wordpress/themes/twentytwelve-child/` bearbeiten.
2. Nur das Theme auf Staging kopieren (kein Neustart):
   ```
   task play -i inventories playbooks/wordpress.yml -l gauss_blog_staging -t wordpress_themes
   ```
3. Auf Staging testen, auch auf dem Handy (Menü-Button, kein seitliches Scrollen).
4. Produktion:
   ```
   task play -i inventories playbooks/wordpress.yml -l gauss_blog -t wordpress_themes
   ```
5. Änderungen im Ansible-Build-Repo committen und pushen.

Im Repo gelöschte Dateien bleiben im Volume liegen – die auf gauss von Hand löschen.

## WordPress-, Plugin- und Theme-Updates

Updates kommen über den WordPress-Admin (Dashboard → Aktualisierungen). Größere Updates (WordPress-Hauptversion, Yoast SEO, Classic Editor …) zuerst auf Staging:

1. Staging mit dem aktuellen Stand der Produktion auffrischen (siehe unten).
2. Auf https://staging.blog.vfll.de im Admin aktualisieren und testen.
3. Wenn alles passt, dasselbe Update im Admin von https://lektorenverband.de.

## Staging mit Produktionsdaten auffrischen

```
task play -i inventories playbooks/vfll_wordpress/staging.yml
```

Das Playbook holt das **neueste nächtliche restic-Backup** der Produktion (direkt auf gauss, nichts geht über den eigenen Rechner), ersetzt Datenbank und Volume von Staging (nur `wp-config.php` von Staging bleibt), stellt die URLs auf staging.blog.vfll.de um und schützt die Kopie:

- ein Must-Use-Plugin blockiert **alle Mails** (`wp_mail()`),
- MailPoet wird deaktiviert (verschickt sonst über einen eigenen Weg),
- WP-Cron ist aus, Suchmaschinen sind ausgesperrt.

Die Produktion wird dabei nur aus dem Backup gelesen, nie angefasst. In der Ausgabe stehen unter „Snapshots used“ die Zeitpunkte der verwendeten Backups.

Achtung: Danach hat Staging das Theme der Produktion. Wer gerade Theme-Änderungen testet, kopiert sie mit `-t wordpress_themes` erneut nach Staging.

## Proxy, Zertifikate, Basic Auth

Geändert in `inventories/host_vars/gauss/vars.yml` (`nginx_proxies`, `htpasswd_credentials`):
```
task play -i inventories playbooks/proxy.yml -l gauss -t htpasswd,certbot,nginx
```
Das lädt nginx01 neu – betrifft Produktion **und** Staging. Neue Domains brauchen vorher den DNS-Eintrag auf gauss (Zertifikat per HTTP-Validierung).

## Konfiguration und Secrets

- `inventories/host_vars/gauss_blog*/vars.yml` bzw. `vault.yml`, danach normal deployen.
- Vault-Werte als nackten Wert verschlüsseln – **keine Anführungszeichen, kein `$`, kein `vault_xyz: `-Präfix im Wert**.
- **DB-Passwort ändern geht nicht nur über den Vault:** MySQL übernimmt `MYSQL_PASSWORD` nur beim allerersten Start mit leerem Volume. Erst in MySQL ändern (`ALTER USER 'wordpress'@'%' IDENTIFIED BY '...'`), dann im Vault, dann deployen.

## Kontrolle

```
curl -sI https://lektorenverband.de/ | head -1            # 200
curl -sI https://www.lektorenverband.de/ | grep -i location  # → https://lektorenverband.de/
curl -sI https://staging.blog.vfll.de/ | head -1          # 401 (Basic Auth)
```

Auf gauss (`task connect-host gauss` oder `ssh scienceuli@gauss.science-and-more.com`):
```
sudo docker ps                          # wordpress01, gauss-mysql01, nginx01 (+ Staging)
sudo docker logs --tail 50 wordpress01
sudo docker logs --tail 50 nginx01
```

PHP-Version prüfen:
```
task play -i inventories playbooks/php_patching/check.yml -l gauss
```

## Neuinstallation des Servers

1. Im Netcup-SCP Debian 13 installieren, alten Host-Key entfernen:
   ```
   ssh-keygen -R gauss.science-and-more.com
   ssh root@gauss.science-and-more.com true
   ```
2. Server-Grundlage:
   ```
   task play -i inventories playbooks/bootstrap.yml -l gauss
   task play -i inventories playbooks/setup.yml -l gauss -t docker_network
   task play -i inventories playbooks/setup.yml -l gauss --skip-tags restic
   ```
3. WordPress und MySQL (leer) – beide Instanzen:
   ```
   task play -i inventories playbooks/wordpress.yml -l gauss_blog
   task play -i inventories playbooks/wordpress.yml -l gauss_blog_staging
   ```
   Die Seite noch nicht aufrufen – eine leere Installation zeigt den Einrichtungsassistenten.
4. Daten zurückholen: [[Prozess - VFLL Blog wiederherstellen]], Abschnitt „Neuinstallation“.
5. Proxy und Backups:
   ```
   task play -i inventories playbooks/proxy.yml -l gauss
   task play -i inventories playbooks/setup.yml -l gauss -t restic
   ```
6. Staging befüllen: `playbooks/vfll_wordpress/staging.yml` (siehe oben).

## Typische Fehler

| Symptom | Ursache / Lösung |
|---|---|
| 502 Bad Gateway | `wordpress01` läuft nicht → `sudo docker ps -a`, `sudo docker logs wordpress01`. nginx01 läuft trotzdem weiter (Docker-DNS pro Anfrage). |
| „Fehler beim Aufbau einer Datenbankverbindung“ | `gauss-mysql01` läuft nicht, oder das Passwort im Vault passt nicht mehr zum MySQL-User (siehe „Konfiguration und Secrets“). |
| Theme-Änderung ist nach einem Deploy wieder weg | Sie wurde im WordPress-Editor statt im Repo gemacht → im Repo nachziehen. |
| Menü-Button auf dem Handy reagiert nicht | `header.php` des Child-Themes hat wieder `<h3 class="menu-toggle">` statt `<button>` → Theme aus dem Repo deployen. |
| certbot schlägt fehl | DNS der Domain zeigt nicht auf gauss, oder Port 80 ist zu. |
| Staging verschickt keine Mails | Gewollt (Must-Use-Plugin `staging-no-mail.php`). |
| `staging.yml`: „Deploy staging first“ | Die Staging-Container fehlen → zuerst `wordpress.yml -l gauss_blog_staging`. |

Weitere Doku im Ansible-Repo: `playbooks/vfll_wordpress/README.md` und `roles/wordpress/README.md`.

Siehe auch: [[Prozess - VFLL Blog wiederherstellen]]
