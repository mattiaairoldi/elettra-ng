# Piano Implementativo Casa E Manutenzioni

## Obiettivo

Integrare nell'MVP una raccolta dati utile anche quando l'utente non ha un problema aperto.

L'obiettivo non è creare un gestionale domestico completo, ma permettere all'utente di:

- documentare immobili, impianti, elettrodomestici e componenti;
- salvare dati essenziali come marca, modello, seriale, data acquisto, garanzia;
- allegare scontrini, manuali, foto e documenti;
- registrare attività svolte;
- programmare promemoria di manutenzione;
- riusare questi dati quando nasce un problema.

## Decisione Di Prodotto

Non inserire la raccolta dati dentro il flusso `Problemi da risolvere`.

La UI deve avere due aree distinte:

- `La mia casa`: documentazione, asset, allegati, storico e promemoria;
- `Problemi da risolvere`: diagnosi, AI, condivisione con professionista.

I due flussi devono però collegarsi:

- da un asset posso aprire un problema;
- da un problema posso selezionare un asset;
- un tecnico può ricevere dati asset selezionati se l'utente li condivide;
- un problema risolto può generare una voce nello storico dell'asset.

## Modello Dominio

Già disponibili:

- `Property`;
- `Asset`;
- `Asset.metadata_json`;
- `Attachment` collegabile ad asset o caso;
- `Case` collegabile ad asset;
- storage S3-compatible.

Da aggiungere:

- `AssetMaintenanceEvent`;
- `AssetMaintenanceReminder`.

### AssetMaintenanceEvent

Rappresenta una attività o informazione storica.

Campi proposti:

- `asset`, opzionale;
- `property`, opzionale;
- `event_type`;
- `title`;
- `description`;
- `event_date`;
- `cost_amount`, opzionale;
- `metadata_json`;
- `created_by_user`;
- `created_at`;
- `updated_at`.

Tipi iniziali:

- `purchase`;
- `cleaning`;
- `replacement`;
- `inspection`;
- `repair`;
- `note`;
- `other`.

Regola:

- deve essere collegato almeno a un asset o a una property;
- se collegato a un asset eredita l'ownership dall'asset;
- non deve richiedere un `Case`.

### AssetMaintenanceReminder

Rappresenta una scadenza o promemoria.

Campi proposti:

- `asset`, opzionale;
- `property`, opzionale;
- `title`;
- `description`;
- `due_at`;
- `recurrence_rule`, inizialmente stringa semplice o enum;
- `status`;
- `last_completed_at`;
- `created_by_user`;
- `created_at`;
- `updated_at`.

Stati iniziali:

- `active`;
- `completed`;
- `suspended`;
- `cancelled`.

Ricorrenze iniziali:

- nessuna;
- mensile;
- trimestrale;
- semestrale;
- annuale;
- custom testuale opzionale.

## Uso Di Asset.metadata_json

Per il primo MVP non creare colonne dedicate per ogni possibile dato tecnico.

Usare `Asset.metadata_json` per:

- marca;
- modello;
- seriale;
- data acquisto;
- garanzia;
- potenza;
- note tecniche libere;
- dati specifici della categoria.

Promuovere a colonne dedicate solo quando:

- serve filtrare o ordinare;
- serve vincolo forte;
- serve reporting;
- il dato è comune a molte categorie.

## API Minime

Endpoint esistenti da usare:

- `GET /api/v1/properties`;
- `POST /api/v1/properties`;
- `GET /api/v1/assets`;
- `POST /api/v1/assets`;
- `GET /api/v1/assets/{id}`;
- `PATCH /api/v1/assets/{id}`;
- `POST /api/v1/attachments`.

Endpoint da aggiungere:

- `GET /api/v1/asset-maintenance-events`;
- `POST /api/v1/asset-maintenance-events`;
- `GET /api/v1/asset-maintenance-events/{id}`;
- `PATCH /api/v1/asset-maintenance-events/{id}`;
- `GET /api/v1/asset-maintenance-reminders`;
- `POST /api/v1/asset-maintenance-reminders`;
- `GET /api/v1/asset-maintenance-reminders/{id}`;
- `PATCH /api/v1/asset-maintenance-reminders/{id}`;
- `POST /api/v1/asset-maintenance-reminders/{id}/complete`.

Filtri minimi:

- `asset_id`;
- `property_id`;
- `status`;
- `due_before`;
- `due_after`.

## Flutter MVP

Aggiungere tab o sezione `Casa`.

Schermate minime:

- elenco immobili;
- dettaglio immobile;
- elenco asset;
- dettaglio asset;
- modifica dati asset;
- allegati asset;
- storico manutenzioni;
- nuovo evento manutenzione;
- promemoria manutenzione;
- nuovo promemoria.

Azioni minime:

- aggiungi asset;
- modifica dati asset;
- allega documento/foto;
- registra manutenzione svolta;
- crea promemoria;
- apri problema da asset.

Stato implementato nel workstream corrente:

- tab `Casa` presente nella shell Flutter;
- lista immobili e asset da API reali;
- dettaglio asset con metadati principali, allegati, ultima attività e prossima scadenza;
- creazione asset con marca, modello e seriale in `metadata_json`;
- upload allegati asset;
- creazione evento manutenzione;
- creazione e completamento promemoria;
- apertura problema partendo da asset.

Restano da completare:

- modifica dati asset esistenti dalla UI;
- dettaglio problema con dati asset visibili;
- condivisione selettiva di dati asset, allegati e storico manutenzione.

## Collegamento Con Problemi

Quando l'utente apre un problema:

- può selezionare un asset esistente;
- se parte da un asset, il problema eredita property/category dove possibile;
- la UI mostra dati essenziali asset nel dettaglio problema;
- AI e riepilogo possono usare un contesto sintetico dell'asset, non tutti gli allegati;
- la condivisione con professionista deve distinguere tra:
  - riepilogo problema;
  - chat diagnostica;
  - dati asset;
  - allegati asset;
  - storico manutenzione.

## Privacy E Condivisione

I dati di casa possono essere sensibili anche quando non sembrano tali.

Prima della condivisione mostrare advice su:

- foto dell'ambiente domestico;
- scontrini e dati personali;
- seriali e garanzie;
- posizione dell'immobile;
- metadati file;
- storico interventi.

Default consigliato:

- non condividere automaticamente allegati asset;
- condividere un riepilogo asset minimale solo se utile;
- chiedere conferma per allegati e storico.

## Seed Demo

Aggiornare `seed_mvp_demo` con:

- immobile demo;
- lavatrice demo con marca/modello/data acquisto;
- quadro elettrico demo;
- allegato placeholder manuale/scontrino;
- evento `pulizia filtro lavatrice`;
- promemoria `prossima pulizia filtro`;
- problema demo collegato a un asset.

## Test

Backend:

- CRUD eventi manutenzione;
- CRUD promemoria;
- permessi per owner organization;
- filtro per asset/property;
- completamento promemoria;
- divieto accesso a dati di altre organizzazioni;
- allegati asset visibili solo a chi ha permesso.

Flutter:

- lista asset;
- dettaglio asset;
- lista eventi manutenzione;
- lista promemoria;
- creazione evento con repository fake;
- apertura problema da asset.

## Fasi

### Fase 1 - Backend Minimo

- [x] aggiungere modelli;
- [x] aggiungere migrazioni;
- [x] aggiungere serializer/viewset/urls;
- [x] aggiornare OpenAPI;
- [x] aggiungere test.

### Fase 2 - Seed E Dati Demo

- [x] estendere `seed_mvp_demo`;
- [x] aggiornare documentazione locale;
- [x] verificare idempotenza tramite test.

### Fase 3 - Flutter Casa

- [x] aggiungere tab `Casa`;
- [x] mostrare immobili e asset reali;
- [x] mostrare dettaglio asset;
- [x] mostrare eventi e promemoria.

### Fase 4 - Scrittura Dati

- [x] aggiungere creazione asset;
- [ ] aggiungere modifica asset;
- [x] aggiungere evento manutenzione;
- [x] aggiungere promemoria;
- [x] allegare documenti asset.

### Fase 5 - Collegamento Problema

- [x] aprire problema partendo da asset;
- [ ] visualizzare dati asset nel problema;
- [ ] predisporre condivisione selettiva dati asset.

## Fuori Perimetro

Non implementare ora:

- inventario avanzato;
- gestione ricambi/magazzino;
- contabilità manutenzioni;
- OCR scontrini;
- estrazione automatica dati da foto/manuali;
- AI su immagini;
- notifiche push complete;
- calendario avanzato multiutente.
