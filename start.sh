#!/bin/bash

# Ensure the scripts directory exists
mkdir -p /scripts

# Function to clone or update a repo
ensure_repo() {
    REPO_URL=$1
    DIR_NAME=$2
    TARGET_PATH="/scripts/$DIR_NAME"

    if [ ! -d "$TARGET_PATH" ]; then
        echo "[INIT] Cloning $DIR_NAME..."
        git clone "$REPO_URL" "$TARGET_PATH"
    else
        echo "[INIT] $DIR_NAME already exists. Creating update script..."
        # We don't auto-pull on restart to avoid overwriting local changes, 
        # but we ensure the directory is there.
    fi
}

ensure_repo "https://github.com/abduznik/AI-Gen-Description" "AI-Gen-Description"
ensure_repo "https://github.com/abduznik/AI-Gen-Issue" "AI-Gen-Issue"
ensure_repo "https://github.com/abduznik/AI-Gen-Profile" "AI-Gen-Profile"
ensure_repo "https://github.com/abduznik/AI-Gen-Topics" "AI-Gen-Topics"

echo "[INIT] Starting Server..."
exec uvicorn app.server:app --host 0.0.0.0 --port 8090
