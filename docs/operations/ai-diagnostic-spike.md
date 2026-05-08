# Spike Diagnostica AI Dinamica

## Stato

Implementato come spike tecnico reversibile.
Non sostituisce ancora i `DiagnosticFlow` statici e non autorizza import da `../elettra`.

## Obiettivo

Verificare se Elettra puo' gestire una diagnostica piu' semplice, guidata da AI, salvando comunque stato strutturato e audit sulla pratica.

## Scelte Implementate

- La `Case` resta il centro operativo.
- La conversazione usa `AiSession` e `AiMessage`.
- Ogni risposta diagnostica produce uno snapshot strutturato.
- Lo snapshot e' salvato in `AiDiagnosticSnapshot`.
- Il payload strutturato della risposta e' salvato anche in `AiMessage.metadata_json`.
- Quando una diagnosi parte da una pratica `open`, la pratica passa a `in_diagnosis`.
- Ogni avanzamento crea un evento `ai_diagnostic_progress` su `CaseEvent`.

## Contratto Diagnostico

La risposta diagnostica normalizzata contiene:

- `assistant_response`: risposta testuale visibile all'utente;
- `case_summary`: riepilogo corrente della pratica;
- `risk_level`: `unknown`, `low`, `medium`, `high` o `urgent`;
- `next_question`: prossima domanda consigliata;
- `escalation_recommended`: booleano;
- `escalation_reason`: motivo dell'escalation;
- `recommendation`: raccomandazione operativa prudente;
- `facts`: fatti strutturati estratti;
- `safety_notes`: note di sicurezza.

## Endpoint

Creazione o riuso sessione AI:

```http
POST /api/v1/ai/sessions
```

Invio turno diagnostico:

```http
POST /api/v1/ai/sessions/{session_id}/diagnostic-turns
```

Body:

```json
{
  "content": "Sento odore di bruciato vicino al quadro elettrico",
  "diagnostic_chapter_id": 1,
  "diagnostic_chapter_option_id": 4
}
```

Risposta:

```json
{
  "user_message": {},
  "assistant_message": {},
  "diagnostic_snapshot": {}
}
```

Recupero snapshot diagnostico:

```http
GET /api/v1/ai/sessions/{session_id}/diagnostic-snapshot
```

## Provider

Il provider locale e' deterministico e serve per test e sviluppo.
Riconosce in modo semplice casi elettrici e segnali di rischio come odore di bruciato, fumo, scintille, scosse e surriscaldamento.

Il provider OpenAI usa lo stesso contratto e viene normalizzato lato backend.

## Vincoli Di Sicurezza

- Nessuna istruzione per aprire quadri elettrici.
- Nessuna istruzione per manipolare cavi o componenti.
- Nessuna misura su circuiti in tensione.
- Escalation consigliata in presenza di segnali di rischio.

## Limiti Voluti

- Non c'e' ancora generazione di contenuti pubblici.
- Non c'e' promozione automatica a knowledge base.
- Non c'e' import di alberi o seed dal vecchio progetto.
- Non c'e' UX definitiva chat/wizard.
- Non c'e' valutazione qualitativa su scenari reali.

## Prossima Verifica

Lo spike va provato su 5 scenari manuali:

- salvavita che scatta;
- presa che non funziona;
- luce che sfarfalla;
- odore di bruciato o surriscaldamento;
- elettrodomestico che fa saltare corrente.

L'obiettivo non e' dimostrare che l'AI sia definitiva, ma capire se questo modello riduce davvero la complessita' degli alberi diagnostici senza perdere controllo operativo.

## Evoluzione Prevista

La direzione successiva e' descritta in [Piano Implementativo Diagnostica Ibrida Chat-First](piano-implementativo-diagnostica-chat-first.md).

Lo spike e' stato esteso con:

- macro-capitoli diagnostici;
- scelte cablate minime;
- contesto AI compatto con ultimi messaggi rilevanti;
- metadati di contesto nello snapshot;
- comando seed locale `seed_diagnostic_chapters`.
- digest periodico `AiContextDigest`;
- endpoint di debug per contesto e digest;
- stima token/costo su digest.

Deve ancora evolvere verso:

- chat come interfaccia principale;
- metriche reali provider quando disponibili;
- valutazione qualita' delle risposte su scenari manuali.

## Endpoint Contesto

Recupero contesto diagnostico compatto:

```http
GET /api/v1/ai/sessions/{session_id}/context
```

Lista digest:

```http
GET /api/v1/ai/sessions/{session_id}/context-digests
```

Compattazione manuale:

```http
POST /api/v1/ai/sessions/{session_id}/compact-context
```

Body:

```json
{
  "force": true
}
```
