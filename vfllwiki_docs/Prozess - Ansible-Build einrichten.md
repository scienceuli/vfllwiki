# Prozess - Ansible-Build einrichten

Einmalige Einrichtung des Ansible-Repos auf dem eigenen Rechner. Danach funktionieren die Deploy- und Restore-Prozesse (z. B. [[Prozess - Eventmanager deployen]], [[Prozess - VFLLCMS deployen]]).

Drei Dinge sind bewusst **nicht** im Repo https://github.com/scienceuli/Ansible-Build und müssen lokal angelegt werden:

| Was | Wofür | Woher |
|---|---|---|
| `inventories/` | Hosts, `host_vars`, `group_vars`, verschlüsselte Secrets (`vault.yml`) | eigenes privates Repo auf Codeberg |
| `ansible.cfg` | Ansible-Konfiguration (Inventory, Vault, Rollenpfad) | Vorlage `ansible.cfg.example` im Repo |
| `.vault-pass` | Passwort zum Entschlüsseln der Vault-Werte | von den Admins, **nie** ins Repo |

Alle drei stehen in `.gitignore`.

## Voraussetzungen

- [[Git]], `uv` (Python-Paketmanager, `brew install uv`)
- SSH-Key bei GitHub und Codeberg hinterlegt, Zugriff auf das private Repo `scienceuli/inventories`
- eigener SSH-Zugang zu den Servern (siehe [[SSH Zugriff]])

## 1. Repos klonen

```
git clone https://github.com/scienceuli/Ansible-Build.git
cd Ansible-Build
git clone git@codeberg.org:scienceuli/inventories.git inventories
```

Das Inventory **muss** im Unterordner `inventories` liegen, alle Befehle verwenden `-i inventories`.

## 2. Python-Umgebung und Ansible installieren

```
./task install          # Python-Version aus .python-version, venv .venv, requirements.txt
source .venv/bin/activate
ansible --version
```

Ohne aktivierte venv geht jeder Befehl auch mit `uv run`, z. B. `uv run ansible-playbook ...`.

## 3. ansible.cfg anlegen

```
cp ansible.cfg.example ansible.cfg
```

Inhalt (siehe Kommentare in der Vorlage):
```ini
[defaults]
inventory = ./inventories
interpreter_python = auto_silent
vault_identity_list = scienceuli@.vault-pass
roles_path = ./roles
```

`vault_identity_list = scienceuli@.vault-pass` bedeutet: Vault-ID `scienceuli`, Passwort aus der Datei `.vault-pass`. Die Secrets im Inventory sind mit dieser ID verschlüsselt (Kopfzeile `$ANSIBLE_VAULT;1.2;AES256;scienceuli`).

Ansible liest `ansible.cfg` nur aus dem **aktuellen Verzeichnis**. Deshalb alle Befehle im Repo-Root ausführen.

## 4. .vault-pass anlegen

Das Vault-Passwort gibt es nur bei den Admins. Es wird auf sicherem Weg weitergegeben (z. B. über [[KeePassXC]]), nie per Mail oder Chat im Klartext.

```
./task generate-vault-password      # schreibt .vault-pass (Modus 600)
```

Das Passwort wird zweimal verdeckt abgefragt. Es landet nicht in der Shell-History, und eine vorhandene `.vault-pass` wird nur nach Rückfrage überschrieben. Die Datei enthält nur das Passwort in **einer Zeile**. Ein anderer Dateiname geht als Argument: `./task generate-vault-password <datei>` (dann auch `ansible.cfg` anpassen).

## 5. Testen

Vault entschlüsseln:
```
ansible -i inventories bohr_vfllcms -m debug -a 'msg={{ vault_vfllcms_secret_key | length }}'
```
Kommt eine Zahl (Länge des Secrets, z. B. `"msg": "40"`) statt `Decryption failed`, passen Passwort und `ansible.cfg`. Den Wert selbst bewusst nicht ausgeben.

Verbindung zum Server:
```
ansible -i inventories bohr -m ping
./task connect-host bohr
```

Ansible-Collections für die Playbooks:
```
ansible-galaxy collection install -r playbooks/eventmanager/requirements.yml
ansible-galaxy collection install -r playbooks/vfllcms/requirements.yml
```

## Typische Fehler

| Symptom | Ursache / Lösung |
|---|---|
| `Attempting to decrypt but no vault secrets found` | `ansible.cfg` fehlt oder Befehl nicht im Repo-Root ausgeführt. |
| `Decryption failed (no vault secrets were found that could decrypt)` | Falsches Passwort in `.vault-pass`, oder falsche Vault-ID in `ansible.cfg` (muss `scienceuli` sein). |
| `Could not match supplied host pattern` | `inventories/` fehlt oder liegt nicht im Repo-Root. |
| `the role 'xyz' was not found` | `roles_path` fehlt in `ansible.cfg`. |
| `ansible-playbook: command not found` | venv nicht aktiviert → `source .venv/bin/activate` oder `uv run ...`. |

Inventory aktualisieren: `git -C inventories pull` (oder `./task pull-repos`).
