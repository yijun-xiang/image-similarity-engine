FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app

RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
    CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); \
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32')"

ENV PYTHONUNBUFFERED=1
ENV MODEL_CACHE_DIR=/app/models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
