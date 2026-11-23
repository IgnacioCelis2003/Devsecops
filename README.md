---

# Guía de Despliegue

El despliegue local se realiza con `iniciar_app.sh` y la **opción 1**. La
opción 2 (dominio + Let's Encrypt) se mantiene en el repositorio, pero **no ha
sido testeada**.

En **Linux con Docker Engine**, lo único necesario es un `.env` configurado
correctamente y ejecutar el script con la opción 1. En otros entornos
(Docker Desktop, WSL2, Podman, macOS o Windows nativo) hay consideraciones
adicionales; revisa la tabla de compatibilidad.

## Requisitos Previos

* **Docker** y **Docker Compose**
* **Bash** y **OpenSSL** disponibles en el host.
* Conexión a internet la primera vez, para descargar imágenes y construir el
  frontend.
* Puertos **8103** (HTTPS) y **8113** (HTTP) disponibles. Si vas a acceder
  desde otro equipo de la red local, habilítalos en el firewall.

## Compatibilidad por Entorno

| Entorno | Estado | Qué tener en cuenta |
|---|---|---|
| Linux + Docker Engine | **Probado** | Ejecuta con `sudo` si tu usuario no pertenece al grupo `docker`. |
| Linux + Podman rootless | Soporte en el script, **no probado** | Requiere `podman-compose`; no uses `sudo`. |
| WSL2 + Docker Desktop | **No probado** | Activa la integración de Docker Desktop con tu distro. Ejecuta el script **dentro de WSL**, no desde PowerShell. Accede desde Windows con `https://localhost:8103`. |
| Docker Desktop en macOS | **No soportado directamente** | El script asume rutas/permisos de Linux y `sudo`; usa una VM Linux o WSL2, o adapta los comandos manualmente. |
| Windows nativo | **No soportado** | Usa WSL2 y sigue las indicaciones de la fila anterior. |

Notas para WSL2 y acceso desde otras máquinas:

* Clona el repositorio dentro del sistema de archivos de WSL (por ejemplo
  `~/Devsecops`), no en `/mnt/c/...`, para evitar problemas de permisos y
  rendimiento.
* `https://localhost:8103` funciona desde Windows gracias al reenvío de WSL2.
  Otra máquina de la red debe usar la IP del host Windows, no la IP interna de
  WSL, y puede requerir una regla de firewall o `portproxy`.
* El certificado autofirmado incluye la IP que detecta `hostname -I` dentro de
  WSL. Si accedes desde otra máquina por la IP de Windows, el navegador mostrará
  una advertencia de nombre; puedes continuar aceptándola.

## Configuración Inicial

El proyecto utiliza un archivo `.env` en la raíz. Es el único paso de
configuración necesario antes de ejecutar el script. Usa `.env.example` como
plantilla y revisa al menos estas variables:

```env
VITE_API_URL=/api
VITE_BASE=/
POSTGRES_DB=vulnerabilidades_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=change-me
ENCRYPTION_KEY=<clave-Fernet>
JWT_SECRET=change-me
```

Genera `ENCRYPTION_KEY` con:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

No publiques el `.env` real. Para el despliegue local deja `VITE_BASE=/` y
`VITE_API_URL=/api`. Solo si el sitio va detrás del proxy `/grupo3` cambia a
`/grupo3/` y `/grupo3/api`.

## Despliegue Local

Con el `.env` listo, ejecuta:

```bash
chmod +x iniciar_app.sh
sudo ./iniciar_app.sh
```

Usa `sudo` en Linux con Docker Engine si tu usuario no está en el grupo
`docker`. En Docker Desktop (especialmente WSL2) o Podman rootless, ejecuta
`./iniciar_app.sh` sin `sudo` si `docker info` funciona con tu usuario. En WSL2,
hazlo desde la terminal de la distro. Si `docker info` falla, revisa
`docker context ls` y activa el contexto correcto con `docker context use`.

Elige la opción **1**. El script detiene contenedores previos, conserva el
volumen de PostgreSQL, genera certificados autofirmados y levanta `db-api`,
`api` y `frontend`.

Accede mediante `https://localhost:8103` o `https://127.0.0.1:8103`. Desde
otro equipo de la red usa `https://<IP-local>:8103`; acepta el aviso de
certificado autofirmado. El puerto `8113` solo redirige de HTTP a HTTPS.

## Ejecución del Proyecto

### Cargar datos de prueba Wazuh

El archivo `vuln-api/app/datos_wazuh.json` contiene los datos de prueba. El
loader usa las dependencias de la imagen de la API y la red de Compose. Con la
base de datos levantada, ejecútalo desde la raíz del repositorio:

```bash
docker compose run --rm --no-deps -v "$PWD:/repo" -w /repo api \
  python frontend/tools-bd/load-data.py --replace
```

`--replace` reemplaza las vulnerabilidades, conexiones, historial e
interacciones del seed; no elimina usuarios. Para cargar otro archivo JSON:

```bash
docker compose run --rm --no-deps -v "$PWD:/repo" -v "/ruta/al:/data:ro" \
  -w /repo api python frontend/tools-bd/load-data.py /data/archivo.json --replace
```

En el entorno local Docker, el seed se carga automáticamente al iniciar la API
porque `docker-compose.yml` y `docker-compose.nodomain.yml` habilitan
`SEED_EXAMPLE_DATA` por defecto. La carga solo se ejecuta si todavía no existen
vulnerabilidades; no reemplaza datos existentes automáticamente. Para
deshabilitarla, define `SEED_EXAMPLE_DATA=false` en `.env`.

No uses `http://` en el puerto 8103 ni omitas el puerto: `https://localhost`
apunta al 443, donde no escucha la aplicación. Si el navegador mantiene un
rechazo anterior, elimina la excepción/certificado guardado para esa dirección
y vuelve a abrirla.

Las contraseñas de conexiones que no sean tokens Fernet se cifran durante la
carga. Las URL incluidas son datos ficticios, por lo que el botón de prueba o
la sincronización contra Wazuh no funcionarán hasta sustituirlas por un
indexador accesible.

Para comprobar la vista con estas fechas históricas, inicia sesión con el
usuario local `admin` y contraseña `admin`, selecciona una conexión y usa el
periodo **Todo** antes de generar la vista; el periodo predeterminado de 30
días no incluye los eventos de marzo de 2026.

## Opciones del Script

### Opción 1: Local (probada en Linux + Docker Engine)

* Detiene contenedores previos sin borrar el volumen `postgres_api_data`.
* Copia la configuración de `docker-compose.nodomain.yml`.
* Genera certificados autofirmados para `localhost`, `127.0.0.1` y la IP local.
* Levanta `db-api`, `api` y `frontend`.
* Expone `https://localhost:8103` y la redirección HTTP en `http://localhost:8113`.
* Conserva la base de datos entre ejecuciones. Para borrarla explícitamente, usa
  `docker compose down -v`.

### Opción 2: Dominio + Let's Encrypt (NO TESTEADA)

La opción 2 se incluye en el repositorio, pero **no ha sido probada** y no se
recomienda para la evaluación. Solo la opción 1 está validada.

## Arquitectura de Servicios

Docker Compose levanta los siguientes servicios interconectados a través de la red `app-network`:

1. **db-api:** Base de datos PostgreSQL 15 con un volumen persistente `postgres_api_data`.
2. **api:** Backend construido desde la carpeta `./vuln-api`, con un *healthcheck* configurado que espera a que la base de datos esté lista antes de iniciar.
3. **frontend:** Servidor Nginx que expone los puertos `8113` (HTTP) y `8103` (HTTPS), construido desde `./frontend`. Tiene montados los volúmenes para leer los certificados.
4. **certbot** (Solo Opción 2): Contenedor encargado de gestionar las renovaciones futuras de SSL.
