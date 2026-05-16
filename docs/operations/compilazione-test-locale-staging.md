# Compilazione E Test In Locale E Test In Staging

Questo documento riassume il flusso operativo per lavorare in locale, costruire un'immagine Docker versionata e pubblicarla sul VPS di staging.

## Sviluppo E Test Locale

Per sviluppo rapido usare il Compose locale. Questo compose usa `build:` e monta il repository dentro il container, quindi riflette il codice locale.

```bash
docker compose up -d db redis minio createbuckets mailpit
docker compose run --rm web uv run python manage.py migrate
docker compose up -d web worker
```

Verifica base:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Test backend:

```bash
docker compose run --rm web uv run pytest -q
docker compose run --rm web uv run python manage.py makemigrations --check --dry-run
docker compose run --rm web uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/elettra-schema.yml
```

Mobile Flutter:

```bash
cd mobile/elettra_mobile
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Build Immagine Da Commit

Per staging non usare un tag casuale o `latest`. Il tag deve indicare il commit.

Flusso consigliato:

```bash
git status
git add <file>
git commit -m "Messaggio commit"

GIT_SHA="$(git rev-parse --short=12 HEAD)"
IMAGE_REPOSITORY=elettra-api IMAGE_TAG="sha-$GIT_SHA" TAG_LOCAL=false scripts/ci/build-images.sh
```

Il tag risultante sara:

```text
elettra-api:sha-<gitsha>
```

Per vedere le immagini disponibili:

```bash
docker images 'elettra-api'
```

## Configurazione Staging

I file locali non committati sono:

```text
.env.staging
deploy/staging.local.env
```

`.env.staging` contiene la configurazione applicativa e i segreti: database, MinIO, SMTP reale, Django secret, host consentiti.

`deploy/staging.local.env` contiene la configurazione del deploy: host SSH, directory remota, dominio, repository/tag immagine.

Dopo la build, aggiornare in `deploy/staging.local.env`:

```env
STAGING_IMAGE_REPOSITORY=elettra-api
STAGING_IMAGE_TAG=sha-<gitsha>
STAGING_UPLOAD_IMAGE=true
STAGING_PULL=false
```

Con `STAGING_UPLOAD_IMAGE=true` non serve un registry: lo script carica l'immagine sul VPS via SSH usando `docker save` e `docker load`.

## Deploy Staging

Prima fare sempre un dry-run:

```bash
scripts/deploy/staging.sh --dry-run
```

Se i comandi previsti sono corretti:

```bash
scripts/deploy/staging.sh
```

Lo script:

- copia `deploy/compose.staging.yml` e `deploy/Caddyfile.staging`;
- carica `.env.staging` sul VPS;
- carica l'immagine Docker se `STAGING_UPLOAD_IMAGE=true`;
- esegue le migrazioni;
- opzionalmente esegue i seed demo;
- avvia lo stack Docker;
- verifica `https://elettra.iapersonale.it/api/v1/health`.

## URL Da Verificare

```text
https://elettra.iapersonale.it/api/v1/health
https://elettra.iapersonale.it/api/v1/docs/
https://elettra.iapersonale.it/admin/
https://gio.sitoistituzionale.ovh/
```

## Nota Su Caddy

In staging Caddy gira dentro Docker ed e il reverse proxy unico su `80/443`.

Serve:

- `elettra.iapersonale.it` verso il backend Django;
- `gio.sitoistituzionale.ovh` come sito statico montato da `/var/www/html/giorgessi/www.giorgessi.it`.

I servizi host legacy `nginx`, `postgresql` e `supervisor` devono restare fermi per evitare collisioni di porte e runtime.
