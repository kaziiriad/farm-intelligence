FROM oven/bun:1-alpine AS deps
WORKDIR /app

COPY package.json bun.lock bunfig.toml ./
RUN bun install --frozen-lockfile

FROM deps AS build
WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY . .
RUN bun run build

FROM node:22-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

COPY --from=build /app/.output ./.output

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
