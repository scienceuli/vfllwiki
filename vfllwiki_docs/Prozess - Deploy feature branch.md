# Prozess - Deploy Feature Branch

Neuen Feature-Branch erstellen:
```
git checkout -b feature-branch
```

Änderungen einbauen und committen:
```
git add -a
git commit -m "new feature branch"
```

Feature Branch pushen und PR erstellen:
```
git push -u origin feature-branch
```



Will man einen feature branch auf eine Staging-Umgebung deployen, hängt man den Branch an den Play-Befehl an, z.B.
```
task play -i inventories playbooks/eventmanager/playbook.yml \
  -l bohr,bohr_eventmanager_staging \
  -e eventmanager_git_version=feature-branch
```

