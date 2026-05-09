# Elettra - MVP

## Sintesi

Elettra è una piattaforma per aiutare utenti domestici, piccoli professionisti e organizzazioni operative a gestire la parte tecnica della casa: oggetti e impianti da documentare, manutenzioni da ricordare, problemi da diagnosticare, informazioni da condividere e richieste di intervento.

L'MVP non vuole sostituire il tecnico.
Vuole fare tre cose in modo semplice:

- aiutare l'utente a documentare casa, impianti ed elettrodomestici;
- aiutare l'utente a descrivere bene un problema quando si presenta;
- raccogliere informazioni ordinate e sicure;
- facilitare, quando serve, il contatto con un professionista.

Il primo perimetro riguarda la manutenzione domestica e tecnica: elettricità, elettrodomestici, idraulica, climatizzazione, domotica, sicurezza domestica e manutenzione generale.

## Problema

Quando una persona ha un problema in casa, spesso non sa come descriverlo.
In più, molte informazioni utili non sono disponibili nel momento del bisogno: marca e modello dell'elettrodomestico, data di acquisto, scontrino, manuale, storico manutenzioni, ultimo cambio filtro o ultimo intervento.

Il tecnico riceve messaggi incompleti, foto sparse, informazioni mancanti e richieste difficili da valutare.

Questo genera:

- telefonate e messaggi ripetuti;
- diagnosi iniziali lente;
- preventivi meno precisi;
- perdita di informazioni importanti;
- rischio di suggerimenti non sicuri;
- difficoltà nel tenere storico di immobili, impianti e interventi.

Elettra organizza sia la fase preventiva sia il momento del problema: prima costruisce un archivio minimo della casa, poi usa quei dati quando serve diagnosi o intervento.

## MVP: Cosa Deve Fare

L'MVP ha due aree principali:

- `La mia casa`: archivio leggero di immobili, oggetti, impianti, documenti e manutenzioni;
- `Problemi da risolvere`: diagnosi, AI e possibile condivisione con professionisti.

Il caso resta l'oggetto aperto dall'utente quando c'è un problema da risolvere.

Un caso/problema contiene:

- titolo e descrizione del problema;
- categoria tecnica;
- immobile o asset coinvolto, se presente;
- stato della richiesta;
- allegati;
- chat diagnostica;
- riepilogo;
- eventuale condivisione con un professionista;
- conversazioni e aggiornamenti.

`La mia casa` contiene:

- immobili;
- asset, per esempio lavatrice, quadro elettrico, caldaia, climatizzatore, lampade o altri componenti;
- dati come marca, modello, seriale, data acquisto, garanzia;
- allegati come scontrini, manuali, foto, certificazioni;
- storico attività svolte;
- promemoria di manutenzione.

L'utente può aprire un problema anche senza scegliere subito un tecnico.
Il problema potrebbe essere risolto con un controllo semplice, oppure richiedere una diagnosi più strutturata, oppure arrivare alla condivisione con un professionista.

Se il problema riguarda un asset già documentato, il contesto è già pronto e può rendere più utile AI, riepilogo e comunicazione con il tecnico.

## Flusso Utente

Il flusso previsto per l'MVP ha due ingressi.

Flusso `La mia casa`:

1. L'utente crea o seleziona un immobile.
2. Aggiunge un asset o componente.
3. Inserisce dati essenziali, anche in forma flessibile.
4. Allega foto, scontrino, manuale o documentazione.
5. Registra un'attività svolta, per esempio pulizia filtro o cambio lampadina.
6. Imposta un promemoria, se utile.

Flusso `Problemi da risolvere`:

1. L'utente apre un problema.
2. Sceglie un grande capitolo diagnostico, per esempio problemi elettrici, idraulica o elettrodomestici.
3. Se esiste, collega l'asset coinvolto.
4. Il sistema propone eventuali scelte semplici, solo dove utili.
5. Prima di usare l'AI, l'app può mostrare consigli guidati già salvati.
6. Alla fine del consiglio chiede: `Hai risolto?`
7. Se il problema non è risolto, l'utente può continuare con AI diagnostica o condividere il caso con un professionista.
8. Il professionista riceve un titolo, un riepilogo e solo le informazioni che l'utente decide di condividere.

Questo mantiene il prodotto semplice e controlla i costi AI.
L'AI viene usata quando aggiunge valore, non come primo passaggio obbligatorio.

## Accesso Senza Registrazione

È utile prevedere una modalità non registrata, ma solo per provare il valore iniziale.
Nel codice attuale è disponibile come diagnostica guest pre-onboarding a quota bassa.

L'utente può entrare come ospite e fare una diagnosi leggera:

- sceglie un capitolo diagnostico;
- descrive il problema;
- riceve consigli salvati;
- usa pochissimi turni AI;
- riceve una CTA per accedere quando vuole salvare o continuare.

La modalità ospite non sostituisce l'account.
Per salvare casa, asset, documenti, storico, promemoria, allegati persistenti, condivisione con professionisti o conversazioni serve registrarsi.

Questo riduce la frizione iniziale senza aprire accesso illimitato ad AI, allegati e dati sensibili.

## AI Diagnostica

L'AI è un assistente operativo.
Serve a fare domande, sintetizzare e rendere il caso più chiaro.

Nel MVP l'AI deve:

- fare domande progressive;
- aggiornare un riepilogo del problema;
- salvare fatti già emersi;
- evitare domande ripetute;
- evidenziare segnali di rischio;
- suggerire escalation verso professionista quando opportuno.

L'AI non deve:

- dare istruzioni rischiose;
- sostituire un professionista;
- ricevere automaticamente tutti gli allegati;
- generare contenuti pubblici senza revisione.

Per motivi di costo, l'accesso AI è limitato.
Il sistema salva lo storico completo, ma invia al modello solo un contesto compatto: riepilogo, fatti rilevanti, domande già poste e pochi messaggi recenti.

## Professionisti E Organizzazioni

L'MVP prevede due modelli iniziali tipici:

- utente finale, che apre problemi/casi per la propria casa;
- professionista o piccola organizzazione, che può ricevere e gestire richieste.

Un professionista può essere una singola persona oppure un piccolo team.
L'organizzazione può avere utenti con ruoli diversi, per esempio admin, tecnico o amministrativo.

Il caso nasce non assegnato.
L'utente decide se e quando condividerlo.
La condivisione deve essere selettiva: solo riepilogo, chat diagnostica, allegati scelti o caso completo.

Questo è importante perché le foto o gli allegati possono contenere dati sensibili, inclusi ambienti domestici o metadati tecnici.

## Stack Tecnologico

Lo stack scelto è pragmatico e orientato a un backend solido.

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
- provider AI astratto, con OpenAI come primo provider reale;
- Flutter come client mobile-ready Android/iOS, con web usato per test e demo.

La scelta è coerente con un prodotto che deve gestire dati, permessi, allegati, processi asincroni, geolocalizzazione e integrazione AI senza costruire infrastruttura custom inutile.

## Cosa Non È Nell'MVP

Per mantenere il primo rilascio gestibile, non sono prioritari:

- marketplace completo dei professionisti;
- pagamenti;
- videochiamate;
- AI su immagini;
- grandi alberi diagnostici importati dal vecchio progetto;
- automazioni avanzate di preventivo;
- gestione completa di cantieri o condomini.

Alcuni di questi scenari restano possibili in futuro, ma non devono complicare il primo MVP.

## Valore Del Primo MVP

Il valore principale è ridurre attrito e disordine nella fase iniziale del problema tecnico.

Per l'utente:

- descrive meglio il problema;
- riceve guida prudente;
- mantiene storico di casa, asset e problemi risolti;
- non deve ricostruire ogni volta marca, modello, manuali e scontrini;
- condivide solo quello che vuole condividere.

Per il professionista:

- riceve richieste più chiare;
- vede riepilogo e contesto;
- riduce messaggi ripetitivi;
- può valutare meglio urgenza e possibile intervento.

Per il prodotto:

- usa AI in modo controllato;
- non dipende da alberi diagnostici rigidi;
- costruisce un database operativo utile nel tempo;
- resta aperto a evoluzioni B2C, professionisti e piccole organizzazioni.

## Stato E Prossimi Passi

La base backend è già impostata:

- casi/problemi;
- immobili e asset;
- allegati su asset e casi;
- storico e promemoria manutenzione asset;
- organizzazioni e permessi;
- allegati su S3-compatible;
- conversazioni;
- inviti organizzazione;
- diagnostica AI chat-first;
- consigli guidati salvati;
- limiti di utilizzo AI;
- guest tier diagnostico pre-onboarding con quote AI molto basse;
- notifiche in-app backend e registrazione dispositivi predisposta;
- auth token-based per mobile;
- app Flutter mobile-ready con accesso ospite, `La mia casa`, apertura problema da asset, dettaglio `Problemi da risolvere`, diagnostica guidata/AI e condivisione professionista collegate ad API reali;
- test automatici e OpenAPI.

Il prossimo lavoro dovrebbe concentrarsi su:

1. verifica manuale del flusso Flutter `La mia casa`;
2. verifica manuale del flusso Flutter problema -> diagnostica -> condivisione;
3. centro notifiche Flutter sulle API in-app;
4. promozione guest -> account/caso se il percorso ospite risulta utile;
5. validazione dei flussi MVP con scenari reali;
6. taratura dei limiti AI su uso reale.

L'obiettivo del primo MVP è dimostrare che la casa può essere documentata senza complessità e che un problema tecnico può nascere in modo semplice, sicuro e ordinato, arrivando al professionista solo quando serve e con informazioni migliori.
