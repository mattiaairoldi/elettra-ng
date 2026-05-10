# Project Tracker

## Obiettivo Corrente

Portare la app Flutter dal flusso web verificato alla validazione mobile nativa.

Snapshot operativo dettagliato: [Stato Attuale](stato-attuale.md).

## In Corso

- [ ] Preparare validazione mobile nativa e percorso signing/TestFlight.

## Stato Sintetico

- Backend API, OpenAPI, auth JWT, organizzazioni, casa/asset, casi, AI diagnostica, guest tier, notifiche in-app e promozione guest -> account/caso sono implementati.
- Flutter web ha smoke verdi sui flussi `La mia casa`, `Problemi da risolvere`, notifiche e guest -> account/caso.
- Il target prodotto resta Android/iOS; web e React sono strumenti di test/demo.
- Il prossimo rischio da ridurre riguarda device/emulatore: storage sicuro token, networking reale e preparazione signing.

## Todo

- [ ] Valutare utente non-root per il container `worker`.
- [ ] Decidere criteri di sicurezza non negoziabili per risposte AI.
- [ ] Tarare soglie di compattazione storico e stime costo/token su dati reali.
- [ ] Decidere quali contenuti di `../elettra` usare come corpus di test, non come import.
- [ ] Decidere strategia seed/conversione.
- [ ] Valutare se `DiagnosticFlow` deve restare solo per guide curate/fallback.
- [ ] Rifinire condivisione selettiva allegati/chat diagnostica su `CaseShareRequest`.
- [ ] Aggiungere assegnazione interna organizzazione/tecnico dopo accettazione richiesta.

## Fatto

- [x] Convertito il PDF sorgente in documento canonico Markdown.
- [x] Creata direttiva implementativa.
- [x] Creato piano implementativo dettagliato.
- [x] Organizzata documentazione in `docs/`.
- [x] Verificata disponibilità locale di Docker e Docker Compose.
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
- [x] Creato primo commit Git `3ee9b1c`.
- [x] Aggiunti modelli `DiagnosticChapter`, `DiagnosticChapterOption`, `DiagnosticSafetyRule`.
- [x] Aggiunti endpoint pubblici `diagnostic-chapters`.
- [x] Esteso `AiDiagnosticSnapshot` con capitolo, opzione, domande poste e metadati contesto.
- [x] Implementato `build_diagnostic_context(session)`.
- [x] Limitato il contesto diagnostico agli ultimi messaggi rilevanti.
- [x] Aggiunto comando `seed_diagnostic_chapters`.
- [x] Aggiunto modello `AiContextDigest`.
- [x] Aggiunta compattazione automatica a soglia.
- [x] Aggiunti endpoint `context`, `context-digests`, `compact-context`.
- [x] Aggiunte stime token/costo sui digest.
- [x] Rifinita astrazione provider AI con package `apps.ai_assistant.providers`.
- [x] Creato documento `docs/operations/ai-provider-abstraction.md`.
- [x] Formalizzato modello unico `Organization` con piani `personal` e `professional`.
- [x] Creato documento `docs/architecture/modello-organizzazioni-permessi.md`.
- [x] Formalizzate ownership `Property`/`Case`, allegati a cascata e conversazioni flessibili.
- [x] Aggiunta app `organizations` con `OrganizationPlan`, `Organization` e `OrganizationMembership`.
- [x] Collegati `Property.organization` e `Case.owner_organization`.
- [x] Eseguita suite test dopo ownership organizzativa: `76 passed`.
- [x] Aggiunto modello `CaseShareRequest` con accettazione, rifiuto e revoca.
- [x] Aggiunta app `conversations` con `Conversation`, `ConversationParticipant` e `ConversationPost`.
- [x] Aggiunti endpoint per `case-share-requests` e `conversations`.
- [x] Eseguita suite test dopo condivisione/conversazioni: `79 passed`.
- [x] Aggiunte API minime per organizzazioni e membership.
- [x] Eseguita suite test dopo API organizzazioni: `84 passed`.
- [x] Aggiunti inviti organizzazione via email asincrona Celery.
- [x] Eseguita suite test dopo inviti organizzazione: `89 passed`.
- [x] Collegato invito organizzazione a preview pubblica, registrazione e login.
- [x] Eseguita suite test dopo collegamento inviti-auth: `93 passed`.
- [x] Aggiunto benchmark ripetibile per diagnostica AI chat-first.
- [x] Eseguita suite test dopo benchmark diagnostico: `94 passed`.
- [x] Definiti 5 scenari canonici per verifica qualitativa dello spike diagnostico.
- [x] Normalizzate domande diagnostiche già poste per ridurre duplicati nel contesto.
- [x] Eseguita suite test dopo normalizzazione domande diagnostiche: `96 passed`.
- [x] Aggiunti ledger uso AI, limiti token/turni e percorso guidato salvato con feedback `Hai risolto?`.
- [x] Eseguita suite test dopo limiti AI e consigli guidati: `101 passed`.
- [x] Creato documento presentazione MVP e PDF.
- [x] Aggiunto tooling `work/md_to_pdf.py` per generare PDF dai Markdown.
- [x] Creato piano implementativo MVP.
- [x] Aggiunto comando `seed_mvp_demo` per dati demo ripetibili.
- [x] Eseguita suite test dopo seed demo MVP: `102 passed`.
- [x] Avviato frontend MVP React/Vite collegato ad API reali.
- [x] Aggiunti id destinatario su profili professionisti e lista richieste di condivisione.
- [x] Eseguita suite test dopo frontend/API MVP: `104 passed`.
- [x] Definita direttiva Flutter mobile-ready con target Android/iOS/web.
- [x] Creato piano implementativo Flutter mobile.
- [x] Documentata strategia notifiche: backend broker logico, Celery, FCM/APNs, payload privacy-safe.
- [x] Documentata strategia sviluppo iOS da Linux con CI macOS e TestFlight successivo.
- [x] Aggiunto auth token-based mobile con JWT access/refresh e blacklist refresh token.
- [x] Creato scaffold Flutter in `mobile/elettra_mobile` con target Android/iOS/web.
- [x] Aggiunta CI mobile Linux e iOS `--no-codesign`.
- [x] Eseguita suite test dopo auth mobile e scaffold Flutter: backend `106 passed`, Flutter analyze/test/build web/build apk debug verdi.
- [x] Collegato login Flutter agli endpoint token e lista cliente `Problemi da risolvere` a `GET /api/v1/cases`.
- [x] Aggiornata documentazione prodotto/MVP per includere `La mia casa`, asset, storico e promemoria manutenzione.
- [x] Creato piano implementativo casa/manutenzioni.
- [x] Documentata decisione guest tier per utenti non registrati.
- [x] Creato piano implementativo guest tier.
- [x] Aggiunti modelli/API `AssetMaintenanceEvent` e `AssetMaintenanceReminder`.
- [x] Esteso seed MVP con lavatrice demo, allegati placeholder, storico manutenzione e promemoria.
- [x] Collegato Flutter a `La mia casa` con immobili, asset, storico, promemoria e azioni minime di creazione/completamento.
- [x] Eseguita verifica dopo `La mia casa`: backend `109 passed`, Flutter analyze/test/build web verdi.
- [x] Allineata visibilità allegati asset alla membership organizzativa.
- [x] Completato flusso Flutter `La mia casa` con lista/upload allegati sugli asset e apertura problematica da asset.
- [x] Eseguita verifica dopo allegati e apertura problematica da asset: backend `110 passed`, Flutter analyze/test/build web verdi.
- [x] Allineata documentazione al codice non committato su casa/manutenzioni, mobile, guest tier e notifiche.
- [x] Completato flusso Flutter `Problemi da risolvere` con dettaglio pratica, consigli guidati, AI diagnostica e condivisione professionista.
- [x] Eseguita verifica dopo flusso problemi Flutter: `flutter analyze`, `flutter test`, `flutter build web` verdi.
- [x] Verificato manualmente su Flutter web con seed demo il flusso `Problemi da risolvere` -> diagnostica guidata -> AI -> condivisione professionista.
- [x] Implementato guest tier diagnostico pre-onboarding con `GuestSession`, token opaco hashato, quote basse, endpoint guest separati e CTA di accesso.
- [x] Collegato Flutter pre-login a `Continua come ospite` con diagnostica leggera, consigli salvati, AI a quota e persistenza token guest.
- [x] Verificato guest tier: backend `115 passed`, Flutter analyze/test/build web verdi, smoke Flutter web ospite -> diagnostica -> snapshot AI.
- [x] Modellate notifiche in-app e `DeviceInstallation` con API lista/summary/mark-read, registrazione dispositivi, task Celery placeholder e hook su condivisioni/conversazioni.
- [x] Collegato Flutter alle notifiche in-app con badge unread in AppBar, centro notifiche, refresh, mark-read e mark-all-read.
- [x] Verificato manualmente su Flutter web il centro notifiche in-app: badge unread, lista, `Segna letta` e DB `read_at` aggiornato.
- [x] Verificato manualmente su Flutter web il flusso `La mia casa` con seed demo reale: immobile, asset, metadati, documenti, ultima attività e promemoria.
- [x] Verificato manualmente su Flutter web il flusso `Problemi da risolvere` corrente: consiglio guidato, turno AI, snapshot, condivisione a `Demo Impianti Rossi` e notifica professionista.
- [x] Implementata promozione guest -> account/caso con JWT, `Case`, ricollegamento sessione AI e cancellazione token guest lato Flutter.
- [x] Eseguita verifica dopo promozione guest: backend `124 passed`, OpenAPI/migrazioni ok, `flutter analyze`, `flutter test`, `flutter build web` verdi.
- [x] Verificato su Flutter web headless il flusso `Continua come ospite` -> diagnosi -> `Salva come pratica` -> account autenticato -> caso visibile in `Problemi da risolvere`.

## Decisioni Confermate

- `elettra2` è la baseline tecnica.
- `elettra-ng` è il repository definitivo.
- Storage allegati solo S3-compatible.
- MinIO obbligatorio in locale.
- PostgreSQL deve includere PostGIS.
- Docker Compose è il percorso locale standard.
- Identità utente globale con `Organization` unica, membership scoped e piani iniziali `personal`/`professional`.
- I casi nascono non assegnati e vengono condivisi con professionisti solo su scelta esplicita dell'utente.
- `Property` e `Case` hanno owner organization; `Case.property` resta opzionale.
- `Conversation`/`ConversationPost` sono thread flessibili, non chat rigide 1:1.
- Il guest tier è consentito solo per diagnosi temporanea e pre-onboarding; `La mia casa`, condivisione, allegati persistenti e professionisti richiedono registrazione.

## Note Operative

- Non importare `.env`, `.venv`, cache, egg-info o dati sensibili da `../elettra2`.
- API locale attiva su `http://127.0.0.1:8000/api/v1/`.
- Mailpit locale attivo su `http://127.0.0.1:8025`.
- MinIO console locale attiva su `http://127.0.0.1:9001`.
- Redis non espone la porta host per evitare conflitti con installazioni locali.
- Nessun import dati da `../elettra` deve partire prima delle decisioni nel documento dedicato.
- La UX diagnostica prevista è ibrida, ma prioritariamente chat.
- Lo spike AI dinamico è implementato per validazione tecnica, non per generare contenuti pubblici automaticamente.
- Gli alberi diagnostici estesi non sono il modello principale da implementare in questa fase.
- La compattazione è deterministica lato backend: non consuma una chiamata AI aggiuntiva.
- L'accesso AI è limitato da quote backend; la UI deve preferire consigli salvati prima dell'escalation AI.
- La nuova app Flutter deve supportare Android/iOS come target prodotto e web come target di test/demo.
- Le notifiche push passeranno da FCM/APNs; Elettra resta broker applicativo e non invia payload sensibili.
- Le notifiche in-app sono il primo canale implementato; le push native restano disattivate finche non viene configurato un provider.
- Lo sviluppo può partire da Linux; iOS va validato presto con CI macOS `--no-codesign` e poi con TestFlight/device fisico.
- `La mia casa` è parte dell'MVP: documentazione asset, allegati, storico e promemoria non devono richiedere un problema aperto.
- Da un asset documentato si può aprire una nuova problematica già collegata all'asset.
- Il piano guest è in `docs/operations/piano-implementativo-guest-tier.md`.
