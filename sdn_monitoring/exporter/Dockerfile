FROM python:3.12

WORKDIR /app

COPY ryu_exporter.py .

RUN pip install prometheus_client requests

CMD ["python","ryu_exporter.py"]