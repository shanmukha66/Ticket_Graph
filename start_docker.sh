#!/bin/bash

# Script to start Neo4j in Docker for the Graph RAG project

echo "=========================================="
echo "Starting Neo4j with Docker Compose"
echo "=========================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        exit 1
    fi
    # Try using docker compose (newer syntax)
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

# Start Neo4j in background
echo "Starting Neo4j container..."
$DOCKER_COMPOSE_CMD up -d neo4j

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
sleep 5

# Check if Neo4j is running
if docker ps | grep -q graph-rag-neo4j; then
    echo "✓ Neo4j is running!"
    echo ""
    echo "Neo4j Browser: http://localhost:7474"
    echo "Bolt URI: bolt://localhost:7687"
    echo "Username: neo4j"
    echo "Password: password123"
    echo ""
    echo "To stop Neo4j, run: docker-compose down"
    echo "To view logs, run: docker-compose logs -f neo4j"
else
    echo "✗ Failed to start Neo4j. Check logs with: docker-compose logs neo4j"
    exit 1
fi

