# LLM Mode Switch Guide

This backend supports two development/deployment inference modes without code changes.

## 1) Local Mode (development)

Runs your local Qwen + LoRA model in the backend process.

Set in `backend/.env`:

```dotenv
LLM_PROVIDER=local
LLM_MODEL=spider1_qlora_latest
LLM_DEVICE=auto
```

Run with launcher from `AI_DASHBOARD`:

```bash
BACKEND_PROVIDER=local BACKEND_DEVICE=cuda ./run_dashboard.sh
```

CPU test mode:

```bash
BACKEND_PROVIDER=local BACKEND_DEVICE=cpu ./run_dashboard.sh
```

## 2) Modal Mode (server inference)

Backend runs on CPU and calls your Modal endpoint for SQL generation.

Set in `backend/.env`:

```dotenv
LLM_PROVIDER=modal
MODAL_ENDPOINT_URL=https://your-modal-endpoint.modal.run/generate-sql
MODAL_API_KEY=optional_if_endpoint_requires_auth
MODAL_TIMEOUT_SECONDS=120
```

Run with launcher from `AI_DASHBOARD`:

```bash
BACKEND_PROVIDER=modal ./run_dashboard.sh
```

## Endpoint contract expected in modal mode

Backend sends JSON payload:

```json
{
  "question": "...",
  "system_prompt": "...",
  "user_prompt": "...",
  "schema_prompt": "...",
  "max_new_tokens": 500,
  "temperature": 0.1
}
```

Your endpoint should return one of these fields:

- `sql`
- `generated_sql`
- `generated_text`
- `text`
- `output`

`choices[0].message.content` and `choices[0].text` are also supported.

## Quick health checks

Backend health:

```bash
curl -s http://127.0.0.1:8000/health
```

SQL generation test:

```bash
curl -s -X POST http://127.0.0.1:8000/debug/generate-sql \
  -H "Content-Type: application/json" \
  -d '{"question":"return all student data"}'
```
