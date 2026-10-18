# ==============================================================================
# IdeaLens Frontend Production Dockerfile
# Multi-stage build compiling React Vite SPA and serving via unprivileged NGINX
# ==============================================================================

FROM node:20-alpine AS build

WORKDIR /app

# Cache package dependencies
COPY package*.json ./
RUN npm ci

# Copy application source code and build production bundle
COPY . .
RUN npm run build

# Runtime Stage
FROM nginxinc/nginx-unprivileged:alpine AS runner

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from build stage
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
