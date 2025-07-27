# EduHub Development Setup

## Architecture Overview

The EduHub project consists of two main components that mirror the production deployment:

1. **Backend (FastAPI + Plone)** → Deploys to Render
2. **Frontend (React SPA)** → Deploys to Vercel

## Local Development Options

### Option 1: Full Stack with Docker (Recommended)

This runs both frontend and backend in Docker containers:

```bash
# 1. Start the backend services (from root directory)
docker-compose up -d

# This starts:
# - FastAPI backend on http://localhost:8000
# - Plone CMS on http://localhost:8080
# - PostgreSQL on localhost:5432
# - Redis on localhost:6379

# 2. Start the frontend (in a separate terminal)
cd frontend
docker-compose up

# Frontend runs on http://localhost:5173
```

### Option 2: Backend in Docker, Frontend Native

This is closer to how you'll work in production:

```bash
# 1. Start backend services
docker-compose up -d

# 2. Run frontend natively (faster hot reload)
cd frontend
npm install
npm run dev
```

### Option 3: Minimal Setup (Frontend Only)

For pure frontend development with mocked APIs:

```bash
cd frontend
npm install
npm run dev

# TODO: Add MSW for API mocking
```

## Environment Variables

### Backend (.env in root)
```env
AUTH0_DOMAIN=dev-1fx6yhxxi543ipno.us.auth0.com
AUTH0_CLIENT_ID=s05QngyZXEI3XNdirmJu0CscW1hNgaRD
AUTH0_CLIENT_SECRET=your-secret-here
AUTH0_AUDIENCE=http://localhost:8000
DATABASE_URL=postgresql://eduhub:eduhub@localhost:5432/eduhub
REDIS_URL=redis://localhost:6379/0
```

### Frontend (frontend/.env)
```env
VITE_AUTH0_DOMAIN=dev-1fx6yhxxi543ipno.us.auth0.com
VITE_AUTH0_CLIENT_ID=s05QngyZXEI3XNdirmJu0CscW1hNgaRD
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/callback
VITE_AUTH0_AUDIENCE=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

## Common Commands

### Backend
```bash
# Start all backend services
docker-compose up -d

# View logs
docker-compose logs -f api

# Run tests
docker-compose exec api pytest

# Access Plone
open http://localhost:8080/Plone

# Stop all services
docker-compose down
```

### Frontend
```bash
# Development
cd frontend
npm run dev

# With Docker
cd frontend
docker-compose up

# Build for production
npm run build

# Preview production build
npm run preview
```

## Deployment

### Frontend → Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel

# Set environment variables in Vercel dashboard
```

### Backend → Render
- Connect GitHub repo to Render
- Set environment variables
- Deploy automatically on push

## Troubleshooting

### Port already in use
```bash
# Find and kill process on port
lsof -ti:5173 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
```

### Docker issues
```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Frontend can't connect to backend
- Check CORS settings in backend
- Ensure `VITE_API_BASE_URL` is correct
- Try `http://host.docker.internal:8000` if running both in Docker