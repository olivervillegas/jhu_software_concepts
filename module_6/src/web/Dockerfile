FROM python:3.11-slim

WORKDIR /app

# Install deps (web-specific)
COPY src/web/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the whole src tree so `import src...` works
COPY src /app/src

ENV PYTHONPATH=/app

EXPOSE 8080
USER 1000

CMD ["python", "-m", "src.web.run"]