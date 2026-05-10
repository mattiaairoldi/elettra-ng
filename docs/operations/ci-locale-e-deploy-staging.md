# CI Locale E Deploy Staging

Questo documento definisce il modello operativo scelto per arrivare a uno staging pubblico su VPS senza legare la logica di build a GitHub Actions, Gitea Actions o un altro provider specifico.

## Decisione

La logica di CI deve stare in script versionati nel repository. La piattaforma CI deve solo eseguire quegli script.

Percorso scelto:

1. oggi: esecuzione locale dopo commit;
2. oggi: build locale delle immagini Docker senza push;
3. staging: stessi script eseguiti da CI con push su registry e deploy SSH;
4. produzione: stessi script attivati da tag Git versionati, con approval manuale.

Il VPS non deve compilare l'applicazione. Deve solo scaricare immagini gia costruite, applicare migrazioni e riavviare i container.

## Principi

- Gli script devono essere POSIX shell quanto possibile, senza dipendenze specifiche di GitHub.
- Gli script devono fallire al primo errore.
- I tag immagine devono essere immutabili e basati su commit SHA o tag Git.
- Non usare `latest` per staging o produzione.
- Il Compose locale resta orientato allo sviluppo e puo usare `build:` e bind mount.
- Il Compose staging/produzione deve usare `image:` e non deve montare il repository dentro i container.
- Una sola immagine backend deve servire `web`, `worker` e `beat`; cambia solo il comando.
- Database, Redis e storage possono essere container in staging iniziale, ma non devono essere un vincolo architetturale per la produzione.

## Script Implementati

Gli script disponibili sono:

```text
scripts/ci/backend.sh
scripts/ci/mobile.sh
scripts/ci/build-images.sh
scripts/ci/local-all.sh
```

### `scripts/ci/backend.sh`

Esegue i controlli backend dentro Docker Compose:

```bash
docker compose run --rm web uv run pytest -q
docker compose run --rm web uv run python manage.py makemigrations --check --dry-run
docker compose run --rm web uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/elettra-schema.yml
```

### `scripts/ci/mobile.sh`

Esegue i controlli Flutter:

```bash
cd mobile/elettra_mobile
flutter pub get
flutter analyze
flutter test
flutter build web --dart-define=API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000/api/v1}"
flutter build apk --debug --dart-define=API_BASE_URL="${ANDROID_API_BASE_URL:-http://10.0.2.2:8000/api/v1}"
```

Per iOS, il controllo `flutter build ios --no-codesign` richiede runner macOS. Deve restare in pipeline quando disponibile, ma non puo essere requisito della CI locale Linux.

Flag utili:

- `BUILD_ANDROID_DEBUG=false` per saltare la build APK locale;
- `BUILD_WEB=false` per saltare la build web;
- `BUILD_IOS_NO_CODESIGN=true` per runner macOS;
- `RUN_ANALYZE=false` o `RUN_TESTS=false` per job specializzati.

### `scripts/ci/build-images.sh`

Costruisce immagini Docker versionate.

Comportamento locale iniziale:

```bash
GIT_SHA="$(git rev-parse --short=12 HEAD)"
docker build \
  -t "elettra-api:sha-${GIT_SHA}" \
  -t "elettra-api:local" \
  .
```

Comportamento futuro con registry:

```bash
REGISTRY=ghcr.io/owner/elettra \
PUSH=true \
scripts/ci/build-images.sh
```

Variabili supportate:

- `REGISTRY`: prefisso registry, per esempio `ghcr.io/owner/elettra`;
- `IMAGE_NAME`: nome immagine, default `elettra-api`;
- `IMAGE_REPOSITORY`: repository completo, se serve bypassare `REGISTRY/IMAGE_NAME`;
- `IMAGE_TAG`: tag principale, default `sha-<gitsha>`;
- `EXTRA_TAGS`: lista di tag aggiuntivi separati da spazio;
- `PUSH=true`: pubblica tutti i tag costruiti;
- `TAG_LOCAL=false`: evita il tag locale `local`.

Tag previsti:

- `sha-<gitsha>` per ogni build riproducibile;
- `staging-<gitsha>` quando la build viene candidata allo staging;
- `vX.Y.Z` per produzione da tag Git;
- `local` solo per sviluppo locale, mai per deploy remoto.

### `scripts/ci/local-all.sh`

Orchestra il controllo completo locale:

```bash
scripts/ci/backend.sh
scripts/ci/mobile.sh
scripts/ci/build-images.sh
```

Uso previsto dopo un commit:

```bash
scripts/ci/local-all.sh
```

## Modello Immagini

### Backend

Immagine unica:

```text
elettra-api:<tag>
```

Servizi che la usano:

- `web`: gunicorn Django;
- `worker`: Celery worker;
- `beat`: Celery beat quando servono task periodici.

Questo evita drift tra runtime web e worker.

### Flutter Web

La web app puo essere gestita in due modi:

1. artifact statico prodotto dalla CI e servito da Caddy/Nginx;
2. immagine separata `elettra-web:<tag>` con build Flutter copiata in un server statico.

Per staging pubblico e test mobile, la priorita e avere API pubblica stabile. La web app puo arrivare subito dopo, usando lo stesso `API_BASE_URL` staging.

## Compose Staging

Il Compose staging deve essere separato da quello locale, per esempio:

```text
deploy/compose.staging.yml
```

Caratteristiche:

- usa `image:` invece di `build:`;
- non monta `.:/app`;
- espone solo reverse proxy pubblico su `80/443`;
- non espone PostgreSQL, Redis, MinIO o Mailpit su internet;
- usa `.env.staging` sul VPS, non committato;
- usa healthcheck e restart policy;
- esegue `web`, `worker`, `db`, `redis`, `minio`, `mailpit` per lo staging iniziale.

Schema operativo:

```bash
docker compose -f deploy/compose.staging.yml pull
docker compose -f deploy/compose.staging.yml run --rm web uv run python manage.py migrate --noinput
docker compose -f deploy/compose.staging.yml up -d --remove-orphans
```

## Deploy Su VPS

Il VPS deve avere:

- Docker e Docker Compose plugin;
- accesso al registry;
- directory applicazione con `deploy/compose.staging.yml` e `.env.staging`;
- reverse proxy Caddy o Nginx con HTTPS;
- firewall con pubbliche solo `80`, `443` e SSH limitato.

Il deploy versionato e disponibile in:

```bash
scripts/deploy/staging.sh
```

Lo script legge una configurazione locale non versionata:

```bash
deploy/staging.local.env
```

File da preparare prima del primo deploy:

```bash
cp deploy/staging.local.env.example deploy/staging.local.env
cp .env.staging.example .env.staging
```

La configurazione `deploy/staging.local.env` contiene host, utente SSH, porta, path remoto, registry e tag immagine. Il file `.env.staging` contiene i segreti applicativi e viene copiato sul VPS come `.env.staging`.

Deploy staging previsto:

```bash
scripts/deploy/staging.sh
```

Rollback:

```bash
STAGING_IMAGE_TAG=sha-<gitsha-precedente> scripts/deploy/staging.sh
```

Le migrazioni irreversibili vanno trattate come blocco operativo prima del deploy produzione.

## Variabili Ambiente

Lo staging deve avere un `.env.staging` non committato. Il repository deve contenere solo un esempio:

```text
.env.staging.example
```

Valori obbligatori da separare dal locale:

- `DJANGO_SETTINGS_MODULE`;
- `DJANGO_SECRET_KEY`;
- `DJANGO_DEBUG=false`;
- `DJANGO_ALLOWED_HOSTS`;
- `APP_BASE_URL`;
- `WEB_APP_BASE_URL`;
- credenziali PostgreSQL;
- credenziali MinIO/S3;
- configurazione email;
- `JWT_*`;
- `OPENAI_API_KEY` se si abilita provider reale;
- `SENTRY_DSN` quando disponibile.

Mailpit in staging deve restare privato o protetto. Non va esposto pubblicamente senza autenticazione o VPN.

## Trigger Futuri

### Staging

Trigger consigliato:

- push su `main`;
- CI esegue test;
- CI builda immagini;
- CI pusha tag `sha-<gitsha>`;
- CI esegue deploy SSH sul VPS staging.

### Produzione

Trigger consigliato:

- tag Git `vX.Y.Z`;
- CI esegue test completi;
- CI builda immagini versionate;
- approval manuale;
- deploy produzione.

La produzione non deve dipendere dal branch `main` direttamente.

## Prossimi Step Implementativi

1. Eseguire un primo dry-run con `scripts/deploy/staging.sh --dry-run`.
2. Eseguire un primo deploy staging reale dopo avere pushato l'immagine su registry.
3. Aggiungere workflow backend/build immagini che invoca gli script.
4. Collegare GitHub Actions o Gitea Actions agli stessi script per push su registry e deploy SSH.
