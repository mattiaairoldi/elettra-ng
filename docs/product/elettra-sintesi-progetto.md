# Elettra - Sintesi Progetto

## Visione

Elettra è una piattaforma per aiutare utenti domestici e piccole attività a gestire la parte tecnica della casa: problemi da risolvere, dati di immobili e impianti, manutenzioni, documenti e richieste di intervento.

Il primo ambito è l'impianto elettrico, ma il progetto deve restare aperto ad altri capitoli: elettrodomestici, idraulica, climatizzazione, domotica, sicurezza e manutenzione generale.

L'obiettivo non è sostituire il tecnico, ma:

- aiutare l'utente a documentare casa, impianti ed elettrodomestici;
- aiutare l'utente a descrivere meglio un problema quando si presenta;
- guidare solo verso controlli sicuri;
- raccogliere informazioni utili;
- creare un archivio ordinato e, quando serve, un caso ordinato;
- facilitare eventuale contatto con un professionista.

## Oggetti Centrali

Elettra ha due centri operativi distinti ma collegati:

- `Asset`: oggetto tecnico, impianto, elettrodomestico o componente della casa da documentare e mantenere;
- `Case`: problema da risolvere, caso diagnostico o richiesta di aiuto.

L'asset raccoglie:

- immobile di riferimento;
- categoria tecnica;
- nome e descrizione;
- posizione o stanza;
- dati strutturati flessibili, per esempio marca, modello, seriale, data acquisto, garanzia;
- allegati come foto, scontrini, manuali, certificazioni;
- storico manutenzioni;
- promemoria futuri.

Un caso/problema raccoglie:

- utente;
- immobile;
- asset o componente coinvolto;
- categoria tecnica;
- descrizione del problema;
- stato e priorità;
- allegati;
- note;
- eventi;
- eventuale sessione AI;
- eventuale appuntamento o professionista.

Attorno ad asset e problemi ruotano:

- sessioni guest temporanee per diagnosi esplorativa prima della registrazione;
- identità utente globali;
- organizzazioni personali o professionali;
- membership con ruolo e scope;
- immobili e asset;
- categorie e tag tecnici;
- allegati su storage S3;
- conversazioni thread/post;
- appuntamenti;
- backoffice Django;
- API versionate e documentate con OpenAPI.

La regola di prodotto è:

- se l'utente vuole documentare o programmare manutenzione, entra in `La mia casa`;
- se l'utente ha qualcosa che non funziona, entra in `Problemi da risolvere`;
- un problema può partire da un asset già documentato;
- un intervento o una manutenzione può aggiornare lo storico dell'asset.

## Stack Tecnico

La base tecnica è `elettra2`, importata in `elettra-ng` come repository definitivo.

Stack previsto:

- Django 5.2 LTS;
- Django REST Framework;
- drf-spectacular / OpenAPI;
- PostgreSQL con PostGIS;
- Redis;
- Celery;
- storage S3-compatible, con MinIO in locale;
- Docker Compose per sviluppo locale;
- test automatici con pytest;
- Flutter come client principale mobile-ready per Android/iOS, con web usato per test e demo;
- React/Vite mantenuto come frontend desktop/demo.

In locale lo stack gira con container per API, worker, database, Redis, MinIO e Mailpit.

## Organizzazioni E Permessi

Elettra usa un solo modello `Organization`.

I due profili iniziali sono:

- `personal`: organizzazione personale dell'utente finale, di norma invisibile nella UI, massimo un membro, può aprire casi e gestire immobili;
- `professional`: organizzazione del professionista singolo o del team, può ricevere richieste, accettarle, gestire chat e interventi.

La distinzione tra utente finale, professionista, amministrativo e admin dipende da membership, ruolo, scope e capability del piano.

Il `Case` nasce non assegnato. L'utente può poi condividerlo con un tecnico preferito, una organizzazione o un professionista trovato per competenza/geolocalizzazione.

La condivisione è selettiva: riepilogo, chat diagnostica, allegati scelti o tutto il caso. Prima della condivisione va mostrato un advice sui dati sensibili e sui metadati degli allegati.

`Property` e `Case` appartengono a una organizzazione proprietaria. Per l'utente finale questa è la sua organizzazione personale, anche se in UI resta semplicemente "il mio immobile" o "il mio caso".

Gli allegati ereditano l'owner dal contesto a cui sono collegati: immobile, asset, caso o conversazione. Non devono esistere allegati orfani.

La chat con professionisti usa conversazioni flessibili con subject/topic e post. Una conversazione può essere collegata a un caso, ma può anche esistere fuori da un caso specifico.

Il modello completo è descritto in [Modello Organizzazioni E Permessi](../architecture/modello-organizzazioni-permessi.md).

## Accesso Guest

È prevista una modalità non registrata, ma solo come pre-onboarding.
Nel codice attuale è documentata e pianificata, ma non ancora implementata.

L'utente guest può:

- avviare una diagnosi leggera;
- usare macro-capitoli e consigli salvati;
- consumare quote AI molto basse, se l'AI viene abilitata nel tier guest;
- mantenere una sessione temporanea per riprendere il flusso a breve termine;
- trasformare la sessione in account registrato.

L'utente guest non può:

- usare stabilmente `La mia casa`;
- salvare immobili, asset, documenti, storico o promemoria permanenti;
- condividere il caso con professionisti;
- aprire conversazioni con tecnici;
- usare allegati persistenti, salvo eventuale sperimentazione molto limitata e a scadenza.

Quando l'utente vuole salvare, continuare nel tempo, condividere o contattare un professionista, deve registrarsi.

La sessione guest non crea una `Organization` personale. L'organizzazione nasce solo al momento della registrazione.

## La Mia Casa

`La mia casa` è parte dell'MVP, non un'estensione futura.

Serve a raccogliere dati anche quando non esiste un problema aperto:

- immobili;
- impianti;
- elettrodomestici;
- componenti tecnici;
- documenti;
- foto;
- scontrini;
- manuali;
- garanzie;
- attività svolte;
- promemoria di manutenzione.

Esempi:

- salvo marca, modello e numero seriale della lavatrice;
- allego scontrino e manuale;
- registro una pulizia filtro;
- programmo un promemoria per la prossima manutenzione;
- annoto il tipo di lampadina sostituita in una stanza.

Questi dati diventano utili quando nasce un problema: se l'utente apre un problema sulla lavatrice, il sistema può usare modello, storico e allegati come contesto, sempre rispettando permessi e condivisione selettiva.

Nel primo MVP i dati specifici dell'asset possono stare in `Asset.metadata_json`, evitando di irrigidire subito il modello con troppi campi. Solo i dati che diventeranno ricorrenti e necessari per ricerca/reporting vanno promossi a colonne dedicate.

## Diagnostica

La direzione scelta è ibrida, ma prioritariamente chat.

Non vogliamo costruire o importare grandi alberi diagnostici statici.
Gli alberi estesi rischiano di diventare difficili da mantenere, costosi da revisionare e poco aderenti a come gli utenti descrivono davvero i problemi.

Il modello preferito è:

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

Esempio: per elettrodomestici può avere senso una scelta cablata iniziale tra lavatrice, forno, frigorifero, lavastoviglie, piano cottura.
Dopo questa scelta, però, il flusso principale torna chat.

## Ruolo Dell'AI

L'AI deve essere un assistente operativo, non il proprietario delle decisioni.

Deve:

- fare una domanda alla volta;
- aggiornare il riepilogo del caso;
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
- fatti già noti;
- domande già poste;
- informazioni escluse;
- rischio corrente;
- prossima domanda;
- regole di sicurezza del macro-capitolo.

Ogni chiamata AI deve usare questo contesto sintetico più poche interazioni recenti.
Periodicamente lo storico viene compattato in un digest, mantenendo comunque i messaggi originali.

L'accesso AI è inoltre limitato da quote configurabili.
Prima dell'escalation AI l'app può proporre consigli salvati per macro-capitolo e chiedere `Hai risolto?`.
Se il problema non è risolto, la UI può proporre prosecuzione guidata, chat AI o condivisione con un professionista.

Questo serve a:

- ridurre token;
- ridurre costo;
- evitare domande ripetute;
- migliorare pertinenza;
- rendere il caso più utile per il tecnico.

## Stato Attuale

La base tecnica e prodotto attuale include:

- Docker Compose completo;
- PostGIS;
- storage S3-only con MinIO;
- API e OpenAPI;
- test automatici;
- modello `Case`;
- immobili e asset con metadati flessibili;
- allegati collegabili ad asset o casi;
- storico e promemoria manutenzione asset;
- sessioni e messaggi AI;
- primo spike di diagnostica AI dinamica;
- snapshot strutturato `AiDiagnosticSnapshot`;
- macro-capitoli diagnostici configurabili;
- scelte cablate minime per capitolo;
- contesto AI compatto per ridurre storico inviato al modello;
- digest periodico dello storico diagnostico;
- stime token/costo sul contesto sintetizzato;
- ledger uso AI con limiti messaggi/token/turni;
- consigli guidati salvati per macro-capitolo;
- endpoint per turno diagnostico;
- endpoint per recupero snapshot;
- auth token-based per mobile;
- app Flutter mobile-ready con login, `La mia casa`, apertura problema da asset, dettaglio problema, consigli guidati, AI diagnostica e condivisione professionista collegati ad API reali.

Lo spike attuale consente di inviare un messaggio diagnostico, generare una risposta strutturata, aggiornare rischio, riepilogo, prossima domanda e audit event sul caso.

## Prossima Direzione

Il prossimo lavoro dovrebbe procedere così:

1. verificare manualmente `La mia casa` e apertura problema da asset su Flutter;
2. verificare manualmente il flusso problema -> diagnostica -> condivisione su Flutter;
3. implementare il tier guest come diagnosi temporanea a quote basse;
4. modellare notifiche in-app e device installation prima delle push native;
5. validare macro-capitoli e scelte cablate su scenari reali;
6. raffinare regole di sicurezza per capitolo;
7. tarare soglie di compattazione e stime costo/token;
8. usare i contenuti storici di `../elettra` come corpus di test, non come import automatico.

La regola operativa resta: niente import massivo di alberi diagnostici prima di aver validato il modello chat-first.
