# Creator Orchestrator API — FastAPI service image
FROM python:3.11-slim

WORKDIR /code

# Install dependencies first for better layer caching
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

# Copy the application source
COPY . /code

EXPOSE 8000

# Production launch (no --reload). Override in docker-compose for dev.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
