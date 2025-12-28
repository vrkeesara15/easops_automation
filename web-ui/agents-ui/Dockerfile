# Build the Vite frontend
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_AGENTS_API_BASE_URL
ENV VITE_AGENTS_API_BASE_URL=${VITE_AGENTS_API_BASE_URL}

COPY package*.json ./
RUN npm install --no-fund --no-audit

COPY . .
RUN npm run build

# Serve the static assets with nginx
FROM nginx:1.27-alpine

# Cloud Run expects the application to listen on $PORT (default 8080)
ENV PORT=8080
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf \
    && sed -i 's/listen       \[::\]:80;/listen       [::]:8080;/' /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
