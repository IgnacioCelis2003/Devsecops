FROM node:24-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci --ignore-scripts

# Copiamos el código fuente
COPY . .

# Definimos las variables de entorno para el build de Vite (con valores por defecto para grupo3)
ARG VITE_API_URL=/grupo3/api
ENV VITE_API_URL=$VITE_API_URL
ARG VITE_BASE=/grupo3/
ENV VITE_BASE=$VITE_BASE

RUN npm run build
# ------------------------------

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80 443
