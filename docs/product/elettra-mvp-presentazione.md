# Elettra - MVP

## Sintesi

Elettra e' una piattaforma per aiutare utenti domestici, piccoli professionisti e organizzazioni operative a gestire problemi tecnici della casa: guasti, manutenzioni, diagnosi iniziali, condivisione delle informazioni e richieste di intervento.

L'MVP non vuole sostituire il tecnico.
Vuole fare tre cose in modo semplice:

- aiutare l'utente a descrivere bene il problema;
- raccogliere informazioni ordinate e sicure;
- facilitare, quando serve, il contatto con un professionista.

Il primo perimetro riguarda la manutenzione domestica e tecnica: elettricita', elettrodomestici, idraulica, climatizzazione, domotica, sicurezza domestica e manutenzione generale.

## Problema

Quando una persona ha un problema in casa, spesso non sa come descriverlo.
Il tecnico riceve messaggi incompleti, foto sparse, informazioni mancanti e richieste difficili da valutare.

Questo genera:

- telefonate e messaggi ripetuti;
- diagnosi iniziali lente;
- preventivi meno precisi;
- perdita di informazioni importanti;
- rischio di suggerimenti non sicuri;
- difficolta' nel tenere storico di immobili, impianti e interventi.

Elettra organizza questo momento iniziale: dalla prima descrizione fino all'eventuale coinvolgimento del professionista.

## MVP: Cosa Deve Fare

L'MVP ruota attorno alla pratica, cioe' il caso aperto dall'utente.

Una pratica contiene:

- titolo e descrizione del problema;
- categoria tecnica;
- immobile o asset coinvolto, se presente;
- stato della richiesta;
- allegati;
- chat diagnostica;
- riepilogo;
- eventuale condivisione con un professionista;
- conversazioni e aggiornamenti.

L'utente puo' aprire una pratica anche senza scegliere subito un tecnico.
Il problema potrebbe essere risolto con un controllo semplice, oppure richiedere una diagnosi piu' strutturata, oppure arrivare alla condivisione con un professionista.

## Flusso Utente

Il flusso previsto per l'MVP e':

1. L'utente apre una pratica.
2. Sceglie un grande capitolo diagnostico, per esempio problemi elettrici, idraulica o elettrodomestici.
3. Il sistema propone eventuali scelte semplici, solo dove utili.
4. Prima di usare l'AI, l'app puo' mostrare consigli guidati gia' salvati.
5. Alla fine del consiglio chiede: `Hai risolto?`
6. Se il problema non e' risolto, l'utente puo' continuare con AI diagnostica o condividere il caso con un professionista.
7. Il professionista riceve un titolo, un riepilogo e solo le informazioni che l'utente decide di condividere.

Questo mantiene il prodotto semplice e controlla i costi AI.
L'AI viene usata quando aggiunge valore, non come primo passaggio obbligatorio.

## AI Diagnostica

L'AI e' un assistente operativo.
Serve a fare domande, sintetizzare e rendere la pratica piu' chiara.

Nel MVP l'AI deve:

- fare domande progressive;
- aggiornare un riepilogo del problema;
- salvare fatti gia' emersi;
- evitare domande ripetute;
- evidenziare segnali di rischio;
- suggerire escalation verso professionista quando opportuno.

L'AI non deve:

- dare istruzioni rischiose;
- sostituire un professionista;
- ricevere automaticamente tutti gli allegati;
- generare contenuti pubblici senza revisione.

Per motivi di costo, l'accesso AI e' limitato.
Il sistema salva lo storico completo, ma invia al modello solo un contesto compatto: riepilogo, fatti rilevanti, domande gia' poste e pochi messaggi recenti.

## Professionisti E Organizzazioni

L'MVP prevede due modelli iniziali tipici:

- utente finale, che apre pratiche per la propria casa;
- professionista o piccola organizzazione, che puo' ricevere e gestire richieste.

Un professionista puo' essere una singola persona oppure un piccolo team.
L'organizzazione puo' avere utenti con ruoli diversi, per esempio admin, tecnico o amministrativo.

La pratica nasce non assegnata.
L'utente decide se e quando condividerla.
La condivisione deve essere selettiva: solo riepilogo, chat diagnostica, allegati scelti o caso completo.

Questo e' importante perche' le foto o gli allegati possono contenere dati sensibili, inclusi ambienti domestici o metadati tecnici.

## Stack Tecnologico

Lo stack scelto e' pragmatico e orientato a un backend solido.

Componenti principali:

- Django come framework backend;
- Django REST Framework per le API;
- OpenAPI per documentare le API;
- PostgreSQL con PostGIS per dati relazionali e geolocalizzazione;
- Redis e Celery per processi asincroni;
- storage S3-compatible per allegati e documenti;
- MinIO in locale per simulare lo storage S3;
- Docker Compose per sviluppo e ambiente locale;
- pytest per test automatici;
- provider AI astratto, con OpenAI come primo provider reale.

La scelta e' coerente con un prodotto che deve gestire dati, permessi, allegati, processi asincroni, geolocalizzazione e integrazione AI senza costruire infrastruttura custom inutile.

## Cosa Non E' Nell'MVP

Per mantenere il primo rilascio gestibile, non sono prioritari:

- marketplace completo dei professionisti;
- pagamenti;
- videochiamate;
- AI su immagini;
- grandi alberi diagnostici importati dal vecchio progetto;
- app mobile nativa;
- automazioni avanzate di preventivo;
- gestione completa di cantieri o condomini.

Alcuni di questi scenari restano possibili in futuro, ma non devono complicare il primo MVP.

## Valore Del Primo MVP

Il valore principale e' ridurre attrito e disordine nella fase iniziale del problema tecnico.

Per l'utente:

- descrive meglio il problema;
- riceve guida prudente;
- mantiene storico di casa, asset e pratiche;
- condivide solo quello che vuole condividere.

Per il professionista:

- riceve richieste piu' chiare;
- vede riepilogo e contesto;
- riduce messaggi ripetitivi;
- puo' valutare meglio urgenza e possibile intervento.

Per il prodotto:

- usa AI in modo controllato;
- non dipende da alberi diagnostici rigidi;
- costruisce un database operativo utile nel tempo;
- resta aperto a evoluzioni B2C, professionisti e piccole organizzazioni.

## Stato E Prossimi Passi

La base backend e' gia' impostata:

- pratiche;
- organizzazioni e permessi;
- allegati su S3-compatible;
- conversazioni;
- inviti organizzazione;
- diagnostica AI chat-first;
- consigli guidati salvati;
- limiti di utilizzo AI;
- test automatici e OpenAPI.

Il prossimo lavoro dovrebbe concentrarsi su:

1. validazione dei flussi MVP con scenari reali;
2. interfaccia utente per apertura pratica e diagnostica guidata;
3. raffinamento delle regole di sicurezza;
4. condivisione selettiva con professionisti;
5. taratura dei limiti AI su uso reale.

L'obiettivo del primo MVP e' dimostrare che una pratica tecnica puo' nascere in modo semplice, sicuro e ordinato, arrivando al professionista solo quando serve e con informazioni migliori.
