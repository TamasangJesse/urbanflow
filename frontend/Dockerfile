# UrbanFlow — Frontend Dockerfile
# Fix 12.2: VITE_GOOGLE_MAPS_API_KEY must be passed as ARG before npm run build.
# Vite bakes env vars into the bundle at compile time, NOT runtime.

# ─── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer-caching: only reinstall when package.json changes)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Fix 12.2 — declare ARG and bind it to ENV so Vite can read it during build
ARG VITE_GOOGLE_MAPS_API_KEY
ENV VITE_GOOGLE_MAPS_API_KEY=$VITE_GOOGLE_MAPS_API_KEY

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the production bundle
RUN npm run build

# ─── Stage 2: Serve ───────────────────────────────────────────────────────────
FROM nginx:alpine AS production

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config for React Router (SPA — all paths served by index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
