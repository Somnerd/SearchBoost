# --- Stage 1: Build (TypeScript Compilation) ---
FROM node:20-alpine AS builder

# Install system dependencies for Prisma
RUN apk add --no-cache openssl libc6-compat

WORKDIR /app

# Copy all dependency files then install everything (including devDependencies for tsc)
COPY package*.json ./
COPY prisma ./prisma/
RUN npm install

# Copy source and config
COPY . .

# Generate Prisma Client and Compile TS -> JS
RUN npm run build

# --- Stage 2: Runtime (Production Environment) ---
FROM node:20-alpine

# Install system dependencies for Prisma
RUN apk add --no-cache openssl libc6-compat

WORKDIR /app

# Copy only production dependencies and compiled code
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules/
COPY --from=builder /app/dist ./dist/
COPY --from=builder /app/prisma ./prisma/

# Ensure we don't bring in dev .env
RUN rm -f .env && chown -R node:node /app

USER node
EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

# Launch from the compiled distribution
CMD ["node", "dist/app.js"]
