FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt ./api_requirements.txt
COPY requirements.txt ./requirements.txt
RUN pip install -r api_requirements.txt -r requirements.txt
COPY src/ ./src/
COPY api/ ./
COPY tests/fixtures/demo_repo/ ./demo_repo/
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--timeout", "60"]
