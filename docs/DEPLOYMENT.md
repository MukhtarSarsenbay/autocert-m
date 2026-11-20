# Автосерт-М: server setup and CI/CD

This guide assumes a fresh Ubuntu 24.04 server, an SSH account called `deploy`,
and a separate checkout at `/opt/autocert-m`. Replace `SERVER_IP` with the server's
public IP address. The application initially runs over HTTP on port `8667`.
A domain and HTTPS are not configured by this repository.

Use a separate directory and an unused port if another application already runs
on this server. Do not point this deployment at another installation's database
or media directory. For an existing installation, back up its database and media
before updating it; changing POSTGRES values does not rename an existing database.

## 1. Install Docker and prepare the deployment account

On a fresh server, install Docker Engine and the Compose plugin using Docker's
[Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
Skip installation if both `docker version` and `docker compose version` work.

As your existing server administrator:

```bash
sudo apt-get update
sudo apt-get install -y git
sudo adduser deploy
sudo usermod -aG docker deploy
sudo systemctl enable --now docker
sudo mkdir -p /opt/autocert-m
sudo chown deploy:deploy /opt/autocert-m
```

Skip `adduser` if that account already exists. Log in again as `deploy` so its
new Docker group membership takes effect. Confirm these work without `sudo`:

```bash
docker version
docker compose version
```

## 2. Clone the repository on the server

As `deploy`:

```bash
git -c credential.helper= clone https://github.com/KaspiNet/autocert-m.git /opt/autocert-m
cd /opt/autocert-m
cp .env.example .env
chmod 600 .env
```

For a private repository, supply your GitHub username and a fine-grained personal
access token with **Contents: read** for this repository when Git prompts. Use the
token at the password prompt, not in the URL. Subsequent CI/CD deployments use
GitHub's automatically supplied, short-lived `GITHUB_TOKEN`.

For an existing checkout, preserve its `.env` instead of copying over it.

## 3. Configure the server environment

Generate two different random values, one for Django and one for PostgreSQL:

```bash
openssl rand -hex 32
openssl rand -hex 32
nano .env
```

Use the following settings, replacing the three placeholder values. Keep
`localhost` in the allowed hosts: container health checks use it.

```dotenv
APP_BIND_ADDRESS=0.0.0.0
APP_PORT=8667
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=PASTE_FIRST_RANDOM_VALUE
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,SERVER_IP
DJANGO_CSRF_TRUSTED_ORIGINS=http://SERVER_IP:8667,http://localhost:8667,http://127.0.0.1:8667
DJANGO_CSRF_COOKIE_NAME=autocert_m_csrftoken
DJANGO_SESSION_COOKIE_NAME=autocert_m_sessionid
DJANGO_SECURE_PROXY_SSL_HEADER=0
DJANGO_USE_X_FORWARDED_HOST=0
DJANGO_CSRF_COOKIE_SECURE=0
DJANGO_SESSION_COOKIE_SECURE=0
POSTGRES_DB=autocert_m
POSTGRES_USER=autocert_m
POSTGRES_PASSWORD=PASTE_SECOND_RANDOM_VALUE
POSTGRES_HOST=db
POSTGRES_PORT=5432
PDF_CONVERTER_URL=http://converter:3000
PDF_CONVERTER_TIMEOUT=120
CORS_ALLOW_ALL_ORIGINS=0
CORS_ALLOW_CREDENTIALS=1
```

If port `8667` is occupied, choose another port in `APP_PORT` and use that same
port in the trusted origins and browser URL. Check before starting:

```bash
ss -ltn | grep ':8667 ' || true
docker compose config --quiet
```

The server needs outbound access to GitHub and container/Python package
registries. GitHub-hosted runners need inbound SSH access. For direct browser
access, allow the chosen application port in the provider's firewall. Docker
published ports can bypass UFW; see Docker's installation documentation.

For private access instead, set `APP_BIND_ADDRESS=127.0.0.1`, then use this tunnel
from your computer and open `http://localhost:8667`:

```bash
ssh -L 8667:127.0.0.1:8667 deploy@SERVER_IP
```

Before using the application publicly with sensitive records, configure HTTPS.
If a TLS reverse proxy is added, it must preserve the external Host and HTTPS
scheme through `nginx/default.conf` (which currently sets the scheme to its own
HTTP connection). Then set the HTTPS trusted origin and secure-cookie settings,
set `DJANGO_SECURE_PROXY_SSL_HEADER=1`, and restrict the application port to that
trusted proxy. Simply turning on the secure-cookie settings on an HTTP URL will
prevent the browser from sending the session cookie.

## 4. Give GitHub Actions SSH access to the server

On your computer, create a dedicated key. Keep the private key out of the
repository and do not reuse a personal SSH key:

```bash
ssh-keygen -t ed25519 -C autocert-m-ci -f ~/.ssh/autocert_m_ci -N ""
```

Install `~/.ssh/autocert_m_ci.pub` in the server deployment account's
`~/.ssh/authorized_keys`. If password login is available, this command does it:

```bash
ssh-copy-id -i ~/.ssh/autocert_m_ci.pub deploy@SERVER_IP
```

Otherwise, use your existing administrator access to append the public key to
`/home/deploy/.ssh/authorized_keys`, with ownership `deploy:deploy`, mode `700`
for `.ssh`, and mode `600` for `authorized_keys`.

Verify from your computer:

```bash
ssh -i ~/.ssh/autocert_m_ci deploy@SERVER_IP 'cd /opt/autocert-m && docker compose version'
```

Use `-p YOUR_SSH_PORT` with SSH commands if the server does not use port `22`.

## 5. Enable Actions and create repository secrets

Open <https://github.com/KaspiNet/autocert-m/settings/actions>.
Enable GitHub Actions and allow `actions/checkout` and `appleboy/ssh-action`.
Organization policies may need an administrator to allow these actions.

Open **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
| --- | --- |
| `SERVER_HOST` | Server IP address or SSH hostname, without `http://` |
| `SERVER_USER` | `deploy` |
| `SERVER_SSH_KEY` | Entire contents of `~/.ssh/autocert_m_ci`, including BEGIN/END lines |
| `SERVER_SSH_PORT` | `22`, or your custom SSH port |
| `SERVER_APP_DIR` | `/opt/autocert-m` |

Do not create a custom `GH_TOKEN` or `GITHUB_TOKEN` secret. The workflow uses
GitHub's built-in token with `contents: read` permission.

Official instructions: [repository secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets),
[enabling workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).

## 6. Push the configuration and run the first deployment

After the server and secrets are ready, commit and push the CI/CD changes from
your development computer:

```bash
git add .github/workflows/deploy.yml docker-compose.yml .env.example docs/DEPLOYMENT.md
git commit -m "Configure CI/CD and document server deployment"
git push origin main
```

The push starts **Actions → CI/CD**. You can also select **Run workflow → main**
when this workflow is on GitHub's default branch. If the workflow is disabled,
select **Enable workflow** first.

The workflow:

1. Builds the Docker application image and collects static files.
2. Runs Django configuration checks and the `testlog` / `cert` test suites in CI.
3. Deploys only if those checks pass, and only for `main`.
4. Checks out the exact tested commit on the server, rebuilds the application,
   applies migrations, and checks the PDF converter and container health.

Pull requests to `main` run CI without deploying or using the server secrets.
A failed CI job prevents deployment. Deployments are serialized. Deployment is
not atomic and has no automatic rollback; a failure after the server update may
require intervention. Tracked server files are overwritten on deployment, so
make application changes in Git, not directly in `/opt/autocert-m`.

## 7. Create your first administrator and verify the application

After the first successful deployment, run on the server:

```bash
cd /opt/autocert-m
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py ensure_testlog_creators
docker compose ps
curl --fail http://127.0.0.1:8667/health/
```

The health response should be `ok`. Open `http://SERVER_IP:8667/` and sign in.
The admin lives at `/`, not `/admin/`. Use your selected port if you changed it.

Future pushes to `main` automatically repeat the build, tests, and deployment.
The database is stored in `postgres_data/`, and uploads in `media/`, outside the
containers. Keep backups of both the database and uploads.

## Troubleshooting

Run on the server:

```bash
cd /opt/autocert-m
docker compose ps
docker compose logs --tail=100 web proxy db converter
docker compose exec web python manage.py check_pdf_converter
```

- SSH authentication failed: verify the private key secret, public key installation,
  username, port, and reachability from GitHub-hosted runners.
- Docker permission denied: verify the `deploy` user's Docker group membership and
  start a new SSH session.
- Port already allocated: change `APP_PORT` and update the trusted origins.
- HTTP 400 / unhealthy web: keep `localhost` and your actual hostname in
  `DJANGO_ALLOWED_HOSTS`.
- CSRF 403: use the exact browser scheme, hostname, and port in
  `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Database authentication failed after changing `.env`: existing PostgreSQL data
  retains the original credentials; changing environment variables does not
  change an initialized database's password.
- Missing new branding: verify the deployed commit and the two cookie settings in
  the server's existing `.env`. The deployment intentionally preserves `.env`.

## Document recognition in acts

On the act form, selecting a PDF/JPG in **Приложения 1** recognizes the identity
card; **Приложения 2** recognizes the vehicle document. Review the populated
fields before saving. Empty recognition results preserve existing field values.
Uploads go through the authenticated Django endpoints under
`/api/actus/documents/recognize/`, which forward them to the configured reader.

The service URLs supplied by the working installation are defaults in Compose
and Django. Override `DOCUMENT_READER_ID_URL` and `DOCUMENT_READER_VIN_URL` in the
server `.env` if the service changes. Optional settings are
`DOCUMENT_READER_CONNECT_TIMEOUT` (5 seconds), `DOCUMENT_READER_READ_TIMEOUT`
(60 seconds), and `DOCUMENT_READER_MAX_FILE_SIZE` (15728640 bytes / 15 MiB).
After changing these settings, recreate the web container:

```bash
docker compose up -d --force-recreate web
```

CI also runs the `actus` recognition tests. Unit tests mock the upstream reader;
verifying OCR accuracy requires uploading a real document after deployment.

## EVAK registration and call status

`docker compose up -d --build` also starts `evak-sync`. It waits for the web
service and database migrations, then checks acts created in the last 30 days.
Checks start every 300 seconds; if a scan takes longer, the next starts after it
finishes. Acts with both dates already filled are skipped. Failed requests and
empty responses preserve existing dates and are retried in subsequent scans.

On the acts list, the checkbox cell becomes yellow for a registration date and
green for a call date. Green takes priority. Refresh the page to see new dates
and colors. There is no next-day timer: green requires a call date from EVAK.

Check the worker after deployment:

```bash
docker compose ps evak-sync
docker compose logs --tail=50 evak-sync
```

Logs report `checked`, `updated`, `failed`, and `skipped` for each scan. A running
container alone does not prove successful EVAK requests; check these counts.
To run a scan manually:

```bash
docker compose exec web python manage.py sync_evak
```

Optional `.env` settings: `EVAK_LOOKBACK_DAYS=30`, `EVAK_SYNC_INTERVAL=300`,
`EVAK_CONNECT_TIMEOUT=5`, `EVAK_READ_TIMEOUT=20`, and
`EVAK_STATUS_URL=https://evak.online/search_reg.php`. After changing them, run
`docker compose up -d web evak-sync`. Remove any old cron entry that invokes
`registred.py` when enabling the worker, to avoid duplicate scans. The legacy
script remains available as a single-pass wrapper for the same command.
