FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV GH_PROMPT_DISABLED=1

# 1. Install Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 3. Install Google Gemini CLI
RUN npm install -g @google/gemini-cli

# 4. Install PowerShell (pwsh)
RUN wget -q "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell

RUN apt-get update && apt-get install -y gh

# 5. Compatibility Wrapper for Windows Scripts (cmd /c)
# Improved version: handles /c safely and executes the rest as a shell command
RUN printf '#!/bin/bash
if [ "$1" == "/c" ]; then shift; fi
exec bash -c "$*"' > /usr/local/bin/cmd \
    && chmod +x /usr/local/bin/cmd

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]
