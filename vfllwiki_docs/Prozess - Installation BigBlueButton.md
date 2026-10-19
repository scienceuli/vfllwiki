Voraussetzungen für die Installation von BBB Version 4 siehe [[BigBlueButton#Installationsvoraussetzungen]]

Vorgehensweise für ein frisch installiertes Server Image:

**Server bestellen** (Netcup, Hetzner)

**SSH-Key** für root hinterlegen

**Ansible Playbooks**

Bootstrap Server: `task play -i inventories playbooks/bootstrap.yml -l bbb` 





