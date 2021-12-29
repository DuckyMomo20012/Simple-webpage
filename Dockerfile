# syntax=docker/dockerfile:1
FROM ubuntu:latest
WORKDIR .
RUN apt-get update && apt-get install -y curl python3 net-tools iputils-ping
COPY . /app
# CMD ["python3", "-u", "server.py"]
