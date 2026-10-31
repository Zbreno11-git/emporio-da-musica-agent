# Demo image: the FastAPI app plus the generated, read-only demo data (catalog, demo orders, manual index).
# Build context comes from .gcloudignore, which uploads only the files listed there.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/srv/data/build EXPOSE_TRACE=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data/build ./data/build

RUN useradd --system --no-create-home appuser
USER appuser

# One worker: sessions live in process memory (docs/DECISIONS.md, D8; guide 02 §8).
CMD ["sh", "-c", "exec uvicorn app.main:get_app --factory --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
