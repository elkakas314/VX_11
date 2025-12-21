FROM node:20-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY . .
RUN npm install
RUN npm run build
EXPOSE 5173
EXPOSE 8020
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8020"]
