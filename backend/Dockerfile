# Production image for the DeepLens API. The RQ worker (Service 2 in the
# target deployment) uses this same image with its start command overridden
# to `python -m app.worker` — do not build a separate worker image.
FROM python:3.10.11-slim

WORKDIR /app

# build-essential covers packages that fall back to building from source
# when no prebuilt wheel matches this exact platform/Python combination.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt is UTF-16 encoded (see CLAUDE.md) — pip auto-detects this
# via the file's byte-order mark, so no special handling is needed here.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injects PORT at container runtime, not build time, so it has to be
# expanded by a shell rather than baked into the image — never hardcode a
# port. --reload is dev-only (it watches the filesystem and restarts on
# every write) and must never run in production.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
