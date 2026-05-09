# Piano Implementativo Diagnostica Ibrida Chat-First

## Stato

Questo documento definisce la direzione implementativa corrente per la diagnostica.
La scelta di prodotto e': esperienza ibrida, ma prioritariamente chat.

Gli alberi diagnostici estesi non sono piu' il modello principale da importare o costruire.
Restano utili solo come guide curate, fallback, checklist ad alta sicurezza o percorsi ufficiali molto controllati.

## Obiettivo

Costruire una diagnostica che:

- parta da pochi macro-capitoli chiari;
- usi scelte cablate solo quando riducono ambiguita', rischio o costo AI;
- mantenga la conversazione come interfaccia principale;
- faccia porre domande all'AI in modo progressivo;
- salvi uno stato strutturato della pratica;
- ottimizzi contesto e token tramite riepiloghi e compattazione dello storico;
- permetta revisione futura dei pattern ricorrenti prima di trasformarli in contenuto ufficiale.

## Principio Guida

La UI deve sembrare una chat guidata, non un questionario lungo.

Le scelte cablate devono apparire quando sono naturalmente utili:

- scelta macro-capitolo;
- scelta asset o famiglia tecnica;
- selezione elettrodomestico;
- conferma di segnali di pericolo;
- scelta tra opzioni brevi e gia' validate;
- escalation verso professionista.

Il resto del flusso deve restare dinamico.
L'AI deve proporre un passaggio pertinente alla volta, anche con opzioni brevi quando utili, aggiornando lo stato della pratica.

## Macro-Capitoli Iniziali

L'elenco non e' ancora canonico.
Serve come base per prototipo e test:

- problemi elettrici;
- elettrodomestici;
- idraulica;
- climatizzazione;
- domotica;
- sicurezza domestica;
- manutenzione generale.

Ogni macro-capitolo deve avere:

- nome pubblico;
- slug stabile;
- descrizione interna;
- prompt context dedicato;
- regole di sicurezza;
- campi strutturati consigliati;
- eventuali scelte cablate iniziali;
- segnali di escalation immediata.

## Scelte Cablate

Le scelte cablate non devono diventare un albero completo.
Devono essere usate come acceleratori.

Esempi:

- elettrodomestici -> lavatrice, lavastoviglie, forno, frigorifero, piano cottura, asciugatrice;
- problemi elettrici -> salvavita, presa, luce, quadro elettrico, citofono, blackout parziale;
- idraulica -> perdita, scarico lento, rubinetto, sanitario, caldaia, pressione acqua;
- climatizzazione -> split, unita' esterna, telecomando, perdita acqua, rumore, aria non fredda;
- domotica -> dispositivo offline, automazione non eseguita, sensore, hub, rete.

Regola:

- cablare solo cio' che e' stabile e utile;
- non cablare varianti troppo specifiche;
- non creare sotto-rami profondi finche' non emergono dai casi reali.

## Esperienza Utente

Flusso consigliato:

1. L'utente apre una nuova pratica o parte dalla diagnostica.
2. Il sistema propone macro-capitoli o prova a classificarli dal testo libero.
3. Se serve, mostra una scelta cablata breve.
4. Si apre la chat diagnostica.
5. L'AI propone un passaggio diagnostico chiaro, anche con opzioni di risposta quando utile.
6. La UI mostra eventualmente un riepilogo progressivo non invasivo.
7. Quando il rischio cresce o i dati sono sufficienti, il sistema propone:
   - apertura/aggiornamento pratica;
   - allegati;
   - professionista;
   - checklist sicura;
   - chiusura con raccomandazione.

La chat deve evitare di chiedere di nuovo informazioni gia' date.
Il backend deve quindi mantenere lo stato strutturato come fonte primaria del contesto.

## Stato Diagnostico

Lo stato diagnostico deve diventare il cuore del contenimento costi.

Lo stato minimo gia' introdotto con `AiDiagnosticSnapshot` va esteso progressivamente con:

- macro-capitolo;
- asset/famiglia tecnica;
- sintomi;
- luogo del problema;
- quando e' iniziato;
- frequenza;
- condizioni in cui si verifica;
- verifiche sicure gia' fatte;
- informazioni escluse;
- domande gia' poste;
- rischio corrente;
- motivazione rischio;
- prossima domanda consigliata;
- criterio per fermare la diagnosi;
- escalation consigliata.

La conversazione completa resta salvata in `AiMessage`.
Il modello pero' non deve ricevere sempre tutta la conversazione.

## Ottimizzazione Costi AI

Il principio operativo e':

- salvare tutto;
- inviare poco;
- inviare contesto migliore, non piu' contesto.

Ogni chiamata AI diagnostica dovrebbe ricevere:

- macro-capitolo;
- regole di sicurezza del macro-capitolo;
- stato sintetico corrente;
- fatti gia' acquisiti;
- domande gia' poste;
- ultime poche interazioni rilevanti;
- obiettivo del prossimo turno;
- schema JSON atteso.

Non dovrebbe ricevere:

- tutto lo storico grezzo;
- allegati completi non rilevanti;
- vecchie risposte gia' riassunte;
- contenuti di altri capitoli;
- grandi alberi diagnostici.

## Accesso AI Limitato

L'AI non e' un canale libero.
Il flusso preferito e':

1. mostrare capitolo e, se utile, opzione cablata;
2. proporre uno o piu' consigli salvati e sicuri;
3. chiedere `Hai risolto?`;
4. se non risolto, proporre azioni successive:
   - continuare con guida salvata;
   - avviare chat diagnostica AI;
   - condividere il caso con un professionista.

Il backend mantiene un ledger `AiUsageLedger` per ogni risposta AI completata.
Il ledger salva:

- utente, organizzazione e pratica se presenti;
- sessione e messaggio AI;
- scopo della chiamata;
- provider e modello;
- token input/output stimati;
- costo stimato;
- metadati del contesto usato.

I limiti iniziali sono configurabili via env:

- `AI_DAILY_MESSAGE_LIMIT_PER_USER`;
- `AI_DAILY_TOKEN_LIMIT_PER_USER`;
- `AI_DAILY_ESTIMATED_COST_LIMIT_PER_USER`;
- `AI_MONTHLY_ESTIMATED_COST_LIMIT_PER_ORGANIZATION`;
- `AI_CASE_DIAGNOSTIC_TURN_LIMIT`.

Il valore `0` sui limiti economici disabilita quel limite.
I limiti vanno mostrati alla UI tramite endpoint di usage, non dedotti dal client.

## Percorso Guidato Salvato

`DiagnosticAdviceStep` rappresenta consigli editoriali brevi collegati a un macro-capitolo e, opzionalmente, a una scelta cablata.
Non e' un nuovo albero diagnostico esteso: e' una prima barriera economica e di sicurezza prima dell'AI.

Endpoint iniziali:

```http
GET /api/v1/diagnostic-chapters/{id}/advice-steps
GET /api/v1/diagnostic-advice-steps/{id}
POST /api/v1/diagnostic-advice-steps/{id}/feedback
GET /api/v1/ai/sessions/{id}/usage
```

Il feedback aggiorna la pratica:

- se l'utente ha risolto, la pratica viene marcata `resolved`;
- se non ha risolto, la pratica passa a `in_diagnosis` e vengono restituite le azioni successive.

## Compattazione Dello Storico

Servono due livelli di sintesi.

### Sintesi Di Turno

Dopo ogni messaggio utente, il sistema aggiorna:

- riepilogo pratica;
- fatti;
- rischio;
- prossima domanda;
- raccomandazione;
- escalation;
- note di sicurezza.

Questo e' il comportamento base dello snapshot diagnostico.

### Sintesi Periodica

Ogni N messaggi, o quando il contesto stimato supera una soglia, il sistema produce una sintesi piu' pulita:

- cosa sappiamo;
- cosa e' stato escluso;
- cosa manca;
- quali domande non ripetere;
- quali vincoli di sicurezza sono attivi;
- quale obiettivo ha il prossimo turno.

Questa sintesi deve essere salvata e versionata.
Non deve cancellare lo storico originale.

## Strategia Token

Soglie iniziali consigliate, da misurare:

- massimo 2-4 messaggi recenti nel prompt;
- massimo 1 riepilogo compatto;
- massimo 1 set di regole di sicurezza del macro-capitolo;
- massimo 1 elenco breve di domande gia' poste;
- compattazione ogni 6-8 turni o quando il contesto supera la soglia configurata.

Metriche salvate o da collegare a metriche reali del provider:

- provider;
- modello;
- token input stimati o reali;
- token output stimati o reali;
- costo stimato;
- durata chiamata;
- motivo della chiamata;
- se e' stata usata sintesi compatta o storico recente.

## Modello Dati Da Introdurre Gradualmente

Non introdurre tutto subito.
Il percorso consigliato e':

### Fase A - Estensione Leggera

Estendere `AiDiagnosticSnapshot` con campi di routing e contesto:

- `macro_chapter`;
- `asset_type`;
- `known_facts_json`;
- `excluded_facts_json`;
- `asked_questions_json`;
- `context_version`;
- `compacted_summary`.

Questa fase basta per validare UX e costi senza creare nuove app.

### Fase B - Catalogo Macro-Capitoli

Introdurre un modello dedicato, se la tassonomia cresce:

- `DiagnosticChapter`;
- `DiagnosticChapterOption`;
- `DiagnosticSafetyRule`.

I capitoli devono essere contenuti configurabili, non codice hardcoded.

### Fase C - Compattazione

Introdurre uno storico delle sintesi:

- `AiContextDigest`;
- riferimento a sessione;
- messaggio fino a cui arriva la sintesi;
- testo compatto;
- fatti strutturati;
- token/costo se disponibili.

### Fase D - Knowledge Candidate

Solo dopo uso reale:

- `KnowledgeCandidate`;
- `KnowledgeReview`;
- promozione manuale a guida, checklist o contenuto pubblico.

Nessun contenuto generato dagli utenti deve diventare pubblico senza revisione.

## Provider AI

Il provider locale deve restare deterministico per test.
Non deve simulare intelligenza reale, ma solo casi prevedibili.

Il provider OpenAI deve:

- ricevere prompt specifico per capitolo;
- restituire JSON strutturato;
- non ricevere storico completo se non necessario;
- rispettare regole di sicurezza;
- permettere logging di metadati costo/uso;
- fallire in modo controllato senza rompere la pratica.

## Sicurezza

Le regole di sicurezza non devono dipendere solo dal modello.

Per ogni macro-capitolo servono segnali bloccanti.
Esempi per problemi elettrici:

- odore di bruciato;
- fumo;
- scintille;
- scosse;
- surriscaldamento;
- quadro elettrico danneggiato;
- acqua vicino a prese o apparecchi elettrici.

Quando emerge un segnale bloccante:

- la risposta deve essere prudente;
- la pratica deve segnare escalation consigliata;
- la chat non deve proporre interventi tecnici;
- il sistema deve proporre professionista o emergenza appropriata.

## API Da Evolvere

Endpoint gia' presente:

```http
POST /api/v1/ai/sessions/{session_id}/diagnostic-turns
GET /api/v1/ai/sessions/{session_id}/diagnostic-snapshot
```

Endpoint probabili:

```http
GET /api/v1/diagnostic-chapters
GET /api/v1/diagnostic-chapters/{id}/options
POST /api/v1/cases/{id}/diagnostic/start
GET /api/v1/ai/sessions/{id}/context
POST /api/v1/ai/sessions/{id}/compact-context
```

La compattazione potra' essere automatica via task, ma e' utile avere un endpoint/admin action per debug.

## Implementazione Per Fasi

### Fase 1 - Consolidare Spike

- [x] Estendere snapshot con macro-capitolo e campi di contesto.
- [x] Aggiungere serializer e OpenAPI.
- [x] Aggiornare provider locale.
- [x] Aggiungere test sui segnali di rischio e sul contesto compatto.
- [x] Mantenere compatibilita' con endpoint esistenti.

### Fase 2 - Routing Ibrido

- [x] Aggiungere catalogo macro-capitoli.
- [x] Aggiungere opzioni cablate minime.
- [x] Aggiungere comando seed locale per macro-capitoli iniziali.
- Permettere classificazione da testo libero.
- Permettere scelta manuale del capitolo.
- [x] Salvare capitolo e opzione scelta nello snapshot.

### Fase 3 - Prompt Per Capitolo

- Prompt base comune.
- Prompt specifico per macro-capitolo.
- Regole sicurezza per capitolo.
- Schema JSON condiviso.
- Test provider locale per ogni capitolo iniziale.

### Fase 4 - Contesto Compatto

- [x] Costruire funzione `build_diagnostic_context(session)`.
- [x] Inviare al provider solo snapshot e ultimi messaggi rilevanti.
- [x] Evitare storico completo nel turno diagnostico.
- [x] Aggiungere limite configurabile `AI_DIAGNOSTIC_RECENT_MESSAGES_LIMIT`.
- [x] Salvare metadati del contesto usato.
- Includere digest periodico quando sara' disponibile.

### Fase 5 - Compattazione Periodica

- [x] Aggiungere `AiContextDigest`.
- [x] Creare task Celery di compattazione.
- [x] Attivare compattazione per soglia messaggi.
- [x] Aggiungere endpoint manuale di debug.
- [x] Aggiungere test su digest e non reinvio dello storico gia' sintetizzato.
- Collegare metriche reali del provider quando disponibili.

### Fase 6 - Accesso AI Controllato

- [x] Aggiungere `AiUsageLedger`.
- [x] Tracciare uso AI per chat e diagnostica.
- [x] Esporre endpoint usage per sessione.
- [x] Bloccare richieste oltre soglia messaggi/token/turni diagnostici.
- [x] Introdurre `DiagnosticAdviceStep` come percorso guidato salvato.
- [x] Aggiungere feedback `Hai risolto?` con aggiornamento pratica.
- Tarare soglie economiche su uso reale OpenAI.

### Fase 7 - Valutazione Scenari

- Creare 5-10 scenari manuali.
- Eseguire sessioni guidate.
- Misurare numero domande, pertinenza, ripetizioni, rischio, escalation.
- Decidere cosa resta cablato e cosa resta dinamico.

### Fase 8 - Revisione Contenuti

- Usare `../elettra` come corpus editoriale e test set.
- Estrarre scenari e warning, non alberi completi.
- Introdurre `KnowledgeCandidate` solo dopo validazione.

## Test Minimi

Ogni fase deve mantenere:

- test API autenticazione e permessi;
- test endpoint diagnostici;
- test OpenAPI senza warning;
- test provider locale deterministico;
- test segnali di rischio;
- test che una sessione senza pratica non possa fare diagnostica;
- test che non si ripetano domande gia' salvate nello stato;
- test che la compattazione non cancelli storico originale;
- test che errori provider non rompano la pratica.
- test su stime token/costo e soglie di compattazione.

## Criteri Di Successo

La direzione e' valida se:

- l'utente completa una prima diagnosi con poche domande;
- il tecnico riceve un riepilogo utile;
- il sistema evita consigli rischiosi;
- le domande non si ripetono;
- il costo per sessione resta controllabile;
- i macro-capitoli aiutano senza diventare alberi lunghi;
- i contenuti storici di `../elettra` possono essere usati come test set, non come import obbligatorio.

## Direttiva Operativa

Da ora lo sviluppo diagnostico deve seguire questo ordine:

1. stabilizzare chat diagnostica;
2. aggiungere macro-capitoli minimi;
3. aggiungere scelte cablate solo dove utili;
4. ottimizzare contesto e costi;
5. valutare scenari;
6. solo dopo decidere eventuali contenuti ufficiali o import selettivi.

Non costruire nuovi alberi diagnostici estesi prima della valutazione dello spike chat-first.
