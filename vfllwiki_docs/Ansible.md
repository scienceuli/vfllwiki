---
tags:
section: infrastructure
kind: reference
---

Ansible ist eine  Technologie, mit der sich eine Server-Infrastruktur managen lässt.  Mit Ansible wird die Server-Konfiguration beschrieben und angewendet. Auch die Server für den VFLL werden mit Ansible konfiguriert.  

Typischer Ansible-Aufruf
```mermaid
sequenceDiagram
    participant D as Docker
    participant M as moodle01
    participant DB as mariadb02
    D->>M: start container
    M->>M: sync Moodle code into moodle_code01 if versions differ
    M->>DB: wait until port 3306 answers
    alt no config.php yet
        M->>M: generate config.php (wwwroot, dbcollation, sslproxy)
        M->>DB: install database (about 500 tables, admin user)
    else config.php exists
        M->>DB: run admin/cli/upgrade.php
    end
    M->>M: start nginx :8080, php-fpm, internal cron
```
