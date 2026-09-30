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


```bash
./server.sh start
./server.sh status
curl -I http://127.0.0.1:8008/
```

Create `/etc/nginx/sites-available/sosh-server`:

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
sudo ln -s /etc/nginx/sites-available/sosh-server /etc/nginx/sites-enabled/sosh-server
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