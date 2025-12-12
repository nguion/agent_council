# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build the app
# Note: VITE_API_URL should be provided at build time or handled via runtime config.
# For a static build, we often bake it in or use a relative path proxy.
# We'll assume a default or allow build-arg override.
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config if needed (using default for now)
# We might need a config to handle React Router (SPA) history mode fallback
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

