# RCA & Triage Agent

LLM-powered triage and root-cause-analysis agents for manufacturing-line failures.
A triage agent classifies an incoming failure (severity, category, routing team);
an RCA agent investigates it across the plant's data sources and returns ranked,
evidence-cited hypotheses with confidence-scored workarounds.

This is a self-contained scaffold: it ships with realistic mock manufacturing data
(historical issues, FMEAs, wirelist, BOM, firmware/test-station configs,
diagnostics, and Slack threads) describing one coherent scenario - an
intermittent USB-C continuity failure at station FCT-2 - plus a few smaller
scenarios, so the agents have something real to reason over out of the box.

## Stack

- **Agents**: Python, Anthropic Claude via a tool-use loop (`backend/app/agents`).
  Triage uses `claude-haiku-4-5` (fast/cheap classification), RCA uses
  `claude-sonnet-5` (deeper multi-tool investigation). Each agent must finish by
  calling a schema-validated "terminal" tool (`submit_triage_result` /
  `submit_rca_report`), so confidence scores and evidence citations are
  structured, not parsed from free text.
- **API**: FastAPI (`backend/app/api`), Postgres (SQLAlchemy models in
  `backend/app/models.py`), Celery + Redis for async agent runs.
- **Data sources**: seeded into Postgres from `backend/app/data/*.json`; retrieval
  tools use Postgres full-text search. `backend/app/ingestion/slack_ingest.py`
  shows the pattern for pulling real Slack history once `SLACK_BOT_TOKEN` is set.
- **UI**: React + TypeScript + Vite (`frontend/`) - a triage queue and an RCA
  detail view with evidence-linked hypothesis cards and engineer feedback
  buttons (feeds the eval loop).
- **Eval**: `backend/app/eval/run_eval.py` runs labeled scenarios through the
  real RCA agent and checks whether the true root cause shows up in the top-3
  hypotheses - a starting point for tracking accuracy as prompts/tools change.

## Running it

1. Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`.
2. `docker compose up --build`
3. UI: http://localhost:5183 · API: http://localhost:8010/health

   (Default host ports are deliberately non-standard - 5183/8010/5442/6389 for
   frontend/backend/postgres/redis - to avoid clashing with other local
   services. Override via `HOST_FRONTEND_PORT` / `HOST_BACKEND_PORT` /
   `HOST_POSTGRES_PORT` / `HOST_REDIS_PORT` in `.env` if you'd rather use the
   conventional ports and they're free on your machine.)

The backend seeds the mock data on first boot (idempotent - safe on every
restart). The pre-filled triage form on the UI's home page matches the seeded
USB-C scenario (station `FCT-2`, test ID `FCT2-88213`) so you can submit it
immediately, watch triage complete, then click "Run RCA" to see the full
investigation with cited evidence.

### Running the eval harness

```
docker compose run --rm backend python -m app.eval.run_eval
```

### Logging

Both the API process and the Celery worker log through the standard `logging`
module (`app/logging_config.py`), controlled by `LOG_LEVEL` in `.env` (`DEBUG`,
`INFO`, `WARNING`, `ERROR`, `CRITICAL`). Notable log points: request-level INFO
in `app/api/*`, per-tool-call and per-iteration INFO in the agent loop
(`app/agents/claude_client.py`), run lifecycle INFO/ERROR in `app/tasks.py`, and
a CRITICAL at startup if `ANTHROPIC_API_KEY` is unset. `docker compose logs -f
backend worker` shows the full trace of a triage/RCA run, including every tool
the agent called and why it finished (or didn't).

### Error tracking (Sentry)

Set `SENTRY_DSN` in `.env` to turn on Sentry for both the API process and the
Celery worker (`backend/app/sentry_init.py`); leave it blank (default) and
nothing is sent anywhere. It's wired through the `logging` integration, so
every `logger.error(...)` / `logger.exception(...)` / `logger.critical(...)`
call already in the codebase - e.g. a failed triage/RCA run, an unknown tool
call, an agent that never converges - shows up as a Sentry event with no extra
instrumentation needed. `SENTRY_ENVIRONMENT` and `SENTRY_TRACES_SAMPLE_RATE`
control the reported environment tag and performance-trace sampling rate.
(Frontend error tracking isn't wired up - ask if you want `@sentry/react` added too.)

## Notes / what's stubbed for a real deployment

- Data source ingestion (historical issues, FMEA, wirelist, BOM, firmware
  config) is mock JSON seeded once. Swap `backend/app/ingestion/seed.py` for
  real connectors into PLM/MES/FMEA systems, matching the same
  `{evidence_id, ...fields}` shape the tools already return.
- Retrieval is Postgres full-text search, sufficient for this data volume.
  Move to pgvector + embeddings if semantic recall over a much larger corpus
  becomes necessary.
- No auth/multi-tenancy - add before exposing beyond local/internal use.
- No Alembic migrations - `Base.metadata.create_all` runs on boot. Add
  migrations before making schema changes against real data.
