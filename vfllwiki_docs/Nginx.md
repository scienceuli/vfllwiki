---
tags:
- Tools
---

# Nginx

## Minimale Installation
Nginx Config:
```bash
sudo nano /etc/nginx/sites-available/vfllfobi_env
```
Settings:
```nginx
server {
    server_name fobidev.vfll.de;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/events_dev/gunicorn_dev.sock;
    }
}

```

Enable config und Restart:
```bash
sudo ln -s /etc/nginx/sites-available/vfllfobi_dev /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

