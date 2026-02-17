#!/usr/bin/env bash
# Build script for Render deployment

set -e  # Exit on error

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📄 Checking for PDF documents..."
if [ ! -f "data/raw/The_Constitution_of_Kenya_2010.pdf" ]; then
    echo "❌ ERROR: Constitution PDF not found in data/raw/"
    exit 1
fi

if [ ! -f "data/raw/THE FINANCE BILL 2025 (Compressed Copy)_2.pdf" ]; then
    echo "❌ ERROR: Finance Bill PDF not found in data/raw/"
    exit 1
fi

echo "✅ PDF documents found"

# Check if vector store already exists
if [ -d "vectorstores/haki_sovereign" ] && [ "$(ls -A vectorstores/haki_sovereign)" ]; then
    echo "✅ Vector store already exists, skipping rebuild"
else
    echo "🔨 Building vector store (this may take 5-10 minutes)..."
    echo "⚠️  This requires OPENAI_API_KEY to be set in environment"
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ ERROR: OPENAI_API_KEY environment variable not set"
        echo "Please set it in Render dashboard under Environment Variables"
        exit 1
    fi
    
    # Build vector store using Python
    python -c "
from src.haki_engine import create_engine
print('Building vector store...')
engine = create_engine(force_rebuild=True)
print('✅ Vector store built successfully')
"
fi

echo "✅ Build completed successfully!"
