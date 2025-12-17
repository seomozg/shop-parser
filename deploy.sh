#!/bin/bash

# Shop Parser Deployment Script

set -e

echo "🚀 Starting Shop Parser deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    if [ -f "install-docker.sh" ]; then
        echo "🔧 Running Docker installation script..."
        bash install-docker.sh
    else
        echo "Please install Docker first or run the installation script."
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

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Build and start containers
echo "🏗️  Building and starting containers..."
docker-compose up -d --build

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

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
