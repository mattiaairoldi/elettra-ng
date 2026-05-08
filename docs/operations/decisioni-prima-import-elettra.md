# Decisioni Prima Dell'Import Da `../elettra`

> Questo documento raccoglie le decisioni da prendere prima di importare contenuti, seed o flussi dal vecchio progetto `../elettra`.

## Principio

L'import da `../elettra` non deve essere una migrazione cieca.

`../elettra` contiene valore prodotto, contenuti e prove UX.
Non deve imporre schema dati, API legacy o vecchi compromessi tecnici.

Esiste inoltre un'ipotesi alternativa da verificare: ridurre fortemente gli alberi diagnostici statici e usare l'AI per costruire domande dinamiche durante l'uso reale.
Questa ipotesi e' descritta in [Ipotesi Diagnostica AI Dinamica](../product/ipotesi-diagnostica-ai-dinamica.md).

## Decisioni Confermate

- `elettra-ng` e' il repository principale.
- `../elettra` e `../elettra2` restano fonti di contesto o import selettivo.
- La diagnostica e' ibrida ma prioritariamente chat-first.
- I macro-capitoli iniziali restano pochi e modificabili.
- Storage documenti: S3-compatible fin dall'inizio, con MinIO in locale.
- AI: un provider reale iniziale, OpenAI, con provider abstraction e possibilita' di usare OpenAI anche in sviluppo/test.
- Nessun import automatico del vecchio albero diagnostico prima di consolidare il modello nuovo.
- `Case` nasce personale/non assegnato e puo' essere condiviso successivamente.
- Introdurre subito `Property` come modello tecnico di "Immobile".
- `Property` appartiene a una `Organization`.
- `Case` appartiene a una `owner_organization` e mantiene il riferimento all'utente richiedente.
- `Case.property` e' opzionale; `Asset` appartiene sempre a una `Property`.
- Gli allegati ereditano l'owner dal contesto, senza duplicare necessariamente `owner_organization`.
- La condivisione caso usa richiesta, accettazione/rifiuto e revoca sempre possibile dall'utente.
- Dopo revoca, il professionista perde accesso al caso e ai documenti, ma mantiene lo storico dei messaggi gia' scambiati nella conversazione.
- La comunicazione usa `Conversation` e `ConversationPost`, thread flessibili collegabili o meno a un caso.
- Usare un solo modello organizzativo, documentato in [Modello Organizzazioni E Permessi](../architecture/modello-organizzazioni-permessi.md).
- Partire con due profili organizzazione iniziali:
  - `personal`, per l'utente finale;
  - `professional`, per professionista singolo o organizzazione professionale.

## Decisioni Da Prendere

### 1. Perimetro dei contenuti

Decidere quali contenuti importare nel primo seed:

- solo elettrico;
- elettrico + climatizzazione;
- elettrico + manutenzione casa generale;
- tutto cio' che esiste nel vecchio progetto, ma revisionato.

### 2. Struttura dei flussi diagnostici

Decidere se il primo rilascio deve avere:

- pochi `DiagnosticFlow` ben curati;
- molti flussi dimostrativi;
- un flusso principale con sotto-rami;
- piu' flussi separati per categoria;
- flussi statici minimi e diagnostica dinamica AI-driven;
- nessun import massivo di alberi, usando i vecchi contenuti solo come corpus revisionabile.

### 3. Tassonomia iniziale

Decidere categorie e tag iniziali:

- categorie tecniche principali;
- tag competenze professionisti;
- tag componenti/asset;
- tag manutenzione/promemoria.

### 4. Politica di sicurezza contenuti

Decidere regole editoriali per diagnosi e AI:

- cosa l'utente puo' fare in autonomia;
- cosa deve sempre portare a escalation;
- testi standard per rischio elettrico;
- limiti delle istruzioni operative.

### 5. Professionisti demo o reali

Decidere se importare:

- professionisti fittizi/demo;
- professionisti reali;
- nessun professionista iniziale;
- solo profili tecnici generici per test.

### 6. Promemoria e manutenzioni

Decidere se i vecchi `TemplatePromemoria` diventano:

- seed ufficiale;
- seed demo;
- materiale da revisionare;
- funzionalita' rinviata.

### 7. Geolocalizzazione

Decidere come trattare coordinate e zone:

- coordinate reali;
- coordinate demo;
- solo citta'/area testuale;
- nessuna geolocalizzazione nei seed iniziali.

### 8. Qualita' contenuti

Decidere il livello minimo prima dell'import:

- import tecnico grezzo e revisione dopo;
- revisione manuale prima dell'import;
- import solo di flussi gia' validati;
- riscrittura contenuti a partire dal PDF canonico.

### 9. Strategia seed

Decidere formato e destinazione:

- fixture Django JSON;
- management command dedicato;
- script di conversione idempotente;
- seed separati per dev, demo e staging.

### 10. Tracciabilita'

Decidere come documentare l'origine dei contenuti:

- mantenere mapping vecchio ID -> nuovo ID;
- registrare fonte file;
- conservare report di conversione;
- non conservare riferimenti vecchi dopo normalizzazione.

## Direttiva Provvisoria

Finche' queste decisioni non sono prese:

- non importare dati da `../elettra`;
- non creare seed derivati dal vecchio progetto;
- non adattare modelli per accomodare contenuti storici;
- non importare alberi diagnostici estesi;
- lavorare solo su fondazione tecnica, schema, test, documentazione e spike controllati.
