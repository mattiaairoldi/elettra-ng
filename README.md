# Elettra NG

Repository di sviluppo del nuovo progetto Elettra.

## Avvio Locale

```bash
docker compose up -d db redis minio createbuckets mailpit
docker compose run --rm web uv run python manage.py migrate
docker compose up -d web worker
```

API locale: `http://127.0.0.1:8000/api/v1/`

Frontend MVP:

```bash
docker compose run --rm web uv run python manage.py seed_mvp_demo
cd frontend
npm install
npm run dev
```

Frontend locale: `http://127.0.0.1:5173`

## Documenti Principali

- [Stato attuale e prossimo step](docs/operations/stato-attuale.md)
- [Progetto Elettra canonico](docs/product/progetto-elettra-canonico.md)
- [Sintesi progetto](docs/product/elettra-sintesi-progetto.md)
- [Direttiva implementativa](docs/architecture/direttiva-implementativa.md)
- [Modello organizzazioni e permessi](docs/architecture/modello-organizzazioni-permessi.md)
- [Piano implementativo dettagliato](docs/operations/piano-implementativo-dettagliato.md)
- [Ipotesi diagnostica AI dinamica](docs/product/ipotesi-diagnostica-ai-dinamica.md)
- [Spike diagnostica AI dinamica](docs/operations/ai-diagnostic-spike.md)
- [Piano diagnostica ibrida chat-first](docs/operations/piano-implementativo-diagnostica-chat-first.md)
- [Astrazione provider AI](docs/operations/ai-provider-abstraction.md)
- [Setup locale](docs/operations/local-setup.md)
- [CI locale e deploy staging](docs/operations/ci-locale-e-deploy-staging.md)
- [Project tracker](docs/operations/project-tracker.md)
- [Decisioni prima dell'import da elettra](docs/operations/decisioni-prima-import-elettra.md)
- [PDF sorgente](docs/sources/Progetto_Elettra.pdf)

## CI Locale

Esecuzione completa locale, pensata per essere riusata anche da GitHub Actions o Gitea Actions:

```bash
scripts/ci/local-all.sh
```
