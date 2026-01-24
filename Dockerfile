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
# We use Python for the wrapper to handle argument quoting reliably
RUN echo '#!/usr/bin/env python3' > /usr/local/bin/cmd && \
    echo 'import sys, subprocess' >> /usr/local/bin/cmd && \
    echo 'args = sys.argv[1:]' >> /usr/local/bin/cmd && \
    echo 'if args and args[0] == "/c": args.pop(0)' >> /usr/local/bin/cmd && \
    echo '# Join args back into a single string for shell execution, as PowerShell expects cmd to parse the string' >> /usr/local/bin/cmd && \
    echo '# However, simply joining by space is dangerous if quotes were stripped. ' >> /usr/local/bin/cmd && \
    echo '# Since pwsh passes the command as a single string to /c, args[0] is likely the whole command.' >> /usr/local/bin/cmd && \
    echo 'cmd_str = " ".join(args)' >> /usr/local/bin/cmd && \
    echo 'subprocess.run(cmd_str, shell=True, check=False)' >> /usr/local/bin/cmd && \
    chmod +x /usr/local/bin/cmd

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]
