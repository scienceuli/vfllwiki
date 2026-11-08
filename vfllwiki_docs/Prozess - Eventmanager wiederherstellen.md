# Prozess - Eventmanager wiederherstellen

Wiederherstellung des Eventmanagers (Produktion, `bohr_eventmanager`) aus dem restic-Backup. Gesichert wird **nur die Produktion**, Ziel ist das Repo `bohr` auf backup.science-and-more.com. Eingerichtet über `playbooks/setup.yml -t restic -l bohr`, konfiguriert in `inventories/host_vars/bohr/vars.yml` (`restic_backup_set`).

## Was wird gesichert?

| Zeit (nachts) | Was | Snapshot-Tags | Pfad im Snapshot |
|---|---|---|---|
| ca. 02:xx | SQL-Dump der Datenbank `eventmanager` | `eventmanager`, `postgres` | `/var/backup/eventmanager-db/eventmanager.sql` |
| ca. 02:xx | Datenverzeichnis (`media/`, `private/` mit Rechnungen, `sent_emails/`, `static/`) | `eventmanager`, `files` | `/opt/docker/eventmanager/data` |
| 23:36 | `forget --prune`: 14 letzte, 14 tägliche, 4 wöchentliche, 3 monatliche | | |

Wichtig:
- Der Datenbank-Dump ist ein **Plain-SQL-Dump** (`pg_dump` ohne `-Fc`). Er wird mit `psql` eingespielt, **nicht** mit `pg_restore` – und deshalb auch nicht über `-e eventmanager_restore_dump=...` im Playbook (das erwartet ein `pg_dump -Fc`-Archiv).
- Die Datenbank und die Dateien liegen in **getrennten Snapshots**. Möglichst Snapshots von derselben Nacht nehmen, damit Rechnungen in der DB und PDFs in `data/private/` zusammenpassen.

## Vorbereitung

Auf bohr einloggen (alle weiteren Befehle laufen dort):
```
task connect-host bohr
# oder: ssh scienceuli@bohr.science-and-more.com
```

`restic-main` ist restic mit voreingestelltem Repo und Passwort, läuft nur mit `sudo`.

Snapshots anzeigen:
```
sudo restic-main snapshots --tag eventmanager,postgres    # Datenbank-Dumps
sudo restic-main snapshots --tag eventmanager,files       # Datenverzeichnis
```

> Achtung bei den Tags: `--tag a,b` heißt „a **und** b“, `--tag a --tag b` heißt „a **oder** b“. Mit `--tag postgres --tag eventmanager` erwischt `latest` unter Umständen den Dump des VFLLCMS oder den Datei-Snapshot.

Die Snapshot-ID (erste Spalte) für die folgenden Schritte notieren, oder `latest` verwenden.

## 1. Datenbank wiederherstellen

**1.1 Sicherheitskopie des aktuellen Stands** (falls die DB noch existiert):
```
sudo docker exec eventmanager-db pg_dump -Fc -U eventmanager eventmanager \
  > ~/eventmanager-vor-restore-$(date +%F).pgdump
```

**1.2 Dump aus restic holen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag eventmanager,postgres
sudo ls -l /tmp/restore/var/backup/eventmanager-db/
```

**1.3 App stoppen, Datenbank neu anlegen und Dump einspielen:**
```
cd /opt/docker/eventmanager
sudo docker compose stop web          # bei eventmanager_mailqueue_autosend: true auch: mailqueue

sudo docker exec eventmanager-db sh -c \
  'dropdb -U eventmanager --maintenance-db=postgres --if-exists --force eventmanager \
   && createdb -U eventmanager --maintenance-db=postgres -O eventmanager eventmanager'

sudo cat /tmp/restore/var/backup/eventmanager-db/eventmanager.sql \
  | sudo docker exec -i eventmanager-db \
    psql -U eventmanager -d eventmanager -v ON_ERROR_STOP=1 --single-transaction -q
```
`--single-transaction` + `ON_ERROR_STOP`: entweder wird der ganze Dump eingespielt oder gar nichts. Bei einem Fehler **web nicht starten** (sonst migriert Django eine leere Datenbank) – erst die Ursache klären bzw. die Sicherheitskopie aus 1.1 zurückspielen.

**1.4 Mail-Queue prüfen, bevor die App startet:**
```
sudo docker exec eventmanager-db psql -U eventmanager eventmanager \
  -c "select sent, count(*) from mailqueue_mailermessage group by 1"
```
Bei `eventmanager_mailqueue_autosend: false` (Standard auf bohr) passiert nichts automatisch. Ist Autosend aktiv, gehen alle ungesendeten Mails des alten Stands sofort raus.

**1.5 App wieder starten** (führt `migrate` aus):
```
sudo docker compose start web
sudo docker compose logs -f web
```

## 2. Dateien wiederherstellen (media, private, sent_emails)

**2.1 In ein temporäres Verzeichnis zurückholen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag eventmanager,files
```
Nur einen Teil (z. B. die Rechnungen):
```
sudo restic-main restore <snapshot-id> --target /tmp/restore \
  --include /opt/docker/eventmanager/data/private/invoices
```

**2.2 Zurückkopieren und Rechte setzen** (Container läuft als UID 1000):
```
sudo rsync -a /tmp/restore/opt/docker/eventmanager/data/ /opt/docker/eventmanager/data/
sudo chown -R 1000:1000 /opt/docker/eventmanager/data/media \
  /opt/docker/eventmanager/data/private /opt/docker/eventmanager/data/sent_emails
```
`rsync` ohne `--delete` überschreibt nur und löscht keine neueren Dateien. Für einen exakten Stand des Snapshots `--delete` ergänzen (vorher mit `-n` testen).

`static/` muss nicht zurück – das erzeugt `collectstatic` beim Start von web.

## 3. Kontrolle

```
curl -I https://veranstaltungskalender.vfll.de     # 200
```
Prüfen, ob jede Rechnung in der DB eine Datei hat:
```
sudo docker exec -i eventmanager python manage.py shell <<'EOF'
from invoices.models import Invoice
qs = Invoice.objects.exclude(pdf="").exclude(pdf__isnull=True)
print(qs.count(), sum(not i.pdf.storage.exists(i.pdf.name) for i in qs))   # fehlend: 0
EOF
```

## 4. Aufräumen

Die wiederhergestellten Daten enthalten personenbezogene Daten und Rechnungen:
```
sudo rm -rf /tmp/restore
rm -f ~/eventmanager-vor-restore-*.pgdump    # erst wenn alles läuft
```

## Variante: Staging aus dem Backup befüllen

Gleiches Vorgehen, aber mit den Staging-Namen: Verzeichnis `/opt/docker/eventmanager-staging`, Container `eventmanager-staging-db` bzw. `eventmanager-staging`. Staging nutzt denselben `ENCRYPT_KEY` wie die Produktion, die verschlüsselten Newsletter-Tokens funktionieren also. Staging verschickt keine Mails (File-Backend).

## Variante: Neuinstallation von bohr

1. Server und Instanz deployen ohne nginx und restic, siehe [[Prozess - Eventmanager deployen]], Abschnitt „Neuinstallation“.
2. restic ist auf dem frischen Server noch nicht eingerichtet. Entweder `setup.yml -l bohr -t restic` vorziehen (dafür müssen die Datenverzeichnisse schon existieren, also nach dem Deploy) oder restic vom Mac aus gegen das Repo `bohr` verwenden. Achtung: Mit `-t restic` laufen ab sofort auch die nächtlichen Backups.
3. Schritte 1–3 dieser Seite.
4. nginx/certbot ausrollen.

Siehe auch: [[Prozess - Eventmanager deployen]], `playbooks/eventmanager/README.md` („Backup & restore“).
