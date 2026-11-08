# Prozess - Rebase Feture branch

Situation: in einer staging-Umgebung ist ein _feature branch_ deployt, aber es ergaben sich in der Zwischenzeit wichtige Änderungen an _main_: 

### 1. publish main
```
git switch main
git pull                      # in case the remote has newer commits
git push origin main
```
### 2. bring main into the feature branch
```
git switch feature-branch
git pull                      # sync the branch with origin
git merge main                # fix conflicts if any, then: git add … && git commit
python manage.py test         # quick check, makemigrations --check if models changed
git push origin feature-branch
```
### 3. redeploy staging with the branch
```
cd ~/Devel/Ansible-Build
task play -i inventories playbooks/eventmanager/playbook.yml \
  -l bohr,bohr_eventmanager_staging \
  -e eventmanager_git_version=feature-company-registration

```