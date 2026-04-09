# Modal Setup for Text2SQL

This folder contains scripts to upload model artifacts to Modal and deploy a SQL generation endpoint.

## 1. Authenticate

From backend root:

```bash
.venv/bin/python -m pip install modal
.venv/bin/python -m modal token new
# if needed, configure profile explicitly:
# .venv/bin/python -m modal profile activate default
```

If you still see "Token missing", run:

```bash
.venv/bin/python -m modal profile current
```

It should print an active profile.

## 2. Upload model files to Modal Volume

```bash
cd /home/su/SIJ/Thesis/AI_DASHBOARD/backend
chmod +x modal/upload_model_to_modal.sh modal/deploy_modal.sh
./modal/upload_model_to_modal.sh
```

Optional env overrides:

- `MODAL_VOLUME_NAME`
- `BASE_MODEL_LOCAL_PATH`
- `ADAPTER_LOCAL_PATH`

## 3. Deploy endpoint

```bash
cd /home/su/SIJ/Thesis/AI_DASHBOARD/backend
./modal/deploy_modal.sh
```

The deploy output includes endpoint URLs.

After deploy, verify endpoint quickly:

```bash
curl -X POST "https://<your-endpoint>.modal.run" \
	-H "Content-Type: application/json" \
	-d '{"question":"return all student data","system_prompt":"You are SQL generator","user_prompt":"Question: return all student data\\n\\nSQL:"}'
```

## 4. Wire backend to Modal mode

Update `backend/.env`:

```dotenv
LLM_PROVIDER=modal
MODAL_ENDPOINT_URL=https://<your-endpoint-url>
MODAL_API_KEY=
MODAL_TIMEOUT_SECONDS=120
```

Then run backend as usual.

## 5. Local mode switch back

To use local GPU/CPU model again:

```dotenv
LLM_PROVIDER=local
LLM_MODEL=spider1_qlora_latest
LLM_DEVICE=auto
```
