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

## Skin lesion classification

`POST /api/gemini-report` (image in, classification + Gemini natural-language report out) returns
`report` (overall summary), plus `texture_note` and `pigment_note` — short observations Gemini
generates by looking directly at the uploaded photo (via structured JSON output, see
`app/services/gemini_report.py`), not static text.

The classification step (predicting one of the 7 HAM10000 lesion types) runs **locally**, in-process
— `app/services/local_predictor.py` loads `app/ml_models/skin_lesion_model.pkl` (a scikit-learn
RandomForest over color/texture/HOG features, see `app/ml/features.py`) once on first use and calls
`predict_proba` on it. No GCP project, endpoint, or credentials needed for this — the model ships
with the repo.

To retrain it (e.g. after collecting more data), point `scripts/train_model.py` at a copy of the
original HAM10000 export (a `vertex_ai_import.csv` manifest + an `images/` folder — see the script's
docstring):

```
python scripts/train_model.py --data-dir /path/to/Dermalyze_data/original
```

This overwrites `app/ml_models/skin_lesion_model.pkl` and prints accuracy / macro-F1 / risk-tier
(Low vs High) precision-recall on the held-out TEST split. The training is tuned to prioritize
**high-risk recall** (catching mel/bcc/akiec cases) over raw accuracy, since a missed high-risk
lesion is a much worse failure than an unnecessary "see a doctor" prompt for this kind of screening
tool — see `HIGH_RISK_LABELS`/`DEFAULT_HIGH_RISK_BOOST` in the script if that trade-off needs
retuning. As shipped: ~86% high-risk recall, ~39% high-risk precision, ~63% raw 7-class accuracy —
a reasonable classical-ML baseline, but meaningfully weaker than a purpose-trained CNN or the
previous Vertex AI AutoML model. Treat it (and the reference-only framing already in the UI) as a
placeholder to improve, not a clinical-grade classifier.

## Env vars

Copy `.env.example` to `.env` and fill in the values — it's loaded automatically on startup
(`app/core/config.py`) and gitignored, so it never gets committed:

```
cp .env.example .env
```

- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/apikey), needed for the
  natural-language report text (not the classification itself, which needs no key/env var).

`GET /api/hospitals/nearby?lat=&lng=` (nearby hospitals/clinics) needs no env var or API key —
it queries the free, keyless OpenStreetMap Overpass API (`app/services/places.py`). Tradeoff: OSM
coverage is community-sourced, so `phone`/`opening_hours` are only present when someone tagged
them, and there's no rating or "open now" — we don't fabricate those, so the UI shows distance/
address/directions plus phone or hours only when real data exists. Swap back to Google Places if
richer, more consistent data becomes worth the cost (see git history for the previous
implementation).

`POST /api/auth/signup`, `POST /api/auth/login`, `GET /api/lesion/body-regions`,
`POST /api/lesion/body-part` (auth + lesion body-part selection) need:

- `DATABASE_URL` — optional. If unset, falls back to a local SQLite file (`dermalyze.db`) for
  dev. Set to a PostgreSQL URL (e.g. `postgresql+psycopg2://user:password@host:5432/dermalyze`)
  once a real DB is provisioned.
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT signing config.
- `CORS_ALLOWED_ORIGINS` — comma-separated frontend origins (`*` for local dev).

Auth uses `HTTPBearer`: call `POST /api/auth/login`, then paste the returned `access_token`
into Swagger's Authorize popup (single "Value" field, no username/password form) to call
`POST /api/lesion/body-part`.

## Deploying to Render

`render.yaml` in this folder is a [Render Blueprint](https://render.com/docs/blueprint-spec)
for this service — connect the repo in the Render dashboard and it picks up the build/start
commands and health check automatically. Then fill in the env vars it declares (all `sync: false`,
so Render prompts for them instead of committing values):

- Same list as above (`GEMINI_API_KEY`, `SECRET_KEY` is auto-generated, etc). No Places API key or
  GCP credentials needed — the classifier's `.pkl` is committed to the repo and loads in-process.
- `DATABASE_URL` — Render's disk is ephemeral, so the SQLite fallback gets wiped on every deploy.
  Provision a Postgres instance (Render's own, or any external one) before real users sign up, and
  set this to its connection string.
- `CORS_ALLOWED_ORIGINS` — set to the frontend's actual deployed origin once it has one (not `*`)
  so only that origin can call the API.

Once deployed, point the frontend at it — see `frontend/README.md`.
