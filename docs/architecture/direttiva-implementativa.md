# Direttiva Implementativa Elettra

> Documento operativo per avviare lo sviluppo di `elettra-ng`.
> Deriva da `PROGETTO_ELETTRA_CANONICO.md` e dall'analisi dei progetti storici `../elettra` e `../elettra2`.
> Stato: direttiva iniziale, modificabile su richiesta esplicita.

## Decisione Principale

La base tecnica di partenza deve essere `../elettra2`.

Non conviene iniziare da zero. `elettra2` è già una riscrittura pulita rispetto al primo prototipo: contiene un backend modulare, API versionate, test, OpenAPI, modelli per pratiche/casi, troubleshooting, allegati, appuntamenti, professionisti e AI contestuale.

La strategia corretta è:

- usare `elettra2` come baseline tecnica;
- promuoverla dentro `elettra-ng`;
- recuperare da `../elettra` solo contenuti, seed, flussi UX e idee già validate;
- non importare contratti legacy, workaround Flutter o sessioni custom del vecchio progetto.

## Quando Ripartire Da Zero

Ripartire da zero avrebbe senso solo se emergesse almeno una di queste condizioni:

- `elettra2` non si avvia più o ha dipendenze non recuperabili;
- le migrazioni sono incoerenti in modo grave;
- i test non sono ripristinabili con effort ragionevole;
- il modello dominio reale diverge radicalmente dal PDF canonico;
- si decide di cambiare stack tecnologico in modo sostanziale.

Allo stato attuale non ci sono segnali sufficienti per scartare `elettra2`.

## Stack Confermato

Lo stack backend da mantenere e consolidare è:

- Django 5.2 LTS.
- Django REST Framework.
- PostgreSQL con estensione PostGIS.
- Redis.
- Celery.
- Storage S3-compatible tramite `django-storages`.
- MinIO come storage S3-compatible locale.
- OpenAPI tramite `drf-spectacular`.
- Django Admin come backoffice iniziale.
- Sentry e logging strutturato per osservabilità.
- Docker Compose come ambiente locale completo.

Non introdurre microservizi.
Non introdurre un pannello custom nelle prime fasi.
Non introdurre storage locale Django per gli allegati.

## Ambiente Docker

Lo sviluppo locale deve poter partire interamente tramite Docker Compose.

Servizi minimi:

- `web`: applicazione Django/DRF.
- `worker`: Celery worker.
- `beat`: Celery beat, solo quando servono task periodici.
- `db`: PostgreSQL con PostGIS.
- `redis`: broker/cache/rate limiting.
- `minio`: storage S3-compatible locale.
- `mailpit` o equivalente: SMTP catcher locale.

Regole:

- Il percorso standard per un nuovo sviluppatore deve essere `docker compose up`.
- L'applicazione deve restare eseguibile anche con comandi locali tramite `uv`, ma Docker Compose è il riferimento per riprodurre tutto lo stack.
- I dati persistenti locali devono stare in volumi Docker nominati.
- Le dipendenze tra servizi devono usare healthcheck, non solo ordine di avvio.
- Produzione e staging possono usare container, ma non devono essere vincolati a un singolo `docker-compose.yml`: database, storage e Redis possono essere servizi gestiti.
- Le immagini devono essere versionate/pinnate, evitando tag generici come `latest`.

Docker non cambia l'architettura: serve a rendere riproducibile l'ambiente, non a introdurre microservizi.

## Geolocalizzazione E PostGIS

PostGIS deve essere previsto da subito.

Motivazione:

- il PDF canonico prevede tecnici geolocalizzati;
- il dominio include abitazioni, sedi, aziende, interventi e professionisti;
- in futuro serviranno ricerche per distanza, copertura territoriale, ordinamento per prossimità e possibilmente aree operative;
- introdurre PostGIS all'inizio costa poco, introdurlo dopo una base dati popolata costa di più.

Regole implementative:

- Usare backend database GIS di Django quando si introducono campi geografici.
- Aggiungere `django.contrib.gis` a `INSTALLED_APPS`.
- Abilitare l'estensione `postgis` nelle migrazioni iniziali o nel bootstrap DB.
- Modellare coordinate come `PointField` dove il dato rappresenta una posizione reale.
- Evitare coppie `latitudine` / `longitudine` separate nei nuovi modelli, salvo campi denormalizzati o casi di integrazione esterna.
- Usare SRID `4326` come standard applicativo.
- Creare indici spaziali sui campi usati per query di distanza o prossimità.

Entità candidate:

- `Property`: posizione dell'abitazione o sede.
- `Asset`: posizione opzionale se l'asset è geograficamente distinto.
- `ProfessionalProfile`: sede o punto di riferimento del professionista.
- `ServiceArea`: futura area operativa del professionista, non necessaria nel primo MVP.
- `Appointment`: eventuale luogo intervento denormalizzato, se diverso dalla `Property`.

Nel primo MVP è sufficiente salvare punti geografici e usare ordinamenti per distanza. Poligoni, zone operative avanzate e ottimizzazione percorsi restano fuori dal primo rilascio.

## Storage Allegati

Lo storage applicativo deve essere S3-compatible da subito.

Regole:

- `STORAGES["default"]` deve usare sempre `storages.backends.s3.S3Storage`.
- MinIO è obbligatorio in locale.
- In produzione si potrà usare MinIO self-hosted o un provider S3-compatible gestito.
- Non aggiungere flag `USE_LOCAL_MEDIA`.
- Non salvare foto/documenti utente su filesystem locale applicativo.
- Gli allegati privati devono essere protetti tramite permessi applicativi o URL firmati a scadenza.

Variabili ambiente minime:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=app-media
AWS_S3_ENDPOINT_URL=http://127.0.0.1:9000
AWS_S3_REGION_NAME=us-east-1
AWS_S3_ADDRESSING_STYLE=path
AWS_DEFAULT_ACL=
```

## Dominio MVP

Il primo MVP deve essere centrato sulla gestione tecnica della casa, non solo sui problemi domestici.

L'utente deve poter:

- documentare immobili, impianti, elettrodomestici e componenti anche quando non esiste un problema;
- registrare manutenzioni svolte;
- programmare promemoria semplici;
- aprire un problema da risolvere quando qualcosa non funziona;
- collegare il problema a dati già raccolti su casa o asset.

Il primo ambito resta l'elettrico, ma il dominio non deve vincolarsi al solo elettrico.

Oggetti centrali:

- `GuestSession`: sessione temporanea non registrata per diagnosi esplorativa e pre-onboarding.
- `User`: identità globale.
- `Organization`: soggetto operativo personale, professionale o futuro gestionale.
- `OrganizationPlan`: piano/capability della organizzazione.
- `OrganizationMembership`: ruolo, scope e stato di un utente dentro una organizzazione.
- `Property`: abitazione o sede.
- `Asset`: impianto, componente o area tecnica della casa.
- `AssetMaintenanceEvent`: storico manutenzioni, sostituzioni, controlli e note non necessariamente legate a un caso.
- `AssetMaintenanceReminder`: promemoria manutenzione o scadenze tecniche.
- `DiagnosticFlow`: percorso diagnostico pubblicabile.
- `DiagnosticNode`: domanda, soluzione, warning o escalation.
- `DiagnosticOption`: transizione tra nodi.
- `Case`: problema/caso aperto dall'utente.
- `CaseEvent`: cronologia tecnica e audit operativo.
- `CaseNote`: note utente/professionista.
- `Attachment`: foto, documenti e allegati.
- `Conversation`: thread comunicativo, opzionalmente legato a un caso o altro contesto.
- `ConversationPost`: post/messaggio dentro una conversazione.
- `ProfessionalProfile`: profilo pubblico/operativo della organizzazione o membership professionale.
- `Appointment`: richiesta/intervento.
- `AiSession` e `AiMessage`: AI contestuale legata a caso o percorso.

La `Case` deve restare l'oggetto operativo centrale solo per problemi, diagnosi e richieste di aiuto.
Per documentazione e manutenzione ordinaria il centro operativo è `Asset`.
La `GuestSession` non deve creare una `Organization` e non deve dare accesso persistente a `La mia casa`.
Il troubleshooting non deve essere una schermata isolata: deve poter generare o aggiornare un caso.
Il modello organizzazioni/permessi è descritto in [Modello Organizzazioni E Permessi](modello-organizzazioni-permessi.md).

## Perimetro Primo Rilascio

Dentro il primo rilascio:

- accesso guest temporaneo per diagnosi esplorativa a quote molto basse;
- registrazione, login, logout, recupero password, verifica email;
- organizzazioni iniziali `personal` e `professional`;
- membership con ruolo e scope;
- categorie e tag tecnici;
- percorsi diagnostici pubblici;
- archivio casa con immobili e asset;
- documentazione asset con metadati flessibili;
- storico manutenzioni asset;
- promemoria manutenzione base;
- creazione caso da problema manuale o da troubleshooting;
- avanzamento troubleshooting dentro un caso;
- allegati su caso e asset;
- conversazioni thread/post tra utenti e organizzazioni, anche fuori da un caso specifico;
- note e storico caso;
- elenco professionisti filtrabile per categoria/tag;
- richiesta appuntamento base;
- AI contestuale con storico persistente e provider astratto;
- backoffice Django operativo;
- test automatici sui contratti principali.

Fuori dal primo rilascio:

- videochiamate;
- pagamenti e commissioni;
- pubblicità;
- abbonamenti complessi;
- AI immagini;
- account guest persistente;
- condivisione professionista senza registrazione;
- dashboard professionista avanzata;
- marketplace evoluto;
- B2B multi-sede completo;
- app mobile pubblicata sugli store.

## Uso Del Vecchio Progetto `../elettra`

`../elettra` non deve diventare la base tecnica.

Va usato per recuperare:

- alberi decisionali e contenuti;
- tag e template promemoria;
- lista professionisti di esempio;
- insight UX già provati nel client Flutter;
- logiche utili come chat contestuale e promemoria da soluzione;
- documentazione storica e pitch.

Non recuperare automaticamente:

- shape API legacy;
- sessioni custom;
- serializer adattati a Flutter;
- tab/navigation del vecchio client;
- organizer generico scollegato dai casi;
- configurazioni nate per workaround temporanei.

## Piano Di Passaggio Da `elettra2` A `elettra-ng`

### Fase 1 - Promozione baseline

- Copiare o importare il codice di `elettra2` dentro `elettra-ng`.
- Conservare la struttura modulare.
- Aggiornare naming progetto e package dove necessario.
- Confermare `Django 5.2 LTS`.
- Confermare storage S3-only.
- Avviare lo stack locale completo con Docker Compose: Django, Celery, PostgreSQL/PostGIS, Redis, MinIO e SMTP catcher.
- Eseguire migrazioni e test.

Output atteso:

- backend avviabile;
- admin accessibile;
- health endpoint attivo;
- OpenAPI disponibile;
- suite test verde.

### Fase 2 - Allineamento dominio al PDF

- Mappare il PDF canonico sui moduli esistenti.
- Verificare che `Property`, `Asset`, `Case` e `DiagnosticFlow` coprano il libretto digitale casa.
- Definire meglio il ciclo del caso: apertura, diagnosi, escalation, appuntamento, risoluzione, chiusura.
- Aggiungere eventuali campi mancanti senza gonfiare il dominio.

Output atteso:

- modello dati aderente al prodotto;
- workflow caso chiaro;
- API coerenti con il primo rilascio.

### Fase 3 - Recupero contenuti

- Estrarre da `../elettra` nodi, risposte, tag, professionisti e template promemoria utili.
- Convertirli nel modello `DiagnosticFlow` / `DiagnosticNode` / `DiagnosticOption`.
- Evitare migrazione cieca: i contenuti vanno normalizzati e revisionati.
- Preparare seed espliciti per ambiente dev/staging.

Output atteso:

- primo set di flussi diagnostici reali;
- seed ripetibile;
- contenuti coerenti con categorie/tag.

### Fase 4 - Client

- Non costruire il frontend prima di avere API stabili.
- Decidere se continuare con Flutter o impostare un nuovo client.
- Se Flutter viene confermato, rifare il client contro le API nuove senza adattare il backend al vecchio client.

Output atteso:

- client MVP con tre aree: Guida, Casa/Problemi, Profilo;
- nessuna dipendenza da endpoint legacy.

## Regole Di Implementazione

- Ogni modifica runtime deve avere test nuovi o aggiornati.
- Le API pubbliche stanno sotto `/api/v1/`.
- I serializer rappresentano contratti di dominio, non esigenze temporanee del client.
- Le transizioni di stato devono essere validate lato backend.
- Gli storici sensibili devono essere append-only o read-only da admin.
- Email e AI devono passare da task async quando non sono immediate.
- Gli allegati devono avere permessi espliciti.
- L'AI deve essere supporto contestuale, non centro del prodotto.

## Priorità Tecnica Immediata

1. Portare `elettra2` in `elettra-ng`.
2. Definire `docker-compose.yml` per stack locale completo.
3. Verificare avvio locale completo con PostgreSQL/PostGIS, Redis, MinIO e Celery.
4. Rendere esplicita la configurazione S3-only.
5. Eseguire la suite test.
6. Creare tracker operativo in `docs/PROJECT_TRACKER.md`.
7. Aggiornare la documentazione locale di setup.
8. Preparare migrazione contenuti da `../elettra`.

## Conclusione Operativa

La scelta consigliata è continuare da `elettra2`, non ripartire puliti.

`elettra2` va trattato come fondazione tecnica già valida ma da consolidare. `elettra-ng` deve diventare il repository definitivo, con documentazione canonica, configurazione pulita e sviluppo progressivo a partire dalla baseline di `elettra2`.
