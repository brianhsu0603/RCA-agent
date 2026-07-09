#!/bin/sh
set -e

DB_HOST=$(python -c "import os,urllib.parse as u; print(u.urlparse(os.environ.get('DATABASE_URL','')).hostname or 'db')")
DB_PORT=$(python -c "import os,urllib.parse as u; print(u.urlparse(os.environ.get('DATABASE_URL','')).port or 5432)")

echo "Waiting for postgres at ${DB_HOST}:${DB_PORT}..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "Postgres is up."

python -m app.ingestion.seed

case "$1" in
  api)
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ;;
  worker)
    exec celery -A app.celery_app worker --loglevel=info
    ;;
  *)
    exec "$@"
    ;;
esac
