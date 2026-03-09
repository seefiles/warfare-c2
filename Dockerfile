FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libssl-dev \
    libffi-dev \
    libpcap-dev \
    libusb-1.0-0-dev \
    portaudio19-dev \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD gunicorn warfare_c2:app --bind 0.0.0.0:$PORT
