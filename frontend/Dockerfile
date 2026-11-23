FROM node:24-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts

# Copiamos el código fuente
COPY . .

# Variables de Vite para despliegue local (el proxy /grupo3 se configura en .env)
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
ARG VITE_BASE=/
ENV VITE_BASE=$VITE_BASE

RUN npm run build
# ------------------------------

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80 443
