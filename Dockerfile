FROM python:3.10-alpine

EXPOSE 8001

RUN mkdir -p /app/static
COPY static /app/static
COPY *.py /app/
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
