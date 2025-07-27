#!/bin/bash

# EduHub Deployment Script
# This script helps deploy the frontend to Vercel and provides instructions for Render

echo "🚀 EduHub Deployment Script"
echo "=========================="

# Check if we're in the project root
if [ ! -f "pyproject.toml" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to deploy frontend
deploy_frontend() {
    echo "\n📦 Deploying Frontend to Vercel..."
    cd frontend
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        echo "❌ Vercel CLI not found. Installing..."
        npm i -g vercel
    fi
    
    # Deploy to Vercel
    echo "🔄 Starting Vercel deployment..."
    vercel --prod
    
    cd ..
    echo "✅ Frontend deployment initiated!"
}

# Function to show backend instructions
show_backend_instructions() {
    echo "\n📋 Backend Deployment Instructions for Render:"
    echo "============================================="
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click 'New +' > 'Web Service'"
    echo "3. Connect your Git repository"
    echo "4. Use these settings:"
    echo "   - Name: eduhub-api"
    echo "   - Runtime: Python"
    echo "   - Build Command: pip install -e \".[dev]\""
    echo "   - Start Command: uvicorn src.eduhub.main:app --host 0.0.0.0 --port \$PORT"
    echo ""
    echo "5. Add environment variables from DEPLOYMENT.md"
    echo ""
    echo "📄 See DEPLOYMENT.md for complete instructions"
}

# Main menu
echo "\nWhat would you like to deploy?"
echo "1. Frontend to Vercel"
echo "2. Show Backend deployment instructions"
echo "3. Both"
echo "4. Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        deploy_frontend
        ;;
    2)
        show_backend_instructions
        ;;
    3)
        deploy_frontend
        show_backend_instructions
        ;;
    4)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo "\n🎉 Deployment process complete!"
echo "📝 Don't forget to:"
echo "   - Update environment variables in both Vercel and Render"
echo "   - Update Auth0 callback URLs"
echo "   - Test all features after deployment"