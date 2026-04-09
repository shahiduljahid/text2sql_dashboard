# text2sql_dashboard

FastAPI backend for text-to-SQL dashboard.

## Railway Deployment

This backend is configured for Railway with the following files:
- `Procfile`
- `nixpacks.toml`
- `railway.json`

### 1. Create a new Railway project
- In Railway, create a new project and connect this repository.
- Set the root directory to `AI_DASHBOARD/backend` if your repo contains multiple folders.

### 2. Set required environment variables

Use Modal inference in Railway to avoid shipping local model files:

- `LLM_PROVIDER=modal`
- `MODAL_ENDPOINT_URL=https://shahiduljahid--text2sql-sql-endpoint-generate-sql.modal.run`
- `MODAL_TIMEOUT_SECONDS=120`

Optional:

- `MODAL_API_KEY=<token>` (only if your Modal endpoint requires auth)
- `ALLOW_WRITE_OPERATIONS=true`
- `MAX_QUERY_ROWS=1000`

### 3. Deploy

Railway will:
- Install dependencies from `requirements-minimal.txt`
- Start the app with `python run.py`
- Health check `GET /health`

### 4. Notes

- App binds to `0.0.0.0:$PORT` automatically.
- If `student_management.db` is missing on first boot, the app initializes it automatically.
- Railway filesystem is ephemeral. For persistent data, attach a Railway volume or switch to a managed database.
