# Stage 1: React app build karo
FROM --platform=linux/amd64 node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --production=false
COPY . .
RUN npm run build

# Stage 2: Nginx se serve karo
FROM --platform=linux/amd64 nginx:1.27-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]