# Use an official Python runtime as a parent image (Debian 12 Bookworm)
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /MoneyPrinterTurbo

# 设置/MoneyPrinterTurbo目录权限为777
RUN chmod 777 /MoneyPrinterTurbo

ENV PYTHONPATH="/MoneyPrinterTurbo"
ENV TZ="Asia/Kolkata"

# Install system dependencies (git, ffmpeg, tzdata)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ffmpeg tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Kolkata /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the codebase into the image
COPY . .
RUN chmod +x start.sh

# Expose the ports the app runs on (FastAPI on 8080, Streamlit on 8501)
EXPOSE 8080 8501

# Run production startup script (FastAPI /health + Telegram VIP Bot)
CMD ["/bin/bash", "./start.sh"]

# 1. Build the Docker image using the following command
# docker build -t moneyprinterturbo .

# 2. Run the Docker container using the following command
## For Linux or MacOS:
# docker run -v $(pwd)/config.toml:/MoneyPrinterTurbo/config.toml -v $(pwd)/storage:/MoneyPrinterTurbo/storage -p 127.0.0.1:8501:8501 moneyprinterturbo
## For Windows:
# docker run -v ${PWD}/config.toml:/MoneyPrinterTurbo/config.toml -v ${PWD}/storage:/MoneyPrinterTurbo/storage -p 127.0.0.1:8501:8501 moneyprinterturbo
