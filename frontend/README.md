# Elettra Frontend MVP

Frontend React/TypeScript per validare il flusso MVP su API reali.

## Avvio

Backend e dati demo:

```bash
docker compose up -d db redis minio createbuckets mailpit
docker compose run --rm web uv run python manage.py migrate
docker compose run --rm web uv run python manage.py seed_mvp_demo
docker compose up -d web worker
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

URL locale: `http://127.0.0.1:5173`

## Credenziali Demo

- Cliente: `demo.customer@example.com` / `Password123!`
- Tecnico: `demo.pro@example.com` / `Password123!`

## Configurazione API

Default:

```text
http://127.0.0.1:8000/api/v1
```

Override:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev
```

## Verifiche

```bash
npm run lint
npm run build
```
