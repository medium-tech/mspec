# mtech




## Ubuntu 24.04 deployment

This setup runs the app with uWSGI on a private localhost port, uses Nginx for
HTTP/HTTPS, and uses Let's Encrypt certificates managed by Certbot. Replace
`example.com`, `deploy`, and paths below with the values for the generated app.

### Install packages

Do not install the project as an editable Python module in production.

```bash
sudo apt update
sudo apt install -y python3.12-venv uwsgi uwsgi-plugin-python3 nginx certbot python3-certbot-nginx mediainfo ffmpeg
```

Create or activate the application's virtual environment and install its
dependencies as usual. The app directory should be owned by the deployment
user, for example `/srv/example-app`.

```bash
sudo adduser --system --group --home /srv/example-app deploy
sudo mkdir -p /srv/example-app
sudo chown -R deploy:deploy /srv/example-app
sudo -iu deploy
cd /srv/example-app
python3 -m venv .venv
source .venv/bin/activate
```

### Configure uWSGI

In `.env`, use the Linux config and production URLs. The public URL must be
HTTPS; leaving `localhost` here causes links and verification emails to point
at the wrong host.

```dotenv
CONFIG_FILE=uwsgi-linux.yaml
MAPP_CLIENT_HOST=https://example.com
MAPP_EMAIL_VERIFICATION_URL=https://example.com/com/verify-email-address
MAPP_EMAIL_INVITE_USER_URL=https://example.com/social/account
MAPP_SERVER_DEVELOPMENT_MODE=false
MAPP_AUTH_SECRET_KEY=<output of: openssl rand -hex 32>
```

Edit `uwsgi-linux.yaml` so uWSGI is reachable only from Nginx. Keep the
existing settings, but change its socket line to:

```yaml
	http-socket: 127.0.0.1:8008
```

Do not bind this socket to `:8008` or expose it through a cloud load balancer.
Start it once and verify the private endpoint before configuring Nginx:

```bash
./server.sh start
./server.sh status
curl -I http://127.0.0.1:8008/
```

### Run uWSGI with systemd

Create `/etc/systemd/system/example-app.service` as root:

```ini
[Unit]
Description=example app uWSGI server
After=network.target

[Service]
Type=forking
User=deploy
Group=deploy
WorkingDirectory=/srv/example-app
EnvironmentFile=/srv/example-app/.env
ExecStart=/srv/example-app/server.sh start
ExecStop=/srv/example-app/server.sh stop
ExecReload=/srv/example-app/server.sh restart
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now example-app
sudo systemctl status example-app
sudo journalctl -u example-app -f
```

### Configure DNS, firewall, and Nginx

Create an `A` (and, if used, `AAAA`) DNS record for `example.com` pointing to
the server. Wait until DNS resolves before requesting the certificate. Allow
SSH, HTTP, and HTTPS, but do not open port `8008`:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status verbose
```

Create `/etc/nginx/sites-available/example-app`:

```nginx
server {
	listen 80;
	listen [::]:80;
	server_name example.com www.example.com;

	client_max_body_size 50m;

	location / {
		proxy_pass http://127.0.0.1:8008;
		proxy_http_version 1.1;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_set_header X-Forwarded-Host $host;
	}
}
```

Enable and validate the site:

```bash
sudo ln -s /etc/nginx/sites-available/example-app /etc/nginx/sites-enabled/example-app
sudo nginx -t
sudo systemctl reload nginx
curl -I http://example.com/
```

Remove the default site if it is still enabled and conflicts with this
server_name:

```bash
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

### Issue and install the SSL certificate

Certbot can update the Nginx configuration and add the HTTP-to-HTTPS redirect.
Run it after DNS and the HTTP site are working:

```bash
sudo certbot --nginx -d example.com -d www.example.com
sudo certbot certificates
curl -I http://example.com/
curl -I https://example.com/
```

Choose the redirect option when prompted. Certbot stores certificates under
`/etc/letsencrypt/live/example.com/`; do not edit files in that directory.
Nginx should reference the managed paths created by Certbot:

```nginx
ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

### Renewal and monitoring

Ubuntu normally installs a `certbot.timer` that runs renewal checks twice a
day. Renewal is safe to run repeatedly because Certbot renews only when the
certificate is near expiry. Verify the timer and perform a dry run:

```bash
systemctl list-timers certbot.timer
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
sudo journalctl -u certbot.service --since today
```

Check the complete request path and certificate details:

```bash
sudo nginx -t
sudo systemctl status nginx example-app
curl -fsS https://example.com/ >/dev/null && echo 'HTTPS request succeeded'
openssl s_client -connect example.com:443 -servername example.com </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
sudo ss -ltnp | grep -E ':(80|443|8008)\b'
```

Port `8008` should show `127.0.0.1:8008`, while ports `80` and `443` should
be owned by Nginx. After a successful renewal, verify Nginx picked up the new
certificate:

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -Iv https://example.com/
```

### Deploying updates

```bash
ssh deploy@example.com
cd /srv/example-app
git pull
source .venv/bin/activate
pip install --upgrade mspec
sudo systemctl restart example-app
sudo systemctl status example-app
```