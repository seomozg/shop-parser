#!/bin/bash

# Install Docker and Docker Compose on Ubuntu/Debian

set -e

echo "🐳 Installing Docker and Docker Compose..."

# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add current user to docker group (optional)
sudo usermod -aG docker $USER

echo "✅ Docker and Docker Compose installed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in to apply docker group changes"
echo "2. Or run: newgrp docker"
echo "3. Configure your .env file with DeepSeek API key"
echo "4. Run: docker-compose up -d"
