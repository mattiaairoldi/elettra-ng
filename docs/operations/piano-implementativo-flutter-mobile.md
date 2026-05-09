# Piano Implementativo App Flutter Mobile

## Obiettivo

Costruire una nuova app Flutter in `elettra-ng`, pronta per diventare app nativa Android e iOS.

Il frontend React/Vite già presente resta utile per:

- test desktop;
- demo interna;
- verifica rapida delle API;
- eventuale esperienza operativa da browser.

La nuova app Flutter diventa invece il client principale per l'utente finale e, in prospettiva, per il professionista.

## Direttiva Tecnica

Creare una nuova app Flutter pulita, non importare direttamente la vecchia app `../elettra/elettra_app`.

La vecchia app va usata solo come riferimento per:

- navigazione principale a tab;
- separazione tra schermate, servizi e stato;
- widget chat;
- uso di markdown nelle risposte AI;
- alcune idee di UX su casa, profilo e guida.

Non va usata come base diretta perché:

- è centrata sul vecchio modello `Node` / `Answer`;
- parla con endpoint non allineati a `/api/v1/`;
- usa sessione custom `X-App-Session`;
- contiene configurazione web-specifica;
- non contiene target nativi Android/iOS generati;
- porterebbe nel nuovo MVP codice legato agli alberi diagnostici estesi.

## Target Supportati

La nuova app Flutter deve nascere con:

- `android`;
- `ios`;
- `web`.

Il target `web` non deve guidare l'architettura applicativa. Serve per test rapidi, demo e debug funzionale.

La priorità resta:

1. Android/iOS come prodotto finale;
2. Web come runner di test e demo;
3. React come frontend desktop separato.

## Stack Flutter Proposto

Stack iniziale:

- Flutter stable;
- Riverpod per stato applicativo e testabilità;
- go_router per routing, deep link e flussi invito;
- Dio per HTTP client con interceptor, timeout ed error handling;
- flutter_secure_storage per token/credenziali native;
- flutter_markdown_plus per contenuti AI e consigli guidati;
- integration_test per flussi end-to-end.

Dipendenze da valutare più avanti, non nella prima fase:

- gestione file picker/upload;
- Firebase Messaging per notifiche push Android/iOS/web;
- geolocalizzazione dispositivo;
- camera/foto;
- offline cache persistente.

## Autenticazione

Prima di collegare seriamente il login Flutter, il backend deve esporre una modalità token-based adatta al mobile.

Situazione attuale:

- session authentication;
- basic authentication;
- utile per test e frontend locale;
- non ideale per app nativa.

Direttiva:

- mantenere session/basic per sviluppo e debug;
- aggiungere autenticazione token-based per mobile;
- salvare i token solo in secure storage;
- non salvare password nell'app;
- predisporre refresh/logout/revoca token.

Scelta tecnica proposta:

- introdurre JWT access/refresh oppure token opachi con refresh.

Per MVP mobile, JWT con refresh token è pragmatico perché è standard, semplice da integrare con DRF e testabile.

## Struttura Progetto

Percorso proposto:

```text
mobile/elettra_mobile/
```

Struttura interna indicativa:

```text
lib/
  app/
    elettra_app.dart
    router.dart
    theme.dart
  core/
    api/
      api_client.dart
      api_error.dart
      auth_interceptor.dart
    config/
      app_config.dart
    storage/
      secure_token_store.dart
  features/
    auth/
    cases/
    diagnostics/
    professionals/
    share_requests/
    conversations/
    notifications/
    profile/
```

Il criterio è feature-first: ogni area funzionale contiene schermate, provider, repository e modelli specifici.

## Chat E Notifiche

La chat resta un dominio applicativo di Elettra, non un servizio esterno.

Il backend mantiene:

- `Conversation`;
- `ConversationParticipant`;
- `ConversationPost`;
- permessi e visibilità;
- audit;
- relazione con pratica, richiesta di condivisione, utenti e organizzazioni.

Le notifiche push devono essere considerate un canale di avviso, non il sistema di chat.

### Principio Architetturale

Il backend Elettra deve fare da broker logico:

- decide quando notificare;
- applica permessi e preferenze utente;
- registra evento, tentativi e stato;
- invia tramite task asincrona.

Il backend non può però sostituire i broker push dei sistemi operativi.

Per la consegna push servono:

- FCM per Android;
- APNs per iOS;
- Web Push/FCM per web, se verrà abilitato;
- eventuale uso di FCM come strato unico anche per iOS, configurando comunque APNs.

Direttiva proposta:

- usare Firebase Cloud Messaging come provider iniziale cross-platform;
- configurare APNs per iOS quando si prepara la build Apple;
- non inviare push in modo sincrono durante una request HTTP;
- usare Celery per invio e retry;
- mantenere notifiche email e notifiche in-app indipendenti dalle push.

### Privacy Del Payload

Le push non devono contenere dati sensibili.

Payload ammesso:

- tipo evento;
- id conversazione o pratica;
- titolo generico;
- conteggio o breve indicazione non sensibile.

Payload da evitare:

- testo completo del messaggio;
- diagnosi;
- foto;
- indirizzo;
- dati EXIF;
- riepiloghi dettagliati;
- informazioni tecniche o domestiche sensibili.

L'app deve aprire la schermata corretta e poi scaricare i contenuti reali dalle API, dopo autenticazione e controllo permessi.

### Modelli Backend Da Prevedere

Modelli consigliati quando si implementano le notifiche:

- `DeviceInstallation`: utente, piattaforma, token provider, app version, ultimo uso, stato attivo. Implementato lato backend;
- `Notification`: evento applicativo, destinatario, titolo sicuro, stato lettura. Implementato lato backend;
- `NotificationDelivery`: provider, token, tentativi, errore, timestamp consegna;
- `NotificationPreference`: preferenze per email, push, in-app, conversazioni e pratiche.

Le notifiche in-app possono arrivare prima delle push e sono utili anche per web/desktop.

### Eventi Iniziali Da Notificare

Eventi candidati:

- nuova richiesta di condivisione caso;
- richiesta accettata o rifiutata;
- nuovo messaggio in conversazione;
- cambio stato pratica rilevante;
- promemoria appuntamento o scadenza;
- invito organizzazione;
- avviso limite AI o completamento diagnostica, solo se utile.

### Real-Time

Le push non sostituiscono il real-time quando l'app è aperta.

Strategia progressiva:

1. polling leggero per MVP;
2. notifiche in-app salvate su backend;
3. push FCM/APNs per background;
4. eventuale WebSocket/Django Channels solo se il polling non basta.

Questo evita complessità prematura e mantiene il backend come sorgente autorevole.

## Flusso MVP Mobile

Il primo flusso da implementare deve restare piccolo ma reale:

1. Login utente demo.
2. Lista problemi da risolvere.
3. Dettaglio problema.
4. Consigli guidati salvati.
5. Feedback `Hai risolto?`.
6. Avvio chat diagnostica AI se il consiglio non basta.
7. Lista professionisti compatibili.
8. Condivisione del caso.
9. Vista professionista delle richieste ricevute.
10. Accettazione/rifiuto richiesta.

La UI non deve cercare di coprire tutta la piattaforma. Deve dimostrare il ciclo:

```text
problema -> diagnostica -> eventuale AI -> condivisione -> professionista
```

Nota terminologica:

- per l'utente finale usare `problema`, `problemi da risolvere` o formule equivalenti;
- riservare `pratica` al lessico operativo interno, professionista, tecnico o backoffice;
- nel backend il modello può restare `Case`, ma la UI cliente non deve esporre questo linguaggio.

## Testabilità

La testabilità va progettata dal primo commit Flutter.

### Test Senza Dispositivo

Da eseguire con:

```bash
flutter test
```

Coprono:

- parsing DTO;
- mapping errori API;
- repository;
- provider Riverpod;
- regole UI indipendenti dal backend;
- gestione limiti AI restituiti dalle API.

Questi test devono essere la prima barriera contro regressioni veloci.

### Widget Test

Coprono schermate isolate con provider sostituiti da fake:

- login;
- lista problemi;
- dettaglio problema;
- advice steps;
- chat diagnostica;
- lista professionisti;
- richieste professionista.

Il backend non deve essere necessario per questi test.

### Integration Test Su Web

Il target web serve soprattutto qui.

Eseguire flussi completi su Chrome consente di testare rapidamente:

- login;
- navigazione;
- chiamate API reali;
- rendering chat;
- condivisione caso.

Questo non sostituisce iOS, ma permette copertura funzionale estesa da Linux.

### Integration Test Su Android

Da eseguire su emulatore o dispositivo fisico.

Serve per verificare:

- secure storage;
- tastiera;
- safe area;
- comportamento rete;
- lifecycle app;
- eventuali permessi nativi.

### Integration Test Su iOS

Non eseguibile direttamente da Linux.

Richiede:

- Mac locale;
- oppure CI macOS;
- oppure servizio come Codemagic/Bitrise.

Gli stessi test `integration_test` devono essere scritti in modo riusabile anche su iOS. La mancanza iniziale di runner iOS non deve impedire di progettare l'app per iOS.

## Sviluppo iOS Da Linux

Lo sviluppo principale può avvenire su Linux senza bloccare la roadmap iOS.

Da Linux si può:

- scrivere tutto il codice Flutter condiviso;
- eseguire `flutter analyze`;
- eseguire `flutter test`;
- testare su Chrome/Flutter web;
- testare su Android emulator o device fisico;
- mantenere nel repository la directory `ios/`;
- preparare API client, routing, stato, UI, test e configurazioni;
- far compilare iOS a una pipeline macOS.

Da Linux non si può coprire bene:

- build iOS locale completa;
- iOS Simulator;
- signing Apple locale;
- debug nativo con Xcode;
- verifica reale di Keychain, push, permessi, background e deep link su iPhone.

Direttiva:

- non serve un device Apple per iniziare;
- serve però una pipeline macOS presto, non a fine sviluppo;
- prima del rilascio pubblico serve almeno test su iPhone fisico, proprio o di tester;
- TestFlight va considerato il canale naturale per beta iOS.

### Pipeline iOS Minima

Appena creato lo scaffold Flutter, aggiungere una CI macOS minimale.

Obiettivo iniziale:

```bash
flutter pub get
flutter analyze
flutter test
flutter build ios --no-codesign
```

Questa pipeline verifica che il progetto resti compilabile per iOS senza richiedere subito certificati Apple.

Provider possibili:

- GitHub Actions con runner macOS;
- Codemagic;
- Bitrise.

Scelta consigliata per partire:

- GitHub Actions se vogliamo restare nel flusso Git standard;
- Codemagic se vogliamo accelerare signing, build mobile e TestFlight.

### Pipeline iOS Firmata

Quando il flusso MVP mobile è stabile, aggiungere signing Apple.

Prerequisiti:

- Apple Developer Program;
- bundle identifier definitivo o semi-definitivo;
- certificati e provisioning profile;
- gestione segreti CI;
- account App Store Connect;
- configurazione TestFlight.

Obiettivo:

- generare `.ipa`;
- caricare su TestFlight;
- distribuire build a tester interni/esterni;
- raccogliere feedback su device reali.

### Device Apple

Un iPhone fisico non è obbligatorio nel primo ciclo, ma diventa importante prima di considerare affidabile l'app.

Serve soprattutto per validare:

- notifiche push;
- deep link;
- secure storage/Keychain;
- camera e permessi;
- upload foto/documenti;
- safe area e gesture;
- comportamento in background;
- rete instabile;
- UX tastiera.

La decisione pratica è:

1. iniziare da Linux con Android e web;
2. aggiungere CI macOS senza signing appena nasce l'app;
3. aggiungere signing/TestFlight quando il flusso MVP mobile è dimostrabile;
4. fare test fisici iOS prima di includere push e rilascio beta esteso.

## Fasi Implementative

### Fase 0 - Preparazione

- creare `mobile/elettra_mobile`;
- generare target Android/iOS/web;
- verificare `flutter analyze`;
- verificare `flutter test`;
- aggiungere CI macOS con `flutter build ios --no-codesign`;
- aggiungere README mobile;
- documentare comandi locali.

Criterio di completamento:

- app Flutter vuota avviabile su Chrome;
- app compilabile almeno per Android debug;
- app compilabile in CI macOS per iOS senza signing;
- test base verdi.

### Fase 1 - Fondamenta Tecniche

- configurare tema e routing;
- creare `ApiClient`;
- creare gestione configurazione API base URL;
- creare gestione errori API;
- creare secure token store;
- predisporre repository/provider iniziali.

Criterio di completamento:

- chiamata `GET /api/v1/health` visibile in una schermata diagnostica interna o log di sviluppo;
- test unitari su API client e config.

### Fase 2 - Auth Mobile

- aggiungere auth token-based lato backend;
- aggiungere endpoint login/refresh/logout;
- aggiornare OpenAPI;
- implementare login Flutter;
- persistere token in secure storage;
- gestire stato autenticato/non autenticato;
- aggiungere test backend e Flutter.

Criterio di completamento:

- login mobile senza basic auth;
- refresh token funzionante;
- logout rimuove token locali.

### Fase 3 - Problemi Da Risolvere

- lista problemi da risolvere;
- dettaglio problema;
- stato problema;
- riepilogo diagnostico se presente;
- collegamento a property/asset quando disponibili.

Criterio di completamento:

- utente demo vede almeno un problema reale dal seed MVP.

### Fase 4 - Diagnostica Guidata E AI

- lista macro-capitoli;
- advice steps salvati;
- feedback `Hai risolto?`;
- avvio sessione AI;
- chat diagnostica;
- rendering limiti AI e messaggi di quota.

Criterio di completamento:

- il flusso usa prima consigli salvati;
- l'AI viene usata solo dopo scelta esplicita;
- i limiti backend sono mostrati in modo comprensibile.

### Fase 5 - Professionisti E Condivisione

- lista professionisti filtrati;
- creazione richiesta condivisione;
- scelta livello condivisione;
- avviso privacy su chat, riepilogo, allegati e metadati;
- vista professionista richieste ricevute;
- accettazione/rifiuto.

Criterio di completamento:

- flusso utente -> professionista verificabile da app.

### Fase 6 - Conversazioni

- lista conversazioni;
- dettaglio conversazione;
- invio messaggi testuali;
- collegamento conversazione a richiesta accettata;
- polling leggero per nuovi messaggi;
- predisposizione deep link interno verso conversazione.

Criterio di completamento:

- dopo accettazione richiesta si apre una conversazione operativa.

### Fase 7 - Notifiche In-App E Predisposizione Push

- [x] aggiungere modello notifiche in-app lato backend;
- [x] registrare eventi applicativi principali: richiesta condivisione, accettazione/rifiuto/revoca, nuovo messaggio conversazione;
- aggiungere preferenze minime utente;
- [x] esporre endpoint lista notifiche, summary, mark-as-read e mark-all-read;
- [x] predisporre modello `DeviceInstallation`;
- [x] predisporre task Celery di consegna, anche se provider push non ancora attivo;
- [x] preparare interfaccia Flutter per centro notifiche.

Criterio di completamento:

- nuovo messaggio o richiesta genera una notifica in-app;
- l'utente può leggere e segnare come vista la notifica;
- l'architettura è pronta per collegare FCM/APNs senza cambiare il dominio chat.

### Fase 8 - Push FCM/APNs

- integrare Firebase Messaging nell'app Flutter;
- registrare token dispositivo su backend;
- gestire refresh token dispositivo;
- inviare push tramite task Celery;
- configurare Android/Firebase;
- configurare iOS tramite APNs/Firebase;
- valutare web push solo per il target Flutter web;
- mantenere payload privacy-safe.

Criterio di completamento:

- a app in background, un nuovo messaggio produce una notifica push;
- il tap apre la conversazione corretta;
- nessun contenuto sensibile è nel payload push.

### Fase 9 - Allegati

- visualizzazione allegati pratica;
- upload foto/documenti tramite API;
- nota privacy su metadati e condivisione;
- eventuale invio allegati in conversazione in fase successiva.

Criterio di completamento:

- upload passa sempre da storage S3-compatible lato backend.

## Criteri Di Qualità

Ogni fase deve rispettare:

- `flutter analyze` verde;
- `flutter test` verde;
- test backend invariati verdi;
- CI macOS iOS `--no-codesign` verde quando disponibile;
- nessuna credenziale hardcoded;
- nessun endpoint mockato nella app reale;
- configurazione API via environment/build define;
- UI mobile-first ma utilizzabile anche su web test.

## Fuori Perimetro Iniziale

Non implementare subito:

- pagamento;
- marketplace completo;
- notifiche push complete FCM/APNs;
- AI su immagini;
- offline completo;
- app store setup definitivo;
- design system avanzato;
- import diretto della vecchia app Flutter.

## Prossimo Passo Consigliato

Stato attuale:

- auth token-based, scaffold Flutter, CI mobile, health check e login sono già implementati;
- `La mia casa` è collegata ad API reali per immobili, asset, allegati, storico, promemoria e apertura problema da asset;
- `Problemi da risolvere` mostra lista casi, dettaglio pratica, diagnostica guidata, chat AI diagnostica e richiesta di condivisione verso professionista tramite API reali;
- il pre-login Flutter offre `Continua come ospite` con diagnostica leggera, consigli salvati, AI limitata e CTA di accesso;
- il backend espone notifiche in-app e registrazione `DeviceInstallation`; le push native non sono ancora abilitate;
- Flutter mostra badge unread e centro notifiche in-app collegati alle API backend, verificati su web con notifica reale e mark-read;
- le sezioni `Diagnosi`, `Tecnici` e `Profilo` restano placeholder operativi separati: il flusso MVP end-to-end oggi passa dal dettaglio problema.

Il prossimo passo operativo è:

1. verificare manualmente su Flutter web il flusso `La mia casa` con seed demo;
2. verificare manualmente su Flutter web il flusso problema -> diagnostica -> condivisione con seed demo;
3. completare promozione guest -> account/caso se serve conservare il riepilogo;
4. preparare signing/TestFlight solo dopo il primo flusso MVP mobile end-to-end validato manualmente.
