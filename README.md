# AI Stack Manager

A centralized Web UI to manage your AI-powered GitHub tools. This dashboard wraps your existing PowerShell scripts into a Dockerized environment, allowing you to run them from any browser on your network.

## Quick Start (Homelab)

1. Create a `docker-compose.yml` file on your server with the following content:

   ```yaml
   version: '3.8'

   services:
     ai-manager:
       image: ghcr.io/abduznik/ai-stack-manager:latest
       container_name: ai-stack-manager
       ports:
         - "8090:8090"
       volumes:
         # Persist the cloned scripts inside the container
         - ai_scripts_data:/scripts
       environment:
         - GEMINI_API_KEY=your_key_here
         - GH_TOKEN=your_token_here
       restart: unless-stopped

   volumes:
     ai_scripts_data:
   ```

2. Run the container:
   ```bash
   docker compose up -d
   ```
   *Note: On first run, the container will automatically clone the necessary AI repositories into its internal volume.*

3. Access: Navigate to `http://your-server-ip:8090`.

## Authentication Setup

To use these tools, you need to provide API keys in the Auth Settings section of the dashboard (or via environment variables above).

### 1. Google Gemini API Key
Used to power the AI logic for descriptions, issues, and categorization.
- Get it here: https://aistudio.google.com/app/apikey

### 2. GitHub Fine-Grained Token
We recommend using a Fine-Grained Token for better security than a classic PAT.
- Get it here: https://github.com/settings/tokens?type=beta

**Required Permissions:**
- Resource Owner: Your username
- Repository Access: "All repositories" (or specific ones you want to manage)
- Permissions:
  - `Contents`: Read & Write (Needed for Profile README updates)
  - `Issues`: Read & Write (Needed for Issue Generator)
  - `Metadata`: Read & Write (Needed for Descriptions & Topics)
  - `Pull requests`: Read & Write (Needed for Profile PR workflow)

## How it Works
This project manages the scripts in a Docker Volume. When you execute a tool:
1. The backend spawns a PowerShell Core (`pwsh`) process inside the container.
2. It executes the script from the cloned repositories.
3. The output is streamed back to the browser.
