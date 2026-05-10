# Stato Attuale

Ultimo aggiornamento: 2026-05-10.

Questo documento fotografa dove e arrivato `elettra-ng` dopo il completamento del flusso guest -> account/caso, della registrazione standard con conferma email e dei tab autenticati `Diagnosi`, `Tecnici` e `Profilo`.

## Stato Operativo

Il backend Django e avviabile localmente con Docker Compose e usa PostgreSQL/PostGIS, Redis, MinIO e Mailpit.

Sono implementati e verificati:

- API `/api/v1/` con schema OpenAPI validato;
- autenticazione mobile token-based con JWT access/refresh, refresh e logout con blacklist;
- registrazione standard con email di conferma, blocco login prima della verifica e link web intercettabile in Mailpit;
- modello organizzativo con `Organization`, piani `personal`/`professional` e membership;
- `La mia casa`: immobili, asset, allegati asset, storico manutenzione e promemoria;
- apertura di una problematica da asset;
- `Problemi da risolvere`: lista casi, dettaglio caso, consigli guidati, AI diagnostica, snapshot e condivisione verso professionista;
- conversazioni e richieste di condivisione caso;
- notifiche in-app con lista, summary, mark-read e `DeviceInstallation`;
- diagnostica AI chat-first con `AiDiagnosticSnapshot`, digest di contesto e ledger uso AI;
- guest tier pre-onboarding con token opaco hashato, scadenza, quote basse, consigli salvati e AI limitata;
- promozione guest -> account/caso con creazione `User`, `Organization` personal, `Case`, JWT, ricollegamento `AiSession`/ledger e cancellazione token guest lato Flutter.

La app Flutter in `mobile/elettra_mobile` e il client principale previsto per Android/iOS. Il target web viene usato per smoke rapidi e demo funzionali.

La strategia scelta per staging/deploy e usare script CI locali versionati come fonte comune: oggi esecuzione locale dopo commit, poi stessi script in GitHub Actions o Gitea Actions, con immagini Docker costruite dalla CI e scaricate dal VPS tramite registry. Dettaglio operativo: [CI Locale E Deploy Staging](ci-locale-e-deploy-staging.md).

Sono operativi in Flutter:

- login token-based;
- registrazione utente;
- conferma email da link web `/verify-email`;
- bootstrap sessione da token salvato;
- `La mia casa`;
- `Problemi da risolvere`;
- `Diagnosi` autenticata con creazione pratica, primo turno AI e apertura diretta del dettaglio pratica;
- `Tecnici` con lista professionisti, filtro categoria, area di servizio, profilo e ingresso rapido a `Problemi da risolvere`;
- `Profilo` con riepilogo account, stato email, stato sessione, refresh da `/auth/me` e logout confermato;
- dettaglio problema con diagnostica guidata/AI;
- condivisione professionista;
- centro notifiche in-app;
- accesso ospite;
- promozione ospite ad account/caso.

Non restano tab placeholder nel flusso autenticato principale.

Il flusso MVP end-to-end oggi passa da `La mia casa`, `Diagnosi`, `Tecnici`, `Profilo`, `Problemi da risolvere` e pre-login guest.

## Verifiche Eseguite

Verifiche automatiche piu recenti:

```bash
docker compose run --rm web uv run pytest
docker compose run --rm web uv run python manage.py makemigrations --check --dry-run
docker compose run --rm web uv run python manage.py spectacular --validate --fail-on-warn --file /tmp/elettra-schema.yml
cd mobile/elettra_mobile && flutter analyze
cd mobile/elettra_mobile && flutter test
cd mobile/elettra_mobile && flutter build web
```

Risultato:

- backend: `126 passed`;
- migrazioni: nessun cambio rilevato;
- OpenAPI: validato senza warning bloccanti;
- Flutter analyze/test/build web: verdi.
- Flutter widget test: `10 passed`.

Smoke funzionali eseguiti su Flutter web:

- login autenticato e `La mia casa` con seed demo reale;
- `Problemi da risolvere` -> consiglio guidato -> turno AI -> snapshot -> condivisione a professionista -> notifica in-app;
- `Continua come ospite` -> diagnosi -> `Salva come pratica` -> creazione account -> caso visibile in `Problemi da risolvere`.
- `Registrati` -> email Mailpit -> conferma email -> ritorno al login.
- `Diagnosi` autenticata -> creazione pratica senza asset -> primo turno AI -> dettaglio pratica con messaggio AI iniziale.

Copertura widget test aggiunta:

- `Tecnici` -> filtro categoria -> lista professionisti -> ingresso rapido a `Problemi da risolvere`.
- `Profilo` -> stato account/sessione -> refresh dati da `/auth/me` -> logout confermato.

## Non Ancora Fatto

Non sono ancora implementati o validati:

- push native FCM/APNs;
- signing Android/iOS;
- TestFlight;
- validazione su device fisico o emulatori nativi;
- build iOS firmata;
- script CI locali `scripts/ci/*`;
- Compose staging remoto `deploy/compose.staging.yml`;
- registry immagini e deploy automatico su VPS;
- API aggregate aggiuntive oltre a quelle emerse come necessarie dalla UI corrente;
- assegnazione interna organizzazione/tecnico dopo accettazione richiesta;
- regole di sicurezza AI non negoziabili formalizzate per ogni capitolo;
- taratura soglie reali di compattazione, token e costi;
- import o conversione dati da `../elettra`;
- marketplace, pagamenti, videochiamate e AI su immagini.

Restano fuori perimetro guest:

- allegati persistenti da guest;
- condivisione con professionisti da guest;
- `La mia casa` guest;
- promemoria guest;
- account anonimi permanenti.

## Prossimo Step

Il prossimo step operativo e preparare la base CI/deploy locale prima della validazione mobile nativa su backend pubblico.

Sequenza consigliata:

1. Implementare gli script CI locali documentati:
   - `scripts/ci/backend.sh`;
   - `scripts/ci/mobile.sh`;
   - `scripts/ci/build-images.sh`;
   - `scripts/ci/local-all.sh`.
2. Preparare Compose staging e variabili esempio:
   - `deploy/compose.staging.yml`;
   - `.env.staging.example`;
   - modello immagine backend versionata.
3. Preparare configurazione runtime per device/emulatore:
   - API base URL per Android emulator (`10.0.2.2`) o device fisico su LAN;
   - profili ambiente Flutter per dev/demo;
   - verifica storage sicuro token su Android/iOS.
4. Validare Android:
   - avvio su emulator o device fisico;
   - login;
   - `La mia casa`;
   - `Problemi da risolvere`;
   - guest -> account/caso;
   - notifiche in-app.
5. Preparare signing:
   - Android keystore e variabili CI;
   - bundle id iOS;
   - Apple Team/App Store Connect;
   - segreti CI per build firmate.
6. Validare iOS:
   - build CI macOS `--no-codesign` come controllo tecnico;
   - build firmata quando sono disponibili certificati/profili;
   - distribuzione TestFlight.

La web app ora copre i tab principali; la prossima riduzione di rischio e rendere ripetibile build/deploy, poi validare networking, storage token e runtime mobile reale.
