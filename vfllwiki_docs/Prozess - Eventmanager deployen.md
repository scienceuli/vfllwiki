# Prozess - Eventmanager deployen

Der VFLL Eventmanager (Veranstaltungskalender) läuft seit 2026-11-07 als Docker-Compose-Stack auf dem Server **bohr** (Netcup, Debian 13). Deployt wird mit [[Ansible]] aus dem Repo `~/Devel/Ansible-Build`.

| | Produktion | Staging |
|---|---|---|
| Inventory-Host | `bohr_eventmanager` | `bohr_eventmanager_staging` |
| Domain | https://veranstaltungskalender.vfll.de | https://staging.veranstaltungskalender.vfll.de (Basic Auth, User `vfll`) |
| Verzeichnis auf bohr | `/opt/docker/eventmanager` | `/opt/docker/eventmanager-staging` |
| Container | `eventmanager`, `eventmanager-db`, `eventmanager-mjml` | `eventmanager-staging`, `-staging-db`, `-staging-mjml` |
| Mail | SMTP | File-Backend (`data/sent_emails`) |
| restic-Backup | ja | nein |

Das Image wird auf bohr aus dem GitHub-Repo `eventmanager` gebaut (Branch über `eventmanager_git_version`, Standard `main`). **Erst pushen, dann deployen.**

## Grundregeln

- Einmalig vorher: Repo, `inventories/`, `ansible.cfg` und `.vault-pass` einrichten, siehe [[Prozess - Ansible-Build einrichten]].
- Alle Befehle **im Repo-Root** `~/Devel/Ansible-Build` ausführen (dort liegen `ansible.cfg` und `.vault-pass`).
- Immer mit `-l` einschränken: **Instanz plus Docker-Host `bohr`**. Der erste und der letzte Play (Docker-Netzwerk, nginx/certbot) laufen auf `bohr`.
- `task play` ist ein Wrapper für `ansible-playbook`. Ohne aktivierte venv geht stattdessen `uv run ansible-playbook ...`.

## Neue Version deployen (Normalfall)

1. Änderungen im eventmanager-Repo nach `main` pushen.
2. **Zuerst auf Staging** deployen und testen:
   ```
   task play -i inventories playbooks/eventmanager/playbook.yml \
     -l bohr,bohr_eventmanager_staging
   ```
3. Wenn alles passt, **Produktion** deployen:
   ```
   task play -i inventories playbooks/eventmanager/playbook.yml \
     -l bohr,bohr_eventmanager
   ```

Das Playbook holt den Code, baut das Image neu und startet den Stack. Der `web`-Container führt beim Start `migrate` und `collectstatic` aus – kurz nach dem Deploy kann es deshalb einige Sekunden lang einen 502 geben.

Einen Feature-Branch auf Staging deployen: siehe [[Prozess - Deploy feature branch]] (`-e eventmanager_git_version=<branch>`).

## Kontrolle

```
curl -I https://veranstaltungskalender.vfll.de            # 200
curl -I https://staging.veranstaltungskalender.vfll.de    # 401 (Basic Auth)
```

Logs auf bohr (`task connect-host bohr`):
```
cd /opt/docker/eventmanager        # bzw. eventmanager-staging
sudo docker compose ps
sudo docker compose logs -f web
```

## Sonderfälle

- **Nur die Proxy-Konfiguration hat sich geändert** (`inventories/host_vars/bohr/vars.yml`):
  ```
  task play -i inventories playbooks/eventmanager/playbook.yml -l bohr -t nginx
  ```
- **Konfiguration/Secrets ändern:** `inventories/host_vars/bohr_eventmanager*/vars.yml` bzw. `vault.yml`, danach normal deployen. Vault-Werte immer als nackten Wert verschlüsseln – **keine Anführungszeichen, kein `$`** (sonst bricht docker compose ab und zeigt den Wert in der Fehlermeldung).
- **Mail-Queue:** Mails bleiben in der Queue, bis ein Admin sie im Admin-Bereich verschickt (`eventmanager_mailqueue_autosend: false`). Vor einem Umstellen auf `true` den Rückstand prüfen – sonst geht jede ungesendete Mail sofort raus.

## Neuinstallation des Servers

Bei einem frisch installierten bohr ist die Reihenfolge wichtig (Details: `playbooks/eventmanager/HOW_TO_DEPLOY.md`):

1. SSH-Host-Key erneuern: `ssh-keygen -R bohr.science-and-more.com` (Achtung: `.com`, nicht `.de`).
2. Bootstrap als root: `task play -i inventories playbooks/bootstrap.yml -l bohr`
3. Server-Setup **ohne restic**: `task play -i inventories playbooks/setup.yml -l bohr --skip-tags restic`
4. Beide Instanzen **ohne nginx** deployen:
   ```
   task play -i inventories playbooks/eventmanager/playbook.yml \
     -l bohr,bohr_eventmanager,bohr_eventmanager_staging \
     --skip-tags htpasswd,certbot,nginx
   ```
5. Daten (Datenbank, `data/`) wiederherstellen: [[Prozess - Eventmanager wiederherstellen]].
6. Erst wenn **auch das VFLLCMS** deployt ist ([[Prozess - VFLLCMS deployen]]) – nginx bindet die Datenverzeichnisse aller Instanzen ein:
   ```
   task play -i inventories playbooks/eventmanager/playbook.yml -l bohr -t htpasswd,certbot,nginx
   ```
7. Backup einrichten: `task play -i inventories playbooks/setup.yml -l bohr -t restic`

## Typische Fehler

| Symptom | Ursache / Lösung |
|---|---|
| `Host key verification failed` | Server wurde neu installiert → Host-Key erneuern. |
| `unexpected character "'" in variable name` | Vault-Wert in Anführungszeichen → ohne neu verschlüsseln. |
| `password authentication failed for user "eventmanager"` | DB-Passwort in Postgres weicht von `POSTGRES_PASSWORD` ab → siehe Troubleshooting in `HOW_TO_DEPLOY.md`. |
| 502 Bad Gateway | `web` startet noch (Migrationen) oder ist abgestürzt → `sudo docker compose logs web`. |
| Rechnungs-Download schlägt fehl | Datei fehlt in `data/private/invoices/` oder gehört root → `sudo chown -R 1000:1000 data/private`. |

Weitere Doku im Ansible-Repo: `playbooks/eventmanager/README.md` und `HOW_TO_DEPLOY.md`.
