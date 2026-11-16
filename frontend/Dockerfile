# Stage 1: Build the React application
FROM node:22-alpine AS builder

WORKDIR /app

# Instalar dependencias con caché de capas
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci

# Copiar código del frontend y fixtures de pruebas requeridos por ?raw imports
COPY frontend/ ./frontend/
COPY tests/fixtures/yaml/ ./tests/fixtures/yaml/

# Compilar para producción
RUN cd frontend && npm run build

# Stage 2: Servidor web ligero con Nginx
FROM nginx:alpine

# Copiar bundle compilado
COPY --from=builder /app/frontend/dist /usr/share/nginx/html

# Copiar configuración con proxy inverso hacia el backend
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
