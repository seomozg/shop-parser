#!/bin/bash

# Simple Docker installation for Ubuntu/Debian

set -e

echo "🐳 Installing Docker using snap (simplest method)..."

# Install Docker via snap
sudo snap install docker

# Enable Docker service
sudo snap start docker

# Add user to docker group
sudo groupadd docker 2>/dev/null || true
sudo usermod -aG docker $USER

echo "✅ Docker installed via snap!"
echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in, or run: newgrp docker"
echo "2. Test Docker: docker run hello-world"
echo "3. Configure your .env file with DeepSeek API key"
echo "4. Run: docker-compose up -d"
