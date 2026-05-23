FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    fontconfig \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-noto-core \
    fonts-noto-color-emoji \
    && locale-gen en_US.UTF-8 ru_RU.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
