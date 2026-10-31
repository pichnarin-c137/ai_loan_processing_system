# Build context: the repo root (the pnpm lockfile lives there).
FROM node:26-slim
RUN npm install --global pnpm@11.9.0
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY auth/package.json auth/
RUN pnpm install --frozen-lockfile --prod --filter auth --ignore-scripts
COPY auth/src auth/src
WORKDIR /repo/auth
USER node
ENV NODE_ENV=production PORT=3001
EXPOSE 3001
CMD ["node", "src/index.ts"]
