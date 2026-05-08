# Project Tracker

## Obiettivo Corrente

Evolvere lo spike diagnostico verso un modello ibrido chat-first con macro-capitoli, scelte cablate minime e contesto AI ottimizzato.

## In Corso

- [ ] Preparare implementazione macro-capitoli diagnostici e contesto compatto.

## Todo

- [ ] Valutare utente non-root per il container `worker`.
- [ ] Definire macro-capitoli iniziali: elettrico, elettrodomestici, idraulica, climatizzazione, domotica, sicurezza, manutenzione generale.
- [ ] Definire opzioni cablate minime per elettrodomestici e problemi elettrici.
- [ ] Decidere criteri di sicurezza non negoziabili per risposte AI.
- [ ] Estendere `AiDiagnosticSnapshot` con macro-capitolo, asset/famiglia tecnica e contesto compatto.
- [ ] Implementare `build_diagnostic_context(session)` per ridurre storico inviato al provider.
- [ ] Definire soglie di compattazione storico e metadati costo/token.
- [ ] Definire 5 scenari reali per verifica qualitativa dello spike.
- [ ] Decidere quali contenuti di `../elettra` usare come corpus di test, non come import.
- [ ] Decidere se i professionisti seed saranno demo o reali.
- [ ] Decidere strategia seed/conversione.
- [ ] Valutare se `DiagnosticFlow` deve restare solo per guide curate/fallback.

## Fatto

- [x] Convertito il PDF sorgente in documento canonico Markdown.
- [x] Creata direttiva implementativa.
- [x] Creato piano implementativo dettagliato.
- [x] Organizzata documentazione in `docs/`.
- [x] Verificata disponibilita' locale di Docker e Docker Compose.
- [x] Importata baseline backend da `../elettra2`.
- [x] Creati `.gitignore`, `.dockerignore` e `.env.example`.
- [x] Aggiornate dipendenze a Django 5.2 LTS.
- [x] Rinominato package Python in `elettra-ng-api`.
- [x] Integrato GeoDjango/PostGIS.
- [x] Aggiunti campi `PointField` su `Property`, `Asset` e `ProfessionalProfile`.
- [x] Aggiunto serializer coordinate `GeoPointField`.
- [x] Aggiunto ordinamento professionisti per distanza quando vengono passate coordinate.
- [x] Confermata configurazione S3-only tramite `django-storages`.
- [x] Creato Dockerfile con librerie GIS.
- [x] Creato Docker Compose completo: web, worker, beat, PostgreSQL/PostGIS, Redis, MinIO, Mailpit.
- [x] Applicate migrazioni su PostgreSQL/PostGIS Docker.
- [x] Verificata scrittura reale su MinIO (`healthcheck/storage.txt True`).
- [x] Eseguita suite test nel container: `60 passed`.
- [x] Verificato `manage.py check` nel container.
- [x] Verificato `makemigrations --check --dry-run` nel container.
- [x] Avviati servizi persistenti `web` e `worker`.
- [x] Verificati endpoint reali: health, schema e docs rispondono `200`.
- [x] Creata documentazione `docs/operations/local-setup.md`.
- [x] Inizializzato repository Git su branch `main`.
- [x] Rifinito schema OpenAPI per API auth.
- [x] Rifinito schema OpenAPI per `GeoPointField`.
- [x] Rifiniti type hint/schema dei campi calcolati AI e professionisti.
- [x] Eliminati warning OpenAPI con `spectacular --validate --fail-on-warn`.
- [x] Eseguita suite test dopo rifinitura OpenAPI: `60 passed`.
- [x] Creato documento decisionale `docs/operations/decisioni-prima-import-elettra.md`.
- [x] Creato documento di contesto `docs/product/ipotesi-diagnostica-ai-dinamica.md`.
- [x] Aggiunto spike tecnico per diagnostica AI dinamica con `AiDiagnosticSnapshot`.
- [x] Aggiunto endpoint `POST /api/v1/ai/sessions/{id}/diagnostic-turns`.
- [x] Aggiunto endpoint `GET /api/v1/ai/sessions/{id}/diagnostic-snapshot`.
- [x] Aggiunto evento pratica `ai_diagnostic_progress`.
- [x] Creato documento operativo `docs/operations/ai-diagnostic-spike.md`.
- [x] Confermata direzione diagnostica ibrida chat-first.
- [x] Creato piano `docs/operations/piano-implementativo-diagnostica-chat-first.md`.

## Decisioni Confermate

- `elettra2` e' la baseline tecnica.
- `elettra-ng` e' il repository definitivo.
- Storage allegati solo S3-compatible.
- MinIO obbligatorio in locale.
- PostgreSQL deve includere PostGIS.
- Docker Compose e' il percorso locale standard.

## Note Operative

- Non importare `.env`, `.venv`, cache, egg-info o dati sensibili da `../elettra2`.
- API locale attiva su `http://127.0.0.1:8000/api/v1/`.
- Mailpit locale attivo su `http://127.0.0.1:8025`.
- MinIO console locale attiva su `http://127.0.0.1:9001`.
- Redis non espone la porta host per evitare conflitti con installazioni locali.
- Nessun import dati da `../elettra` deve partire prima delle decisioni nel documento dedicato.
- La UX diagnostica prevista e' ibrida, ma prioritariamente chat.
- Lo spike AI dinamico e' implementato per validazione tecnica, non per generare contenuti pubblici automaticamente.
- Gli alberi diagnostici estesi non sono il modello principale da implementare in questa fase.
