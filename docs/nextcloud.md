# Nextcloud-Anbindung

Für die gemeinsame Arbeit an Office-Dokumenten steht eine [Nextcloud-Instanz](https://oonc.vfll.de) zur Verfügung, die mit einem OnlyOffice-Server kommuniziert (wird in Zukunft vermutlich gegen Collabora ausgetauscht). Die Dateien, die gemeinsam bearbeitet werden, liegen in der Nextcloud und werden im KollTool nur verwaltet.

## Voraussetzungen

- Die KollTool-User, die gemeinsam Office-Dokumente bearbeiten wollen, benötigen ein Nextcloud-Konto. Außerdem muss für das entsprechende Team eine Nextcloud-Gruppe und ein Nextcloud-Verzeichnis vorhanden sein. Wer diese Nextcloud-Infrastruktur benötigt, wende sich bitte an die KollTool-Admins.  
Beispiel: User *Anna* und *Ben* aus dem Team *Planung* wollen gemeinsam am Dokument *planung.docx* arbeiten. Dazu müssen auf Nextcloud von einem Admin die User *Ben* und *Anna* und die Gruppe *Planung* angelegt werden. Dieses Verzeichnis wird mit allen Mitglieder der Gruppe geteilt (*sharing*). 
- Das Office-Dokument, das im KollTool als Attachment hochgeladen wurde, muss auf die Nextcloud geschoben werden. Im KollTool selbst ist keine kollaborative Bearbeitung von Office-Dokumenten möglich, nur auf der Nextcloud!
- User, die Dokumente auf die Nextcloud verschieben wollen, müssen in ihrem Profilbereich (*Profil*->*Edit*) ihr Nextcloud-Passwort hinterlegen. 

## Vorgehensweise

- Benötigt ein KollTool-Team ein Nextcloud-Verzeichnis, kontaktiert es den Admin. Er legt für alle User des Teams Nextcloud-Accounts an und richtet ein Nextcloud-Verzeichnis für das Team ein. Nextcloud verschickt automatisch an neue Accounts eine E-Mail mit der Aufforderung, ein Passwort festzulegen.
- Soll ein Office-Dokument (zur Zeit nur docx-Dateien), das als Attachment an einem KollTool-Dokument hängt, gemeinsam bearbeitet werden, wird es über den Button *->NC* auf die Nextcloud geschoben. Solche Attachments werden hinter dem Dateinamen durch ein **NC** gekennzeichnet. Dahinter liegt gleichzeitig ein Link auf das Nextcloud-Verzeichnis (also das Team-Verzeichnis), in dem das Office-Dokument liegt.  
Wichtig: Um diese Aktion ausführen zu können, muss im Profil das Nextcloud-Passwort des Users hinterlegt sein (siehe oben).

## Todo

- Verzeichnisstrukturen auf Nextcloud anlegen
- Dateien synchronisieren