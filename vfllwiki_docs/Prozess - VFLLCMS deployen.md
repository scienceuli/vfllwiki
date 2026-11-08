# Prozess - VFLLCMS deployen

Das VFLL-CMS (Wagtail, Website vfll.de) läuft seit 2026-11-07 als Docker-Compose-Stack auf dem Server **bohr** (Netcup, Debian 13). Deployt wird mit [[Ansible]] aus dem Repo https://github.com/scienceuli/Ansible-Build.

| | Produktion | Staging |
|---|---|---|
| Inventory-Host | `bohr_vfllcms` | `bohr_vfllcms_staging` |
| Domain | https://vfll.de (`www.vfll.de` → 301) | https://staging.vfll.de (Basic Auth, User `vfll`) |
| Verzeichnis auf bohr | `/opt/docker/vfllcms` | `/opt/docker/vfllcms-staging` |
| Container | `vfllcms-web`, `vfllcms-db` | `vfllcms-staging-web`, `vfllcms-staging-db` |
| Cronjobs `get_events` (06:00), `get_blog` (00:00) | ja | nein |
| restic-Backup | ja | nein |

Das Image wird auf bohr aus dem **privaten** GitHub-Repo `scienceuli/vfllcms` gebaut (Branch über `vfllcms_git_version`, Standard `main`). Dafür braucht bohr den Deploy Key `/root/.ssh/vfllcms_deploy_key`, siehe [[Prozess - Deploy Key]]. **Erst pushen, dann deployen.**

## Grundregeln

- Einmalig vorher: Repo, `inventories/`, `ansible.cfg` und `.vault-pass` einrichten, siehe [[Prozess - Ansible-Build einrichten]].
- Alle Befehle **im Repo-Root** `Ansible-Build` ausführen (dort liegen `ansible.cfg` und `.vault-pass`).
- Immer mit `-l` einschränken: **Instanz plus Docker-Host `bohr`**. Der erste und der letzte Play (Docker-Netzwerk, nginx/certbot) laufen auf `bohr`.
- `task play` ist ein Wrapper für `ansible-playbook`. Ohne aktivierte venv geht stattdessen `uv run ansible-playbook ...`.

## Neue Version deployen (Normalfall)

1. Änderungen im vfllcms-Repo nach `main` pushen.
2. **Zuerst auf Staging** deployen und testen:
   ```
   task play -i inventories playbooks/vfllcms/playbook.yml \
     -l bohr,bohr_vfllcms_staging
   ```
3. Wenn alles passt, **Produktion** deployen:
   ```
   task play -i inventories playbooks/vfllcms/playbook.yml \
     -l bohr,bohr_vfllcms
   ```

Das Playbook holt den Code, baut das Image neu und startet den Stack. Der `web`-Container führt beim Start `migrate` und `collectstatic` aus – kurz nach dem Deploy kann es deshalb einige Sekunden lang einen 502 geben.

Einen Feature-Branch auf Staging deployen: wie in [[Prozess - Deploy feature branch]], nur mit `-e vfllcms_git_version=<branch>`.

## Kontrolle

```
curl -I https://vfll.de              # 200
curl -I https://www.vfll.de          # 301 → https://vfll.de/
curl -I https://staging.vfll.de      # 401 (Basic Auth)
```

Auf bohr (`task connect-host bohr`):
```
sudo docker logs vfllcms-web 2>&1 | grep "Listening at"
cd /opt/docker/vfllcms               # bzw. vfllcms-staging
sudo docker compose logs -f web
journalctl -t vfllcms-cron           # get_events / get_blog
```

## Sonderfälle

- **Staging mit Produktionsdaten auffrischen:** auf bohr einen Dump ziehen, auf den Mac kopieren und mit dem Playbook einspielen:
  ```
  # auf bohr
  sudo docker exec vfllcms-db pg_dump -Fc -U vfllcms vfllcms > ~/vfllcms.pgdump
  # auf dem Mac
  scp scienceuli@bohr.science-and-more.com:vfllcms.pgdump ~/Downloads/
  task play -i inventories playbooks/vfllcms/playbook.yml \
    -l bohr,bohr_vfllcms_staging --skip-tags htpasswd,certbot,nginx \
    -e vfllcms_restore_dump=$HOME/Downloads/vfllcms.pgdump
  ```
  Der Dump enthält keine Medien – die Bilder ggf. per rsync aus `/opt/docker/vfllcms/data/media/` nachziehen.
- **Nur die Proxy-Konfiguration hat sich geändert** (`inventories/host_vars/bohr/vars.yml`):
  ```
  task play -i inventories playbooks/vfllcms/playbook.yml -l bohr -t nginx
  ```
- **Konfiguration/Secrets ändern:** `inventories/host_vars/bohr_vfllcms*/vars.yml` bzw. `vault.yml`, danach normal deployen. Vault-Werte als nackten Wert verschlüsseln – **keine Anführungszeichen, kein `$`**. `vault_vfllcms_google_credentials` muss das vollständige JSON des Google-Service-Accounts sein.

## Neuinstallation des Servers

1. Server-Grundlage (Host-Key, `bootstrap.yml`, `setup.yml --skip-tags restic`): einmal pro Server, siehe [[Prozess - Eventmanager deployen]], Abschnitt „Neuinstallation“.
2. Deploy Key auf bohr erzeugen und bei GitHub eintragen: [[Prozess - Deploy Key]]. Den alten Key „bohr (ansible)“ bei GitHub löschen.
3. Beide Instanzen **ohne nginx** deployen:
   ```
   task play -i inventories playbooks/vfllcms/playbook.yml \
     -l bohr,bohr_vfllcms,bohr_vfllcms_staging \
     --skip-tags htpasswd,certbot,nginx
   ```
4. Datenbank und Medien wiederherstellen: [[Prozess - VFLLCMS wiederherstellen]].
5. Erst wenn **auch der Eventmanager** deployt ist – nginx bindet die Datenverzeichnisse aller Instanzen ein:
   ```
   task play -i inventories playbooks/vfllcms/playbook.yml -l bohr -t htpasswd,certbot,nginx
   task play -i inventories playbooks/setup.yml -l bohr -t restic
   ```

## Typische Fehler

| Symptom | Ursache / Lösung |
|---|---|
| git: `Permission denied (publickey)` | Deploy Key fehlt bei GitHub oder liegt nicht unter `/root/.ssh/vfllcms_deploy_key` → [[Prozess - Deploy Key]]. |
| web startet ständig neu, `JSONDecodeError` bei `GOOGLE_CREDENTIALS` | `vault_vfllcms_google_credentials` ist kein gültiges JSON → vollständig neu verschlüsseln. |
| `password authentication failed for user "vfllcms"` | DB-Passwort in Postgres weicht von `POSTGRES_PASSWORD` ab → siehe Troubleshooting in `HOW_TO_DEPLOY.md`. |
| 502 Bad Gateway | web startet noch (Migrationen) oder ist abgestürzt → `sudo docker compose logs web`. |
| Seiten ok, Bilder fehlen | Medien nicht wiederhergestellt oder gehören root → `sudo chown -R 1000:1000 data/media`. |
| Keine neuen Veranstaltungen auf vfll.de | `journalctl -t vfllcms-cron`; die API von https://veranstaltungskalender.vfll.de muss antworten. |

Weitere Doku im Ansible-Repo: `playbooks/vfllcms/README.md` und `HOW_TO_DEPLOY.md`.
