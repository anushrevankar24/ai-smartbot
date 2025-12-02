#!/bin/bash

# ERP AI Assistant Setup Script

echo "Setting up ERP AI Assistant..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: Virtual environment not detected."
    echo "Please activate your .venv first:"
    echo "  source .venv/bin/activate"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with the following variables:"
    echo ""
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo "SUPABASE_URL=https://your-project.supabase.co"
    echo "SUPABASE_KEY=your_supabase_anon_or_service_key"
    echo "COMPANY_ID=bc90d453-0c64-4f6f-8bbe-dca32aba40d1"
    echo "DIVISION_ID=b38bfb72-3dd7-4aa5-b970-71b919d5ded4"
    echo ""
    exit 1
fi

echo "SUCCESS: Setup complete!"
echo ""
echo "To run the assistant:"
echo "  Terminal 1: ./start-backend.sh"
echo "  Terminal 2: ./start-frontend.sh"
echo ""
echo "Or see ./start.sh for instructions"
echo ""

