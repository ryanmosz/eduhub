# Deployment Guide

This guide covers deploying the EduHub application with:
- Frontend on Vercel
- Backend on Render
- Mock Plone CMS (for demo)

## Prerequisites

- Vercel account and CLI installed (`npm i -g vercel`)
- Render account
- Git repository pushed to GitHub/GitLab

## Frontend Deployment (Vercel)

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy Frontend
```bash
cd frontend
vercel
```

### 3. Configure Environment Variables in Vercel Dashboard

Go to your project settings in Vercel and add:

```
VITE_API_URL=https://your-eduhub-api.onrender.com
VITE_AUTH0_DOMAIN=dev-1fx6yhxxi543ipno.us.auth0.com
VITE_AUTH0_CLIENT_ID=s05QngyZXEI3XNdirmJu0CscW1hNgaRD
VITE_AUTH0_REDIRECT_URI=https://your-app.vercel.app
VITE_AUTH0_AUDIENCE=https://eduhub-api.example.com
```

### 4. Configure Production Domain

In Vercel dashboard:
1. Go to Settings > Domains
2. Add your custom domain or use the generated `.vercel.app` domain

## Backend Deployment (Render)

### 1. Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" > "Web Service"
3. Connect your GitHub/GitLab repository
4. Configure:
   - Name: `eduhub-api`
   - Runtime: Python
   - Build Command: `pip install -e ".[dev]"`
   - Start Command: `uvicorn src.eduhub.main:app --host 0.0.0.0 --port $PORT`

### 2. Configure Environment Variables

Add these in Render dashboard:

```bash
# Core Settings
SECRET_KEY=<generate-random-key>
JWT_SECRET_KEY=<generate-random-key>
ENVIRONMENT=production
LOG_LEVEL=INFO
PORT=8000

# Database (auto-configured by Render)
DATABASE_URL=<auto-filled-by-render>

# Redis (if using Render Redis)
REDIS_URL=<auto-filled-by-render>

# Mock Plone Settings (for demo)
PLONE_URL=http://localhost:8080/Plone
PLONE_USERNAME=admin
PLONE_PASSWORD=admin

# Auth0
AUTH0_DOMAIN=dev-1fx6yhxxi543ipno.us.auth0.com
AUTH0_API_AUDIENCE=https://eduhub-api.example.com
AUTH0_ALGORITHMS=RS256
AUTH0_ISSUER=https://dev-1fx6yhxxi543ipno.us.auth0.com/

# CORS (update with your Vercel URL)
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173

# WebSocket URL (for alerts)
WEBSOCKET_URL=wss://your-eduhub-api.onrender.com
```

### 3. Create Database and Redis

1. In Render dashboard, create:
   - PostgreSQL database (starter plan)
   - Redis instance (starter plan)
2. Connect them to your web service

### 4. Deploy

1. Push your code to the connected repository
2. Render will automatically build and deploy

## Post-Deployment Checklist

### Update Frontend Environment
After backend is deployed, update Vercel environment variables:
```
VITE_API_URL=https://your-eduhub-api.onrender.com
```

### Update Auth0 Settings
1. Go to Auth0 Dashboard
2. Update Allowed Callback URLs:
   ```
   https://your-app.vercel.app/callback,
   http://localhost:5173/callback
   ```
3. Update Allowed Logout URLs:
   ```
   https://your-app.vercel.app,
   http://localhost:5173
   ```
4. Update Allowed Web Origins:
   ```
   https://your-app.vercel.app,
   http://localhost:5173
   ```

### Test Deployment

1. **Frontend Health Check**
   ```bash
   curl https://your-app.vercel.app
   ```

2. **Backend Health Check**
   ```bash
   curl https://your-eduhub-api.onrender.com/health
   ```

3. **API Documentation**
   - Visit: `https://your-eduhub-api.onrender.com/docs`

4. **Test Authentication Flow**
   - Visit frontend and try logging in
   - Check that JWT tokens are properly validated

5. **Test WebSocket Connection**
   - Go to Real-time Alerts page
   - Check that WebSocket connects (should show "Live" status)

6. **Test Core Features**
   - [ ] OAuth2 login/logout
   - [ ] Course browsing
   - [ ] Schedule import (CSV upload)
   - [ ] Rich media embeds (oEmbed)
   - [ ] Workflow templates
   - [ ] Real-time alerts

## Troubleshooting

### Frontend Issues
- **Blank page**: Check browser console for errors
- **API connection errors**: Verify VITE_API_URL is correct
- **Auth errors**: Check Auth0 configuration and callbacks

### Backend Issues
- **502 Bad Gateway**: Check Render logs, may be startup timeout
- **Database errors**: Verify DATABASE_URL is set correctly
- **WebSocket issues**: Ensure CORS allows WebSocket origins

### Common Fixes
1. **CORS errors**: Add frontend URL to CORS_ORIGINS
2. **Auth failures**: Verify Auth0 domain and audience match
3. **WebSocket disconnects**: Check that WSS protocol is used in production

## Monitoring

### Render Dashboard
- View logs: Dashboard > Service > Logs
- Monitor metrics: Dashboard > Service > Metrics
- Set up alerts for downtime

### Vercel Dashboard
- View function logs
- Monitor build times
- Set up deployment notifications

## Rollback Procedure

### Vercel
```bash
vercel rollback
```

### Render
1. Go to Dashboard > Service > Events
2. Click "Rollback" on a previous deploy

## Security Checklist

- [ ] Environment variables are not committed to git
- [ ] Production secrets are different from development
- [ ] HTTPS is enforced on both frontend and backend
- [ ] Auth0 production keys are configured
- [ ] Database has strong password
- [ ] Redis has authentication enabled
- [ ] CORS is restricted to production domains only