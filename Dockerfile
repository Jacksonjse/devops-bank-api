FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from app import init_db; init_db()"

EXPOSE 5000

CMD ["python", "app.py"]
