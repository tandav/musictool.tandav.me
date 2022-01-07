FROM python:3.10-alpine

RUN pip install fastapi uvicorn aiofiles musictool

EXPOSE 8001

RUN mkdir -p /app/musictool
RUN mkdir -p /app/static
COPY static /app/static
COPY *.py /app/
WORKDIR /app
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
