FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV GH_PROMPT_DISABLED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# 1. Install Dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    git \
    wget \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate locales
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

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

# 5. Install Python Deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy App Code
COPY . .

# 7. Verify Server Code
RUN python -m py_compile app/server.py

# 8. Optimized Compatibility Wrapper for Windows Scripts (cmd /c)
# Improved logic to handle both single-string and multi-argument calls
RUN echo '#!/bin/bash' > /usr/local/bin/cmd && \
    echo 'if [ "$1" = "/c" ]; then shift; fi' >> /usr/local/bin/cmd && \
    echo 'if [ $# -eq 1 ]; then exec /bin/bash -c "$1"; else exec "$@"; fi' >> /usr/local/bin/cmd && \
    chmod +x /usr/local/bin/cmd

RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]