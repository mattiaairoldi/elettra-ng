# Local Setup

## Prerequisiti

- Docker.
- Docker Compose.
- `uv` opzionale per esecuzione locale fuori container.

Il percorso standard e' Docker Compose.

## Avvio Rapido

```bash
docker compose up -d db redis minio createbuckets mailpit
docker compose run --rm web uv run python manage.py migrate
docker compose up -d web worker
```

Seed opzionale dei macro-capitoli diagnostici iniziali:

```bash
docker compose run --rm web uv run python manage.py seed_diagnostic_chapters
```

Variabili AI utili in locale:

```env
AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT=4
AI_CONTEXT_COMPACTION_MESSAGE_THRESHOLD=8
AI_ESTIMATED_INPUT_COST_PER_1K_TOKENS=0
AI_ESTIMATED_OUTPUT_COST_PER_1K_TOKENS=0
```

Verifica:

```bash
curl http://127.0.0.1:8000/api/v1/health
docker compose ps
```

## URL Locali

- API: `http://127.0.0.1:8000/api/v1/`
- Health: `http://127.0.0.1:8000/api/v1/health`
- OpenAPI schema: `http://127.0.0.1:8000/api/v1/schema/`
- Swagger docs: `http://127.0.0.1:8000/api/v1/docs/`
- MinIO API: `http://127.0.0.1:9000`
- MinIO console: `http://127.0.0.1:9001`
- Mailpit UI: `http://127.0.0.1:8025`
- PostgreSQL host locale: `127.0.0.1:5433`

Credenziali locali MinIO:

```text
user: minio
password: minio-password
bucket: app-media
```

## Test

```bash
docker compose run --rm web uv run pytest -q
```

Ultima verifica: `89 passed`.

## OpenAPI

Generazione e validazione schema:

```bash
docker compose run --rm web uv run python manage.py spectacular --file /tmp/elettra-schema.yaml --validate --fail-on-warn
```

Il comando deve terminare senza warning.

## Migrazioni

```bash
docker compose run --rm web uv run python manage.py makemigrations --check --dry-run
docker compose run --rm web uv run python manage.py migrate
```

## Storage S3 / MinIO

Lo storage applicativo usa sempre S3-compatible tramite `django-storages`.

Verifica scrittura reale su MinIO:

```bash
docker compose run --rm web uv run python -c "from django.core.files.base import ContentFile; from django.core.files.storage import default_storage; name = default_storage.save('healthcheck/storage.txt', ContentFile(b'ok')); print(name, default_storage.exists(name)); default_storage.delete(name)"
```

Output atteso:

```text
healthcheck/storage.txt True
```

## Comandi Utili

```bash
docker compose ps
docker compose logs -f web
docker compose logs -f worker
docker compose down
```

Per fermare i container lasciando i volumi:

```bash
docker compose down
```

Per eliminare anche i dati locali:

```bash
docker compose down -v
```

Usare `down -v` solo quando si vuole resettare database, Redis e MinIO locali.

## Note

- Redis non espone piu' la porta host `6379`, per evitare conflitti con Redis locali gia' installati.
- PostgreSQL/PostGIS espone la porta host `5433`.
- Il bucket MinIO viene creato dal servizio `createbuckets`.
- Gli allegati privati restano non pubblici.
