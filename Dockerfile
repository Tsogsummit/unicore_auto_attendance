FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Ulaanbaatar

WORKDIR /app

# Install tzdata for timezone support
RUN apt-get update && apt-get install -y tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Ulaanbaatar /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

CMD ["python3", "main.py", "daemon"]
