FROM node:20-alpine

WORKDIR /app
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json
RUN corepack enable && pnpm install --frozen-lockfile=false
COPY . .
RUN pnpm --filter @autoapply/web build

CMD ["pnpm", "--filter", "@autoapply/web", "start"]

