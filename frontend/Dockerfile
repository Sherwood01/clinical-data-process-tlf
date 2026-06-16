# Stage 1: Build
FROM node:20-alpine AS builder

ARG NEXT_PUBLIC_API_URL=http://localhost:8100/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_STACK_PROJECT_ID
ENV NEXT_PUBLIC_STACK_PROJECT_ID=$NEXT_PUBLIC_STACK_PROJECT_ID
ARG NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY
ENV NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=$NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY
ARG NEXT_PUBLIC_STACK_URL
ENV NEXT_PUBLIC_STACK_URL=$NEXT_PUBLIC_STACK_URL
ARG NEXT_PUBLIC_BROWSER_STACK_API_URL
ENV NEXT_PUBLIC_BROWSER_STACK_API_URL=$NEXT_PUBLIC_BROWSER_STACK_API_URL
ARG NEXT_PUBLIC_STACK_EXTRA_REQUEST_HEADERS
ENV NEXT_PUBLIC_STACK_EXTRA_REQUEST_HEADERS=$NEXT_PUBLIC_STACK_EXTRA_REQUEST_HEADERS

WORKDIR /app
COPY package.json package-lock.json ./
COPY patches ./patches
RUN npm config set registry https://registry.npmmirror.com && npm ci

COPY . .
# 修补 @hexclave/ui 的 SimpleTooltip，使其自包含 TooltipProvider，解决多实例 React Context 报错
RUN node patch-ui-tooltip.js
RUN npm run build
# 用独立脚本对 standalone/server.js 进行 require 劫持补丁
RUN node patch-standalone.js

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
