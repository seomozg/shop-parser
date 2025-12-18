#!/bin/bash

# Shop Parser Deployment Script

set -e

echo "🚀 Starting Shop Parser deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    if command -v snap &> /dev/null; then
        echo "🔧 Installing Docker via snap (recommended)..."
        sudo snap install docker
        sudo snap start docker
        sudo groupadd docker 2>/dev/null || true
        sudo usermod -aG docker $USER
        echo "✅ Docker installed! Please log out and log back in, or run: newgrp docker"
    elif [ -f "install-docker.sh" ]; then
        echo "🔧 Running Docker installation script..."
        bash install-docker.sh
    else
        echo "Please install Docker manually or use snap."
        echo "Quick install: sudo snap install docker && sudo snap start docker"
        exit 1
    fi
fi

# Check if docker-compose is available (either standalone or plugin)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ docker-compose is not available. Installing..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y docker-compose-plugin
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo "Please install docker-compose manually."
        exit 1
    fi
fi

# Create output directory if it doesn't exist
mkdir -p output/images

# Copy .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env .env.backup 2>/dev/null || true
    echo "⚠️  .env file not found. Please create one with your DeepSeek API key."
    echo "   Copy .env template and configure DEEPSEEK_API_KEY"
    exit 1
fi

# Install Playwright browsers (local development)
echo "🎭 Installing Playwright browsers..."
if command -v playwright &> /dev/null; then
    playwright install --yes || echo "⚠️  Local Playwright browser installation failed, but continuing..."
else
    echo "ℹ️  Playwright not available locally - browsers will be installed in Docker container"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE_CMD down || true

# Build and start containers
echo "🏗️  Building and starting containers..."
$DOCKER_COMPOSE_CMD up -d --build

# Wait for service to be ready and ensure browsers are installed
echo "⏳ Waiting for service to be ready..."
sleep 15

# Check if container is running and install browsers if needed
if $DOCKER_COMPOSE_CMD ps | grep -q "shop-parser"; then
    echo "🔧 Ensuring Playwright browsers are installed in container..."
    $DOCKER_COMPOSE_CMD exec -T shop-parser playwright install chromium --force || echo "⚠️  Browser installation in container failed, but continuing..."
fi

# Check if service is running
if curl -f http://localhost:5000 &>/dev/null; then
    echo "✅ Deployment successful!"
    echo "🌐 Web interface available at: http://localhost:5000"
    echo "📊 Output files will be saved to: ./output/"
else
    echo "❌ Service failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop service: docker-compose down"
echo "  Restart: docker-compose restart"
