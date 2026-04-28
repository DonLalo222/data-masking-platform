FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy English model used by Presidio
RUN python -m spacy download en_core_web_lg
# Download the spaCy Spanish model for clinical support
RUN python -m spacy download es_core_news_lg

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
