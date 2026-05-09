# Piano Implementativo Dettagliato

> Piano operativo per trasformare `elettra-ng` nel repository definitivo del nuovo Elettra.
> Questo documento serve come guida di lavoro quando verrà dato il via allo sviluppo autonomo.
> Fonti principali: `docs/product/progetto-elettra-canonico.md`, `docs/architecture/direttiva-implementativa.md`, analisi dei progetti `../elettra` e `../elettra2`.

## Obiettivo

Costruire il nuovo Elettra partendo da `../elettra2` come baseline tecnica, evitando una riscrittura da zero non necessaria.

Il risultato atteso è un backend modulare, avviabile e testato, centrato su:

- gestione casa/sedi;
- asset tecnici;
- diagnosi guidata;
- pratiche/casi;
- allegati su storage S3-compatible;
- professionisti geolocalizzati;
- appuntamenti;
- AI contestuale;
- backoffice operativo.

## Principio Guida

`elettra2` è la base tecnica.
`elettra` è archivio di valore funzionale.
`elettra-ng` è il repository definitivo.

Non si devono importare vecchi vincoli per compatibilità con il client Flutter storico.
Le API nuove devono rappresentare il dominio, non la UI esistente.

## Decisioni Già Prese

- Usare `elettra2` come punto di partenza.
- Non ripartire da zero salvo blocchi tecnici gravi.
- Stack backend: Django 5.2 LTS, DRF, PostgreSQL/PostGIS, Redis, Celery.
- Storage allegati: solo S3-compatible tramite `django-storages`.
- Locale: Docker Compose con PostgreSQL/PostGIS, Redis, MinIO, Celery, SMTP catcher.
- Backoffice iniziale: Django Admin.
- API pubbliche: `/api/v1/`.
- Primo MVP senza videochiamate, pagamenti, AI immagini, marketplace avanzato.
- Identità globale con modello unico `Organization`, membership scoped e piani iniziali `personal`/`professional`.
- Il `Case` nasce personale/non assegnato e può essere condiviso selettivamente con professionisti.
- `Property` e `Case` appartengono a una `Organization`; `Asset` appartiene sempre a una `Property`.
- Conversazioni modellate come thread flessibili: `Conversation` + `ConversationPost`.

## Fase 0 - Preparazione Repository

### Scopo

Preparare `elettra-ng` come repository ordinato prima di importare codice.

### Attività

- Verificare struttura corrente del repository.
- Mantenere in root solo file operativi essenziali.
- Conservare documentazione in `docs/`.
- Creare tracker operativo in `docs/operations/project-tracker.md`.
- Aggiungere `.gitignore` adeguato a Python, Django, Docker, env locali, cache, media temporanei.
- Creare `.env.example` iniziale.
- Decidere se inizializzare Git se il repository non è ancora versionato.

### File attesi

- `README.md`
- `.gitignore`
- `.env.example`
- `docs/product/progetto-elettra-canonico.md`
- `docs/architecture/direttiva-implementativa.md`
- `docs/operations/piano-implementativo-dettagliato.md`
- `docs/operations/project-tracker.md`
- `docs/sources/Progetto_Elettra.pdf`

### Criteri di completamento

- Struttura documentale pulita.
- README con link ai documenti principali.
- Tracker operativo creato.
- Nessun file temporaneo o artefatto generato in root.

## Fase 1 - Import Di `elettra2`

### Scopo

Portare in `elettra-ng` la base backend già funzionante di `../elettra2`.

### Attività

- Copiare lo scaffold Django da `../elettra2`.
- Mantenere la struttura modulare:
  - `config`
  - `apps/identity`
  - `apps/taxonomy`
  - `apps/troubleshooting`
  - `apps/cases`
  - `apps/professionals`
  - `apps/appointments`
  - `apps/attachments`
  - `apps/ai_assistant`
  - `apps/common`
- Portare `manage.py`, `pyproject.toml`, `uv.lock` se coerente.
- Portare i test esistenti.
- Portare documenti tecnici utili da `../elettra2/docs/` solo se ancora attuali.
- Aggiornare naming progetto dove necessario.
- Evitare riferimenti concettuali troppo generici se il repo è ormai Elettra, mantenendo però API client-agnostiche.

### Regole

- Non cambiare logica durante la copia, salvo fix necessari per avvio.
- Non importare `.env` reale.
- Non importare `.venv`, cache, egg-info o file generati.
- Non importare dati sensibili.

### Criteri di completamento

- Codice backend presente in `elettra-ng`.
- Dipendenze installabili.
- Test copiati.
- Nessun segreto importato.

## Fase 2 - Stack Docker Locale

### Scopo

Rendere l'ambiente locale riproducibile con un solo comando.

### Servizi Docker Compose

- `web`: Django/DRF.
- `worker`: Celery worker.
- `beat`: Celery beat, opzionale ma previsto.
- `db`: PostgreSQL con PostGIS.
- `redis`: broker, cache e rate limiting.
- `minio`: storage S3-compatible.
- `createbuckets` o init equivalente per creare bucket MinIO.
- `mailpit`: SMTP catcher locale.

### Attività

- Creare `Dockerfile`.
- Creare `docker-compose.yml`.
- Creare eventuale `docker/entrypoint.sh`.
- Configurare healthcheck per `db`, `redis`, `minio`, `mailpit`.
- Usare volumi nominati per database, Redis e MinIO.
- Pin delle immagini, evitando `latest`.
- Aggiornare `.env.example` con variabili Docker.
- Aggiornare README o `docs/operations/local-setup.md`.

### Variabili minime

```env
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,web

POSTGRES_DB=elettra_ng
POSTGRES_USER=elettra
POSTGRES_PASSWORD=elettra
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio-password
AWS_STORAGE_BUCKET_NAME=app-media
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_S3_REGION_NAME=us-east-1
AWS_S3_ADDRESSING_STYLE=path

EMAIL_HOST=mailpit
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@local.test
```

### Criteri di completamento

- `docker compose up` avvia tutto lo stack.
- `web` raggiunge il database.
- `worker` si collega a Redis.
- MinIO ha il bucket applicativo.
- Email locali intercettate da Mailpit.

## Fase 3 - Aggiornamento Stack Applicativo

### Scopo

Allineare la baseline tecnica alle decisioni finali.

### Attività

- Fissare Django a `5.2.x`.
- Verificare compatibilità DRF, drf-spectacular, django-storages, Celery.
- Aggiungere o confermare `django.contrib.gis`.
- Usare backend PostgreSQL GIS.
- Abilitare estensione PostGIS.
- Confermare storage S3-only.
- Rimuovere ogni fallback applicativo a filesystem locale per allegati.
- Verificare OpenAPI.
- Verificare configurazione logging e Sentry predisposta.

### Criteri di completamento

- `python manage.py check` verde.
- Migrazioni applicabili da zero.
- OpenAPI disponibile.
- Storage default punta sempre a S3.
- PostGIS abilitato.

## Fase 4 - Revisione Modello Geografico

### Scopo

Preparare bene il dominio geolocalizzato senza sovra-progettare.

### Attività

- Sostituire nuovi campi `lat/lng` con `PointField` dove opportuno.
- Aggiungere `location` a `Property`.
- Aggiungere `location` a `ProfessionalProfile`.
- Valutare `location` opzionale su `Asset`.
- Mantenere SRID `4326`.
- Aggiungere indici spaziali.
- Aggiungere serializer coerenti per input/output coordinate.
- Aggiungere test su salvataggio e ordinamento per distanza, se implementato subito.

### Fuori Perimetro Iniziale

- Poligoni area operativa.
- Ottimizzazione percorsi.
- Routing su mappa.
- Geocoding automatico indirizzi.

### Criteri di completamento

- Coordinate salvabili come dato geografico.
- Migrazioni pulite.
- API non espongono un formato fragile.

## Fase 5 - Consolidamento Dominio MVP

### Scopo

Rendere `Case` il centro operativo del prodotto.
Allineare identità, organizzazioni e permessi al modello descritto in [Modello Organizzazioni E Permessi](../architecture/modello-organizzazioni-permessi.md).

### Attività

- Introdurre o rifinire:
  - `Organization`
  - `OrganizationPlan`
  - `OrganizationMembership`
  - `Conversation`
  - `ConversationPost`
  - `ConversationParticipant`
  - `CaseShareRequest`
  - membership role/scope/status
  - preferenze tecnici come riferimento a membership professionale
- Collegare `Property` a `Organization`.
- Collegare `Case` a `owner_organization` e `requester`.
- Mantenere `Case.property` opzionale.
- Mantenere `Asset` sempre collegato a `Property`.
- Modellare allegati con owner risolto dal contesto proprietario, evitando allegati orfani.
- Rivedere stati di `Case`.
- Rivedere transizioni consentite per ruolo.
- Verificare relazione `Case` con:
  - `Property`
  - `Asset`
  - `DiagnosticFlow`
  - `DiagnosticNode`
  - `Attachment`
  - `CaseNote`
  - `CaseEvent`
  - `Appointment`
  - `AiSession`
- Verificare permessi per utente finale, organization admin, tecnico, amministrativo e platform owner.
- Implementare il principio: il caso nasce non assegnato e può essere condiviso dopo.
- Modellare richiesta di condivisione, accettazione/rifiuto, partecipazione e revoca.
- Modellare chat utente-professionista come conversazione flessibile, non come relazione rigida 1:1.
- Modellare condivisione selettiva di riepilogo, chat diagnostica e allegati.
- Prevedere advice sui dati sensibili e sui metadati degli allegati.
- Rendere gli eventi storici append-only o read-only dove necessario.
- Definire in modo chiaro quando una diagnosi genera una pratica.
- Definire in modo chiaro quando una pratica richiede escalation professionista.

### Workflow Minimo

1. Utente apre problema.
2. Utente sceglie o avvia percorso diagnostico.
3. Sistema registra avanzamento nel caso.
4. Utente collega eventuale immobile e allega foto/documenti.
5. AI può aiutare sul caso senza ricevere automaticamente tutti gli allegati.
6. Se necessario, utente sceglie cosa condividere con tecnico/organizzazione.
7. Tecnico o organizzazione accetta o rifiuta la richiesta.
8. Dopo accettazione si apre o collega una conversazione utente-professionista.
9. Appuntamento o preventivo di massima vengono richiesti e gestiti.
10. Caso viene risolto, chiuso o cancellato.
11. L'utente può revocare la condivisione; resta visibile al professionista solo lo storico conversazione già scambiato.

### Criteri di completamento

- Workflow documentato.
- API principali coerenti.
- Test su permessi e transizioni.

## Fase 6 - API V1 E Contratti

### Scopo

Stabilizzare contratti backend prima del frontend.

### Endpoint Minimi

- `GET /api/v1/health`
- `GET /api/v1/schema/`
- `GET /api/v1/docs/`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/verify-email`
- `GET /api/v1/organizations`
- `GET /api/v1/organizations/{id}`
- `GET /api/v1/organizations/{id}/memberships`
- `POST /api/v1/organizations/{id}/memberships`
- `GET /api/v1/categories`
- `GET /api/v1/tags`
- `GET /api/v1/flows`
- `GET /api/v1/flows/{id}`
- `GET /api/v1/flows/{id}/nodes`
- `GET /api/v1/nodes/{id}`
- `GET /api/v1/nodes/{id}/options`
- `GET /api/v1/properties`
- `POST /api/v1/properties`
- `GET /api/v1/assets`
- `POST /api/v1/assets`
- `GET /api/v1/cases`
- `POST /api/v1/cases`
- `GET /api/v1/cases/{id}`
- `PATCH /api/v1/cases/{id}`
- `GET /api/v1/cases/{id}/events`
- `GET /api/v1/cases/{id}/notes`
- `POST /api/v1/cases/{id}/notes`
- `GET /api/v1/cases/{id}/share-requests`
- `POST /api/v1/cases/{id}/share-requests`
- `POST /api/v1/case-share-requests/{id}/accept`
- `POST /api/v1/case-share-requests/{id}/reject`
- `POST /api/v1/case-share-requests/{id}/revoke`
- `POST /api/v1/cases/{id}/troubleshooting/start`
- `POST /api/v1/cases/{id}/troubleshooting/progress`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{id}`
- `GET /api/v1/conversations/{id}/posts`
- `POST /api/v1/conversations/{id}/posts`
- `GET /api/v1/professionals`
- `POST /api/v1/appointments`
- `GET /api/v1/appointments`
- `POST /api/v1/attachments`
- `GET /api/v1/attachments/{id}`
- `POST /api/v1/ai/sessions`
- `POST /api/v1/ai/sessions/{id}/messages`
- `GET /api/v1/ai/sessions/{id}`

### Regole API

- JSON client-agnostico.
- Errori HTTP standard.
- Nessun formato ereditato dal vecchio Flutter.
- OpenAPI aggiornata.
- Permessi testati.
- Nessun endpoint legacy.

### Criteri di completamento

- OpenAPI coerente con endpoint reali.
- Test di contratto sui flussi principali.
- Documentazione locale aggiornata.

## Fase 7 - Import Contenuti Da `../elettra`

### Scopo

Recuperare valore dal prototipo storico senza importare debito.

### Fonti

- `../elettra/django_backend/seed/`
- `../elettra/django_backend/core/models.py`
- `../elettra/docs/EVOLUZIONE.md`
- `../elettra/docs/PROGRESS.md`
- `../elettra/docs/progetto/`
- client Flutter solo per insight UX.

### Dati Da Recuperare

- nodi e risposte;
- tag;
- template promemoria;
- professionisti demo;
- categorie tecniche;
- esempi di promemoria;
- logiche testuali dei percorsi diagnostici.

### Strategia

- Non fare migrazione cieca.
- Scrivere uno script di conversione esplicito.
- Mappare `Node` storico su `DiagnosticFlow` / `DiagnosticNode`.
- Mappare `Answer` storico su `DiagnosticOption`.
- Mappare `Professionista` su `ProfessionalProfile` o seed separato.
- Convertire coordinate vecchie in `PointField`.
- Normalizzare naming e contenuti.
- Produrre seed ripetibili per dev/staging.

### Criteri di completamento

- Seed applicabili da zero.
- Primo set di flussi diagnostici reali.
- Nessun vincolo al vecchio schema dati.

## Fase 8 - Backoffice

### Scopo

Rendere Django Admin sufficiente per gestire il primo MVP.

### Attività

- Registrare tutti i modelli principali.
- Migliorare list display, filtri e ricerca.
- Proteggere storici sensibili in read-only.
- Impedire incoerenze dal backoffice dove possibile.
- Aggiungere validazioni a livello modello/serializer, non solo UI admin.

### Modelli Critici

- `User`
- `Category`
- `Tag`
- `DiagnosticFlow`
- `DiagnosticNode`
- `DiagnosticOption`
- `Property`
- `Asset`
- `Case`
- `CaseEvent`
- `CaseNote`
- `Attachment`
- `ProfessionalProfile`
- `Appointment`
- `AiSession`
- `AiMessage`

### Criteri di completamento

- Admin usabile per contenuti e supporto.
- Storici protetti.
- Editing troubleshooting non genera grafi incoerenti.

## Fase 9 - AI Contestuale

### Scopo

Tenere l'AI come supporto operativo, non come centro del prodotto.

### Attività

- Conservare provider abstraction.
- Conservare provider locale deterministico per test.
- Configurare provider OpenAI solo via env.
- Legare sessione AI a `Case` quando possibile.
- Includere nel contesto:
  - categoria;
  - pratica;
  - asset;
  - nodo diagnostico corrente;
  - storico essenziale.
- Mantenere rate limiting.
- Gestire risposte async via Celery.
- Mantenere polling/SSE se già presenti e testati.

### Regole Di Sicurezza

- Risposte in italiano.
- Nessun consiglio per operazioni elettriche rischiose.
- Escalation chiara verso professionista in caso di pericolo.
- Se fuori contesto, riportare l'utente al caso o alla guida.

### Criteri di completamento

- AI funziona con provider locale in test.
- AI funziona con provider reale se configurato.
- Errori provider non rompono il caso.
- Test su limiti, pending reply e failure.

## Fase 10 - Documentazione Operativa

### Scopo

Rendere il progetto gestibile anche dopo sessioni lunghe di sviluppo.

### Documenti Attesi

- `docs/operations/local-setup.md`
- `docs/operations/project-tracker.md`
- `docs/operations/api-runbook.md`
- `docs/operations/seed-data.md`
- `docs/operations/deployment-notes.md`

### Regole Tracker

- Un solo tracker operativo principale.
- Ogni blocco ha stato: todo, in corso, fatto.
- Ogni decisione rilevante va riportata.
- I dettagli storici lunghi possono andare in `docs/history/`.

### Criteri di completamento

- Nuovo sviluppatore può avviare il progetto.
- Stato lavori comprensibile senza rileggere tutta la chat.

## Fase 11 - Preparazione Frontend

### Scopo

Preparare il frontend solo dopo contratti API stabili.

### Decisione Da Prendere

- Continuare con Flutter.
- Oppure costruire nuovo client web/mobile con stack diverso.

### Regola

Il frontend consuma le API nuove.
Il backend non deve essere adattato per imitare il vecchio client.

### Aree MVP Client

- `Guida`: diagnosi guidata.
- `Casa`: pratiche, asset, documenti, storico.
- `Profilo`: utente, impostazioni, accesso professionista se previsto.

### Criteri di completamento

- OpenAPI stabile.
- Workflow principali backend testati.
- UX disegnata sui casi reali, non sui vecchi tab.

## Sequenza Di Lavoro Quando Si Parte

Quando viene dato il via, procedere in questo ordine:

1. Creare tracker operativo.
2. Importare baseline `elettra2`.
3. Pulire file non necessari e segreti.
4. Aggiornare dipendenze e settings.
5. Creare Docker Compose completo.
6. Avviare stack locale.
7. Applicare migrazioni.
8. Eseguire test.
9. Aggiungere PostGIS/GeoDjango se non già integrato.
10. Rendere storage S3-only.
11. Consolidare modelli geografici.
12. Consolidare workflow `Case`.
13. Aggiornare OpenAPI e docs.
14. Preparare import contenuti da `../elettra`.
15. Creare seed dati.
16. Eseguire test completi.

## Comandi Attesi

I comandi definitivi dipenderanno dalla struttura importata, ma il percorso deve convergere verso:

```bash
docker compose up --build
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py createsuperuser
docker compose exec web uv run python manage.py check
docker compose exec web uv run pytest -q
```

Se l'immagine non usa `uv` dentro container, documentare il comando equivalente e mantenerlo coerente.

## Rischi E Mitigazioni

### Rischio: importare troppo dal vecchio `elettra`

Mitigazione:

- importare contenuti tramite script;
- non copiare API legacy;
- non copiare sessioni custom.

### Rischio: Docker diventa ambiente fragile

Mitigazione:

- healthcheck;
- immagini pinnate;
- `.env.example` completo;
- volumi nominati;
- setup documentato.

### Rischio: PostGIS complica troppo l'MVP

Mitigazione:

- usare solo `PointField` inizialmente;
- niente poligoni nel primo rilascio;
- query distanza solo quando servono al prodotto.

### Rischio: AI prende troppo spazio

Mitigazione:

- AI solo contestuale;
- provider locale per test;
- rate limiting;
- escalation sicurezza.

### Rischio: backend guidato dal frontend

Mitigazione:

- OpenAPI prima del client;
- serializer di dominio;
- niente formati compatibilità Flutter storico.

## Definizione Di Pronto Per Il Frontend

Il frontend può iniziare quando:

- Docker Compose avvia lo stack.
- Migrazioni da zero funzionano.
- Test backend principali sono verdi.
- OpenAPI è raggiungibile.
- Auth funziona.
- `Case` workflow è stabile.
- Troubleshooting è navigabile via API.
- Allegati funzionano su MinIO.
- Professionisti hanno geolocalizzazione base.
- AI contestuale funziona almeno con provider locale.

## Definizione Di MVP Backend

Il backend MVP è pronto quando:

- utente può registrarsi e autenticarsi;
- utente può creare casa/sede;
- utente può creare o avviare una pratica;
- utente può seguire una guida diagnostica;
- avanzamento diagnostico viene tracciato nella pratica;
- utente può caricare foto/documenti;
- utente può vedere storico pratica;
- sistema propone o filtra professionisti;
- appuntamento base può essere richiesto;
- AI può rispondere sul contesto della pratica;
- admin può gestire contenuti principali;
- test e OpenAPI sono aggiornati.

## Note Finali

La scelta più efficiente è continuare da `elettra2`.

La priorità non è aggiungere subito funzioni visibili, ma rendere solida la fondazione:

- ambiente riproducibile;
- storage corretto;
- geolocalizzazione impostata bene;
- dominio coerente;
- test e contratti API stabili.

Solo dopo ha senso investire seriamente sul client.
