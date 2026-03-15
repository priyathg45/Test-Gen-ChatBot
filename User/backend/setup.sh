#!/bin/bash

# Quick Start Guide for Aluminum Products Chatbot
# This script helps you set up and run the chatbot quickly

set -e

echo "=========================================="
echo "Aluminum Products Chatbot - Quick Start"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || true

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "You can now run the chatbot in two ways:"
echo ""
echo "1. Interactive CLI (Recommended for testing):"
echo "   python -m src.main"
echo ""
echo "2. REST API Server:"
echo "   python src/api/app.py"
echo "   Then make requests to http://localhost:5000"
echo ""
echo "For more information, see README.md"
