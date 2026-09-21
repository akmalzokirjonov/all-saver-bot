FROM python:3.12-slim

# ── System dependencies ────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    nodejs \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    # Always use the latest yt-dlp
    && pip install --no-cache-dir --upgrade yt-dlp

# ── Application code ──────────────────────────────────────────────────────
COPY . .

# ── Storage directories ───────────────────────────────────────────────────
RUN mkdir -p /tmp/tg_downloads logs

# ── Entrypoint ────────────────────────────────────────────────────────────
CMD ["python", "main.py"]
