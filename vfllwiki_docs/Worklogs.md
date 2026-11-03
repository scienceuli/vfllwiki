# Worklogs

### 3.11.2026 21:00 Update Server hertz.science-and-more.com

Netcup scp > hertz > Snapshot
**snapshot_20261103** Snapshot vor Ubuntu Update vda 03.11.2026 21:20

 ```
$ ssh scienceuli@hertz.science-and-more.com
$ tmux new -s update        # reattach after a disconnect: tmux attach -t update
 ```

Fresh Backups:
```
$ sudo restic-nextcloud-backup -c nextcloud01 -m mariadb01 -D /data -o /var/backup/nextcloud -t nextcloud
$ sudo restic-main snapshots --latest 1 --tag nextcloud
$ sudo restic-main snapshots --latest 1 --tag moodle
$ sudo restic-main snapshots --latest 1 --tag etherpad
```

State:
```
$ docker ps --format '{{.Names}} {{.Image}} {{.Status}}' | sort > ~/pre-update-containers.txt

alloy01 grafana/alloy:v1.20.1 Up 4 minutes
collabora01 collabora/code:26.04.5.1.1 Up 4 minutes (healthy)
doc01 onlyoffice/documentserver:9.4.0 Up 4 minutes
etherpad01 etherpad/etherpad:3.3.9 Up 4 minutes (healthy)
mariadb01 mariadb:10.11 Up 4 minutes
mariadb02 mariadb:11.4 Up 4 minutes
mariadb03 mariadb:11.4 Up 4 minutes
moodle01 erseco/alpine-moodle:v5.3.0 Up 4 minutes (healthy)
nextcloud01 nextcloud:35-apache Up 4 minutes
nginx01 nginx:1.31.3-alpine Up 4 minutes
redis01 redis:7-alpine Up 4 minutes
vfllcms-db postgres:16-alpine Up 4 minutes (healthy)
vfllcms-web vfllcms:latest Up 4 minutes
```

```
$ uname -r; docker version --format '{{.Server.Version}}'
5.15.0-71-generic
24.0.1
```

Preview of upgrade
```
scienceuli@oonc:~$ sudo apt-get update
OK:1 http://de.archive.ubuntu.com/ubuntu jammy InRelease
Holen:2 https://download.docker.com/linux/ubuntu jammy InRelease [48,5 kB]
Holen:3 http://de.archive.ubuntu.com/ubuntu jammy-updates InRelease [128 kB]
Holen:4 http://de.archive.ubuntu.com/ubuntu jammy-backports InRelease [127 kB]
Holen:5 http://de.archive.ubuntu.com/ubuntu jammy-security InRelease [129 kB]
Holen:6 http://de.archive.ubuntu.com/ubuntu jammy-updates/main amd64 Packages [3.939 kB]
Holen:7 http://de.archive.ubuntu.com/ubuntu jammy-updates/universe amd64 Packages [1.289 kB]
Holen:8 http://de.archive.ubuntu.com/ubuntu jammy-security/main amd64 Packages [3.674 kB]
Holen:9 http://de.archive.ubuntu.com/ubuntu jammy-security/main Translation-en [513 kB]
Holen:10 http://de.archive.ubuntu.com/ubuntu jammy-security/universe amd64 Packages [1.057 kB]
Holen:11 http://de.archive.ubuntu.com/ubuntu jammy-security/universe Translation-en [238 kB]
Es wurden 11,1 MB in 2 s geholt (6.655 kB/s).
Paketlisten werden gelesen… Fertig
scienceuli@oonc:~$ apt-mark showhold
scienceuli@oonc:~$ sudo apt-get -s dist-upgrade | grep -E '^(Inst|Remv)' | wc -l
424
scienceuli@oonc:~$ sudo apt-get -s dist-upgrade | grep '^Remv'
scienceuli@oonc:~$
```

-> no removals

Nextcloud Maintenance Mode:
```
docker exec -u www-data nextcloud01 php occ maintenance:mode --on
```

**Upgrade**
```
sudo apt-get dist-upgrade
```

Config prompts: take defaults

```
docker version --format '{{.Server.Version}}'     # 29.x
containerd --version                              # 2.x
docker ps --format '{{.Names}} {{.Status}}' | sort
```


**Reboot**

```
[ -f /var/run/reboot-required ] && cat /var/run/reboot-required.pkgs | head
sudo reboot

```

**Checks:**

```
uname -r                                          # new 5.15.0-xxx
systemctl --failed # should be empty
docker ps --format '{{.Names}} {{.Image}} {{.Status}}' | sort | diff ~/pre-update-containers.txt - 
docker ps --filter health=unhealthy
docker logs --tail 20 nginx01
docker exec -u www-data nextcloud01 php occ maintenance:mode --off
docker exec -u www-data nextcloud01 php occ status
sudo crontab -l | grep -c restic                  # backup jobs still there
```

On local machine:
```
for u in oonc.vfll.de office.vfll.de staging.moodle.vfll.de staging.pad.vfll.de staging.doc.vfll.de; do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' https://$u/)" $u
done
```
 ->
 
 ```
302 oonc.vfll.de
302 office.vfll.de
303 staging.moodle.vfll.de
200 staging.pad.vfll.de
200 staging.doc.vfll.de
 ```

PHP Patching:
```
task play -i inventories playbooks/php_patching/check.yml -l hertz
```
no change expected

