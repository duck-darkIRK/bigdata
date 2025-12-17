FROM python:3.10-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Cài các công cụ cần thiết + Java
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    openjdk-11-jdk-headless \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME cho PySpark
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH:$PATH

# Copy source code và requirements
COPY requirements.txt .
COPY data .
COPY src .

# Cài Python packages
RUN pip install --upgrade pip && \
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

CMD ["bash"]
