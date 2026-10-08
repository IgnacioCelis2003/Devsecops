# GUÍA DEFINITIVA DE TAREAS Y PLAN DE IMPLEMENTACIÓN - PEP 1 DEVSECOPS (NOTA MÁXIMA 7.0)
**Proyecto:** VulnApp Wazuh  
**Objetivo:** Cumplir el 100% de los requerimientos diagnosticados en la Rúbrica Oficial, las directrices de cobertura sobre la totalidad del repositorio y las correcciones de UX/UI capturadas con el cliente.

---

# ÍNDICE GENERAL DE TAREAS

* [BLOQUE 1: SEGURIDAD (5 Tareas)](#bloque-1-seguridad)
  * [Tarea 1: Corrección de Firma JWT (Secret Mismatch)](#tarea-1-corrección-de-firma-jwt-secret-mismatch)
  * [Tarea 2: Control de Intentos en Login (Anti-Brute Force) y Aseguramiento de Admin](#tarea-2-control-de-intentos-en-login-anti-brute-force-y-aseguramiento-de-admin)
  * [Tarea 3: Gestión Segura de Credenciales y Archivos de Entorno](#tarea-3-gestión-segura-de-credenciales-y-archivos-de-entorno)
  * [Tarea 4: Sistema de Control de Acceso Basado en Roles (RBAC)](#tarea-4-sistema-de-control-de-acceso-basado-en-roles-rbac)
  * [Tarea 5: Validación Estricta de Certificados TLS en Wazuh Client](#tarea-5-validación-estricta-de-certificados-tls-en-wazuh-client)
* [BLOQUE 2: ESCALABILIDAD EN BASE DE DATOS Y BACKEND (4 Tareas)](#bloque-2-escalabilidad-en-base-de-datos-y-backend)
  * [Tarea 6: Activación Real de TimescaleDB y Modelado de Hypertable](#tarea-6-activación-real-de-timescaledb-y-modelado-de-hypertable)
  * [Tarea 7: Funciones Almacenadas SQL (PL/pgSQL) para Métricas de Tiempo](#tarea-7-funciones-almacenadas-sql-plpgsql-para-métricas-de-tiempo)
  * [Tarea 8: Optimización de Sincronización Masiva Wazuh (Eliminar Cuello de Botella N+1)](#tarea-8-optimización-de-sincronización-masiva-wazuh-eliminar-cuello-de-botella-n1)
  * [Tarea 9: Paginación y Filtrado en Servidor en `GET /vulns`](#tarea-9-paginación-y-filtrado-en-servidor-en-get-vulns)
* [BLOQUE 3: ESCALABILIDAD EN FRONTEND (2 Tareas)](#bloque-3-escalabilidad-en-frontend)
  * [Tarea 10: Refactorización de Dashboard.vue para Consumir Paginación del Servidor](#tarea-10-refactorización-de-dashboardvue-para-consumir-paginación-del-servidor)
  * [Tarea 11: Manejo y Alerta Visual de Truncamiento en useTimelineData.js](#tarea-11-manejo-y-alerta-visual-de-truncamiento-en-usetimelinedatajs)
* [BLOQUE 4: ARQUITECTURA Y ORGANIZACIÓN DEL CÓDIGO (1 Tarea)](#bloque-4-arquitectura-y-organización-del-código)
  * [Tarea 12: Desacoplamiento Modular del Monolito `main.py`](#tarea-12-desacoplamiento-modular-del-monolito-mainpy)
* [BLOQUE 5: DEVSECOPS Y COBERTURA DE LA TOTALIDAD DEL REPOSITORIO (3 Tareas)](#bloque-5-devsecops-y-cobertura-de-la-totalidad-del-repositorio)
  * [Tarea 13: Pipeline de Integración Continua (CI) en GitHub Actions para Backend + Frontend](#tarea-13-pipeline-de-integración-continua-ci-en-github-actions-para-backend--frontend)
  * [Tarea 14: Actualización y Creación de Tests Unitarios (Mantener Cobertura >= 80%)](#tarea-14-actualización-y-creación-de-tests-unitarios-mantener-cobertura--80)
  * [Tarea 15: Reparación y Documentación de Herramientas Locales en dev-tools (OWASP ZAP y SonarQube)](#tarea-15-reparación-y-documentación-de-herramientas-locales-en-dev-tools-owasp-zap-y-sonarqube)
* [BLOQUE 6: EXPERIENCIA DE USUARIO Y REUNIONES CON CLIENTE (2 Tareas)](#bloque-6-experiencia-de-usuario-y-reuniones-con-cliente)
  * [Tarea 16: Correcciones de Interfaz y Usabilidad (Navegación, Logo y Clic Exterior)](#tarea-16-correcciones-de-interfaz-y-usabilidad-navegación-logo-y-clic-exterior)
  * [Tarea 17: Visualización y Modo de Datos de Prueba Locales](#tarea-17-visualización-y-modo-de-datos-de-prueba-locales)
* [BLOQUE 7: LIMPIEZA Y CORRECCIÓN OPERATIVA (1 Tarea)](#bloque-7-limpieza-y-corrección-operativa)
  * [Tarea 18: Reparación del Importador `load-data.py` y Limpieza de Residuos](#tarea-18-reparación-del-importador-load-datapy-y-limpieza-de-residuos)
* [ORDEN CRONOLÓGICO Y GRAFO DE DEPENDENCIAS TÉCNICAS (18 PASOS)](#orden-cronológico-y-grafo-de-dependencias-técnicas-18-pasos)

---

# BLOQUE 1: SEGURIDAD

---

### Tarea 1: Corrección de Firma JWT (Secret Mismatch)
* **Severidad en Rúbrica:** Crítica.
* **El Problema:**
  En `vuln-api/app/auth.py` (línea 15), el código busca `JWT_SECRET`, pero el archivo `.env` define `SECRET_KEY`. Al no coincidir, recurre al valor por defecto `"dev-secret-key"`. Cualquiera con acceso al código fuente puede firmar tokens JWT válidos de administrador.
* **Lo que hay que solucionar:**
  Garantizar que la clave secreta provenga obligatoriamente del entorno y que el sistema impida arrancar si la clave no está configurada o es débil.
* **Cómo solucionarlo:**
  1. En `auth.py`, unificar a `SECRET_KEY = os.getenv("SECRET_KEY")` (o `JWT_SECRET` en ambos lados).
  2. Implementar una validación estricta *fail-fast*: si la variable no existe o es `"dev-secret-key"`, lanzar `RuntimeError("SECRET_KEY obligatoria no configurada")`.
  3. Asegurar que `.env.example` y `.env` contengan la misma variable.
* **Dónde aplicar la solución:**
  * `vuln-api/app/auth.py` (Línea 15)
  * `.env.example`
  * `.env`

---

### Tarea 2: Control de Intentos en Login (Anti-Brute Force) y Aseguramiento de Admin
* **Severidad en Rúbrica:** Alta.
* **El Problema:**
  1. `/auth/login` permite intentos ilimitados sin rate limit ni bloqueo, vulnerable a ataques de fuerza bruta.
  2. `create_default_admin()` crea en cada arranque un usuario `admin/admin` activo.
* **Lo que hay que solucionar:**
  1. Limitar los intentos de inicio de sesión fallidos.
  2. Forzar que el administrador cambie su clave al primer ingreso impidiendo cualquier otra acción.
* **Cómo solucionarlo:**
  1. En el endpoint `/auth/login`, implementar un contador de intentos fallidos por IP/usuario: tras 5 intentos fallidos consecutivos, bloquear temporalmente por 15 minutos o responder HTTP 429.
  2. En `create_default_admin()`, mantener `is_default_password = True` y asegurar que la API rechace con HTTP 403 cualquier endpoint protegido si `current_user.is_default_password` es `True`.
* **Dónde aplicar la solución:**
  * `vuln-api/app/main.py` (o `routers/auth.py`)
  * `vuln-api/app/auth.py`

---

### Tarea 3: Gestión Segura de Credenciales y Archivos de Entorno
* **Severidad en Rúbrica:** Alta.
* **El Problema:**
  El `.env` original con credenciales reales estaba versionado en el repositorio git.
* **Lo que hay que solucionar:**
  Asegurar que ningún secreto local pueda volver a filtrarse a Git ni empaquetarse en Docker.
* **Cómo solucionarlo:**
  1. Mantener `.env.example` como plantilla con valores de ejemplo (`change-me`).
  2. Verificar que `.gitignore` y los archivos `.dockerignore` excluyan `.env`, `.env.*`, `*.key`, `*.crt` y `postgres_data/`.
* **Dónde aplicar la solución:**
  * `.gitignore`
  * `.dockerignore`
  * `.env.example`
  * `vuln-api/.dockerignore`
  * `frontend/.dockerignore`

---

### Tarea 4: Sistema de Control de Acceso Basado en Roles (RBAC)
* **Severidad en Rúbrica:** Media.
* **El Problema:**
  No existe discriminación de roles. Cualquier usuario puede borrar otros usuarios, crear conexiones a Wazuh y forzar sincronizaciones.
* **Lo que hay que solucionar:**
  Implementar roles (`admin` y `viewer`) y restringir endpoints administrativos exclusivamente a administradores.
* **Cómo solucionarlo:**
  1. En `models.py`, agregar a `User`: `role = Column(String(20), nullable=False, default="viewer")`.
  2. En `auth.py`, crear la dependencia `require_role(allowed_roles)`.
  3. Proteger endpoints: `POST /users`, `DELETE /users/{id}`, `POST /wazuh-connections`, `DELETE /wazuh-connections/{id}` exigiendo rol `admin`.
* **Dónde aplicar la solución:**
  * `vuln-api/app/models.py`
  * `vuln-api/app/auth.py`
  * `vuln-api/app/main.py` (o routers)

---

### Tarea 5: Validación Estricta de Certificados TLS en Wazuh Client
* **Severidad en Rúbrica:** Media.
* **El Problema:**
  `VERIFY_SSL` venía en `False`, omitiendo la verificación TLS hacia el indexador Wazuh (riesgo MitM).
* **Lo que hay que solucionar:**
  Forzar `VERIFY_SSL=True` por defecto y permitir configurar certificados CA personalizados.
* **Cómo solucionarlo:**
  1. En `wazuh_client.py`, asegurar que `VERIFY_SSL = os.getenv("VERIFY_SSL", "True").lower() == "true"` use `True` por defecto.
  2. Agregar soporte para `WAZUH_CA_BUNDLE` para pasar una ruta de certificado al parámetro `verify` de `requests.post`.
* **Dónde aplicar la solución:**
  * `vuln-api/app/wazuh_client.py` (Línea 7)
  * `.env.example`

---

# BLOQUE 2: ESCALABILIDAD EN BASE DE DATOS Y BACKEND

---

### Tarea 6: Activación Real de TimescaleDB y Modelado de Hypertable
* **Severidad en Rúbrica:** Crítica.
* **El Problema:**
  1. `docker-compose.yml` usa `postgres:15` estándar en vez de TimescaleDB.
  2. El script `db-init/10-init.sql` nunca se montó en Docker.
  3. TimescaleDB exige que la columna temporal (`detected_at`) forme parte de la clave primaria y de cualquier `UniqueConstraint`. En `models.py`, `WazuhVulnerability` omite `detected_at` en su PK y en `uniq_wazuh_vuln`.
* **Lo que hay que solucionar:**
  Activar TimescaleDB, montar los scripts SQL y hacer el modelo compatible con Hypertables.
* **Cómo solucionarlo:**
  1. En `docker-compose.yml` (y plantillas de `prod_config/`), cambiar imagen a `timescale/timescaledb:latest-pg15`.
  2. Montar volumen `- ./db-init:/docker-entrypoint-initdb.d:ro`.
  3. En `models.py`, definir en `WazuhVulnerability`:
     * Clave primaria compuesta: `PrimaryKeyConstraint('id', 'detected_at')`.
     * `UniqueConstraint("connection_id", "agent_id", "package_name", "package_version", "cve_id", "detected_at", name="uniq_wazuh_vuln")`.
  4. En `db-init/10-init.sql`, agregar `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.
* **Dónde aplicar la solución:**
  * `docker-compose.yml`
  * `prod_config/docker-compose.*.yml`
  * `vuln-api/app/models.py`
  * `db-init/10-init.sql`

---

### Tarea 7: Funciones Almacenadas SQL (PL/pgSQL) para Métricas de Tiempo
* **Severidad en Rúbrica:** Media.
* **El Problema:**
  El cálculo de permanencia (*dwell time*) y antigüedad (*total age*) se realiza en el ORM de Python en vez de delegarse al motor de base de datos.
* **Lo que hay que solucionar:**
  Crear funciones PL/pgSQL en PostgreSQL para optimizar consultas por rangos.
* **Cómo solucionarlo:**
  1. En `db-init/10-init.sql`, definir `fn_calculate_dwell_time(p_first_seen, p_last_seen)` y `fn_calculate_total_age(p_first_seen)`.
  2. Invocar estas funciones en las consultas del backend (`func.fn_calculate_dwell_time(...)`).
* **Dónde aplicar la solución:**
  * `db-init/10-init.sql`
  * `vuln-api/app/main.py` (o `routers/vulns.py`)

---

### Tarea 8: Optimización de Sincronización Masiva Wazuh (Eliminar Cuello de Botella N+1)
* **Severidad en Rúbrica:** Crítica.
* **El Problema:**
  En `process_wazuh_vulnerabilities`, por cada vulnerabilidad de `raw_vulns` se ejecuta un `SELECT` individual y un `db.flush()` individual (10.000 viajes a la BD).
* **Lo que hay que solucionar:**
  Reemplazar el bucle individual por operaciones masivas en bloque (*bulk upsert*).
* **Cómo solucionarlo:**
  1. Cargar las vulnerabilidades existentes en un diccionario indexado por `(agent_id, package_name, package_version, cve_id)`.
  2. Clasificar en memoria registros nuevos y existentes.
  3. Insertar nuevos registros y eventos de `VulnerabilityHistory` mediante `bulk_save_objects` o sentencias `INSERT ... ON CONFLICT DO UPDATE` en un solo lote.
  4. Eliminar `db.flush()` dentro del ciclo `for`.
* **Dónde aplicar la solución:**
  * `vuln-api/app/main.py` (Líneas 376–450)

---

### Tarea 9: Paginación y Filtrado en Servidor en `GET /vulns`
* **Severidad en Rúbrica:** Crítica.
* **El Problema:**
  `GET /vulns` devuelve todas las filas y serializa todo el historial histórico, provocando N+1 en lazy loading.
* **Lo que hay que solucionar:**
  Convertir `GET /vulns` en un endpoint paginado en el servidor con filtros opcionales y desacoplar el historial.
* **Cómo solucionarlo:**
  1. Recibir parámetros: `page`, `page_size`, `connection_id`, `severity`, `status`, `search`.
  2. Aplicar filtros y paginación con `.offset((page - 1) * page_size).limit(page_size)`.
  3. Retornar estructura: `{"total": int, "page": int, "page_size": int, "items": list}`.
  4. Crear endpoint separado `GET /vulns/{id}/history` para cargar el detalle de historial bajo demanda.
* **Dónde aplicar la solución:**
  * `vuln-api/app/main.py` (Líneas 491–548)

---

# BLOQUE 3: ESCALABILIDAD EN FRONTEND

---

### Tarea 10: Refactorización de Dashboard.vue para Consumir Paginación del Servidor
* **Severidad en Rúbrica:** Crítica.
* **El Problema:**
  `Dashboard.vue` descarga todas las vulnerabilidades y hace filtros y paginación en el navegador, congelando la interfaz.
* **Lo que hay que solucionar:**
  Delegar la paginación y filtrado al backend y renderizar solo la página actual.
* **Cómo solucionarlo:**
  1. En `vulnService.js`, hacer que `getVulns(params)` envíe query params.
  2. En `Dashboard.vue`, conectar los controles de filtro y paginador para disparar peticiones al cambiar de página o criterio.
  3. Añadir indicador de carga (*loading spinner*).
* **Dónde aplicar la solución:**
  * `frontend/src/presentation/views/Dashboard.vue`
  * `frontend/src/application/services/vulnService.js`

---

### Tarea 11: Manejo y Alerta Visual de Truncamiento en useTimelineData.js
* **Severidad en Rúbrica:** Alta.
* **El Problema:**
  `const LIMIT = 2000` trunca los datos en silencio sin advertir al usuario.
* **Lo que hay que solucionar:**
  Alertar visiblemente al usuario cuando los datos visualizados alcancen el límite de registros.
* **Cómo solucionarlo:**
  1. En `useTimelineData.js`, activar `isTruncated = true` si los registros recibidos igualan o superan el límite.
  2. En `Timeline.vue`, mostrar un banner de advertencia si `isTruncated` es verdadero.
* **Dónde aplicar la solución:**
  * `frontend/src/presentation/views/timeline/useTimelineData.js`
  * `frontend/src/presentation/views/Timeline.vue`

---

# BLOQUE 4: ARQUITECTURA Y ORGANIZACIÓN DEL CÓDIGO

---

### Tarea 12: Desacoplamiento Modular del Monolito `main.py`
* **Severidad en Rúbrica:** Alta.
* **El Problema:**
  `main.py` concentra rutas, esquemas, servicios y sincronización en más de 540 líneas.
* **Lo que hay que solucionar:**
  Separar en arquitectura limpia por capas.
* **Cómo solucionarlo:**
  1. Crear `vuln-api/app/schemas/` (Pydantic models).
  2. Crear `vuln-api/app/routers/` (`auth_router.py`, `users_router.py`, `wazuh_router.py`, `vulns_router.py`).
  3. Crear `vuln-api/app/services/` (`wazuh_sync_service.py`).
  4. Implementar `vuln-api/app/repositories/vulnerability_repository.py`.
  5. En `main.py`, mantener solo la inicialización de FastAPI, CORS y el registro de routers.
* **Dónde aplicar la solución:**
  * `vuln-api/app/`

---

# BLOQUE 5: DEVSECOPS Y COBERTURA DE LA TOTALIDAD DEL REPOSITORIO

---

### Tarea 13: Pipeline de Integración Continua (CI) en GitHub Actions para Backend + Frontend
* **Severidad en Rúbrica:** Requisito Central de Evaluación (*"Operativo sobre la totalidad del repositorio"*).
* **El Problema:**
  El pipeline `.github/workflows/sonar.yml` solo analiza el backend y omite el frontend. Además, apunta a la cuenta personal de Stephan.
* **Lo que hay que solucionar:**
  Configurar el pipeline para que ejecute los tests de backend y de frontend, genere ambos reportes de cobertura y apruebe el Quality Gate en SonarCloud.
* **Cómo solucionarlo:**
  1. En `.github/workflows/sonar.yml`, agregar un paso de Node.js para ejecutar los tests del frontend con Vitest (`npm run test:run`) generando `frontend/coverage/lcov.info`.
  2. Pasar a SonarCloud ambos reportes de cobertura (`sonar.python.coverage.reportPaths` y `sonar.javascript.lcov.reportPaths`).
  3. Parametrizar `sonar.projectKey` y `sonar.organization` y configurar `SONAR_TOKEN` en GitHub Secrets.
* **Dónde aplicar la solución:**
  * `.github/workflows/sonar.yml`

---

### Tarea 14: Actualización y Creación de Tests Unitarios (Mantener Cobertura >= 80%)
* **Severidad en Rúbrica:** Requisito Central de Evaluación.
* **El Problema:**
  Al incorporar roles (RBAC), rate-limiting y cambiar modelos para TimescaleDB, los tests existentes pueden fallar o no cubrir la nueva funcionalidad, haciendo caer el Quality Gate.
* **Lo que hay que solucionar:**
  Actualizar los fixtures y agregar tests específicos para las nuevas funcionalidades de seguridad y paginación.
* **Cómo solucionarlo:**
  1. En `vuln-api/tests/conftest.py`, actualizar modelos para reflejar la columna `role` y clave compuesta.
  2. En `vuln-api/tests/test_api.py`, agregar tests para:
     * Rechazo por rate limit tras intentos fallidos.
     * Restricción de endpoints según rol (admin vs viewer).
     * Paginación en `/vulns`.
* **Dónde aplicar la solución:**
  * `vuln-api/tests/conftest.py`
  * `vuln-api/tests/test_api.py`

---

### Tarea 15: Reparación y Documentación de Herramientas Locales en `dev-tools/` (OWASP ZAP y SonarQube)
* **Severidad en Rúbrica:** Requisito Central de Evaluación.
* **El Problema:**
  `dev-tools/zap/docker-compose.yml` tiene la ruta quemada `/home/fabian/...`. SonarQube local no tiene instrucciones de ejecución claras.
* **Lo que hay que solucionar:**
  Corregir la ruta de OWASP ZAP a `./reports:/zap/wrk` y documentar en `dev-tools/README.md` cómo ejecutar SonarQube local en el puerto 9000.
* **Cómo solucionarlo:**
  1. En `dev-tools/zap/docker-compose.yml`, cambiar volumen a `./reports:/zap/wrk`.
  2. En `dev-tools/README.md`, documentar los comandos de arranque para SonarQube local.
* **Dónde aplicar la solución:**
  * `dev-tools/zap/docker-compose.yml`
  * `dev-tools/README.md`

---

# BLOQUE 6: EXPERIENCIA DE USUARIO Y REUNIONES CON CLIENTE

---

### Tarea 16: Correcciones de Interfaz y Usabilidad (Navegación, Logo y Clic Exterior)
* **Severidad en Rúbrica:** Requisito de Captura con el Cliente (Mencionado en `TODO.md`).
* **El Problema:**
  1. El logo superior no redirige a la vista principal.
  2. Los botones de zoom del Timeline no se cierran al hacer clic afuera (`clickOutside`).
  3. No existe un menú de perfil de usuario al hacer clic en el nombre en la esquina superior derecha.
* **Lo que hay que solucionar:**
  Resolver los 3 detalles de usabilidad en el frontend.
* **Cómo solucionarlo:**
  1. En la barra de navegación de `App.vue`, envolver el logo en `<router-link to="/dashboard">`.
  2. En `TimelineFilters.vue` o componentes del Timeline, aplicar la directiva `v-click-outside` para cerrar popovers al hacer clic fuera.
  3. En la barra superior, agregar un menú desplegable al hacer clic en el usuario con opción "Cerrar Sesión" y "Cambiar Contraseña".
* **Dónde aplicar la solución:**
  * `frontend/src/App.vue`
  * `frontend/src/presentation/views/timeline/components/TimelineFilters.vue`
  * `frontend/src/presentation/directives/clickOutside.js`

---

### Tarea 17: Visualización y Modo de Datos de Prueba Locales
* **Severidad en Rúbrica:** Requisito de Captura con el Cliente (Mencionado en `TODO.md`).
* **El Problema:**
  En entornos locales de demostración, no es posible ver datos en la interfaz sin contar con un agente Wazuh real conectado.
* **Lo que hay que solucionar:**
  Permitir que la interfaz cargue y visualice los datos importados de `datos_de_prueba_wazuh.json` de forma transparente.
* **Cómo solucionarlo:**
  Asegurar que los datos importados por `load-data.py` se muestren automáticamente en el Dashboard y Timeline seleccionando la conexión de prueba en el selector.
* **Dónde aplicar la solución:**
  * `frontend/src/presentation/views/Dashboard.vue`
  * `frontend/src/presentation/views/Timeline.vue`

---

# BLOQUE 7: LIMPIEZA Y CORRECCIÓN OPERATIVA

---

### Tarea 18: Reparación del Importador `load-data.py` y Limpieza de Residuos
* **Severidad en Rúbrica:** Operativa.
* **El Problema:**
  `load-data.py` no soporta argumentos de terminal (`--replace`), busca el archivo inexistente `seed_data.json` y existe un archivo residual de 0 bytes `git` en la raíz.
* **Lo que hay que solucionar:**
  Hacer que `load-data.py` soporte `--replace` y rutas personalizadas con fallback a `datos_de_prueba_wazuh.json`, y eliminar el archivo `git`.
* **Cómo solucionarlo:**
  1. En `load-data.py`, implementar `argparse` para aceptar `--replace` y un archivo JSON opcional (por defecto `datos_de_prueba_wazuh.json`).
  2. Eliminar el archivo vacío `git` de la raíz del proyecto.
* **Dónde aplicar la solución:**
  * `vuln-api/app/load-data.py`
  * Raíz del repositorio

---

# ORDEN CRONOLÓGICO Y GRAFO DE DEPENDENCIAS TÉCNICAS (18 PASOS)

A continuación se detalla el orden de ejecución óptimo basado estrictamente en **dependencias técnicas de código y arquitectura**. 

> **Principio de Desbloqueo Temprano:**  
> La **Tarea 18** (poblamiento de datos) y la **Tarea 12** (desacoplamiento modular del monolito `main.py`) se colocan en la **Fase 1** porque son los habilitadores de todo el equipo:
> 1. Si no se desacopla `main.py` primero, cualquier integrante que intente programar seguridad, paginación o sincronización colisionará en un único archivo de 540 líneas generando conflictos masivos de Git (*Merge Conflicts*).
> 2. Al crear de inmediato los directorios `routers/`, `schemas/` y `services/`, cada desarrollador pasa a trabajar en archivos completamente independientes.

---

```
                       [ GRAFO DE DEPENDENCIAS TÉCNICAS ]

 [Paso 1: Tarea 18 (Load-Data & Limpieza)]
       │
       ▼
 [Paso 2: Tarea 12 (Desacoplar main.py en Routers y Services)] ◄── ¡HABILITADOR CRÍTICO!
       │
       ├────────────────────────────────────────┬────────────────────────────────────────┐
       ▼                                        ▼                                        ▼
 [FASE 2: Base de Datos & TimescaleDB]   [FASE 3: Seguridad Backend]             [FASE 5: UX/UI Frontend]
 ├── Paso 3: Tarea 6 (Docker TimescaleDB)├── Paso 6: Tarea 1 (JWT Secret)        └── Paso 15: Tarea 16
 ├── Paso 4: Tarea 7 (PL/pgSQL DwellTime)├── Paso 7: Tarea 3 (.env.example)          (Logo & ClickOutside)
 └── Paso 5: Tarea 4 (Model User.role)   ├── Paso 8: Tarea 2 (Rate Limit Login)
       │                                 ├── Paso 9: Tarea 4 (RBAC Endpoints)
       │                                 └── Paso 10: Tarea 5 (Wazuh TLS Strict)
       ▼                                        │
 [FASE 4: Escalabilidad Backend]                │
 ├── Paso 11: Tarea 8 (Sync Masivo sin N+1) ────┘
 └── Paso 12: Tarea 9 (Paginación GET /vulns en Servidor)
       │
       ▼
 [FASE 5: Escalabilidad Frontend]
 ├── Paso 13: Tarea 10 (Dashboard.vue Paginado) ◄── (Depende estrictamente de Paso 12)
 ├── Paso 14: Tarea 11 (Timeline Alerta Límite)
 └── Paso 16: Tarea 17 (Visualizar Datos Locales)
       │
       ▼
 [FASE 6: CI/CD, Pruebas & Calidad Final]
 ├── Paso 17: Tarea 14 (Actualizar Tests Pytest >= 80% Cobertura)
 ├── Paso 18: Tarea 15 (Reparar OWASP ZAP & Documentar SonarQube)
 └── Paso 19: Tarea 13 (Pipeline GitHub Actions Backend + Frontend con Quality Gate Verde)
```

---

## DETALLE CRONOLÓGICO PASO A PASO Y DEPENDENCIAS

---

### FASE 1: HABILITACIÓN ARQUITECTÓNICA Y LIMPIEZA INICIAL

#### Paso 1: Tarea 18 - Reparación del importador `load-data.py` y eliminación de archivo `git`
* **Prerrequisitos / Dependencias:** Ninguno.
* **Qué desbloquea:** Permite que cualquier desarrollador pueda poblar y resetear su base de datos local en cualquier momento con `python vuln-api/app/load-data.py --replace` para hacer pruebas inmediatas sin depender de una conexión a Wazuh real.
* **Justificación:** Es la herramienta de soporte base para probar todo lo que viene a continuación.

#### Paso 2: Tarea 12 - Desacoplamiento modular del monolito `main.py`
* **Prerrequisitos / Dependencias:** Paso 1 (para poblar datos y probar que el split inicial no rompa ninguna ruta existente).
* **Qué desbloquea:** **Desbloqueo total del equipo.** Crea la estructura modular:
  * `vuln-api/app/schemas/`
  * `vuln-api/app/routers/` (`auth_router.py`, `users_router.py`, `wazuh_router.py`, `vulns_router.py`)
  * `vuln-api/app/services/` (`wazuh_sync_service.py`)
  * `vuln-api/app/repositories/`
* **Justificación:** Debe ser lo primero en el backend para que los integrantes puedan trabajar simultáneamente en ramas de Git separadas (uno en autenticación, otro en base de datos, otro en sincronización) sin tocar jamás el mismo archivo.

---

### FASE 2: CIMIENTOS DE BASE DE DATOS Y TIMESCALEDB

#### Paso 3: Tarea 6 - Activación real de TimescaleDB y Modelado de Hypertable
* **Prerrequisitos / Dependencias:** Paso 2 (los nuevos routers importan desde `models.py` y `db.py`).
* **Qué desbloquea:** Establece el motor `timescale/timescaledb:latest-pg15` en `docker-compose.yml`, monta `./db-init` y define la clave primaria compuesta `(id, detected_at)` en `models.py`.
* **Justificación:** El esquema de base de datos debe quedar congelado y correcto antes de escribir consultas avanzadas, funciones SQL o migraciones.

#### Paso 4: Tarea 7 - Funciones Almacenadas SQL (PL/pgSQL) para Métricas de Tiempo
* **Prerrequisitos / Dependencias:** Paso 3 (la base de datos y la tabla `wazuh_vulnerabilities` deben existir con sus tipos de datos definidos).
* **Qué desbloquea:** Crea `fn_calculate_dwell_time` y `fn_calculate_total_age` en PostgreSQL dentro de `10-init.sql`.
* **Justificación:** Deja disponibles las funciones nativas en base de datos para que el router de vulnerabilidades las consuma directamente.

#### Paso 5: Tarea 4 (Parte 1) - Sistema RBAC: Columna `role` en Modelo `User`
* **Prerrequisitos / Dependencias:** Paso 3 (se agrega la columna `role = Column(String(20), default="viewer")` en `models.py` mientras se está ajustando el modelo de base de datos).
* **Qué desbloquea:** Persistencia de roles en PostgreSQL para poder implementar el control de accesos.

---

### FASE 3: NÚCLEO DE SEGURIDAD Y AUTENTICACIÓN EN BACKEND

#### Paso 6: Tarea 1 - Corrección de Firma JWT (Secret Mismatch)
* **Prerrequisitos / Dependencias:** Paso 2 (`auth_router.py` y `auth.py` ya separados).
* **Qué desbloquea:** Unifica la lectura a `SECRET_KEY = os.getenv("SECRET_KEY")` y agrega validación *fail-fast*. Permite emitir tokens JWT válidos y legítimos.
* **Justificación:** Toda la seguridad de las demás rutas depende de que la firma de tokens sea criptográficamente segura.

#### Paso 7: Tarea 3 - Gestión Segura de Credenciales y Archivos de Entorno
* **Prerrequisitos / Dependencias:** Paso 6 (sincroniza los nombres de variables exactos en `.env.example`).
* **Qué desbloquea:** Asegura que `.gitignore` y `.dockerignore` bloqueen cualquier filtración de credenciales reales.

#### Paso 8: Tarea 2 - Control de Intentos en Login (Anti-Brute Force) y Aseguramiento de Admin
* **Prerrequisitos / Dependencias:** Paso 6 (la autenticación base de `auth_router.py` ya funciona).
* **Qué desbloquea:** Protege `/auth/login` con rate limiting/bloqueo de 5 intentos y asegura que la cuenta admin inicial deba cambiar credenciales obligatoriamente.

#### Paso 9: Tarea 4 (Parte 2) - Protección de Endpoints según Roles (`require_role`)
* **Prerrequisitos / Dependencias:** Paso 5 (columna `role` en BD) y Paso 6 (autenticación JWT funcional).
* **Qué desbloquea:** Protege los endpoints administrativos en `users_router.py` y `wazuh_router.py` con `Depends(require_role(["admin"]))`.

#### Paso 10: Tarea 5 - Validación Estricta de Certificados TLS en Wazuh Client
* **Prerrequisitos / Dependencias:** Paso 2 (`wazuh_client.py`).
* **Qué desbloquea:** Fuerza `VERIFY_SSL=True` por defecto y soporte para CA privada en conexiones contra el indexador de Wazuh.

---

### FASE 4: ESCALABILIDAD Y OPTIMIZACIÓN EN BACKEND

#### Paso 11: Tarea 8 - Optimización de Sincronización Masiva Wazuh (Eliminar Cuello de Botella N+1)
* **Prerrequisitos / Dependencias:** Paso 2 (`services/wazuh_sync_service.py`) y Paso 3 (modelo compatible con TimescaleDB).
* **Qué desbloquea:** Reemplaza el bucle de 10.000 `SELECT` individuales y `flush` por carga en memoria con `bulk_save_objects` o UPSERT nativo en `wazuh_sync_service.py`.
* **Justificación:** Elimina el cuello de botella más grave de la API antes de exponer las consultas al frontend.

#### Paso 12: Tarea 9 - Paginación y Filtrado en Servidor en `GET /vulns` y Desacoplamiento de Historial
* **Prerrequisitos / Dependencias:** Paso 4 (funciones SQL PL/pgSQL) y Paso 2 (`routers/vulns_router.py`).
* **Qué desbloquea:** Modifica `GET /vulns` para recibir `page`, `page_size`, `severity`, `search` y desacopla el historial a `GET /vulns/{id}/history`.
* **Justificación:** **Prerrequisito obligatorio para el Frontend.** El frontend no puede paginar por servidor hasta que este endpoint esté operativo.

---

### FASE 5: ESCALABILIDAD Y EXPERIENCIA DE USUARIO EN FRONTEND

#### Paso 13: Tarea 10 - Refactorización de `Dashboard.vue` para Consumir Paginación del Servidor
* **Prerrequisitos / Dependencias:** **Paso 12 (Dependencia estricta del backend paginado).**
* **Qué desbloquea:** Actualiza `vulnService.js` y `Dashboard.vue` para enviar query params de página y filtros, eliminando la paginación local en memoria del navegador.

#### Paso 14: Tarea 11 - Manejo y Alerta Visual de Truncamiento en `useTimelineData.js` y `Timeline.vue`
* **Prerrequisitos / Dependencias:** Paso 12 y Paso 2.
* **Qué desbloquea:** Detecta si la respuesta llega al límite de 2.000 registros y muestra un banner visual en `Timeline.vue` advirtiendo al usuario.

#### Paso 15: Tarea 16 - Correcciones de Interfaz y Usabilidad (Navegación, Logo y Clic Exterior)
* **Prerrequisitos / Dependencias:** Ninguna en backend. Puede realizarse en paralelo en cualquier momento dentro de `frontend/src/App.vue` y `TimelineFilters.vue`.
* **Qué desbloquea:** Resuelve los 3 detalles de usabilidad pedidos por el cliente en `TODO.md` (redirección del logo a `/dashboard`, cerrar menús con `clickOutside` y menú de usuario).

#### Paso 16: Tarea 17 - Visualización y Modo de Datos de Prueba Locales
* **Prerrequisitos / Dependencias:** Paso 1 (datos de prueba disponibles) y Paso 13 (Dashboard paginado listo).
* **Qué desbloquea:** Asegura que un evaluador pueda iniciar sesión localmente con datos precargados y ver tanto el Dashboard como el Timeline funcionando fluidamente.

---

### FASE 6: ASEGURAMIENTO DE CALIDAD, PIPELINE DEVSECOPS Y VALIDACIÓN FINAL

#### Paso 17: Tarea 14 - Actualización y Creación de Tests Unitarios (Mantener Cobertura >= 80%)
* **Prerrequisitos / Dependencias:** Pasos 2, 6, 8, 9 y 12 (todos los cambios de endpoints, roles y paginación deben estar terminados para escribir las pruebas definitivas).
* **Qué desbloquea:** Actualiza `conftest.py` y `test_api.py` para validar roles, rate limit y paginación, asegurando que `pytest` pase al 100% con alta cobertura.

#### Paso 18: Tarea 15 - Reparación y Documentación de Herramientas Locales en `dev-tools/` (OWASP ZAP y SonarQube)
* **Prerrequisitos / Dependencias:** Paso 3 (la infraestructura Docker base debe estar operativa).
* **Qué desbloquea:** Corrige el volumen `./reports:/zap/wrk` en `dev-tools/zap/docker-compose.yml` y documenta el arranque de SonarQube local en `dev-tools/README.md`.

#### Paso 19: Tarea 13 - Pipeline de Integración Continua (CI) en GitHub Actions con Quality Gate Verde
* **Prerrequisitos / Dependencias:** Paso 17 (los tests pasan localmente) y Paso 13 (el frontend compila limpiamente).
* **Qué desbloquea:** Configura `.github/workflows/sonar.yml` para ejecutar las pruebas del backend y del frontend (`npm run test:run`), enviando ambos reportes de cobertura a SonarCloud y logrando el check verde del **Quality Gate**.
* **Paso Final:** Ejecutar una prueba general de arranque limpio con `./iniciar_app.sh` (Opción 1) verificando que el sistema levante sin ningún error de consola.

