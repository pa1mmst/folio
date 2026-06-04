#!/bin/bash
# deploy.sh — деплой folio с автоматическим версионированием

set -e

echo "=== Step 1: semantic-release version ==="
semantic-release version --no-push

echo "=== Step 2: deploy ==="
# Render/Heroku запустят Procfile автоматически после git push
git push --follow-tags origin master

echo "=== Done ==="
echo "Version: $(semantic-release version --print)"
