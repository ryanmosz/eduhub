# Vercel Deployment from GitHub

## Steps to Deploy Frontend to Vercel

1. **Go to Vercel Dashboard**
   - Visit <https://vercel.com>
   - Sign in with your GitHub account

2. **Import GitHub Repository**
   - Click "Add New..." → "Project"
   - Select "Import Git Repository"
   - Choose `ryanmosz/eduhub` from your GitHub repos

3. **Configure Project**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend` (IMPORTANT: click "Edit" and set to `frontend`)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. **Set Environment Variables**
   Click "Environment Variables" and add:

   ```
   VITE_API_URL = https://your-eduhub-api.onrender.com
   VITE_AUTH0_DOMAIN = dev-1fx6yhxxi543ipno.us.auth0.com
   VITE_AUTH0_CLIENT_ID = s05QngyZXEI3XNdirmJu0CscW1hNgaRD
   VITE_AUTH0_REDIRECT_URI = https://your-project.vercel.app
   VITE_AUTH0_AUDIENCE = https://eduhub-api.example.com
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Note your deployment URL (e.g., `eduhub-frontend.vercel.app`)

## After Deployment

1. **Update Auth0 Settings**
   - Add your Vercel URL to Allowed Callback URLs
   - Add your Vercel URL to Allowed Logout URLs
   - Add your Vercel URL to Allowed Web Origins

2. **Update Backend CORS**
   - Add your Vercel URL to CORS_ORIGINS in Render

3. **Test Your Deployment**
   - Visit your Vercel URL
   - Try logging in with Auth0
   - Verify all features work
