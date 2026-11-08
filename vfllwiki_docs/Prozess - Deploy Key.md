# Prozess - Deploy Key erzeugen und transferieren

Auf Target Server einloggen, z.B. _bohr_ :
```
task connect-host bohr
```

Public Key unter /root anlegen
```bash
sudo -n test -f /root/.ssh/vfllcms_deploy_key || sudo -n ssh-keygen -q -t ed25519 -N "" -C "bohr (ansible) vfllcms deploy key" -f /root/.ssh/vfllcms_deploy_key
sudo -n cat /root/.ssh/vfllcms_deploy_key.pub
gh repo deploy-key list -R scienceuli/vfllcms
```

Deploy Key zum github-Repo hinzufügen:
```bash
sudo -n cat /root/.ssh/vfllcms_deploy_key.pub > /tmp/bohr_vfllcms_deploy_key.pub && gh repo deploy-key add /tmp/bohr_vfllcms_deploy_key.pub -R scienceuli/vfllcms --title "bohr (ansible)" && gh repo deploy-key list -R scienceuli/vfllcms
sudo -n ssh -i /root/.ssh/vfllcms_deploy_key -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | head -2
```
