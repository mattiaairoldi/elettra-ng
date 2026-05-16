# Stato Attuale

Ultimo aggiornamento: 2026-05-16.

Questo documento fotografa dove e arrivato `elettra-ng` dopo il completamento del flusso guest -> account/caso, della registrazione standard con conferma email, dei tab autenticati `Diagnosi`, `Tecnici` e `Profilo`, e del primo staging VPS Docker/Caddy con Flutter web servito sulla root del dominio.

## Stato Operativo

Il backend Django e avviabile localmente con Docker Compose e usa PostgreSQL/PostGIS, Redis, MinIO e Mailpit. Lo staging pubblico e operativo su VPS con Docker Compose, Caddy, PostgreSQL/PostGIS, Redis, MinIO, Mailpit privato e Flutter web servito da `https://elettra.iapersonale.it/`.

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

La strategia scelta per staging/deploy e usare script CI locali versionati come fonte comune: oggi lo staging funziona con build/upload locale dell'immagine e upload del bundle Flutter web; il prossimo passaggio e spostare l'immagine backend su registry, cosi il VPS scarica immagini gia costruite invece di riceverle dal checkout locale. Dettaglio operativo: [CI Locale E Deploy Staging](ci-locale-e-deploy-staging.md).

Sono disponibili gli script `scripts/ci/backend.sh`, `scripts/ci/mobile.sh`, `scripts/ci/build-images.sh`, `scripts/ci/local-all.sh` e `scripts/deploy/staging.sh`.

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
- promozione ospite ad account/caso;
- localizzazione italiana dei livelli di rischio diagnostico (`unknown`, `low`, `medium`, `high`, `urgent`).

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
scripts/ci/local-all.sh
```

Risultato dell'ultimo giro completo:

- backend: `126 passed`;
- migrazioni: nessun cambio rilevato;
- OpenAPI: validato senza warning bloccanti;
- Flutter analyze/test/build web: verdi.
- Flutter widget test: `10 passed`.
- CI locale: `scripts/ci/local-all.sh` verde, inclusa build APK debug e build immagine Docker backend.

Verifiche successive eseguite dopo il deploy staging e la localizzazione dei livelli di rischio:

- `flutter analyze`: verde;
- `flutter test`: `12 passed`;
- `flutter build web --dart-define=API_BASE_URL=https://elettra.iapersonale.it/api/v1`: verde;
- deploy Flutter web su staging: completato;
- health staging `https://elettra.iapersonale.it/api/v1/health`: `{"status": "ok"}`;
- provider AI OpenAI configurato su staging con chiave presente nel container, senza esporre il valore.

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
- registry immagini con push remoto configurato;
- deploy staging basato su pull da registry invece che upload locale dell'immagine;
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

Il prossimo step operativo e trasformare lo staging gia funzionante in un deploy ripetibile tramite registry, poi passare alla validazione mobile nativa su backend pubblico.

Sequenza consigliata:

1. Decidere il registry immagini:
   - GitHub Container Registry, Gitea registry o registry Docker privato;
   - convenzione tag per staging, per esempio `sha-<commit>`.
2. Configurare build/push immagine:
   - usare `scripts/ci/build-images.sh`;
   - abilitare push solo quando `PUSH=true`;
   - salvare credenziali fuori repo.
3. Adeguare deploy staging al pull:
   - `STAGING_UPLOAD_IMAGE=false`;
   - `STAGING_PULL=true`;
   - `STAGING_IMAGE_REPOSITORY` puntato al registry;
   - deploy via SSH con migrate/up/restart.
4. Verificare staging post-registry:
   - API health;
   - Flutter web;
   - registrazione/conferma email;
   - diagnosi AI con provider reale;
   - flusso casa/asset/problemi.
5. Preparare configurazione runtime per device/emulatore:
   - API base URL per Android emulator (`10.0.2.2`) o device fisico su LAN;
   - profili ambiente Flutter per dev/demo;
   - verifica storage sicuro token su Android/iOS.
6. Validare Android:
   - avvio su emulator o device fisico;
   - login;
   - `La mia casa`;
   - `Problemi da risolvere`;
   - guest -> account/caso;
   - notifiche in-app.
7. Preparare signing:
   - Android keystore e variabili CI;
   - bundle id iOS;
   - Apple Team/App Store Connect;
   - segreti CI per build firmate.
8. Validare iOS:
   - build CI macOS `--no-codesign` come controllo tecnico;
   - build firmata quando sono disponibili certificati/profili;
   - distribuzione TestFlight.

La web app ora copre i tab principali ed e pubblicata su staging; la prossima riduzione di rischio e eliminare l'upload manuale dell'immagine backend, poi validare networking, storage token e runtime mobile reale.
