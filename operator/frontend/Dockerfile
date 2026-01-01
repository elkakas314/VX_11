# ==== BUILD STAGE ====
FROM node:20-alpine AS build

WORKDIR /app

COPY operator/frontend/package.json operator/frontend/package-lock.json ./
RUN npm ci

COPY operator/frontend/ .

ARG VITE_API_BASE=/operator
ARG VITE_VX11_TOKEN=vx11-test-token
ENV VITE_API_BASE=${VITE_API_BASE}
ENV VITE_VX11_TOKEN=${VITE_VX11_TOKEN}

RUN npm run build

# ==== RUNTIME STAGE (dist exporter) ====
FROM alpine:3.19

WORKDIR /app
COPY --from=build /app/dist /dist

CMD ["sh", "-c", "mkdir -p /shared/dist && cp -r /dist/* /shared/dist/ && tail -f /dev/null"]
