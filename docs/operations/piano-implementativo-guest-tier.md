# Piano Implementativo Guest Tier

## Obiettivo

Introdurre una modalità non registrata per far provare Elettra prima della creazione account.

Il guest tier serve a ridurre la frizione iniziale, non a creare un uso anonimo completo.

Il guest può:

- avviare una diagnosi leggera;
- selezionare un macro-capitolo;
- ricevere consigli salvati;
- usare eventualmente pochissimi turni AI;
- salvare temporaneamente lo stato della sessione;
- registrarsi e trasformare il riepilogo utile in account/caso.

Il guest non può:

- usare `La mia casa`;
- creare immobili, asset, documenti, storico o promemoria permanenti;
- condividere con professionisti;
- aprire conversazioni;
- mantenere allegati persistenti;
- superare quote molto basse.

## Decisione Di Prodotto

Il guest tier è pre-onboarding.

La call to action deve comparire quando l'utente vuole:

- salvare il percorso;
- continuare oltre la scadenza breve;
- usare quote AI superiori;
- aggiungere allegati;
- creare un caso vero;
- condividere con un professionista;
- usare `La mia casa`.

Il messaggio deve essere chiaro: la registrazione serve a proteggere dati, storico, allegati e condivisioni.

## Modello Dominio

### GuestSession

Modello implementato nella app `guests`.

Campi:

- `id`;
- `public_id`, UUID non sequenziale;
- `token_hash`, hash del token consegnato al client;
- `status`: `active`, `promoted`, `expired`, `revoked`;
- `started_at`;
- `expires_at`;
- `promoted_to_user`, opzionale;
- `promoted_at`, opzionale;
- `ip_hash`, opzionale;
- `user_agent_hash`, opzionale;
- `metadata_json`;
- `created_at`;
- `updated_at`.

Regole:

- il token completo non va salvato in chiaro;
- la sessione ha scadenza breve, per esempio 24 o 72 ore;
- una sessione scaduta non può usare endpoint guest;
- la promozione ad account è irreversibile.

### AI E Diagnostica

Strada implementata nella prima iterazione:

- estendere `AiSession` con `guest_session` opzionale;
- rendere `AiSession.user` opzionale;
- aggiungere vincolo: una sessione AI deve avere esattamente uno tra `user` e `guest_session`;
- mantenere `AiSession.case` opzionale;
- estendere `AiUsageLedger` con `guest_session` opzionale e `user` opzionale;
- applicare quote guest su `guest_session`, IP hash e finestra temporale.

Motivo: evita un secondo sistema parallelo di messaggi AI e mantiene compattazione, snapshot e provider abstraction riutilizzabili.

Per sicurezza, gli endpoint guest sono separati da quelli autenticati:

- `POST /api/v1/guest/sessions`;
- `GET /api/v1/guest/sessions/current`;
- `POST /api/v1/guest/diagnostic-turns`;
- `GET /api/v1/guest/messages/{message_id}`;
- `GET /api/v1/guest/diagnostic-snapshot`.

Endpoint previsto ma non implementato nella prima iterazione:

- `POST /api/v1/guest/promote`.

Gli endpoint autenticati restano sotto JWT utente.

## Quote

Quote iniziali consigliate:

- massimo 1 sessione guest attiva per token;
- massimo 1-3 turni AI per sessione;
- massimo 5-10 messaggi diagnostici complessivi;
- massimo contesto ridotto;
- nessun upload allegati nella prima implementazione;
- TTL sessione 24/72 ore;
- rate limit per IP hash.

Configurazione ambiente:

```env
GUEST_SESSION_TTL_HOURS=72
GUEST_AI_TURN_LIMIT=2
GUEST_MESSAGE_LIMIT=8
GUEST_RATE_LIMIT_PER_IP_PER_DAY=5
```

## Sicurezza E Privacy

Il guest non ha identità verificata.

Regole:

- non salvare dati personali non necessari;
- non mostrare dati sensibili in payload client non firmati;
- non usare email guest come identificativo se non nel flusso di promozione;
- non permettere condivisione professionista;
- non permettere allegati persistenti inizialmente;
- cancellare o anonimizzare sessioni scadute con task periodico;
- usare token opaco, non solo UUID pubblico.

Se in futuro si abilita upload guest:

- bucket/path separato;
- TTL breve;
- dimensione molto bassa;
- antivirus o validazione MIME;
- cancellazione automatica;
- nessun invio automatico ad AI.

## Promozione Ad Account

Flusso:

1. Il guest sceglie `Salva e continua`.
2. Inserisce email e password oppure usa registrazione standard.
3. Il backend crea `User` e `Organization` personal.
4. La `GuestSession` passa a `promoted`.
5. Il backend crea un `Case` solo se l'utente conferma.
6. Il riepilogo diagnostico, rischio, capitolo e fatti rilevanti vengono copiati nel caso.
7. I messaggi originali possono essere mantenuti solo se esplicitamente consentito.

Regola conservativa:

- migrare riepilogo e snapshot;
- non migrare automaticamente eventuali dati sensibili non necessari;
- non creare asset o property da sessione guest.

## API Minime

### POST `/api/v1/guest/sessions`

Crea sessione guest.

Risposta:

- `guest_session_id`;
- `guest_token`;
- `expires_at`;
- quote disponibili.

### GET `/api/v1/guest/sessions/current`

Richiede token guest.

Restituisce:

- stato sessione;
- scadenza;
- quote residue;
- ultimo snapshot diagnostico.

### POST `/api/v1/guest/diagnostic-turns`

Richiede token guest.

Input:

- `diagnostic_chapter_id`;
- `diagnostic_chapter_option_id`, opzionale;
- `message`;
- eventuale `use_ai`, booleano.

Output:

- consiglio salvato se disponibile;
- risposta AI se consentita;
- snapshot compatto;
- call to action se quota esaurita o serve registrazione.

### POST `/api/v1/guest/promote`

Richiede token guest e dati di registrazione o token registrazione.

Output:

- user autenticato;
- token JWT;
- eventuale `case_id` creato.

Stato: endpoint non implementato nella prima iterazione. La UI mostra CTA di accesso, ma la conversione automatica guest -> account/caso resta un passo separato.

## Flutter

Schermate implementate:

- scelta iniziale: `Accedi`, `Registrati`, `Continua come ospite`;
- diagnostica guest;
- quota residua o limite raggiunto;
- call to action `Salva e continua`.

Schermate previste per una iterazione successiva:

- promozione ad account;
- passaggio da guest ad area autenticata.

Storage client:

- token guest in secure storage su mobile;
- localStorage/sessionStorage su web test;
- cancellazione token guest dopo promozione o logout.

Il guest non deve vedere tab completi `La mia casa`, `Tecnici` o `Profilo`.
La UI può mostrare teaser o call to action, ma non funzioni operative.

## Backend Fasi

Stato implementazione corrente:

- [x] `GuestSession` in app `guests` con `public_id`, token hashato, scadenza, stato, hash IP/user-agent e metadati.
- [x] Endpoint pubblici separati: `POST /guest/sessions`, `GET /guest/sessions/current`, `POST /guest/diagnostic-turns`, `GET /guest/messages/{id}`, `GET /guest/diagnostic-snapshot`.
- [x] `AiSession` e `AiUsageLedger` supportano esattamente uno tra utente autenticato e guest session.
- [x] Quote guest configurabili: TTL, turni AI, messaggi e rate limit IP giornaliero.
- [x] Diagnostica guest riusa macro-capitoli, consigli salvati, messaggi AI e `AiDiagnosticSnapshot` senza creare `Case`, `Organization`, allegati o conversazioni.
- [x] Flutter pre-login espone `Continua come ospite`, salva token guest, mostra quote, consigli, risposta AI, snapshot e CTA di accesso.
- [ ] Promozione guest -> account/caso.

### Fase 1 - GuestSession

- [x] creare modello;
- [x] creare token service;
- [x] creare endpoint sessione;
- [x] aggiungere test token, scadenza e revoca.

### Fase 2 - Quote Guest

- [x] estendere ledger o creare ledger guest;
- [x] aggiungere configurazioni;
- [x] bloccare turni oltre limite;
- [x] aggiungere test su quote.

### Fase 3 - Diagnostica Guest

- [x] creare endpoint guest diagnostico;
- [x] riusare macro-capitoli, consigli salvati e snapshot;
- [x] permettere AI solo se quota disponibile;
- [x] non creare `Case`.

### Fase 4 - Promozione

- [ ] collegare registrazione;
- [ ] creare user e organization personal;
- [ ] creare eventuale caso da riepilogo;
- [ ] invalidare o marcare promossa la sessione guest.

### Fase 5 - Flutter

- [x] aggiungere entrypoint guest;
- [x] salvare token guest;
- [x] costruire UI diagnostica leggera;
- [x] aggiungere call to action di registrazione;
- [ ] collegare promozione.

## Test

Backend:

- [x] creazione guest session;
- [x] token non in chiaro;
- [x] token invalido rifiutato;
- [x] sessione scaduta rifiutata;
- [x] quote AI applicate;
- [x] endpoint guest non crea organization;
- [x] guest non accede ad asset/property/case autenticati;
- [ ] promozione crea user e organization;
- [ ] promozione opzionale crea case da snapshot.

Flutter:

- [x] accesso come ospite;
- [x] persistenza token guest;
- [x] diagnostica guest con repository fake;
- [x] limite quota mostrato;
- [ ] promozione cancella token guest e passa a sessione autenticata.

## Fuori Perimetro Iniziale

Non implementare nella prima iterazione:

- upload allegati guest;
- condivisione con professionisti da guest;
- `La mia casa` guest;
- promemoria guest;
- account anonimi permanenti;
- marketplace anonimo;
- pagamento senza account.

## Criterio Di Completamento

La feature è completa per MVP quando:

- un utente può provare una diagnosi senza registrarsi;
- il backend applica quote e scadenza;
- il guest riceve una call to action naturale alla registrazione;
- la registrazione conserva il riepilogo utile, se viene attivata la promozione automatica;
- nessun dato guest apre accesso a funzioni persistenti senza account.
