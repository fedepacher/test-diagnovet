FROM python:3.13

WORKDIR /app

COPY frontend/requirements.txt .

RUN pip install -U pip && pip install -r requirements.txt

COPY frontend/ .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
