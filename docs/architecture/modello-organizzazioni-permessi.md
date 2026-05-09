# Modello Organizzazioni E Permessi

> Decisione architetturale per identità, organizzazioni, ruoli, visibilità casi e condivisione con professionisti.

## Sintesi

Elettra deve usare un solo modello `Organization`, valido sia per utenti finali sia per professionisti.

Non devono esistere due alberi separati, uno per "utenti" e uno per "professionisti". La distinzione deve dipendere da piano, capability, membership e permessi.

Questo permette di partire con due casi prodotto semplici e mantenere spazio per scenari futuri come direttori lavori, amministratori di condominio, property manager o organizzazioni ibride.

## Principi

- `GuestSession` è una sessione temporanea anonima o pseudonima, non una identità stabile.
- `User` è una identità globale della piattaforma.
- `Organization` è il soggetto operativo.
- `OrganizationMembership` collega un utente a una organizzazione.
- Un utente può appartenere a più organizzazioni.
- Le autorizzazioni non dipendono solo dal tipo utente, ma da ruolo, scope, capability e assegnazioni.
- Il concetto di organizzazione deve restare invisibile o quasi per l'utente finale privato.
- Una sessione guest non crea `Organization`, `OrganizationMembership` o dati permanenti di casa.

## Modelli Concettuali

### Organization

Entità concreta: persona privata, professionista singolo, ditta, studio, team operativo o futura struttura gestionale.

Campi concettuali:

- `name`
- `kind`: `personal`, `professional`, futuro `managed`, `hybrid`
- `plan`
- `status`
- dati fiscali/contatto quando necessari

### OrganizationPlan

Piano commerciale/funzionale applicato alla organizzazione.

Responsabilità:

- limite utenti attivabili;
- capability abilitate;
- eventuali soglie operative;
- distinzione tra piano gratuito, professionale singolo, professionale multiutente, ecc.

Capability iniziali:

- `can_open_cases`
- `can_manage_properties`
- `can_share_cases`
- `can_receive_cases`
- `can_accept_case_requests`
- `can_manage_members`
- `can_manage_billing`
- `can_view_all_org_cases`
- `can_use_ai_diagnostics`

### OrganizationMembership

Relazione tra `User` e `Organization`.

Campi concettuali:

- `user`
- `organization`
- `role`
- `scope`
- `status`
- eventuale approvazione piattaforma per casi multi-organizzazione

Ruoli iniziali:

- `owner`
- `admin`
- `administrative`
- `technician`

Scope iniziali:

- `organization`: vede ciò che appartiene alla organizzazione, secondo ruolo e capability;
- `assigned`: vede solo casi/task assegnati direttamente alla membership.

Stati iniziali:

- `pending`
- `active`
- `rejected`
- `suspended`

## Due Profili Iniziali

### Guest

Il guest non è una organizzazione e non è un utente registrato.

Serve solo per provare una diagnosi leggera prima della registrazione.

Caratteristiche:

- sessione temporanea con token opaco o firmato;
- scadenza breve;
- quote molto basse;
- diagnostica limitata;
- niente `La mia casa`;
- niente allegati persistenti, salvo sperimentazione dedicata a scadenza;
- niente condivisione con professionisti;
- promozione possibile ad account registrato.

Quando il guest si registra, il sistema crea il normale `User`, la `Organization` personal e può migrare il riepilogo diagnostico utile in un nuovo `Case`.

### Personal

Profilo creato automaticamente per l'utente finale privato.

Caratteristiche:

- organizzazione personale nascosta o quasi nella UI;
- massimo un membro;
- il primo e unico membro è admin/owner;
- può aprire casi;
- può gestire immobili, impianti, documenti e scadenze;
- può condividere casi con professionisti;
- non può ricevere casi da terzi come professionista.

Questo profilo rappresenta il caso atomico: singolo utente che si registra e usa Elettra per la propria casa.

### Professional

Profilo per professionista singolo, studio, ditta o team operativo.

Caratteristiche:

- può avere uno o più membri in base al tier;
- il primo membro è admin/owner;
- può ricevere richieste di condivisione casi;
- può accettare o rifiutare richieste;
- può gestire conversazioni e interventi;
- può assegnare casi internamente alla organizzazione o a un tecnico specifico;
- i membri vedono tutta l'organizzazione o solo gli assegnati, in base allo scope.

Il piccolo professionista è una `Organization` professional con un solo membro, che è sia admin sia tecnico.

## Appartenenze Multiple

Un utente può appartenere a più organizzazioni.

Regola iniziale:

- la gestione ordinaria degli utenti di una singola organizzazione è responsabilità degli admin della organizzazione;
- l'admin può invitare utenti entro i limiti del piano;
- l'attivazione avviene via link/token email, dettaglio implementativo da decidere;
- una appartenenza operativa multi-organizzazione richiede approvazione piattaforma;
- gli admin delle singole organizzazioni non possono abilitare liberamente un utente a lavorare per più organizzazioni operative.

L'approvazione piattaforma deve essere riservata a ruoli elevati del prodotto, non agli admin delle singole organizzazioni.

## Tecnici Preferiti

L'utente finale può salvare tecnici preferiti per condividere rapidamente un caso.

La preferenza deve puntare alla membership organizzativa del tecnico, cioè:

`tecnico presso Organizzazione X`

Non deve puntare solo all'account utente del tecnico, perché lo stesso tecnico può appartenere a più organizzazioni.

Regola UX:

- se il tecnico appartiene a una sola organizzazione, non si mostra la scelta;
- se appartiene a più organizzazioni, l'utente deve selezionare il contesto organizzativo.

## Case E Visibilità

Il `Case` nasce personale e non assegnato.

Ogni `Case` deve avere una `owner_organization`, di norma la `Organization` personal dell'utente che lo apre.
Il caso deve anche conservare il riferimento all'utente richiedente/creatore, per esempio `requester` o `created_by`.

Motivazione:

- il problema può essere risolto in autonomia;
- la diagnostica AI può bastare;
- l'utente può decidere solo dopo se coinvolgere un professionista.

Il caso può poi essere condiviso con:

- un tecnico preferito;
- una organizzazione professionale;
- un tecnico trovato tramite geolocalizzazione;
- un professionista compatibile per categoria/competenza.

La visibilità deve derivare da:

- richiedente del caso;
- `owner_organization` del caso;
- richieste di condivisione;
- accettazioni;
- assegnazioni;
- membership, ruolo e scope.

Un `Case` può nascere senza `Property`.
L'utente va invitato a collegare un immobile quando utile, ma non deve essere bloccato nella diagnosi rapida.

## Condivisione Caso

La condivisione non trasferisce ownership del caso.

È una richiesta di accesso o collaborazione.
Il modello concettuale minimo è:

- `CaseShareRequest`: richiesta iniziale, con destinatario, riepilogo visibile prima dell'accettazione e stato;
- partecipazione o assegnazione stabile dopo accettazione, per esempio `CaseParticipant` o `CaseAssignment`;
- revoca sempre possibile da parte dell'utente proprietario.

Prima dell'accettazione, il tecnico o l'organizzazione vede solo:

- titolo descrittivo;
- riepilogo breve;
- eventuale contesto minimo necessario a decidere se accettare.

Non vede chat completa, allegati o dettagli sensibili prima dell'accettazione.

Azioni possibili:

- accettare con click semplice;
- rifiutare senza motivazione;
- rifiutare con motivazione opzionale, per esempio indisponibilità o carico di lavoro.

Dopo accettazione, si apre una chat semplice utente-professionista dentro il caso.

Obiettivo iniziale della chat:

- accordarsi;
- chiarire dettagli;
- arrivare a un preventivo di massima.

Allegati nella chat utente-professionista sono utili, ma possono essere una fase successiva.

La revoca blocca da quel momento l'accesso a:

- caso;
- allegati;
- chat diagnostica AI;
- documenti;
- dettagli condivisi.

Il professionista può mantenere la visibilità dei messaggi già scambiati nella conversazione utente-professionista.
Questo serve come traccia storica/amministrativa della relazione, senza mantenere accesso al materiale tecnico revocato.
Nuovi messaggi non sono possibili dopo revoca, salvo nuova condivisione o nuovo contesto autorizzato.

## Condivisione Selettiva

L'utente deve scegliere cosa condividere.

Opzioni minime:

- solo riepilogo;
- chat diagnostica;
- allegati selezionati;
- tutto il caso.

Prima della condivisione deve comparire un advice esplicito sui dati sensibili.

Esempi:

- foto di ambienti domestici;
- documenti personali;
- dati tecnici dell'immobile;
- metadati file;
- EXIF;
- geolocalizzazione;
- data, dispositivo o informazioni incorporate negli allegati.

Il sistema non deve rimuovere automaticamente i metadati, perché possono essere utili alla diagnosi o alla gestione di più immobili.

Potranno essere aggiunti in futuro strumenti opzionali per anteprima o pulizia metadati.

## Chat E Materiali

Nel caso devono essere distinti almeno tre flussi:

1. chat diagnostica AI;
2. richiesta di condivisione/accettazione;
3. chat utente-professionista dopo accettazione.

La comunicazione utente-professionista non deve essere modellata come chat rigida 1:1 interna al caso.

Il modello concettuale è:

- `Conversation`: thread con subject/topic;
- `ConversationPost`: messaggio/post dentro la conversazione;
- `ConversationParticipant`: partecipante flessibile, con utente reale e, se necessario, membership/organizzazione rappresentata.

Una conversazione può:

- essere collegata a un `Case`;
- esistere fuori da un caso specifico;
- essere collegata in futuro a `Property`, `Asset` o altro contesto operativo;
- includere più utenti;
- includere utenti della stessa organizzazione;
- includere utenti di organizzazioni diverse.

La struttura del database non deve decidere da sola chi può entrare in una conversazione.
Accesso e partecipazione devono essere governati dalle policy applicative, dal contesto operativo, dalle membership, dagli scope e dal flusso che ha aperto la conversazione.

Gli allegati caricati durante la diagnosi possono essere:

- documentazione del caso;
- documentazione stabile dell'immobile;
- materiale utile alla chat;
- materiale che l'AI può usare solo se esplicitamente consentito.

Caricare un allegato non significa inviarlo automaticamente all'AI.

## Immobili

Il modello `Property` deve essere introdotto subito.
Ogni `Property` appartiene a una `Organization`, non direttamente a un `User`.

Per l'utente finale privato questa organizzazione è la sua `Organization` personal.
Nella UI può continuare a essere mostrato come "mio immobile".

Motivazione:

- molti problemi sono legati a un immobile specifico;
- gli allegati possono descrivere impianti, locali, documenti o scadenze non limitati al singolo caso;
- la geolocalizzazione può essere utile quando l'utente gestisce più immobili;
- futuri soggetti gestionali potranno usare lo stesso modello senza cambio architetturale.

Per il primo rilascio, l'utente finale usa `Property` come "Immobile".

## Asset

Un `Asset` deve appartenere sempre a una `Property`.

Se una organizzazione ha asset generali non legati a un immobile specifico, può creare una `Property` generica/convenzionale.
Questo mantiene il modello semplice e riduce eccezioni autorizzative.

## Allegati E Ownership A Cascata

Gli allegati non devono avere necessariamente una `owner_organization` duplicata.

L'owner deve essere risolto a cascata dal contesto proprietario:

- allegato su `Property`: owner = organization della property;
- allegato su `Asset`: owner = organization della property dell'asset;
- allegato su `Case`: owner = owner organization del case;
- allegato su messaggio o conversazione: owner = contesto autorizzativo della conversazione e dei suoi partecipanti.

Regola tecnica: non devono esistere allegati orfani.

Ogni allegato deve avere almeno un contesto proprietario risolvibile.
Se in futuro servirà un'area temporanea di upload, dovrà avere una scadenza o un owner provvisorio esplicito.

## Tipologie Future

Non implementare subito flussi prodotto dedicati per:

- direttori lavori;
- amministratori di condominio;
- property manager;
- organizzazioni ibride;
- team misti utente/professionista.

Il modello deve però permetterli in futuro tramite nuovi piani, capability e UI dedicate, senza cambiare l'architettura di base.

## Direttiva Implementativa

Implementare una sola struttura organizzativa:

- `Organization`
- `OrganizationPlan`
- `OrganizationMembership`
- `Conversation`
- `ConversationPost`
- `ConversationParticipant`

Evitare modelli paralleli come `CustomerOrganization` e `ProfessionalOrganization`.

Evitare anche conversazioni vincolate rigidamente a una sola coppia utente-professionista.
Le conversazioni devono essere thread contestuali, con partecipanti e visibilità gestiti dalle policy applicative.

Le prime API devono coprire solo i due profili iniziali:

- utente finale `personal`;
- professionista `professional`.

Tutto il resto deve restare possibile a livello schema, ma fuori dal flusso prodotto iniziale.
