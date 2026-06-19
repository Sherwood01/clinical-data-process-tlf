# Stage 1: Build
FROM node:20-alpine AS builder

ARG NEXT_PUBLIC_API_URL=http://localhost:8100/api/v1
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ARG NEXT_PUBLIC_GITHUB_CLIENT_ID
ARG NEXT_PUBLIC_MICROSOFT_CLIENT_ID
ARG API_REWRITE_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_GITHUB_CLIENT_ID=$NEXT_PUBLIC_GITHUB_CLIENT_ID
ENV NEXT_PUBLIC_MICROSOFT_CLIENT_ID=$NEXT_PUBLIC_MICROSOFT_CLIENT_ID
ENV API_REWRITE_URL=$API_REWRITE_URL

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci

COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
