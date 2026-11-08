---
tags:
section: infrastructure
kind: reference
website: https://restic.net/
---

# Restic

restic ist ein freies, quelloffenes Backup-Programm (Kommandozeile, Go). Es sichert Dateien **verschlüsselt**, **dedupliziert** und **inkrementell** in ein Repository. Auf den Servern, die mit [[Ansible]] verwaltet werden, laufen die nächtlichen Backups mit restic.

## Begriffe

| Begriff | Bedeutung |
|---|---|
| **Repository** | Ablageort der Backups (lokales Verzeichnis, SFTP, S3 oder ein REST-Server). Mit einem Passwort verschlüsselt. |
| **Snapshot** | Stand der gesicherten Pfade zu einem Zeitpunkt. Jeder `restic backup`-Lauf erzeugt einen Snapshot mit eigener ID (z. B. `4f2a9c1e`). |
| **Tag** | Etikett an einem Snapshot (z. B. `eventmanager`, `postgres`), um Snapshots zu filtern. |
| **Deduplizierung** | Daten werden in Blöcke zerlegt, gleiche Blöcke nur einmal gespeichert. Jeder Snapshot ist vollständig, belegt aber nur Platz für Änderungen. |
| **forget / prune** | `forget` entfernt Snapshots nach einer Aufbewahrungsregel, `prune` löscht danach die nicht mehr benötigten Daten. |

**Wichtig:** Ohne das Repository-Passwort sind die Backups nicht wiederherstellbar. Es gibt keine Hintertür.

## Unser Setup

- **Backup-Server:** `backup.science-and-more.com` mit dem restic **REST-Server** im Container (Ansible-Rolle `restic_server`, Playbook `playbooks/backup/playbook.yml`).
- **Ein Repository pro Server**, benannt nach dem Inventory-Host: `backup.science-and-more.com/<host>`, z. B. `bohr`.
- **Clients:** Die Ansible-Rolle `restic` richtet auf jedem Server Folgendes ein:
  - restic selbst und den Wrapper `/usr/local/bin/restic-main` (restic mit voreingestelltem Repository und Passwort, Modus 0750: nur root und die Gruppe `restic_group`, Standard `backup`),
  - Hilfsskripte für Datenbank-Dumps (z. B. `docker-postgres-backup`),
  - Cronjobs von root für die einzelnen Backups und das nächtliche Aufräumen.
- **Konfiguration:** `restic_backup_set` in `inventories/host_vars/<host>/vars.yml`. Jeder Eintrag ist ein Backup-Job:
  ```yaml
  restic_backup_set:
    - id: "Backup Vfllcms database"     # Name des Cronjobs
      type: postgres-dump               # Dump aus einem Postgres-Container
      container: vfllcms-db
      databases: vfllcms
      tags: [vfllcms, postgres]
      hour: "2"                         # Minute wird pro Job zufällig, aber fest gewählt
    - id: "Backup Vfllcms data"
      type: file                        # Verzeichnis direkt sichern
      path: /opt/docker/vfllcms/data
      tags: [vfllcms, files]
      hour: "2"
  ```
  Weitere Typen u. a.: `docker-volume`, `mysql`/`mariadb`-Dumps, `sqlite`, `odoo`, `nextcloud` (siehe `roles/restic/README.md`).
- **Datenbank-Dumps** landen zuerst unter `/var/backup/<container>/<datenbank>.sql` (Plain SQL) und werden dann mit restic gesichert.
- **Aufbewahrung** (`restic_backup_rotation`): 14 letzte, 14 tägliche, 4 wöchentliche, 3 monatliche Snapshots. `forget --prune` läuft jeden Abend um 23 Uhr, die Minute ist pro Repository fest (auf bohr 23:36).
- **Monitoring:** Jeder Job schreibt seinen Exit-Code als Metrik für den Node Exporter (`write-node-exporter-metric`), siehe [[Grafana]].

Ausrollen bzw. nach Änderungen an `restic_backup_set` aktualisieren:
```
task play -i inventories playbooks/setup.yml -l <host> -t restic
```
Die Rolle prüft, ob die zu sichernden Pfade existieren. Auf einem frischen Server deshalb erst die Apps deployen, dann restic einrichten.

## Wichtige Befehle

Auf dem jeweiligen Server, immer mit `sudo`:

```
sudo restic-main snapshots                            # alle Snapshots
sudo restic-main snapshots --tag vfllcms,postgres     # gefiltert
sudo restic-main ls <snapshot-id>                     # Inhalt eines Snapshots
sudo restic-main restore <snapshot-id> --target /tmp/restore
sudo restic-main restore latest --tag vfllcms,files --target /tmp/restore \
  --include /opt/docker/vfllcms/data/media/documents  # nur einen Teil
sudo restic-main diff <id1> <id2>                     # Unterschiede zweier Snapshots
sudo restic-main stats                                # Größe des Repositorys
sudo restic-main check                                # Integrität prüfen
sudo crontab -l                                       # eingerichtete Backup-Jobs
```

Vom eigenen Rechner aus (im Ansible-Build-Repo): `./task list-backups <host>` zeigt die Snapshots eines Servers.

## Fallstricke

- **Tags filtern:** `--tag a,b` heißt „a **und** b“, `--tag a --tag b` heißt „a **oder** b“. Mit der falschen Form wählt `latest` womöglich den Snapshot einer anderen App.
- **Pfade beim Restore:** restic stellt den vollen Pfad unter dem Ziel wieder her, z. B. landet `/opt/docker/vfllcms/data` unter `/tmp/restore/opt/docker/vfllcms/data`.
- **Dumps sind Plain SQL:** Sie werden mit `psql` eingespielt, nicht mit `pg_restore`.
- **Aufräumen:** Wiederhergestellte Daten unter `/tmp/restore` enthalten oft personenbezogene Daten und sollten danach gelöscht werden.
- **Restore testen:** Ein Backup ist erst dann etwas wert, wenn die Wiederherstellung einmal ausprobiert wurde (z. B. auf Staging).

## Prozesse

- [[Prozess - Eventmanager wiederherstellen]]
- [[Prozess - VFLLCMS wiederherstellen]]
