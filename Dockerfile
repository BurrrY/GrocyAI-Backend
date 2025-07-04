FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential git


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

CMD ["python", "app.py"]
