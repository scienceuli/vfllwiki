# Prozess - VFLLCMS wiederherstellen

Wiederherstellung des VFLL-CMS (Wagtail, Produktion `bohr_vfllcms`) aus dem restic-Backup. Gesichert wird **nur die Produktion**, Ziel ist das Repo `bohr` auf backup.science-and-more.com. Eingerichtet über `playbooks/setup.yml -t restic -l bohr`, konfiguriert in `inventories/host_vars/bohr/vars.yml` (`restic_backup_set`).

## Was wird gesichert?

| Zeit (nachts) | Was | Snapshot-Tags | Pfad im Snapshot |
|---|---|---|---|
| ca. 02:xx | SQL-Dump der Datenbank `vfllcms` | `vfllcms`, `postgres` | `/var/backup/vfllcms-db/vfllcms.sql` |
| ca. 02:xx | Datenverzeichnis (`media/` mit Bildern und Dokumenten, `static/`) | `vfllcms`, `files` | `/opt/docker/vfllcms/data` |
| 23:36 | `forget --prune`: 14 letzte, 14 tägliche, 4 wöchentliche, 3 monatliche | | |

Wichtig:
- Der Datenbank-Dump ist ein **Plain-SQL-Dump** (`pg_dump` ohne `-Fc`). Er wird mit `psql` eingespielt, **nicht** mit `pg_restore` – und deshalb auch nicht über `-e vfllcms_restore_dump=...` im Playbook (das erwartet ein `pg_dump -Fc`-Archiv).
- Datenbank und Medien liegen in **getrennten Snapshots**. Möglichst Snapshots von derselben Nacht nehmen, damit Bilder/Dokumente in der DB und Dateien in `data/media/` zusammenpassen.

## Vorbereitung

Auf bohr einloggen (alle weiteren Befehle laufen dort):
```
task connect-host bohr
# oder: ssh scienceuli@bohr.science-and-more.com
```

`restic-main` ist restic mit voreingestelltem Repo und Passwort, läuft nur mit `sudo`.

Snapshots anzeigen:
```
sudo restic-main snapshots --tag vfllcms,postgres    # Datenbank-Dumps
sudo restic-main snapshots --tag vfllcms,files       # Datenverzeichnis
```

> Achtung bei den Tags: `--tag a,b` heißt „a **und** b“, `--tag a --tag b` heißt „a **oder** b“. Mit `--tag postgres --tag vfllcms` erwischt `latest` unter Umständen den Dump des Eventmanagers oder den Datei-Snapshot.

Die Snapshot-ID (erste Spalte) für die folgenden Schritte notieren, oder `latest` verwenden.

## 1. Datenbank wiederherstellen

**1.1 Sicherheitskopie des aktuellen Stands** (falls die DB noch existiert):
```
sudo docker exec vfllcms-db pg_dump -Fc -U vfllcms vfllcms \
  > ~/vfllcms-vor-restore-$(date +%F).pgdump
```

**1.2 Dump aus restic holen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag vfllcms,postgres
sudo ls -l /tmp/restore/var/backup/vfllcms-db/
```

**1.3 App stoppen, Datenbank neu anlegen und Dump einspielen:**
```
cd /opt/docker/vfllcms
sudo docker compose stop web

sudo docker exec vfllcms-db sh -c \
  'dropdb -U vfllcms --maintenance-db=postgres --if-exists --force vfllcms \
   && createdb -U vfllcms --maintenance-db=postgres -O vfllcms vfllcms'

sudo cat /tmp/restore/var/backup/vfllcms-db/vfllcms.sql \
  | sudo docker exec -i vfllcms-db \
    psql -U vfllcms -d vfllcms -v ON_ERROR_STOP=1 --single-transaction -q
```
`--single-transaction` + `ON_ERROR_STOP`: entweder wird der ganze Dump eingespielt oder gar nichts. Bei einem Fehler **web nicht starten** (sonst migriert Django eine leere Datenbank) – erst die Ursache klären bzw. die Sicherheitskopie aus 1.1 zurückspielen.

**1.4 App wieder starten** (führt `migrate` und `collectstatic` aus):
```
sudo docker compose start web
sudo docker compose logs -f web      # warten auf "Listening at"
```

## 2. Medien wiederherstellen

**2.1 In ein temporäres Verzeichnis zurückholen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag vfllcms,files
```
Nur einen Teil (z. B. die Dokumente):
```
sudo restic-main restore <snapshot-id> --target /tmp/restore \
  --include /opt/docker/vfllcms/data/media/documents
```

**2.2 Zurückkopieren und Rechte setzen** (Container läuft als UID 1000):
```
sudo rsync -a /tmp/restore/opt/docker/vfllcms/data/media/ /opt/docker/vfllcms/data/media/
sudo chown -R 1000:1000 /opt/docker/vfllcms/data/media
```
`rsync` ohne `--delete` überschreibt nur und löscht keine neueren Dateien. Für einen exakten Stand des Snapshots `--delete` ergänzen (vorher mit `-n` testen).

`static/` muss nicht zurück – das erzeugt `collectstatic` beim Start von web.

## 3. Kontrolle

```
curl -I https://vfll.de      # 200
```
Prüfen, ob jedes Bild und Dokument in der DB eine Datei hat:
```
sudo docker exec -i vfllcms-web uv run manage.py shell <<'EOF'
from wagtail.images import get_image_model
from wagtail.documents import get_document_model
for M in (get_image_model(), get_document_model()):
    print(M.__name__, M.objects.count(), sum(not o.file.storage.exists(o.file.name) for o in M.objects.all()))
EOF
```
Die zweite Zahl (fehlende Dateien) sollte 0 sein. Zusätzlich ein paar Seiten mit Bildern und einen Dokument-Download im Browser prüfen.

Veranstaltungen und Blogposts kommen ohnehin nachts neu per Cronjob (`get_events`, `get_blog`). Sofort aktualisieren:
```
sudo docker exec vfllcms-web uv run manage.py get_events
sudo docker exec vfllcms-web uv run manage.py get_blog
```

## 4. Aufräumen

```
sudo rm -rf /tmp/restore
rm -f ~/vfllcms-vor-restore-*.pgdump    # erst wenn alles läuft
```

## Variante: Staging aus dem Backup befüllen

Gleiches Vorgehen, aber mit den Staging-Namen: Verzeichnis `/opt/docker/vfllcms-staging`, Container `vfllcms-staging-db` bzw. `vfllcms-staging-web`. Danach die Domain von `Site` 1 im Wagtail-Admin prüfen.

## Variante: Neuinstallation von bohr

1. Server und Instanz deployen ohne nginx und restic, siehe [[Prozess - VFLLCMS deployen]], Abschnitt „Neuinstallation“.
2. restic ist auf dem frischen Server noch nicht eingerichtet. Entweder `setup.yml -l bohr -t restic` vorziehen (dafür müssen die Datenverzeichnisse von VFLLCMS **und** Eventmanager schon existieren) oder restic vom Mac aus gegen das Repo `bohr` verwenden. Achtung: Mit `-t restic` laufen ab sofort auch die nächtlichen Backups.
3. Schritte 1–3 dieser Seite.
4. nginx/certbot ausrollen.

Siehe auch: [[Prozess - VFLLCMS deployen]], [[Prozess - Eventmanager wiederherstellen]], `playbooks/vfllcms/README.md` („Backup & restore“).
