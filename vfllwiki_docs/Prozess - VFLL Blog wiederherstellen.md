# Prozess - VFLL Blog wiederherstellen

Wiederherstellung des VFLL-Blogs (WordPress, Produktion `gauss_blog`, https://lektorenverband.de) aus dem restic-Backup. Gesichert wird **nur die Produktion**, Ziel ist das Repo `gauss` auf backup.science-and-more.com. Eingerichtet über `playbooks/setup.yml -t restic -l gauss`, konfiguriert in `inventories/host_vars/gauss/vars.yml` (`restic_backup_set`).

Für Staging gibt es kein Backup – Staging wird bei Bedarf aus dem Produktions-Backup neu befüllt (siehe unten).

## Was wird gesichert?

| Zeit (nachts) | Was | Snapshot-Tags | Pfad im Snapshot |
|---|---|---|---|
| ca. 02:05 | SQL-Dump der Datenbank `wordpress` (Container `gauss-mysql01`) | `wordpress`, `gauss-mysql01` | `/var/backup/gauss-mysql01/wordpress.sql` |
| ca. 02:47 | Volume `wordpress_data01` als tar: WordPress-Core, `wp-config.php`, `wp-content` (Plugins, Themes, Uploads) | `wordpress`, `wordpress01` | `/var/backup/wordpress01/wordpress_data01.tar` |
| 23:02 | `forget --prune`: 14 letzte, 14 tägliche, 4 wöchentliche, 3 monatliche | | |

Wichtig:
- Datenbank und Volume liegen in **getrennten Snapshots**. Möglichst Snapshots von derselben Nacht nehmen, damit Beiträge in der DB und Bilder in `wp-content/uploads` zusammenpassen.
- Im tar beginnen alle Pfade mit `_data/` (z. B. `_data/wp-content/uploads/2026/11/bild.jpg`). Beim Auspacken deshalb `--strip-components=1`.
- Das Child-Theme hat seine Masterkopie im Ansible-Repo. Nach einem Restore aus einem älteren Backup das Theme neu deployen (Schritt 3).

## Vorbereitung

Auf gauss einloggen (alle weiteren Befehle laufen dort, wenn nicht anders angegeben):
```
task connect-host gauss
# oder: ssh scienceuli@gauss.science-and-more.com
```

`restic-main` ist restic mit voreingestelltem Repo und Passwort, läuft nur mit `sudo`.

Snapshots anzeigen:
```
sudo restic-main snapshots --tag wordpress,gauss-mysql01    # Datenbank-Dumps
sudo restic-main snapshots --tag wordpress,wordpress01      # Volume
```

> Achtung bei den Tags: `--tag a,b` heißt „a **und** b“, `--tag a --tag b` heißt „a **oder** b“. Mit `--tag wordpress` allein erwischt `latest` den falschen Snapshot.

Die Snapshot-ID (erste Spalte) für die folgenden Schritte notieren, oder `latest` verwenden.

Für die Kontrolle hilft wp-cli. Diese Shell-Funktion startet es in einem Wegwerf-Container mit Volume und DB-Zugang von `wordpress01` (gilt für die aktuelle Shell):
```
wp() {
  sudo docker run --rm --user 33:33 --volumes-from wordpress01 --network science-and-more.com \
    $(sudo docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' wordpress01 | grep '^WORDPRESS_DB_' | sed 's/^/-e /') \
    wordpress:cli wp "$@"
}
wp option get siteurl      # Test
```

## 1. Datenbank wiederherstellen

**1.1 Sicherheitskopie des aktuellen Stands** (falls die DB noch existiert):
```
sudo docker exec gauss-mysql01 sh -c 'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction wordpress' \
  > ~/wordpress-vor-restore-$(date +%F).sql
```

**1.2 Dump aus restic holen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag wordpress,gauss-mysql01
sudo ls -l /tmp/restore/var/backup/gauss-mysql01/
sudo tail -1 /tmp/restore/var/backup/gauss-mysql01/wordpress.sql   # muss "-- Dump completed" sein
```

**1.3 WordPress stoppen, Datenbank neu anlegen und Dump einspielen:**
```
sudo docker stop wordpress01

sudo docker exec gauss-mysql01 sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "
  DROP DATABASE IF EXISTS \`wordpress\`;
  CREATE DATABASE \`wordpress\` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"'

sudo cat /tmp/restore/var/backup/gauss-mysql01/wordpress.sql \
  | sudo docker exec -i gauss-mysql01 sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" wordpress'
```
Die Rechte des MySQL-Users `wordpress` hängen am Datenbanknamen und überleben das `DROP`. Bei einem Fehler beim Einspielen die Sicherheitskopie aus 1.1 auf dieselbe Weise zurückspielen.

Wenn nur die Datenbank zurück soll: weiter mit Schritt 3.

## 2. Volume (Uploads, Plugins, Core) wiederherstellen

**2.1 tar aus restic holen:**
```
sudo restic-main restore <snapshot-id> --target /tmp/restore     # oder: latest --tag wordpress,wordpress01
sudo ls -lh /tmp/restore/var/backup/wordpress01/                 # wordpress_data01.tar, ca. 2,5 GB
```

**Variante A – nur einzelne Dateien** (z. B. ein versehentlich gelöschtes Bild); WordPress kann dabei weiterlaufen:
```
sudo tar -tf /tmp/restore/var/backup/wordpress01/wordpress_data01.tar | grep 'uploads/2026/11/'
sudo tar -C /var/lib/docker/volumes/wordpress_data01/_data --strip-components=1 \
  -xf /tmp/restore/var/backup/wordpress01/wordpress_data01.tar \
  _data/wp-content/uploads/2026/11/bild.jpg
sudo chown -R 33:33 /var/lib/docker/volumes/wordpress_data01/_data/wp-content/uploads/2026/11
```

**Variante B – das ganze Volume** (exakter Stand des Snapshots):
```
sudo docker stop wordpress01
V=/var/lib/docker/volumes/wordpress_data01/_data

# Sicherheitskopie des aktuellen Stands (ca. 2,5 GB)
sudo tar -C $V -cf /var/tmp/wordpress_data01-vor-restore-$(date +%F).tar .

# leeren und auspacken
sudo find $V -mindepth 1 -delete
sudo tar -C $V --strip-components=1 -xf /tmp/restore/var/backup/wordpress01/wordpress_data01.tar
sudo chown -R 33:33 $V
```
Die `wp-config.php` aus dem Backup ist die der Produktion und passt – Datenbank-Zugang kommt ohnehin aus den Umgebungsvariablen des Containers.

## 3. Starten und Theme nachziehen

```
sudo docker start wordpress01
```

Auf dem **Mac** im Repo-Root das Child-Theme aus dem Repo neu deployen (ein älteres Backup kann einen alten Stand enthalten):
```
task play -i inventories playbooks/wordpress.yml -l gauss_blog -t wordpress_themes
```

## 4. Kontrolle

Auf gauss mit der `wp`-Funktion von oben:
```
wp option get siteurl                 # https://lektorenverband.de
wp option get home                    # https://lektorenverband.de
wp post list --post_type=post --post_status=publish --format=count
wp core version
wp plugin list --status=active
```
Falls der Core im Volume neuer ist als die Datenbank (WordPress meldet „Datenbank-Aktualisierung erforderlich“):
```
wp core update-db
```

Von außen:
```
curl -sI https://lektorenverband.de/ | head -1      # 200
```
Im Browser: Startseite, ein paar Beiträge mit Bildern, Admin-Login, Plugins → Aktualisierungen. Falls Beiträge 404 liefern: Einstellungen → Permalinks einmal „Speichern“.

## 5. Aufräumen

```
sudo rm -rf /tmp/restore
rm -f ~/wordpress-vor-restore-*.sql                          # erst wenn alles läuft
sudo rm -f /var/tmp/wordpress_data01-vor-restore-*.tar        # erst wenn alles läuft
```

## Variante: Staging aus dem Backup befüllen

Automatisch per Playbook vom Mac aus (neuestes Backup, URLs umgestellt, Mails blockiert):
```
task play -i inventories playbooks/vfll_wordpress/staging.yml
```
Details: [[Prozess - VFLL Blog deployen]], Abschnitt „Staging mit Produktionsdaten auffrischen“.

## Variante: Neuinstallation von gauss

1. Server und leere Instanzen deployen, **ohne** restic, siehe [[Prozess - VFLL Blog deployen]], Abschnitt „Neuinstallation“, Schritte 1–3.
2. restic ist auf dem frischen Server noch nicht eingerichtet. Am einfachsten:
   ```
   task play -i inventories playbooks/setup.yml -l gauss -t restic
   ```
   Das richtet `restic-main` ein (das Repo `gauss` existiert schon), **aber auch die nächtlichen Backup-Jobs**. Den Restore deshalb vor 02:00 Uhr erledigen – sonst landet ein Backup der leeren Installation im Repo (die alten Snapshots bleiben trotzdem erhalten).
3. Schritte 1–4 dieser Seite (beim Volume Variante B).
4. Proxy: `task play -i inventories playbooks/proxy.yml -l gauss`.
5. Staging befüllen: `task play -i inventories playbooks/vfll_wordpress/staging.yml`.

## Notfall: Backup vom Umzug 2026-10

Vor der Neuinstallation im Oktober 2026 wurde das alte System auf den Mac gesichert (`~/Backups/gauss-vfllwp/<datum>/`). Das Playbook `playbooks/vfll_wordpress/restore.yml` spielt so ein Backup komplett ein. Es ist inzwischen **veraltet** (alle Beiträge seit Oktober fehlen) und nur gedacht, falls das restic-Repo selbst verloren ist.

Siehe auch: [[Prozess - VFLL Blog deployen]], [[Restic - Wiederherstellung von Backups]], `playbooks/vfll_wordpress/README.md`.
