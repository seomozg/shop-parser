#!/bin/bash

# Install Docker on Ubuntu/Debian without snap

set -e

echo "🐳 Installing Docker using apt (Ubuntu/Debian method)..."

# Remove any existing docker packages
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Update package index
sudo apt update

# Install required packages
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
sudo apt update

# Install Docker Engine
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo groupadd docker 2>/dev/null || true
sudo usermod -aG docker $USER

echo "✅ Docker installed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in to apply docker group changes"
echo "2. Or run: newgrp docker"
echo "3. Test: docker run hello-world"
echo "4. Configure your .env file"
echo "5. Run: docker-compose up -d"
