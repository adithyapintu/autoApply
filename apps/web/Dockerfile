FROM node:20-alpine

WORKDIR /app
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared/package.json ./packages/shared/package.json
COPY packages/ui/package.json ./packages/ui/package.json
COPY packages/playwright/package.json ./packages/playwright/package.json
RUN corepack enable && \
    echo "shamefully-hoist=true" > .npmrc && \
    pnpm install --frozen-lockfile=false
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN cd /app/apps/web && /app/node_modules/.bin/next build

WORKDIR /app/apps/web
CMD ["/app/node_modules/.bin/next", "start", "--hostname", "0.0.0.0"]

