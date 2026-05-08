# Ipotesi Diagnostica AI Dinamica

## Scopo

Questo documento non prende decisioni definitive.
Serve a valutare se Elettra debba ridurre drasticamente gli alberi diagnostici statici e spostare parte della guida utente verso una diagnostica dinamica assistita da AI.

L'ipotesi da verificare e':

- pochi contenuti strutturati, semplici e controllati;
- domande generate dinamicamente durante la conversazione;
- apprendimento progressivo dai casi creati dagli utenti;
- revisione umana prima di trasformare pattern ricorrenti in conoscenza ufficiale.

## Problema Del Modello Ad Alberi

Gli alberi diagnostici estesi hanno alcuni rischi:

- diventano presto troppo numerosi da mantenere;
- obbligano a prevedere molti casi prima di vedere l'uso reale;
- rendono difficile correggere il percorso quando l'utente descrive il problema in modo imprevisto;
- aumentano il costo editoriale prima di aver validato il prodotto;
- possono importare nel nuovo progetto troppo debito dal vecchio `../elettra`.

Il valore del vecchio progetto non va perso, ma non e' detto che debba diventare un grande set di `DiagnosticFlow`, `DiagnosticNode` e `DiagnosticOption`.

## Ipotesi Di Prodotto

L'esperienza potrebbe essere piu' semplice:

1. L'utente descrive il problema con testo libero e, in seguito, allegati.
2. Il sistema classifica il problema in una tassonomia leggera.
3. L'AI pone poche domande successive, una alla volta.
4. Ogni risposta aggiorna una pratica (`Case`) e un riepilogo strutturato.
5. Quando emerge rischio, incertezza o bisogno operativo, il sistema propone escalation verso professionista.
6. I pattern ricorrenti vengono salvati come candidati, non come contenuto ufficiale.
7. Un admin puo' revisionare i candidati e promuoverli a template, checklist o guida pubblicata.

In questo scenario la `Case` resta il centro operativo.
La diagnostica non e' piu' solo navigazione di un albero, ma una sessione guidata che produce stato strutturato.

## Approccio Consigliato Per La Verifica

La strada piu' prudente non e' passare direttamente a "AI libera".
Conviene testare un modello ibrido:

- tassonomia minima e controllata;
- poche regole di sicurezza non negoziabili;
- prompt e output strutturati;
- AI usata per scegliere la prossima domanda e sintetizzare il caso;
- vecchi contenuti usati come materiale di riferimento, non importati automaticamente;
- promozione a contenuto ufficiale solo dopo revisione.

Questo permette di validare la semplificazione senza perdere controllo su sicurezza, qualita' e tracciabilita'.

## Cosa Deve Restare Strutturato

Anche con AI dinamica, alcuni elementi devono restare espliciti nel database:

- categoria tecnica del problema;
- immobile e asset coinvolto, se presenti;
- stato della pratica;
- livello di rischio;
- domande poste e risposte ricevute;
- riepilogo corrente;
- raccomandazione finale;
- motivo dell'eventuale escalation;
- fonte dei suggerimenti generati;
- esito della revisione umana, quando presente.

La regola operativa e': l'AI puo' generare contenuto, ma l'app deve salvare fatti e decisioni in campi strutturati.

## Cosa Non Dovrebbe Essere Automatico

Non e' opportuno, almeno nel primo ciclo:

- trasformare ogni conversazione utente in contenuto pubblico;
- lasciare all'AI la decisione finale su interventi rischiosi;
- generare istruzioni operative dettagliate su lavori elettrici pericolosi;
- modificare tassonomie ufficiali senza revisione;
- importare tutti i vecchi alberi diagnostici solo per usarli come base del nuovo sistema.

## Modello Concettuale Da Valutare

Entita' possibili, da non implementare finche' non servono:

- `TroubleshootingSession`: sessione diagnostica legata a una pratica.
- `TroubleshootingTurn`: domanda/risposta, anche se generata dall'AI.
- `CaseSummary`: riepilogo strutturato aggiornabile.
- `RiskAssessment`: livello di rischio e motivazione.
- `KnowledgeCandidate`: pattern o guida candidata emersa dai casi.
- `KnowledgeReview`: revisione admin prima della pubblicazione.

I modelli attuali possono restare una buona base, ma il ruolo dei `DiagnosticFlow` statici diventerebbe meno centrale.
Potrebbero servire per guide ufficiali, fallback, demo e percorsi ad alta sicurezza.

## Criteri Di Valutazione

Prima di decidere, conviene misurare:

- quante domande servono per arrivare a un riepilogo utile;
- quante volte l'AI chiede informazioni gia' fornite;
- quante volte produce consigli troppo operativi o rischiosi;
- quanto spesso riconosce correttamente che serve un professionista;
- se il riepilogo e' abbastanza chiaro per un tecnico;
- se i pattern ricorrenti sono davvero riutilizzabili;
- quanto lavoro richiede la revisione editoriale;
- se l'utente percepisce il flusso come piu' semplice di un albero.

## Prototipo Di Validazione

Un primo spike potrebbe evitare import e nuove grandi migrazioni:

1. Scegliere 5 scenari reali e frequenti.
2. Definire una tassonomia minima.
3. Usare `Case` + `AiSession` per simulare la conversazione.
4. Imporre output AI in JSON strutturato.
5. Salvare domanda, risposta, riepilogo e rischio.
6. Confrontare il risultato con un flusso ad albero minimo.
7. Decidere se modellare nuove entita' o estendere quelle esistenti.

Scenari iniziali possibili:

- salvavita che scatta;
- presa che non funziona;
- luce che sfarfalla;
- odore di bruciato o surriscaldamento;
- elettrodomestico che fa saltare corrente.

## Impatto Sull'Import Da `../elettra`

Se questa ipotesi viene confermata, l'import da `../elettra` cambia natura:

- non importare grandi alberi come verita' applicativa;
- estrarre solo scenari, frasi, categorie e warning utili;
- creare un set ridotto di casi di test e prompt di validazione;
- usare i vecchi contenuti come corpus editoriale revisionabile;
- promuovere contenuti ufficiali solo dopo prova nel nuovo flusso.

## Domande Aperte

- La diagnostica deve sembrare una chat o un wizard guidato?
- L'utente deve vedere una domanda alla volta o un riepilogo progressivo?
- Quante domande massime prima di proporre apertura pratica o escalation?
- Chi revisiona i pattern generati dagli utenti?
- Quali categorie sono abbastanza stabili da restare manuali?
- Quali scenari devono essere sempre bloccati da regole fisse?
- Quale parte del vecchio contenuto merita di diventare test set?

## Direttiva Provvisoria

Finche' questa ipotesi non viene validata:

- non importare alberi diagnostici estesi;
- non riscrivere il database attorno a contenuti AI-generated;
- mantenere `Case` e `AiSession` come base sperimentale;
- trattare `DiagnosticFlow` come supporto curato, non come unico motore;
- progettare il prossimo sviluppo come spike misurabile, non come migrazione definitiva.

## Primo Spike Tecnico

Il primo spike e' descritto in [Spike Diagnostica AI Dinamica](../operations/ai-diagnostic-spike.md).
Lo spike salva uno snapshot strutturato per sessione AI e permette di valutare il modello senza importare contenuti dal vecchio progetto.

## Direzione Confermata

La direzione attuale e' ibrida, ma chat-first.

I macro-capitoli diagnostici servono per orientare contesto, sicurezza e scelte iniziali.
La conversazione resta il motore principale.

Le scelte cablate sono ammesse quando:

- riducono ambiguita';
- migliorano sicurezza;
- riducono costo AI;
- raccolgono dati strutturati;
- evitano domande inutili.

Non devono pero' diventare alberi profondi.
Il piano operativo e' descritto in [Piano Implementativo Diagnostica Ibrida Chat-First](../operations/piano-implementativo-diagnostica-chat-first.md).
