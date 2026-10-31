#!/bin/bash

# Intentar agregar rutas estándar si PATH no es de solo lectura
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH" 2>/dev/null || true

# Rutas absolutas compatibles con entornos restringidos (labjail)
RM_BIN="/bin/rm"
MKDIR_BIN="/bin/mkdir"
CP_BIN="/bin/cp"
CHMOD_BIN="/bin/chmod"
CHOWN_BIN="/bin/chown"
SED_BIN="/bin/sed"
OPENSSL_BIN="/usr/bin/openssl"

PROJECT_DIR=$(pwd)
CRON_MARKER="# VULN_APP_CERTBOT_RENEWAL"
DB_CERT_DEST="$HOME/certs_db"
DB_CERT_UID=70

# Detectar motor de contenedores (Podman rootless vs Docker)
if command -v podman-compose >/dev/null 2>&1; then
    USE_PODMAN=1
    COMPOSE_CMD="podman-compose"
    CONTAINER_ENGINE="podman"
else
    USE_PODMAN=0
    COMPOSE_CMD="sudo -E docker compose"
    CONTAINER_ENGINE="sudo docker"
fi

CRON_CMD="0 3 * * * cd \"$PROJECT_DIR\" && $COMPOSE_CMD run --rm certbot renew --quiet && $CONTAINER_ENGINE exec frontend nginx -s reload"

echo "================================================="
echo "   Selector de Entorno: Autofirmado vs Let's Encrypt"
echo "================================================="
echo "1) Sin Dominio (Certificados Autofirmados / Local)"
echo "2) Con Dominio (Certificados Let's Encrypt / Prod)"
echo "================================================="
read -p "Selecciona una opción (1 o 2): " OPCION

if [ "$OPCION" == "1" ]; then
    echo -e "\n[+] Deteniendo contenedores y limpiando certificados y volúmenes anteriores..."
    $COMPOSE_CMD down -v 2>/dev/null
    if [ "$USE_PODMAN" -eq 1 ]; then
        podman volume rm -f vulnapp_postgres_api_data postgres_api_data 2>/dev/null || true
        "$MKDIR_BIN" -p "$HOME/.config/containers"
        if [ ! -f "$HOME/.config/containers/registries.conf" ]; then
            cat << 'EOF' > "$HOME/.config/containers/registries.conf"
unqualified-search-registries = ["docker.io"]
EOF
        fi
        if [ -f ".env" ]; then
            "$CP_BIN" .env "$HOME/.env" 2>/dev/null || true
        fi
    fi
    "$RM_BIN" -rf ./certbot ./nginx/ssl

    echo "[+] Configurando entorno SIN dominio..."
    "$CP_BIN" prod_config/docker-compose.nodomain.yml docker-compose.yml
    "$CP_BIN" prod_config/nginx.nodomain.conf frontend/nginx.conf

    echo "[+] Generando certificados autofirmados locales..."
    "$MKDIR_BIN" -p ./nginx/ssl
    CERT_SAN="DNS:localhost,IP:127.0.0.1,IP:::1"
    "$OPENSSL_BIN" req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ./nginx/ssl/nginx-selfsigned.key \
        -out ./nginx/ssl/nginx-selfsigned.crt \
        -subj "/C=CL/ST=RM/L=Santiago/O=Desarrollo/CN=localhost" \
        -addext "subjectAltName=$CERT_SAN" 2>/dev/null

    echo "[+] Configurando permisos seguros para Base de Datos..."
    "$RM_BIN" -rf "$DB_CERT_DEST"
    "$MKDIR_BIN" -p "$DB_CERT_DEST"
    "$CP_BIN" ./nginx/ssl/nginx-selfsigned.crt "$DB_CERT_DEST/"
    "$CP_BIN" ./nginx/ssl/nginx-selfsigned.key "$DB_CERT_DEST/"

    if [ "$USE_PODMAN" -eq 1 ]; then
        podman unshare "$CHOWN_BIN" -R "$DB_CERT_UID:$DB_CERT_UID" "$DB_CERT_DEST"
        podman unshare "$CHMOD_BIN" 600 "$DB_CERT_DEST/nginx-selfsigned.key"
        podman unshare "$CHMOD_BIN" 644 "$DB_CERT_DEST/nginx-selfsigned.crt"
    else
        sudo "$CHOWN_BIN" "$DB_CERT_UID:$DB_CERT_UID" "$DB_CERT_DEST/nginx-selfsigned.key" "$DB_CERT_DEST/nginx-selfsigned.crt"
        sudo "$CHMOD_BIN" 600 "$DB_CERT_DEST/nginx-selfsigned.key"
        sudo "$CHMOD_BIN" 644 "$DB_CERT_DEST/nginx-selfsigned.crt"
        if [ -d "/root" ]; then
            sudo "$RM_BIN" -rf /root/certs_db
            sudo "$MKDIR_BIN" -p /root/certs_db
            sudo "$CP_BIN" ./nginx/ssl/nginx-selfsigned.crt /root/certs_db/
            sudo "$CP_BIN" ./nginx/ssl/nginx-selfsigned.key /root/certs_db/
            sudo "$CHOWN_BIN" "$DB_CERT_UID:$DB_CERT_UID" /root/certs_db/nginx-selfsigned.key /root/certs_db/nginx-selfsigned.crt
            sudo "$CHMOD_BIN" 600 /root/certs_db/nginx-selfsigned.key
            sudo "$CHMOD_BIN" 644 /root/certs_db/nginx-selfsigned.crt
        fi
    fi
    echo "[+] Certificados replicados en $DB_CERT_DEST con permisos 600."

    echo "[+] Levantando contenedores..."
    $COMPOSE_CMD up -d --build

elif [ "$OPCION" == "2" ]; then
    echo -e "\n[+] Configurando entorno CON dominio..."
    read -p "Ingresa tu dominio (ej: midominio.cl): " DOMINIO
    read -p "Ingresa tu correo (para avisos de expiración de Let's Encrypt): " EMAIL

    echo "[+] Deteniendo contenedores y limpiando certificados anteriores..."
    $COMPOSE_CMD down 2>/dev/null
    "$RM_BIN" -rf ./certbot ./nginx/ssl

    echo "[+] Aplicando configuraciones de red..."
    "$CP_BIN" prod_config/docker-compose.domain.yml docker-compose.yml
    "$CP_BIN" prod_config/nginx.domain.conf frontend/nginx.conf

    "$SED_BIN" -i "s/{{DOMAIN}}/$DOMINIO/g" frontend/nginx.conf

    echo "[+] Solicitando certificado oficial a Let's Encrypt para $DOMINIO..."
    if $CONTAINER_ENGINE run --rm -p 8113:80 \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        docker.io/certbot/certbot certonly --standalone \
        -d "$DOMINIO" \
        --non-interactive \
        --agree-tos \
        -m "$EMAIL"; then

        echo -e "\n[+] Certificados obtenidos correctamente. Levantando la aplicación..."
        $COMPOSE_CMD up -d --build
    else
        echo -e "\n[ERROR] Certbot falló en la obtención del certificado."
        exit 1
    fi

else
    echo "Opción inválida. Abortando."
    exit 1
fi

echo -e "\n================================================="
echo "¡Cambio de entorno completado con éxito!"
echo "================================================="
