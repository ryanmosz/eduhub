# Update CORS Origins on Render

The frontend is now deployed at a new Vercel URL. You need to update the CORS_ORIGINS environment variable on Render:

1. Go to your Render dashboard
2. Click on your eduhub-api service
3. Go to "Environment" tab
4. Find the `CORS_ORIGINS` variable
5. Update it to include the new Vercel URL:

```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8001,https://eduhub-frontend.vercel.app,https://eduhub-frontend-kvnw5o58q-ryan-moszynskis-projects.vercel.app,https://eduhub-frontend-*.vercel.app
```

Or if you want to allow all Vercel preview deployments:

```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8001,https://eduhub-frontend.vercel.app,https://eduhub-frontend-*.vercel.app,https://*.vercel.app
```

6. Save and let Render redeploy

The error shows your frontend is at: `https://eduhub-frontend-kvnw5o58q-ryan-moszynskis-projects.vercel.app`