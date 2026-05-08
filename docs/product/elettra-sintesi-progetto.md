# Elettra - Sintesi Progetto

## Visione

Elettra e' una piattaforma per aiutare utenti domestici e piccole attivita' a gestire problemi tecnici, manutenzioni e richieste di intervento legate alla casa.

Il primo ambito e' l'impianto elettrico, ma il progetto deve restare aperto ad altri capitoli: elettrodomestici, idraulica, climatizzazione, domotica, sicurezza e manutenzione generale.

L'obiettivo non e' sostituire il tecnico, ma:

- aiutare l'utente a descrivere meglio il problema;
- guidare solo verso controlli sicuri;
- raccogliere informazioni utili;
- creare una pratica ordinata;
- facilitare eventuale contatto con un professionista.

## Oggetti Centrali

La `Case` e' il centro operativo del sistema.

Una pratica raccoglie:

- utente;
- immobile;
- asset o componente coinvolto;
- categoria tecnica;
- descrizione del problema;
- stato e priorita';
- allegati;
- note;
- eventi;
- eventuale sessione AI;
- eventuale appuntamento o professionista.

Attorno alla pratica ruotano:

- identita' utente globali;
- organizzazioni personali o professionali;
- membership con ruolo e scope;
- immobili e asset;
- categorie e tag tecnici;
- allegati su storage S3;
- conversazioni thread/post;
- appuntamenti;
- backoffice Django;
- API versionate e documentate con OpenAPI.

## Stack Tecnico

La base tecnica e' `elettra2`, importata in `elettra-ng` come repository definitivo.

Stack previsto:

- Django 5.2 LTS;
- Django REST Framework;
- drf-spectacular / OpenAPI;
- PostgreSQL con PostGIS;
- Redis;
- Celery;
- storage S3-compatible, con MinIO in locale;
- Docker Compose per sviluppo locale;
- test automatici con pytest.

In locale lo stack gira con container per API, worker, database, Redis, MinIO e Mailpit.

## Organizzazioni E Permessi

Elettra usa un solo modello `Organization`.

I due profili iniziali sono:

- `personal`: organizzazione personale dell'utente finale, di norma invisibile nella UI, massimo un membro, puo' aprire casi e gestire immobili;
- `professional`: organizzazione del professionista singolo o del team, puo' ricevere richieste, accettarle, gestire chat e interventi.

La distinzione tra utente finale, professionista, amministrativo e admin dipende da membership, ruolo, scope e capability del piano.

Il `Case` nasce non assegnato. L'utente puo' poi condividerlo con un tecnico preferito, una organizzazione o un professionista trovato per competenza/geolocalizzazione.

La condivisione e' selettiva: riepilogo, chat diagnostica, allegati scelti o tutto il caso. Prima della condivisione va mostrato un advice sui dati sensibili e sui metadati degli allegati.

`Property` e `Case` appartengono a una organizzazione proprietaria. Per l'utente finale questa e' la sua organizzazione personale, anche se in UI resta semplicemente "il mio immobile" o "il mio caso".

Gli allegati ereditano l'owner dal contesto a cui sono collegati: immobile, asset, caso o conversazione. Non devono esistere allegati orfani.

La chat con professionisti usa conversazioni flessibili con subject/topic e post. Una conversazione puo' essere collegata a un caso, ma puo' anche esistere fuori da un caso specifico.

Il modello completo e' descritto in [Modello Organizzazioni E Permessi](../architecture/modello-organizzazioni-permessi.md).

## Diagnostica

La direzione scelta e' ibrida, ma prioritariamente chat.

Non vogliamo costruire o importare grandi alberi diagnostici statici.
Gli alberi estesi rischiano di diventare difficili da mantenere, costosi da revisionare e poco aderenti a come gli utenti descrivono davvero i problemi.

Il modello preferito e':

- pochi macro-capitoli diagnostici;
- scelte cablate solo quando servono;
- chat come interfaccia principale;
- AI che pone domande progressive;
- stato strutturato salvato nel backend;
- escalation prudente quando emergono rischi.

Macro-capitoli iniziali da validare:

- problemi elettrici;
- elettrodomestici;
- idraulica;
- climatizzazione;
- domotica;
- sicurezza domestica;
- manutenzione generale.

Esempio: per elettrodomestici puo' avere senso una scelta cablata iniziale tra lavatrice, forno, frigorifero, lavastoviglie, piano cottura.
Dopo questa scelta, pero', il flusso principale torna chat.

## Ruolo Dell'AI

L'AI deve essere un assistente operativo, non il proprietario delle decisioni.

Deve:

- fare una domanda alla volta;
- aggiornare il riepilogo della pratica;
- estrarre fatti strutturati;
- stimare il livello di rischio;
- evitare consigli pericolosi;
- proporre escalation verso professionista quando opportuno.

Non deve:

- dare istruzioni per lavori elettrici rischiosi;
- trasformare automaticamente conversazioni in contenuto pubblico;
- modificare tassonomie ufficiali senza revisione;
- sostituire la valutazione di un professionista.

## Controllo Costi AI

Lo storico completo della chat viene salvato, ma non deve essere inviato sempre per intero al modello.

Il backend deve mantenere uno stato diagnostico compatto:

- riepilogo corrente;
- fatti gia' noti;
- domande gia' poste;
- informazioni escluse;
- rischio corrente;
- prossima domanda;
- regole di sicurezza del macro-capitolo.

Ogni chiamata AI deve usare questo contesto sintetico piu' poche interazioni recenti.
Periodicamente lo storico viene compattato in un digest, mantenendo comunque i messaggi originali.

Questo serve a:

- ridurre token;
- ridurre costo;
- evitare domande ripetute;
- migliorare pertinenza;
- rendere la pratica piu' utile per il tecnico.

## Stato Attuale

La baseline tecnica e' stata inizializzata.

Sono gia' presenti:

- Docker Compose completo;
- PostGIS;
- storage S3-only con MinIO;
- API e OpenAPI;
- test automatici;
- modello `Case`;
- sessioni e messaggi AI;
- primo spike di diagnostica AI dinamica;
- snapshot strutturato `AiDiagnosticSnapshot`;
- macro-capitoli diagnostici configurabili;
- scelte cablate minime per capitolo;
- contesto AI compatto per ridurre storico inviato al modello;
- digest periodico dello storico diagnostico;
- stime token/costo sul contesto sintetizzato;
- endpoint per turno diagnostico;
- endpoint per recupero snapshot.

Lo spike attuale consente di inviare un messaggio diagnostico, generare una risposta strutturata, aggiornare rischio, riepilogo, prossima domanda e audit event sulla pratica.

## Prossima Direzione

Il prossimo lavoro dovrebbe procedere cosi':

1. validare macro-capitoli e scelte cablate su scenari reali;
2. raffinare regole di sicurezza per capitolo;
3. tarare soglie di compattazione e stime costo/token;
4. collegare metriche reali del provider quando disponibili;
5. usare i contenuti storici di `../elettra` come corpus di test, non come import automatico.

La regola operativa resta: niente import massivo di alberi diagnostici prima di aver validato il modello chat-first.
