# AI Stack Manager

A centralized Web UI to manage your AI-powered GitHub tools. This dashboard wraps your existing PowerShell scripts into a Dockerized environment, allowing you to run them from any browser on your network.

## Quick Start (Homelab)

1. **Clone your script repositories** into a folder on your server:
   - `AI-Gen-Description`
   - `AI-Gen-Issue`
   - `AI-Gen-Profile`
   - `AI-Gen-Topics`

2. **Download `homelab-compose.yml`** and place it in the same parent directory.

3. **Deploy:**
   ```bash
   docker compose -f homelab-compose.yml up -d
   ```

4. **Access:** Navigate to `http://your-server-ip:8090`.

---

## Authentication Setup

To use these tools, you need to provide API keys in the **Auth Settings** section of the dashboard.

### 1. Google Gemini API Key
Used to power the AI logic for descriptions, issues, and categorization.
- **Get it here:** [Google AI Studio - API Keys](https://aistudio.google.com/app/apikey)

### 2. GitHub Fine-Grained Token
We recommend using a **Fine-Grained Token** for better security than a classic PAT.
- **Get it here:** [GitHub - Fine-grained tokens](https://github.com/settings/tokens?type=beta)

**Required Permissions:**
- **Resource Owner:** Your username
- **Repository Access:** "All repositories" (or specific ones you want to manage)
- **Permissions:**
  - `Contents`: **Read & Write** (Needed for Profile README updates)
  - `Issues`: **Read & Write** (Needed for Issue Generator)
  - `Metadata`: **Read & Write** (Needed for Descriptions & Topics)
  - `Pull requests`: **Read & Write** (Needed for Profile PR workflow)

---

## How it Works
This project mounts your local `.ps1` files as volumes. When you execute a tool:
1. The backend (FastAPI) spawns a PowerShell Core (`pwsh`) process inside the container.
2. It dot-sources your script and calls the corresponding function.
3. The output is streamed back to the browser via WebSockets in real-time.

**Updating scripts:** Simply update the `.ps1` files on your host machine. The container sees the changes immediately!
