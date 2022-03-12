FROM python:3.10-alpine

RUN pip install -r requirements.txt

EXPOSE 8001

RUN mkdir -p /app/static
COPY static /app/static
COPY *.py /app/
WORKDIR /app
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
