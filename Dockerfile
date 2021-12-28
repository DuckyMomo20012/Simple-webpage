# syntax=docker/dockerfile:1
FROM python:latest
WORKDIR .
COPY . .
# CMD ["python3", "-u", "server.py"]
