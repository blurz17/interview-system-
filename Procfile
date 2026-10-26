web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir apps/api
release: PYTHONPATH=apps/api alembic -c apps/api/alembic.ini upgrade head
