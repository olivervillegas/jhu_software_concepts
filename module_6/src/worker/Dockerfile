FROM python:3.11-slim

WORKDIR /app

COPY src/worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

ENV PYTHONPATH=/app

USER 1000

CMD ["python", "-m", "src.worker.consumer"]