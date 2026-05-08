# Decisioni Prima Dell'Import Da `../elettra`

> Questo documento raccoglie le decisioni da prendere prima di importare contenuti, seed o flussi dal vecchio progetto `../elettra`.

## Principio

L'import da `../elettra` non deve essere una migrazione cieca.

`../elettra` contiene valore prodotto, contenuti e prove UX.
Non deve imporre schema dati, API legacy o vecchi compromessi tecnici.

Esiste inoltre un'ipotesi alternativa da verificare: ridurre fortemente gli alberi diagnostici statici e usare l'AI per costruire domande dinamiche durante l'uso reale.
Questa ipotesi e' descritta in [Ipotesi Diagnostica AI Dinamica](../product/ipotesi-diagnostica-ai-dinamica.md).

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
