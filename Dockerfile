FROM python:3.11-slim

WORKDIR /srv

# install deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

EXPOSE 8000

# DATABASE_URL / JWT_SECRET / Celery URLs are provided at runtime, never baked in.
# entrypoint runs `alembic upgrade head` then starts uvicorn.
CMD ["./entrypoint.sh"]
