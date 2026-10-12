# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-12
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
# Builds the image for the FastAPI app in app/.
# Build: docker build -t study-cloud .
# Run:   docker run -p 8000:8000 study-cloud

# 1. Base image: Debian with Python, "slim" = without extras we don't need
FROM python:3.10-slim

# 2. All following paths are relative to /code inside the image
WORKDIR /code

# 3. Dependencies first: this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Then the code, which changes often
COPY app/ app/

# 5. The port the app listens on (documentation for readers and tools)
EXPOSE 8000

# 6. Start the server; 0.0.0.0 so it accepts connections from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
