# Piano Implementativo MVP

## Obiettivo

Portare Elettra da backend strutturato a MVP verificabile end-to-end.

Il risultato atteso è una demo realistica in cui:

1. un utente può provare una diagnosi leggera come ospite;
2. se vuole salvare o continuare stabilmente, si registra;
3. documenta casa, asset e documenti essenziali;
4. registra o programma una manutenzione semplice;
5. apre un problema da risolvere, possibilmente collegato a un asset;
6. segue un primo percorso guidato;
7. usa l'AI solo se serve;
8. condivide il caso con un professionista;
9. il professionista riceve informazioni utili e può rispondere.

## Stato Di Partenza

Già disponibile:

- backend Django/DRF modulare;
- Docker Compose completo;
- PostgreSQL/PostGIS;
- Redis e Celery;
- storage S3-compatible con MinIO;
- organizzazioni e membership;
- casi/problemi, immobili, asset, allegati;
- conversazioni;
- notifiche in-app e `DeviceInstallation` backend, con push native ancora fuori perimetro;
- richiesta di condivisione caso;
- diagnostica chat-first;
- consigli guidati salvati;
- ledger e limiti uso AI;
- decisione guest tier come pre-onboarding limitato;
- OpenAPI validata;
- suite test automatica.

## Principio Operativo

Il prossimo sviluppo non deve aggiungere altro dominio astratto prima di aver provato il flusso.

La priorità è:

- dati demo ripetibili;
- UI minima o client demo;
- flusso utente reale su `La mia casa` e `Problemi da risolvere`;
- correzioni API emerse dall'uso;
- solo dopo estensione funzionale.

## Fase 1 - Demo Data Ripetibile

Scopo: avere un ambiente locale pronto in pochi comandi.

Attività:

- creare comando `seed_mvp_demo`;
- creare utente finale demo;
- creare professionista demo;
- creare organizzazione professionale demo;
- creare categorie iniziali;
- collegare macro-capitoli diagnostici alle categorie;
- creare immobile e asset demo;
- aggiungere metadati asset demo, per esempio marca, modello, seriale, data acquisto;
- creare allegati demo o placeholder per manuale/scontrino;
- creare storico manutenzione demo;
- creare promemoria manutenzione demo;
- creare almeno un caso/problema demo;
- creare una richiesta di condivisione demo.

Criterio di completamento:

- il comando può essere eseguito più volte senza duplicare dati critici;
- stampa credenziali demo e id principali.

## Fase 2 - Scenari MVP

Scopo: descrivere pochi scenari concreti da usare per test manuale e demo.

Scenari iniziali:

- utente non registrato prova una diagnosi leggera e poi si registra per salvare;
- utente aggiunge una lavatrice con marca, modello e scontrino;
- utente registra pulizia filtro e programma il prossimo promemoria;
- problema elettrico semplice, risolto da consiglio salvato;
- segnale elettrico rischioso, escalation consigliata;
- elettrodomestico non urgente, con dati asset già disponibili;
- utente condivide caso con professionista;
- professionista accetta richiesta e apre conversazione.

Criterio di completamento:

- ogni scenario ha dati iniziali, azioni utente e risultato atteso.

## Fase 3 - Frontend Minimo

Scopo: costruire una UI leggera per provare il flusso.

Schermate minime:

- login/register;
- accesso ospite;
- promozione guest ad account, in una iterazione successiva;
- `La mia casa`;
- elenco immobili;
- elenco asset;
- dettaglio asset;
- modifica metadati asset;
- upload documenti/foto asset;
- storico manutenzioni asset;
- promemoria manutenzione;
- elenco problemi da risolvere;
- apertura problema;
- selezione macro-capitolo;
- consigli guidati e domanda `Hai risolto?`;
- chat AI diagnostica;
- lista professionisti;
- condivisione caso;
- vista professionista per richieste ricevute.

Indicazione stack frontend:

- React + TypeScript + Vite resta utile come frontend desktop/demo;
- Flutter diventa il client principale per l'esperienza mobile nativa;
- niente design system pesante nella prima demo;
- usare API reali, non mock statici;
- tenere una UI semplice, densa e operativa.

Direttiva aggiornata:

- mantenere il frontend React esistente per test desktop;
- creare una nuova app Flutter in `mobile/elettra_mobile`;
- generare target Android, iOS e web;
- usare il target web Flutter per test e demo, non come vincolo architetturale;
- non riusare direttamente la vecchia app `../elettra/elettra_app`.

Criterio di completamento:

- il flusso utente -> asset/documentazione -> problema -> diagnostica -> condivisione funziona localmente.

## Fase 4 - Archivio Casa E Manutenzioni

Scopo: introdurre la raccolta dati non legata a un problema senza trasformare l'MVP in un gestionale complesso.

Dominio minimo:

- mantenere `Property` come immobile;
- mantenere `Asset` come oggetto/impianto/componente;
- usare `Asset.metadata_json` per dati flessibili iniziali;
- mantenere `Attachment` collegato ad asset o caso;
- aggiungere storico manutenzione;
- aggiungere promemoria manutenzione.

Modelli proposti:

- `AssetMaintenanceEvent`;
- `AssetMaintenanceReminder`.

`AssetMaintenanceEvent` deve coprire:

- asset o property;
- tipo evento: acquisto, pulizia, sostituzione, controllo, riparazione, nota;
- data evento;
- titolo;
- note;
- costo opzionale;
- metadati flessibili.

`AssetMaintenanceReminder` deve coprire:

- asset o property;
- titolo;
- prossima scadenza;
- ricorrenza semplice opzionale;
- stato: attivo, completato, sospeso.

Criterio di completamento:

- l'utente può documentare un asset senza aprire un problema;
- può allegare documenti all'asset;
- può registrare almeno una manutenzione svolta;
- può creare un promemoria;
- quando apre un problema può collegarlo a un asset già documentato.

## Fase 5 - Rifinitura API Emersa Dal Frontend

Scopo: non anticipare endpoint non necessari.

Possibili aggiunte solo se richieste dalla UI:

- endpoint aggregato per dashboard `La mia casa`;
- endpoint dettaglio asset con allegati, storico e promemoria;
- endpoint aggregato per bootstrap caso;
- endpoint riepilogo caso con snapshot diagnostico;
- endpoint azioni disponibili sul caso;
- endpoint semplificato per avvio AI diagnostica;
- endpoint professionista per richieste pendenti.

Criterio di completamento:

- le API restano documentate in OpenAPI;
- ogni aggiunta ha test mirati.

## Fase 6 - Guest Tier

Scopo: ridurre la frizione iniziale senza esporre AI, allegati e dati sensibili a uso anonimo illimitato.

Regola prodotto:

- il guest può provare una diagnosi esplorativa;
- il guest non può usare stabilmente `La mia casa`;
- il guest non può condividere con professionisti;
- il guest non può aprire conversazioni;
- il guest deve registrarsi per salvare, continuare nel tempo o condividere.

Modello minimo:

- `GuestSession`;
- token temporaneo;
- scadenza breve;
- quote dedicate;
- retention automatica;
- promozione ad account registrato.

Criterio di completamento:

- un utente può entrare senza account, ricevere consigli salvati e arrivare a una call to action di registrazione;
- le quote guest sono applicate lato backend;
- una sessione guest scaduta non è più utilizzabile;
- la promozione, quando attivata, crea account e conserva solo il riepilogo utile, non dati non consentiti.

Piano dettagliato: [Piano Implementativo Guest Tier](piano-implementativo-guest-tier.md).

## Fase 7 - Validazione

Scopo: capire se l'MVP dimostra il valore del prodotto.

Metriche qualitative:

- l'utente capisce la differenza tra `La mia casa` e `Problemi da risolvere`;
- l'utente riesce a documentare un asset senza aprire un problema;
- l'utente riesce ad aprire un problema senza confusione;
- i dati asset rendono più rapido descrivere un problema;
- il consiglio salvato evita almeno alcuni usi AI;
- l'AI non ripete domande già poste;
- il riepilogo è utile per il professionista;
- la condivisione selettiva è comprensibile;
- il professionista capisce se accettare o rifiutare.

Metriche tecniche:

- test verdi;
- OpenAPI senza warning;
- seed demo idempotente;
- nessuna mail sincrona;
- allegati sempre su S3-compatible;
- limiti AI applicati lato backend.

## Fuori Perimetro

Non implementare ora:

- marketplace completo;
- pagamenti;
- videochiamate;
- AI su immagini;
- push native complete;
- allegati persistenti per guest;
- contatto professionisti senza registrazione;
- import massivo dei vecchi alberi diagnostici;
- gestione avanzata condomini/cantieri;
- gestione inventario avanzata, magazzino, ricambi e contabilità manutenzioni.

## Stato E Prossima Sequenza Di Lavoro

Già implementato nel workstream MVP:

- seed demo ripetibile con casa, asset, allegati placeholder, manutenzione e promemoria;
- auth mobile token-based;
- scaffold Flutter Android/iOS/web;
- flusso Flutter autenticato con `La mia casa`, allegati asset, apertura problema da asset, dettaglio `Problemi da risolvere`, diagnostica guidata/AI e condivisione professionista;
- guest tier diagnostico pre-onboarding con sessione opaca, quote basse e UI Flutter pre-login;
- API e test per storico e promemoria manutenzione asset;
- API notifiche in-app e `DeviceInstallation` con hook su condivisioni/conversazioni;
- centro notifiche Flutter con badge unread, lista notifiche e azioni mark-read, verificato manualmente su web.

Prossima sequenza:

1. Verificare manualmente il flusso Flutter `La mia casa` su dati demo reali.
2. Verificare manualmente il flusso problema -> diagnostica -> condivisione.
3. Completare promozione guest -> account/caso solo se validata dal percorso ospite.
4. Rifinire API aggregate solo sulla base delle frizioni emerse dalla UI reale.
