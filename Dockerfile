FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install flask requests python-dotenv

CMD ["python", "app.py"]
