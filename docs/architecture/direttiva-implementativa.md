# Direttiva Implementativa Elettra

> Documento operativo per avviare lo sviluppo di `elettra-ng`.
> Deriva da `PROGETTO_ELETTRA_CANONICO.md` e dall'analisi dei progetti storici `../elettra` e `../elettra2`.
> Stato: direttiva iniziale, modificabile su richiesta esplicita.

## Decisione Principale

La base tecnica di partenza deve essere `../elettra2`.

Non conviene iniziare da zero. `elettra2` e' gia' una riscrittura pulita rispetto al primo prototipo: contiene un backend modulare, API versionate, test, OpenAPI, modelli per pratiche/casi, troubleshooting, allegati, appuntamenti, professionisti e AI contestuale.

La strategia corretta e':

- usare `elettra2` come baseline tecnica;
- promuoverla dentro `elettra-ng`;
- recuperare da `../elettra` solo contenuti, seed, flussi UX e idee gia' validate;
- non importare contratti legacy, workaround Flutter o sessioni custom del vecchio progetto.

## Quando Ripartire Da Zero

Ripartire da zero avrebbe senso solo se emergesse almeno una di queste condizioni:

- `elettra2` non si avvia piu' o ha dipendenze non recuperabili;
- le migrazioni sono incoerenti in modo grave;
- i test non sono ripristinabili con effort ragionevole;
- il modello dominio reale diverge radicalmente dal PDF canonico;
- si decide di cambiare stack tecnologico in modo sostanziale.

Allo stato attuale non ci sono segnali sufficienti per scartare `elettra2`.

## Stack Confermato

Lo stack backend da mantenere e consolidare e':

- Django 5.2 LTS.
- Django REST Framework.
- PostgreSQL con estensione PostGIS.
- Redis.
- Celery.
- Storage S3-compatible tramite `django-storages`.
- MinIO come storage S3-compatible locale.
- OpenAPI tramite `drf-spectacular`.
- Django Admin come backoffice iniziale.
- Sentry e logging strutturato per osservabilita'.
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
- L'applicazione deve restare eseguibile anche con comandi locali tramite `uv`, ma Docker Compose e' il riferimento per riprodurre tutto lo stack.
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
- in futuro serviranno ricerche per distanza, copertura territoriale, ordinamento per prossimita' e possibilmente aree operative;
- introdurre PostGIS all'inizio costa poco, introdurlo dopo una base dati popolata costa di piu'.

Regole implementative:

- Usare backend database GIS di Django quando si introducono campi geografici.
- Aggiungere `django.contrib.gis` a `INSTALLED_APPS`.
- Abilitare l'estensione `postgis` nelle migrazioni iniziali o nel bootstrap DB.
- Modellare coordinate come `PointField` dove il dato rappresenta una posizione reale.
- Evitare coppie `latitudine` / `longitudine` separate nei nuovi modelli, salvo campi denormalizzati o casi di integrazione esterna.
- Usare SRID `4326` come standard applicativo.
- Creare indici spaziali sui campi usati per query di distanza o prossimita'.

Entita' candidate:

- `Property`: posizione dell'abitazione o sede.
- `Asset`: posizione opzionale se l'asset e' geograficamente distinto.
- `ProfessionalProfile`: sede o punto di riferimento del professionista.
- `ServiceArea`: futura area operativa del professionista, non necessaria nel primo MVP.
- `Appointment`: eventuale luogo intervento denormalizzato, se diverso dalla `Property`.

Nel primo MVP e' sufficiente salvare punti geografici e usare ordinamenti per distanza. Poligoni, zone operative avanzate e ottimizzazione percorsi restano fuori dal primo rilascio.

## Storage Allegati

Lo storage applicativo deve essere S3-compatible da subito.

Regole:

- `STORAGES["default"]` deve usare sempre `storages.backends.s3.S3Storage`.
- MinIO e' obbligatorio in locale.
- In produzione si potra' usare MinIO self-hosted o un provider S3-compatible gestito.
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

Il primo MVP deve essere centrato sulla gestione tecnica della casa e sui problemi domestici, partendo dall'elettrico ma senza vincolare il dominio al solo elettrico.

Oggetti centrali:

- `User`: cliente, professionista, admin.
- `Property`: abitazione o sede.
- `Asset`: impianto, componente o area tecnica della casa.
- `DiagnosticFlow`: percorso diagnostico pubblicabile.
- `DiagnosticNode`: domanda, soluzione, warning o escalation.
- `DiagnosticOption`: transizione tra nodi.
- `Case`: pratica/problema aperto dall'utente.
- `CaseEvent`: cronologia tecnica e audit operativo.
- `CaseNote`: note utente/professionista.
- `Attachment`: foto, documenti e allegati.
- `ProfessionalProfile`: profilo professionista.
- `Appointment`: richiesta/intervento.
- `AiSession` e `AiMessage`: AI contestuale legata a caso o percorso.

La `Case` deve restare l'oggetto operativo centrale.
Il troubleshooting non deve essere una schermata isolata: deve poter generare o aggiornare una pratica.

## Perimetro Primo Rilascio

Dentro il primo rilascio:

- registrazione, login, logout, recupero password, verifica email;
- ruoli base: customer, professional, admin;
- categorie e tag tecnici;
- percorsi diagnostici pubblici;
- creazione pratica da problema manuale o da troubleshooting;
- avanzamento troubleshooting dentro una pratica;
- allegati su pratica e asset;
- note e storico pratica;
- elenco professionisti filtrabile per categoria/tag;
- richiesta appuntamento base;
- AI contestuale con storico persistente e provider astratto;
- backoffice Django operativo;
- test automatici sui contratti principali.

Fuori dal primo rilascio:

- videochiamate;
- pagamenti e commissioni;
- pubblicita';
- abbonamenti complessi;
- AI immagini;
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
- insight UX gia' provati nel client Flutter;
- logiche utili come chat contestuale e promemoria da soluzione;
- documentazione storica e pitch.

Non recuperare automaticamente:

- shape API legacy;
- sessioni custom;
- serializer adattati a Flutter;
- tab/navigation del vecchio client;
- organizer generico scollegato dalle pratiche;
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
- Definire meglio il ciclo pratica: apertura, diagnosi, escalation, appuntamento, risoluzione, chiusura.
- Aggiungere eventuali campi mancanti senza gonfiare il dominio.

Output atteso:

- modello dati aderente al prodotto;
- workflow pratica chiaro;
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

- client MVP con tre aree: Guida, Casa/Pratiche, Profilo;
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

## Priorita' Tecnica Immediata

1. Portare `elettra2` in `elettra-ng`.
2. Definire `docker-compose.yml` per stack locale completo.
3. Verificare avvio locale completo con PostgreSQL/PostGIS, Redis, MinIO e Celery.
4. Rendere esplicita la configurazione S3-only.
5. Eseguire la suite test.
6. Creare tracker operativo in `docs/PROJECT_TRACKER.md`.
7. Aggiornare la documentazione locale di setup.
8. Preparare migrazione contenuti da `../elettra`.

## Conclusione Operativa

La scelta consigliata e' continuare da `elettra2`, non ripartire puliti.

`elettra2` va trattato come fondazione tecnica gia' valida ma da consolidare. `elettra-ng` deve diventare il repository definitivo, con documentazione canonica, configurazione pulita e sviluppo progressivo a partire dalla baseline di `elettra2`.
