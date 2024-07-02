FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY run.sh /app/run.sh

RUN chmod +x /app/run.sh

COPY worker /app/worker

CMD ["/app/run.sh"]