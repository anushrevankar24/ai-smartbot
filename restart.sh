#!/bin/bash

# ERP AI Assistant - Restart Script

echo "Restarting ERP AI Assistant..."
echo ""

# Run stop script
./stop.sh

echo ""
echo "Waiting 2 seconds..."
sleep 2
echo ""

# Run start script
./start.sh

