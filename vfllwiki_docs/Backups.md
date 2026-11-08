---
section: infrastructure
kind: explain
---

# Backups

## Strategie

Die Daten der Applikations-Container werden täglich gesichert. Container, die Nutzerdaten verarbeiten, speichern diese auf dem Filesystem des Docker Hosts. Diese Daten-Ordner werden fortlaufend gesichert werden.

### Backup Management

Das Backup Management wird mit [[Restic]] ausgeführt. Restic ist ein Kommandozeilen-Tool zur automatisierten Ausführung von Backups. Es werden verschiedene Storage-Endpoints unterstützt.

Als Teil der Ansible-Infrastruktur wird ein automatisierter Backupzyklus konfiguriert. Neue Server und Container können so ohne erheblichen Aufwand gesichert werden.

### Backup Storage

Backups werden auf einem remote Backup-Server gesichert. Dieser Server hat ein externe Disk gemounted, die flexibel vergrössert werden kann.

### Backup Replication

Damit die Backups auch bei einem Ausfall des Backup Servers zur Verfügung stehen, werden die Backup-Daten auf einer _Storage Box_ gespiegelt.

## Architektur

![[attachments/Backup_Architektur.png]]

## Anwendung

[[Restic - Wiederherstellung von Backups]]