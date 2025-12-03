#!/bin/bash

# Complete setup script for cluster benchmarking system
# This script generates tickets, creates clusters, and ingests into Neo4j

set -e  # Exit on error

echo "=========================================="
echo "CLUSTER BENCHMARKING SYSTEM SETUP"
echo "=========================================="
echo ""

# Check if Neo4j is running
echo "Step 1: Checking Neo4j connection..."
if ! curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo "⚠️  Neo4j not running. Starting Docker container..."
    ./start_docker.sh
    echo "Waiting for Neo4j to be ready..."
    sleep 10
else
    echo "✓ Neo4j is running"
fi
echo ""

# Generate tickets
echo "Step 2: Generating 5000 support tickets..."
python3 backend/generate_support_tickets.py --num-tickets 5000
echo ""

# Create clusters
echo "Step 3: Creating clustering strategies..."
python3 backend/cluster_tickets.py --input ./mnt/data/support_tickets.jsonl
echo ""

# Ingest into Neo4j
echo "Step 4: Ingesting into Neo4j..."
python3 backend/ingest_clustered_tickets.py
echo ""

echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start backend API:"
echo "   cd backend && uvicorn app_main:app --host 127.0.0.1 --port 8001 --reload"
echo ""
echo "2. Test benchmark API:"
echo "   curl -X POST http://127.0.0.1:8001/benchmark/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"login issue\", \"top_k\": 10}'"
echo ""
echo "3. View cluster stats:"
echo "   curl http://127.0.0.1:8001/benchmark/stats"
echo ""

