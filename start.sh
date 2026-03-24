#!/bin/bash

echo "==================================="
echo "  Coursework Docker Launcher"
echo "==================================="
echo ""

# Перевірка чи існує .env файл
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "Please copy .env.example to .env and fill in your credentials"
    echo ""
    echo "Run: cp .env.example .env"
    exit 1
fi

if [ ! -f "backend/.env" ]; then
    echo "[ERROR] backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and fill in your credentials"
    echo ""
    echo "Run: cp backend/.env.example backend/.env"
    exit 1
fi

echo "[INFO] Environment files found!"
echo ""
echo "[INFO] Starting Docker containers..."
echo ""

docker-compose up --build
