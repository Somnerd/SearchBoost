# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

RUN npm run build

# Serve stage
FROM nginxinc/nginx-unprivileged:stable-alpine

# Use unprivileged user for security
USER 101

# Copy build output to nginx path
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default nginx config with our SPA + Proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
