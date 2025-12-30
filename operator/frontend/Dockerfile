# ==== BUILD STAGE ====
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE=/operator
ENV VITE_API_BASE=${VITE_API_BASE}

RUN npm run build

# ==== RUNTIME STAGE (dist exporter) ====
FROM alpine:3.19

WORKDIR /app
COPY --from=build /app/dist /dist

CMD ["sh", "-c", "mkdir -p /shared/dist && cp -r /dist/* /shared/dist/ && tail -f /dev/null"]
