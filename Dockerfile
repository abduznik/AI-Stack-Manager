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

# 5. Install GitHub CLI (gh)
RUN mkdir -p -m 755 /etc/apt/keyrings \
    && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]