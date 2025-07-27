# Deployment Checklist

## Pre-Deployment
- [x] WebSocket URLs use dynamic configuration
- [x] Environment variables documented
- [x] Deployment scripts created
- [x] Production configs ready

## Frontend (Vercel)
- [ ] Run deployment script: `./deploy.sh`
- [ ] Set environment variables in Vercel:
  - `VITE_API_URL` = https://your-eduhub-api.onrender.com
  - `VITE_AUTH0_DOMAIN` = dev-1fx6yhxxi543ipno.us.auth0.com  
  - `VITE_AUTH0_CLIENT_ID` = s05QngyZXEI3XNdirmJu0CscW1hNgaRD
  - `VITE_AUTH0_REDIRECT_URI` = https://your-app.vercel.app
  - `VITE_AUTH0_AUDIENCE` = https://eduhub-api.example.com
- [ ] Note Vercel URL for backend CORS

## Backend (Render)
- [ ] Push to GitHub/GitLab
- [ ] Create new Web Service on Render
- [ ] Set build command: `pip install -e ".[dev]"`
- [ ] Set start command: `uvicorn src.eduhub.main:app --host 0.0.0.0 --port $PORT`
- [ ] Configure environment variables:
  - Core settings (SECRET_KEY, JWT_SECRET_KEY)
  - Auth0 settings
  - CORS_ORIGINS (include Vercel URL)
  - Database and Redis URLs (auto-configured)
- [ ] Create PostgreSQL database
- [ ] Create Redis instance
- [ ] Deploy and wait for build

## Auth0 Configuration
- [ ] Update Allowed Callback URLs:
  - https://your-app.vercel.app/callback
  - http://localhost:5173/callback
- [ ] Update Allowed Logout URLs:
  - https://your-app.vercel.app
  - http://localhost:5173
- [ ] Update Allowed Web Origins:
  - https://your-app.vercel.app
  - http://localhost:5173

## Post-Deployment Testing
- [ ] Frontend loads without errors
- [ ] Backend health check passes
- [ ] API docs accessible at /docs
- [ ] OAuth2 login/logout works
- [ ] WebSocket connects (check Real-time Alerts)
- [ ] Test each feature:
  - [ ] Course listing
  - [ ] Schedule import (CSV)
  - [ ] Rich media embeds
  - [ ] Workflow templates
  - [ ] Real-time alerts
  - [ ] Open data API

## Monitoring
- [ ] Check Vercel logs
- [ ] Check Render logs
- [ ] Monitor WebSocket connections
- [ ] Verify no CORS errors

## Final Steps
- [ ] Update README with production URLs
- [ ] Document any issues encountered
- [ ] Create monitoring alerts