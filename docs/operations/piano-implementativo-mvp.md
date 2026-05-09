# Piano Implementativo MVP

## Obiettivo

Portare Elettra da backend strutturato a MVP verificabile end-to-end.

Il risultato atteso e' una demo realistica in cui:

1. un utente apre una pratica;
2. segue un primo percorso guidato;
3. usa l'AI solo se serve;
4. condivide il caso con un professionista;
5. il professionista riceve informazioni utili e puo' rispondere.

## Stato Di Partenza

Gia' disponibile:

- backend Django/DRF modulare;
- Docker Compose completo;
- PostgreSQL/PostGIS;
- Redis e Celery;
- storage S3-compatible con MinIO;
- organizzazioni e membership;
- pratiche, immobili, asset, allegati;
- conversazioni;
- richiesta di condivisione caso;
- diagnostica chat-first;
- consigli guidati salvati;
- ledger e limiti uso AI;
- OpenAPI validata;
- suite test automatica.

## Principio Operativo

Il prossimo sviluppo non deve aggiungere altro dominio astratto prima di aver provato il flusso.

La priorita' e':

- dati demo ripetibili;
- UI minima o client demo;
- flusso utente reale;
- correzioni API emerse dall'uso;
- solo dopo estensione funzionale.

## Fase 1 - Demo Data Ripetibile

Scopo: avere un ambiente locale pronto in pochi comandi.

Attivita':

- creare comando `seed_mvp_demo`;
- creare utente finale demo;
- creare professionista demo;
- creare organizzazione professionale demo;
- creare categorie iniziali;
- collegare macro-capitoli diagnostici alle categorie;
- creare immobile e asset demo;
- creare almeno una pratica demo;
- creare una richiesta di condivisione demo.

Criterio di completamento:

- il comando puo' essere eseguito piu' volte senza duplicare dati critici;
- stampa credenziali demo e id principali.

## Fase 2 - Scenari MVP

Scopo: descrivere pochi scenari concreti da usare per test manuale e demo.

Scenari iniziali:

- problema elettrico semplice, risolto da consiglio salvato;
- segnale elettrico rischioso, escalation consigliata;
- elettrodomestico non urgente, raccolta informazioni;
- utente condivide caso con professionista;
- professionista accetta richiesta e apre conversazione.

Criterio di completamento:

- ogni scenario ha dati iniziali, azioni utente e risultato atteso.

## Fase 3 - Frontend Minimo

Scopo: costruire una UI leggera per provare il flusso.

Schermate minime:

- login/register;
- elenco pratiche;
- apertura pratica;
- selezione macro-capitolo;
- consigli guidati e domanda `Hai risolto?`;
- chat AI diagnostica;
- lista professionisti;
- condivisione caso;
- vista professionista per richieste ricevute.

Indicazione stack frontend:

- React + TypeScript + Vite e' la scelta proposta;
- niente design system pesante nella prima demo;
- usare API reali, non mock statici;
- tenere una UI semplice, densa e operativa.

Criterio di completamento:

- il flusso utente -> pratica -> diagnostica -> condivisione funziona localmente.

## Fase 4 - Rifinitura API Emersa Dal Frontend

Scopo: non anticipare endpoint non necessari.

Possibili aggiunte solo se richieste dalla UI:

- endpoint aggregato per bootstrap pratica;
- endpoint riepilogo caso con snapshot diagnostico;
- endpoint azioni disponibili sul caso;
- endpoint semplificato per avvio AI diagnostica;
- endpoint professionista per richieste pendenti.

Criterio di completamento:

- le API restano documentate in OpenAPI;
- ogni aggiunta ha test mirati.

## Fase 5 - Validazione

Scopo: capire se l'MVP dimostra il valore del prodotto.

Metriche qualitative:

- l'utente riesce ad aprire una pratica senza confusione;
- il consiglio salvato evita almeno alcuni usi AI;
- l'AI non ripete domande gia' poste;
- il riepilogo e' utile per il professionista;
- la condivisione selettiva e' comprensibile;
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
- import massivo dei vecchi alberi diagnostici;
- app mobile nativa;
- gestione avanzata condomini/cantieri.

## Prossima Sequenza Di Lavoro

1. Chiudere documentazione MVP e PDF.
2. Aggiungere seed demo ripetibile.
3. Aggiornare setup locale.
4. Eseguire test e commit.
5. Iniziare frontend minimo.
6. Rifinire API solo sulla base del flusso UI reale.
