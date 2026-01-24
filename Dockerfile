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

# 2. Install Node.js (Still needed for other potential tools, but not for gemini anymore)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 3. Install PowerShell (pwsh)
RUN wget -q "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y powershell

RUN apt-get update && apt-get install -y gh

# 4. Install Python Deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy App Code
COPY . .

# 6. VERIFY SERVER CODE (Fail build if broken)
RUN python -m py_compile app/server.py

# 7. Install Custom Gemini Wrapper (Replaces npm gemini-cli)
# We rename our python script to /usr/local/bin/gemini and make it executable
RUN cp fake_gemini.py /usr/local/bin/gemini && \
    chmod +x /usr/local/bin/gemini

# 8. Compatibility Wrapper for Windows Scripts (cmd /c)
RUN echo '#!/usr/bin/env python3' > /usr/local/bin/cmd && \
    echo 'import sys, subprocess' >> /usr/local/bin/cmd && \
    echo 'args = sys.argv[1:]' >> /usr/local/bin/cmd && \
    echo 'if args and args[0] == "/c": args.pop(0)' >> /usr/local/bin/cmd && \
    echo 'cmd_str = " ".join(args)' >> /usr/local/bin/cmd && \
    echo 'subprocess.run(cmd_str, shell=True, check=False)' >> /usr/local/bin/cmd && \
    chmod +x /usr/local/bin/cmd

RUN chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]