# Development Dockerfile for React Frontend
# This mirrors local Vercel development environment

FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies first (for better caching)
COPY package*.json ./
RUN npm ci

# Copy the rest of the application
COPY . .

# Expose the Vite dev server port
EXPOSE 5173

# Environment variables (will be overridden by docker-compose or runtime)
ENV VITE_API_BASE_URL=http://localhost:8000

# Start the development server with host binding
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]