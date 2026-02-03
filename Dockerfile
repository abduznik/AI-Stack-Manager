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

# 2. Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg  \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg  \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null  \
    && apt-get update  \
    && apt-get install gh -y

# 3. Install Python Dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy App Code
COPY . .

# 5. [LEGACY COMPAT] Create 'gemini' shim
# Points to the new core logic if any old scripts remain
RUN echo '#!/bin/bash' > /usr/local/bin/gemini && \
    echo 'python3 /app/app/git_alchemist/src/core.py "$@"' >> /usr/local/bin/gemini && \
    chmod +x /usr/local/bin/gemini

RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]
