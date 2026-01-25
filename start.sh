#!/bin/bash

# Ensure the scripts directory exists
mkdir -p /scripts

# Function to ALWAYS clone a fresh copy
ensure_repo() {
    REPO_URL=$1
    DIR_NAME=$2
    TARGET_PATH="/scripts/$DIR_NAME"

    # FORCE WIPE: If the folder exists, delete it so we can clone fresh
    if [ -d "$TARGET_PATH" ]; then
        echo "[INIT] Wiping old $DIR_NAME to force update..."
        rm -rf "$TARGET_PATH"
    fi

    # Clone fresh
    echo "[INIT] Cloning $DIR_NAME..."
    git clone "$REPO_URL" "$TARGET_PATH"
}

ensure_repo "https://github.com/abduznik/AI-Gen-Description" "AI-Gen-Description"
ensure_repo "https://github.com/abduznik/AI-Gen-Issue" "AI-Gen-Issue"
ensure_repo "https://github.com/abduznik/AI-Gen-Profile" "AI-Gen-Profile"
ensure_repo "https://github.com/abduznik/AI-Gen-Topics" "AI-Gen-Topics"

echo "[INIT] Starting Server..."
exec uvicorn app.server:app --host 0.0.0.0 --port 8090
