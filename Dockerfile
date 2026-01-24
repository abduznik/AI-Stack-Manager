FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Dependencies
# Removed software-properties-common to fix build error
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js (for @google/gemini-cli)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 3. Install Google Gemini CLI
RUN npm install -g @google/gemini-cli

# 4. Install PowerShell (pwsh)
# Update to Debian 12 (Bookworm) repo
RUN wget -q "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell

RUN apt-get update && apt-get install -y gh

# 5.5 Compatibility Wrapper for Windows Scripts (cmd /c)
RUN echo '#!/bin/bash\nif [ "$1" = "/c" ]; then shift; fi\neval "$@"' > /usr/local/bin/cmd \
    && chmod +x /usr/local/bin/cmd

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]