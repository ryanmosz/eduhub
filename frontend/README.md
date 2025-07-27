# EduHub Admin Frontend

React-based admin panel for the EduHub educational content management system.

## Overview

This is the Phase 9 implementation - a modern React SPA that provides a user-friendly interface for all the APIs developed in Phases 1-8 of the EduHub project.

## Features

### Implemented
- ✅ **Authentication** (Phase 3) - Auth0 integration with JWT
- ✅ **Dashboard** - Overview of all system metrics
- ✅ **Schedule Import** (Phase 4) - CSV upload wizard with preview
- 🚧 **Media Embeds** (Phase 5) - oEmbed preview interface (UI ready, needs API integration)
- 🚧 **Open Data Explorer** (Phase 6) - Browse public content (placeholder)
- 🚧 **Workflow Templates** (Phase 7) - Manage workflows (placeholder)
- 🚧 **Real-time Alerts** (Phase 8) - WebSocket notifications (placeholder)

## Tech Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS v4
- **UI Components**: Custom components inspired by ShadCN UI
- **Authentication**: Auth0 React SDK
- **Routing**: React Router v7
- **State Management**: React Query (TanStack Query)
- **Icons**: Lucide React

## Getting Started

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Auth0 credentials if needed
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

### Docker Development (Recommended)

1. **Using Docker Compose** (includes backend):
   ```bash
   # From the root directory
   docker-compose -f docker-compose.frontend.yml up
   ```
   
   This will start:
   - Frontend on http://localhost:5173
   - Backend on http://localhost:8000
   - Redis on localhost:6379

2. **Frontend only**:
   ```bash
   cd frontend
   docker build -t eduhub-frontend:dev .
   docker run -p 5173:5173 -v $(pwd)/src:/app/src eduhub-frontend:dev
   ```

### Production Build

1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Docker production build**:
   ```bash
   npm run docker:build
   npm run docker:run
   ```
   
   The production image uses nginx and runs on port 80.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/         # Auth0 provider wrapper
│   │   ├── layout/       # Main layout with navigation
│   │   └── ui/           # Reusable UI components
│   ├── pages/            # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── ScheduleImport.tsx
│   │   └── ... (other feature pages)
│   ├── lib/              # Utilities
│   └── App.tsx           # Main app with routing
├── .env.example          # Environment template
└── vite.config.ts        # Vite configuration
```

## Authentication Flow

1. User clicks "Sign in with Auth0"
2. Redirected to Auth0 login page
3. After successful login, redirected back to `/callback`
4. Token stored in localStorage
5. User redirected to dashboard

## API Integration

The frontend is designed to work with the FastAPI backend running on `http://localhost:8000`. Currently implemented:

- **Auth endpoints**: `/auth/login`, `/auth/user`
- **Schedule Import**: `/import/schedule`
- **oEmbed**: `/embed/*`
- **Open Data**: `/data/*` (Phase 6 - recovered)
- **Workflows**: `/workflows/*` (Phase 7 - recovered)
- **Alerts**: `/alerts/*` (Phase 8 - in development)

## Next Steps

1. Add MSW for API mocking
2. Implement remaining feature pages
3. Add real API integration for all endpoints
4. Set up CI/CD with Vercel
5. Add comprehensive testing

## Development Notes

- The app uses Tailwind CSS v4 with the new Vite plugin
- Components follow a consistent pattern with TypeScript interfaces
- Navigation automatically shows which features are from which phase
- Responsive design with mobile-friendly sidebar