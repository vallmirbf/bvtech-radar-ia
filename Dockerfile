FROM python:3.12-slim
WORKDIR /opt/radar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /data
ENV PYTHONUNBUFFERED=1
