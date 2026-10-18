**BigBlueButton** (kurz auch **BBB**)ist ein Open Source Webkonferenzsystem.  Es verfügt über Integrationen für viele der wichtigsten Lern- und Inhaltsverwaltungssysteme. Eine Teilnahme mit Anmeldung erfolgt plattformunabhängig im jeweils eigenen (ausreichend modernen) Browser und bedarf keiner besonderen Installierung.

Github: https://github.com/bigbluebutton/bigbluebutton

Hosting einer eigenen BBB-Instanz: [[Prozess - Installation BigBlueButton]]

The latest version is BigBlueButton 4.0. You can install BigBlueButton it on Ubuntu 24.04 using [bbb-install.sh](https://github.com/bigbluebutton/bbb-install) within 30 minutes.

Die wichtigsten Änderungen der Versionen 3.0 und 4.0 gegenüber 2.7 sind [[BigBlueButton Änderungen in 3.0 und 4.0]] zusammengefasst.

### Installationsvoraussetzungen

- Ubuntu 24.04 64-bit OS running Linux kernel 6.x
- Latest version of docker installed
- 16 GB of memory with swap enabled
- 8 CPU cores, with high single-thread performance
- 500 GB of free disk space (or more) for recordings, or 50GB if session recording is disabled on the server.
- TCP ports 80 and 443 are accessible
- UDP ports 16384 - 32768 are accessible
- 250 Mbits/sec bandwidth (symmetrical) or more
- TCP port 80 and 443 are **not** in use by another web server or reverse proxy
- A hostname (such as bbb.example.com) for setup of a SSL certificate
- IPV4 and IPV6 address