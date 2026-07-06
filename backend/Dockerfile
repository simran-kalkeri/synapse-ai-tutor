FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc g++ ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (backend infra)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI modules first (needed for second requirements file)
COPY synapse_ai_tutor/ /app/synapse_ai_tutor/

# Install AI module dependencies (groq, sentence-transformers, faiss-cpu, etc.)
COPY synapse_ai_tutor/requirements.txt /app/synapse_ai_tutor/requirements.txt
RUN pip install --no-cache-dir -r /app/synapse_ai_tutor/requirements.txt

# Copy backend source
COPY backend/ /app/

ENV PYTHONPATH=/app:/app/synapse_ai_tutor
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
