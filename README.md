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

* **Docker** y **Docker Compose**.
* **Bash** y **OpenSSL** disponibles en el entorno donde se ejecuta el script
  (host Linux o distro WSL).
* En Windows: **WSL2** con una distro Linux y **Docker Desktop** con la
  integración WSL habilitada para esa distro. Windows nativo no es compatible.
* Conexión a internet la primera vez, para descargar imágenes y construir el
  frontend.
* Puertos **8103** (HTTPS) y **8113** (HTTP) disponibles. Si vas a acceder
  desde otro equipo de la red local, habilítalos en el firewall.

## Compatibilidad por Entorno

| Entorno | Estado | Qué tener en cuenta |
|---|---|---|
| Linux + Docker Engine | **Probado** | Ejecuta con `sudo` si tu usuario no pertenece al grupo `docker`. |
| Linux + Podman rootless | Soporte en el script, **no probado** | Requiere `podman-compose`; no uses `sudo`. |
| WSL2 + Docker Desktop | **Probado** | Habilita la integración WSL de Docker Desktop para la distro, copia el repositorio dentro del filesystem de WSL y ejecuta el script desde la terminal de la distro. Ver [WSL2 + Docker Desktop](#wsl2--docker-desktop-probado). |
| Docker Desktop en macOS | **No soportado directamente** | El script asume rutas/permisos de Linux y `sudo`; usa una VM Linux o WSL2, o adapta los comandos manualmente. |
| Windows nativo | **No soportado** | Usa WSL2 y sigue las indicaciones de la fila anterior. |

### WSL2 + Docker Desktop (probado)

Esta es la ruta recomendada en Windows. Requiere Docker Desktop con el motor
Linux, una distro WSL2 (por ejemplo Ubuntu) y la integración WSL habilitada
para esa distro. Ejecuta todos los comandos **dentro de WSL**, no desde
PowerShell.

#### 1. Habilitar la integración WSL

En Docker Desktop abre **Settings → Resources → WSL Integration**, activa
**Enable integration with my default WSL distro** y la distro concreta
(por ejemplo `Ubuntu`), y aplica los cambios (Docker Desktop se reinicia).
Asegúrate también de que Docker Desktop use el motor Linux y, si aparece la
opción, **Use the WSL 2 based engine**.

Si no tienes acceso a la interfaz, el equivalente en
`%APPDATA%\Docker\settings-store.json` es:

```json
{
  "EnableIntegrationWithDefaultWslDistro": true,
  "IntegratedWslDistros": ["Ubuntu"],
  "WslEngineEnabled": true
}
```

Haz una copia de seguridad del archivo antes de editarlo y reinicia Docker
Desktop (`docker desktop restart`, o ciérralo y ábrelo de nuevo). La edición
manual no es el método oficial de Docker; úsala solo si la UI no está
disponible.

Verifica desde la distro:

```bash
docker info
docker compose version
```

Si aparece `The command 'docker' could not be found in this WSL 2 distro`,
la integración no está habilitada para esa distro. Comprueba que sea WSL2 con
`wsl -l -v` y, si el contexto no es el correcto:

```bash
docker context ls
docker context use desktop-linux
```

Si la integración está activada pero sigue fallando, prueba a reiniciar WSL y
Docker Desktop:

```powershell
wsl --shutdown
docker desktop restart
```

#### 2. Copiar el proyecto al filesystem de WSL

No ejecutes el proyecto desde `/mnt/c/...`: los bind mounts, los permisos de
los certificados y el rendimiento pueden fallar. Copia el repositorio a tu home
de WSL:

```bash
rsync -a /mnt/c/Users/<usuario>/Desktop/Devsecops/ ~/Devsecops/
cd ~/Devsecops
chmod +x iniciar_app.sh
```

Si no tienes `rsync`, usa `cp -a`. Mantén una sola copia desplegada: los
nombres de contenedor (`db-api`, `api`, `frontend`) son fijos y dos copias
simultáneas chocan.

#### 3. Configurar el `.env`

Crea el `.env` dentro de la copia de WSL, siguiendo
[Configuración Inicial](#configuración-inicial). Para WSL2 ten en cuenta:

* `SEED_EXAMPLE_DATA=true` si quieres cargar los datos de prueba. El
  `.env.example` trae `false`, y ese valor **anula** el default `true` de
  Compose; si copias el ejemplo tal cual, el seed no se cargará.
* `chmod 600 .env` para limitar los permisos.
* Si cambias `POSTGRES_PASSWORD` después de crear el volumen de PostgreSQL, la
  API no podrá conectarse. Mantén la misma contraseña o elimina el volumen con
  `docker compose down -v` antes de volver a levantar.

#### 4. Ejecutar el script

Desde la terminal de WSL, en la copia del proyecto:

```bash
./iniciar_app.sh
```

Elige la opción **1**. En Docker Desktop/WSL2 no uses `sudo` si `docker info`
funciona con tu usuario. Si la distro entra como `root`, el script funciona
igual y `sudo` no pedirá contraseña.

Para seleccionar la opción 1 sin interacción:

```bash
printf '1\n' | ./iniciar_app.sh
```

#### 5. Acceder y verificar

Desde Windows abre:

```text
https://localhost:8103
```

o `https://127.0.0.1:8103`. Acepta el aviso de certificado autofirmado. El
puerto `8113` solo redirige de HTTP a HTTPS. Desde la propia distro WSL también
funcionan `https://localhost:8103` y la IP de `hostname -I`.

Comprobaciones útiles:

```bash
docker compose ps
docker compose logs -f api
curl -k https://localhost:8103/
curl -k https://localhost:8103/api/docs
```

Desde Windows también puedes usar `curl.exe -k https://localhost:8103/`.

Desde otra máquina de la red usa la IP del host Windows, no la IP interna de
WSL; puede requerir una regla de firewall o `portproxy`. El certificado incluye
la IP de WSL, así que el navegador mostrará una advertencia de nombre; puedes
continuar aceptándola.

#### 6. Persistencia, reinicio y limpieza

* `docker compose down` detiene los contenedores y **conserva** el volumen
  `devsecops_postgres_api_data`.
* `docker compose down -v` elimina también la base de datos. Úsalo solo si
  quieres empezar de cero.
* Docker Desktop debe estar iniciado. Si no lo configuraste para arrancar con
  Windows, ábrelo manualmente después de reiniciar. Los contenedores tienen
  `restart: unless-stopped`; si no vuelven solos, ejecuta
  `cd ~/Devsecops && docker compose up -d`.
* Para actualizar el código desde Windows, vuelve a sincronizar con
  `rsync -a /mnt/c/Users/<usuario>/Desktop/Devsecops/ ~/Devsecops/` y ejecuta de
  nuevo `./iniciar_app.sh`. El `rsync` sin `--delete` conserva el `.env` y los
  certificados; el volumen de PostgreSQL es independiente y no se toca.
* El script copia `prod_config/docker-compose.nodomain.yml` y
  `prod_config/nginx.nodomain.conf` sobre `docker-compose.yml` y
  `frontend/nginx.conf` en cada ejecución. Para conservar cambios, edita las
  plantillas de `prod_config/`, no los archivos generados.
* El script borra `nginx/ssl` y `certbot` y regenera los certificados en cada
  ejecución. El certificado incluye `localhost`, `127.0.0.1`, `::1` y la
  primera IP de `hostname -I` (la IP interna de WSL). Si esa IP cambia o
  accedes por la IP de Windows, el navegador mostrará una advertencia de
  nombre; puedes continuar o volver a ejecutar el script.
* El aviso de Nginx `can not modify /etc/nginx/conf.d/default.conf` es normal:
  el archivo se monta como solo lectura y no impide el arranque.
* Si editas `iniciar_app.sh` desde Windows, guárdalo con finales de línea LF.
  Si ves errores `$'\r'`, corrígelo dentro de WSL con
  `sed -i 's/\r$//' iniciar_app.sh`.

## Configuración Inicial

El proyecto utiliza un archivo `.env` en la raíz. Es el único paso de
configuración de la aplicación necesario antes de ejecutar el script. Usa
`.env.example` como plantilla y revisa al menos estas variables:

```env
VITE_API_URL=/api
VITE_BASE=/
POSTGRES_DB=vulnerabilidades_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=change-me
ENCRYPTION_KEY=<clave-Fernet>
JWT_SECRET=change-me
SEED_EXAMPLE_DATA=true
```

Genera `ENCRYPTION_KEY` con:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Si `cryptography` no está instalado en el entorno, esta alternativa usa solo la
librería estándar y también produce una clave Fernet válida:

```bash
python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

No publiques el `.env` real. En Linux/WSL limita sus permisos:

```bash
chmod 600 .env
```

Para cargar los datos de prueba en el primer arranque define
`SEED_EXAMPLE_DATA=true`. El `.env.example` trae `false`, y ese valor tiene
prioridad sobre el default `true` de Compose. La carga solo se ejecuta si la
tabla de vulnerabilidades está vacía.

Para el despliegue local deja `VITE_BASE=/` y `VITE_API_URL=/api`. Solo si el
sitio va detrás del proxy `/grupo3` cambia a `/grupo3/` y `/grupo3/api`.

## Despliegue Local

Con el `.env` listo, ejecuta:

```bash
chmod +x iniciar_app.sh
sudo ./iniciar_app.sh
```

Usa `sudo` en Linux con Docker Engine si tu usuario no está en el grupo
`docker`. En Docker Desktop (especialmente WSL2) o Podman rootless, ejecuta
`./iniciar_app.sh` sin `sudo` si `docker info` funciona con tu usuario. En WSL2,
hazlo desde la terminal de la distro; la configuración previa (integración WSL,
copia del proyecto y `.env`) está detallada en
[WSL2 + Docker Desktop](#wsl2--docker-desktop-probado). Si `docker info` falla,
revisa `docker context ls` y activa el contexto correcto con
`docker context use`.

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
si `SEED_EXAMPLE_DATA=true`. Las variantes sin dominio (`docker-compose.yml` y
`docker-compose.nodomain.yml`) usan `true` como default, pero el `.env.example`
define `false`; como `.env` tiene prioridad, si copias el ejemplo tal cual el
seed **no** se cargará. La carga solo se ejecuta si todavía no existen
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

El API marca `admin/admin` como contraseña temporal y exige cambiarla para las
rutas protegidas por rol. Si una llamada autenticada devuelve `403` con el
mensaje `Debe cambiar su contraseña por defecto antes de continuar`, completa el
cambio desde la interfaz antes de seguir probando.

## Opciones del Script

### Opción 1: Local (probada en Linux + Docker Engine y WSL2 + Docker Desktop)

* Detiene contenedores previos sin borrar el volumen `postgres_api_data`.
* Copia la configuración de `prod_config/docker-compose.nodomain.yml` y
  `prod_config/nginx.nodomain.conf`.
* Genera certificados autofirmados para `localhost`, `127.0.0.1`, `::1` y la IP
  local.
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
2. **api:** Backend construido desde la carpeta `./vuln-api`; depende de `db-api` y reintenta la conexión al arrancar mientras la base de datos termina de inicializarse.
3. **frontend:** Servidor Nginx que expone los puertos `8113` (HTTP) y `8103` (HTTPS), construido desde `./frontend`. Tiene montados los volúmenes para leer los certificados.
4. **certbot** (Solo Opción 2): Contenedor encargado de gestionar las renovaciones futuras de SSL.
