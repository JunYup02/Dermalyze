# Backend

FastAPI service.

```
app/
  main.py       # FastAPI app entrypoint
  api/routes/   # feature routers (one file per feature, included in routes/__init__.py)
  schemas/      # pydantic request/response models
  models/       # data models
  services/     # business logic
  core/         # config, shared setup
tests/
```

## Run locally

```
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Env vars

`POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/lesion/body-regions`,
`POST /api/lesion/body-part` (auth + lesion body-part selection) need these set. Copy
`.env.example` to `.env` and fill in the values — it's loaded automatically on startup
(`app/core/config.py`) and gitignored, so it never gets committed:

```
cp .env.example .env
```

- `DATABASE_URL` — optional. If unset, falls back to a local SQLite file (`dermalyze.db`) for
  dev. Set to a PostgreSQL URL (e.g. `postgresql+psycopg2://user:password@host:5432/dermalyze`)
  once a real DB is provisioned.
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT signing config.
- `CORS_ALLOWED_ORIGINS` — comma-separated frontend origins (`*` for local dev).

Auth uses `HTTPBearer`: call `POST /api/auth/login`, then paste the returned `access_token`
into Swagger's Authorize popup (single "Value" field, no username/password form) to call
`POST /api/lesion/body-part`.
