# Astrazione Provider AI

## Scopo

L'AI backend deve poter cambiare provider senza riscrivere task, API o logica diagnostica.
Per ora i provider reali restano due:

- `local`: deterministico, usato in sviluppo e test;
- `openai`: provider reale configurato via environment.

Non sono stati introdotti provider non usati.

## Struttura

La logica provider vive in:

```text
apps/ai_assistant/providers/
```

File principali:

- `base.py`: errore comune, protocollo provider e normalizzazione payload diagnostico;
- `context.py`: costruzione contesto, prompt e messaggi da inviare al provider;
- `local.py`: provider locale deterministico;
- `openai.py`: provider OpenAI;
- `registry.py`: registry e factory `get_ai_provider`;
- `apps/ai_assistant/provider.py`: compat layer temporaneo.

## Contratto Provider

Un nuovo provider deve implementare:

```python
build_reply(session, messages)
stream_reply(session, messages)
build_diagnostic_reply(session, messages)
```

Il payload diagnostico deve essere normalizzato tramite `normalize_diagnostic_payload`.
Il backend si aspetta sempre questi campi:

- `assistant_response`;
- `case_summary`;
- `risk_level`;
- `next_question`;
- `escalation_recommended`;
- `escalation_reason`;
- `recommendation`;
- `facts`;
- `excluded_facts`;
- `asked_questions`;
- `safety_notes`.

## Registry

I provider sono registrati in `AI_PROVIDER_REGISTRY`.

La scelta avviene con:

```env
AI_PROVIDER=local
```

oppure:

```env
AI_PROVIDER=openai
```

Provider non supportati generano `AiProviderError` con elenco dei provider disponibili.

## Regole

- Non importare SDK provider fuori dai file provider dedicati.
- Non mettere logiche OpenAI-specifiche nei task Celery o nelle view.
- Non cambiare il contratto diagnostico per un singolo provider.
- Non introdurre fallback automatici finche' non servono davvero.
- Mantenere `local` deterministico per test automatici.

## Prossimi Passi Possibili

Se in futuro serviranno piu' provider:

- aggiungere classe provider concreta;
- registrarla in `registry.py`;
- aggiungere env dedicati;
- testare errori, payload diagnostico e streaming;
- aggiungere metriche reali token/costo se disponibili.
