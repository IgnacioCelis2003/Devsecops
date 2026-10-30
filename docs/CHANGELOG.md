## Changelog del proyecto



### Resumen

Este documento recoge los cambios relevantes realizados durante el desarrollo del proyecto hasta el momento, centrados en la preparación del entorno local, la carga de datos de prueba, la integración con Wazuh, la seguridad en Git/Docker, la compatibilidad con la API/Frontend, la activación de TimescaleDB, la creación de la hypertable de eventos temporales y la emisión de eventos desde la sincronización.

---

### 1) Preparación de datos y carga local

- Se verificó que los datos de prueba no estaban en un formato correcto para la aplicación original (un JSON válido, pero guardado como `.md`).
- Se corrigió la carga de datos para que leyera el JSON correcto y no una ruta fija inexistente.
- Se añadió soporte para cargar datos desde una ruta configurada y con opción `--replace` para reconstruir la base local.
- Se actualizó la importación para normalizar etiquetas (`tags`) y datos Wazuh provenientes de distintos formatos.
- Se creó la lógica automática a través de `seed_data.py`, dejando el arranque local más sencillo y evitando depender del script manual `load-data.py`.
- El archivo activo para la carga automática es `vuln-api/app/datos_wazuh.json`.
- Se definió la estructura para que los usuarios y vulnerabilidades incluyeran atributos como `role`, `email` y `tags`.

---

### 2) Modelado de la base de datos y compatibilidad

- Se añadió el campo `tags` a `WazuhVulnerability` y a `User` para soportar etiquetas asociadas a usuarios y vulnerabilidades.
- Se creó `ensure_schema_compatibility()` en `db.py` para añadir columnas faltantes en bases de datos ya existentes, sin destruir datos actuales.
- Se dejó claro que esta compatibilidad es una solución temporal, y que para producción conviene migraciones formales.
- Se revisó la relación entre `wazuh_vulnerabilities` y `vulnerability_history`, y se decidió que la tabla de estado actual y la tabla de historial deben mantenerse separadas conceptualmente.

---

### 3) Integración con Wazuh y datos reales

- Se revisó la estructura real del JSON de Wazuh, que resulta ser una respuesta tipo OpenSearch/Indexer, con `hits.hits[*]._source` como contenido real de cada vulnerabilidad.
- Se confirmó que la librería cliente de Wazuh estaba haciendo scroll y paginación por batches, pero que aún no había una estrategia de carga por lotes en la base de datos.
- Se validó la estructura real de `datos_reales.json`, `agentes.json` y `grupos.json` para comprender que `agentes` y `grupos` son metadatos de agentes y no el cuerpo principal de vulnerabilidades.
- Se adaptó el trabajo para distinguir entre: el JSON de vulnerabilidades reales, el inventario de agentes y el metadata de grupos.
- Se preparó el flujo para que el normalizador pueda extraer `agent`, `host`, `package`, `vulnerability` y `wazuh` sin depender del formato de prueba ficticio del proyecto.

---

### 4) Frontend y API

- Se corrigió la respuesta de `/vulns` para devolver campos calculados como `dwell_time_days` y `total_age_days` usando expresiones SQL con `func.extract()` de SQLAlchemy.
- Se añadieron `offset` y `limit` para paginar la lectura de vulnerabilidades, evitando cargar todo el conjunto en memoria y en el navegador.
- Se mejoró el manejo de errores de login para distinguir errores HTTP reales de fallos de conexión o certs.
- Se añadió soporte para mostrar etiquetas (`tags`) en el Dashboard y en el detalle de la Timeline.
- Se actualizó `TimelineDetailModal` para mostrar etiquetas Wazuh junto al resto del contenido.
- Se revisó el acceso de usuarios y se dejó preparado el storage de `tags` en `User`, aunque aún no se implementa la restricción de visibilidad por etiquetas.

---

### 5) Seguridad y entorno local

- Se ampliaron `.gitignore` y `.dockerignore` para excluir `.env`, certificados, claves privadas, bases de datos locales, cachés, logs y artefactos de build.
- Se creó `.env.example` como plantilla segura para configuración local.
- Se corrigió la generación de certificados autofirmados y la inclusión de SAN para `localhost`, `127.0.0.1` y `::1`.
- Se ajustó la configuración CORS para permitir más orígenes locales y se evitó mostrar errores de conexión cuando el problema real era HTTP/SSL.
- Se revisó la compatibilidad con HTTPS y la necesidad de aceptar el certificado autofirmado en el navegador.
- Se dejaron preparadas las rutas para la ejecución con certificados locales en Docker y NGINX.

---

### 6) Docker y despliegue local

- Se revisó la estructura de `docker-compose.yml` para dejar la base de datos, la API y el frontend levantándose en orden.
- Se añadió permisos de certificados para la base de datos y se preparó el montaje del directorio de init SQL para Postgres.
- Se preparó el entorno para migrar con TimescaleDB mediante cambio de imagen y montaje de scripts; la activación real se completó en la Fase 0 (sección 9) y la hypertable de eventos en la Fase 1 (sección 10).
- Se revisó `prod_config/docker-compose.nodomain.yml` para intentar adaptar la infraestructura local con la base de datos y los certificados adecuados.
- Se dejó claro que a nivel de trabajo local hay que manejar el volumen de PostgreSQL con cuidado cuando la base ya estaba creada, porque los scripts de arranque solo se ejecutan si el volumen está vacío.

---

### 7) Arquitectura y rendimiento

- Se detectó el problema N+1 en la sincronización de Wazuh y se refactorizó la lógica para cargar una vez los registros existentes y luego comparar en memoria, en lugar de consultar la base por cada vulnerabilidad recibida.
- Se mejoró la lógica de detección de vulnerabilidades nuevas, reabiertas y resueltas para mantener el estado correcto sin consultar query por query.
- Se añadió carga perezosa y `selectinload`/`joinedload` para evitar consultas adicionales al visualizar `/vulns` y su historial.
- Se revisó la necesidad de implementar TimescaleDB, y se concluyó que la tabla actual `wazuh_vulnerabilities` no debe convertirse inmediatamente en hypertable; la decisión correcta es separar el estado actual de los eventos temporales.
- Se concluyó que una hypertable de eventos temporales es más apropiada para métricas y series temporales, mientras que la tabla actual sigue siendo el estado presente de cada vulnerabilidad.

---

### 8) Estado actual / pendientes

- El proyecto ya puede cargar datos locales y mostrar vulnerabilidades en la UI con etiquetas.
- Se ha trabajado con datos reales y se ha validado la estructura de OpenSearch/Wazuh como fuente de vulnerabilidades.
- La lógica de visibilidad por etiquetas aún no está implementada: la base de datos almacena `tags`, pero no hay ningún filtro en la API ni en el frontend para ocultar agentes o vulnerabilidades ajenos a un usuario.
- La extensión de TimescaleDB ya está activa y verificada (Fase 0) y la hypertable `vulnerability_events` ya existe con sus índices y funciones PL/pgSQL (Fase 1). La sincronización ya emite eventos y el seed los genera (Fase 2 parcial); falta el nuevo contrato de paginación server-side y adaptar el Dashboard y el Timeline.
- La seguridad de JWT, RBAC y validación avanzada aún requiere trabajo adicional si se quiere un sistema más robusto.

---

### 9) Activación de TimescaleDB (Fase 0)

- Se reemplazó la imagen `postgres:15` por `timescale/timescaledb:2.28.3-pg15` en `docker-compose.yml`, `prod_config/docker-compose.nodomain.yml` y `prod_config/docker-compose.domain.yml`, fijando una versión reproducible en lugar de usar `latest`.
- Se simplificó `db-init/10-init.sql` para crear únicamente la extensión `timescaledb` en la base definida por `POSTGRES_DB`. Se eliminaron el `CREATE DATABASE sonarqube` y el `\c vulnerabilidades_db` hardcodeado.
- Se agregó el montaje `./db-init:/docker-entrypoint-initdb.d:ro` en `prod_config/docker-compose.domain.yml`, que antes no inicializaba la extensión.
- Se ajustó `iniciar_app.sh` para asignar los certificados de la base de datos al UID 70, usuario `postgres` de la imagen Alpine de TimescaleDB, en lugar del UID 999 usado por la imagen Debian de PostgreSQL.
- Se añadió a `iniciar_app.sh` una validación de terminal interactiva y una autenticación única con `sudo -v` para evitar intentos fallidos repetidos y bloqueos por `pam_faillock` cuando el script se ejecuta sin TTY.
- Se verificó el arranque completo con Docker Compose: `db-api`, `api` y `frontend` en estado healthy, `timescaledb 2.28.3` activo, `shared_preload_libraries=timescaledb`, y carga correcta de 300 vulnerabilidades, 445 registros de historial y 4 usuarios.
- La base de datos se recreó desde cero y el volumen anterior se respaldó antes de eliminarlo.
- En esta fase `timescaledb_information.hypertables` devolvía 0 filas; la hypertable de eventos se creó en la Fase 1 (sección 10).
- Queda pendiente alinear el SSL de la base de datos en `prod_config/docker-compose.domain.yml`, ya que `vuln-api/app/db.py` fuerza `sslmode=require` y ese entorno todavía no monta certificados de base de datos.

---

### 10) Esquema SQL-only y hypertable de eventos (Fase 1)

- Se definió el esquema completo en `db-init/10-init.sql`, que pasa a ser la única fuente de verdad para PostgreSQL: tablas `users`, `wazuh_connections`, `user_interactions`, `wazuh_vulnerabilities`, `vulnerability_history` y `vulnerability_events`, más la extensión `timescaledb`, índices y funciones.
- Se creó `vulnerability_events` como hypertable de TimescaleDB sobre `event_time`, con `id BIGSERIAL`, `event_time`, `event_type`, `connection_id`, `vulnerability_id`, `agent_id`, `cve_id`, `severity`, `details JSONB` y restricción única `(id, event_time)`.
- Se añadieron índices temporales compuestos para las consultas previstas: por tipo, CVE, severidad, agente, conexión y vulnerabilidad, todos combinados con `event_time DESC`.
- Se mantuvo `wazuh_vulnerabilities` como estado actual y `vulnerability_history` como auditoría por vulnerabilidad; los eventos temporales se separan en la nueva hypertable para no romper las claves foráneas existentes.
- Se añadieron las funciones PL/pgSQL `fn_calculate_dwell_time`, `fn_calculate_total_age` y `fn_vulnerability_events_in_range` para centralizar el cálculo de tiempos y el filtrado por rango temporal.
- Se adoptó una gestión de esquema SQL-only, sin Alembic: al ser un entorno controlado y aceptar la recreación del volumen, `db-init` define el esquema y la aplicación no lo modifica en PostgreSQL.
- Se limitó `Base.metadata.create_all()` a SQLite (tests y desarrollo local) en `main.py` y `seed_data.py`, y se eliminó `ensure_schema_compatibility()` de `db.py` junto con sus imports.
- Se creó el modelo ORM `VulnerabilityEvent` en `vuln-api/app/models/vulnerability_event.py` y se registró en `vuln-api/app/models/__init__.py`.
- Se validó el DDL en una base temporal: hypertable creada, 8 índices, 3 funciones, inserción de un evento y resultados correctos de las funciones.
- Se recreó la base real desde cero (`docker compose down -v` + `up -d --build`): 6 tablas, hypertable activa, 300 vulnerabilidades, 445 registros de historial, 4 usuarios y 0 eventos; `api`, `db-api` y `frontend` sanos y endpoints `https://localhost/` y `/api/docs` con HTTP 200.
- Se ejecutaron los tests con SQLite: 64 pasaron. En el contenedor es necesario usar `SEED_EXAMPLE_DATA=false` para que el arranque de `TestClient` no consulte la base PostgreSQL de la API.
- Nota operativa: `db-init` solo se ejecuta cuando el volumen está vacío. Cualquier cambio de esquema requiere `docker compose down -v` y volver a levantar; el runbook debe reflejarlo.

---

### 11) Eventos temporales, funciones PL/pgSQL y endpoints (Fase 2, parcial)

- La sincronización de Wazuh ahora emite eventos en `vulnerability_events` para las transiciones `DETECTED`, `REOPENED`, `RESOLVED` y `SEVERITY_CHANGED`, además de mantener el historial de auditoría existente.
- Los eventos solo se generan en transiciones reales: sincronizaciones repetidas de una vulnerabilidad activa no crean eventos duplicados. También se deduplican las claves repetidas dentro de un mismo payload.
- El seed genera eventos a partir del historial cargado: 300 `DETECTED` y 145 `STATUS_CHANGED`, 445 eventos en total, con `event_time` histórico.
- Se añadió `GET /vulns/events` con filtros por `connection_id`, `event_type`, `agent_id`, `cve_id`, rango `from`/`to`, `limit` y `offset`. En PostgreSQL usa la función `fn_vulnerability_events_in_range`; en SQLite usa una consulta ORM equivalente para los tests.
- Se añadió `GET /vulns/{id}/history` como consulta puntual; el listado también conserva `history` en cada item.
- En PostgreSQL, `GET /vulns` calcula `dwell_time_days` y `total_age_days` con `fn_calculate_dwell_time` y `fn_calculate_total_age`; en SQLite se conserva el cálculo portable para los tests.
- Se actualizó `fn_vulnerability_events_in_range` para aceptar `p_from`/`p_to` nulos y no filtrar por rango cuando no se indican.
- Se añadieron tests de emisión de eventos, idempotencia, endpoints de eventos e historial. Resultado: 66 tests pasan con SQLite.
- Se recreó la base desde cero y se verificaron 445 eventos, 300 vulnerabilidades, 445 registros de historial, 4 usuarios, hypertable activa y endpoints `https://localhost/` y `/api/docs` con HTTP 200.
- El contrato de `GET /vulns` cambió en la Fase 2 a paginación server-side (`{total, page, page_size, items}`) e incluye `history` en cada item. El frontend debe adaptar Dashboard, Timeline y etiquetas; el contrato está documentado en `docs/FRONTEND_API_NOTES.md`.
- El cambio es incompatible con el frontend actual. No se modificó código frontend en esta fase.

---

### 12) Correcciones de la revisión (Must fix)

- Se corrigió `seed_database()` para avanzar las secuencias de PostgreSQL (`wazuh_vulnerabilities`, `vulnerability_history` y `user_interactions`) con `setval(pg_get_serial_sequence(...), MAX(id)+1, false)` después de insertar los IDs explícitos del seed. Sin esto, el primer sync que insertaba historial fallaba por clave duplicada (`id=1`) y las interacciones nuevas podían colisionar.
- Se cambiaron las claves foráneas de `vulnerability_events` hacia `wazuh_vulnerabilities` y `wazuh_connections` a `ON DELETE SET NULL` en `db-init/10-init.sql`, y se actualizó el modelo ORM `VulnerabilityEvent`. Al borrar una conexión, los eventos se conservan con las referencias en `NULL` y el endpoint de borrado deja de fallar.
- Se aplicó el cambio equivalente al volumen actual con `ALTER TABLE`; TimescaleDB propagó las restricciones a la tabla y a sus chunks. También se avanzaron las secuencias existentes (`401`, `446` y `25`). `db-init` queda correcto para volúmenes nuevos.
- Verificación: `confdeltype='n'` en las dos claves foráneas de la tabla y de cada chunk; secuencias en `max(id)+1`; 66 tests de SQLite pasan.

---

### 13) Fase 2 backend: paginación, historial desacoplado y sync masivo

- `GET /vulns` ahora usa `page`/`page_size` (máximo 500), devuelve `{total, page, page_size, items}` y aplica en servidor los filtros `connection_id`, `severity`, `status`, `search`, `date_from` y `date_to`.
- `search` es insensible a mayúsculas sobre CVE, agente, nombre de agente, paquete y descripción. `date_from`/`date_to` filtran `detected_at` con rango `[date_from, date_to)`.
- Se conserva `history` en cada item del listado paginado, para que la Timeline lo consuma sin N+1; el detalle puntual sigue en `GET /vulns/{id}/history`.
- La sincronización usa un único lote de actualizaciones con `bulk_update_mappings`; las vulnerabilidades nuevas se insertan con un solo `add_all` + `flush`. El historial y los eventos se siguen generando solo en transiciones reales.
- Se corrigió `frontend/tools-bd/load-data.py` para importar `app` desde `vuln-api` y cargar el `.env` de la raíz; `README.md` ahora ejecuta el loader dentro de la red de Compose con la ruta real.
- Se añadió `docs/FRONTEND_API_NOTES.md` con el contrato nuevo y la migración mínima de `vulnService`, Dashboard, Timeline y etiquetas.
- Verificación: 72 tests de SQLite pasan en el contenedor `devsecops-api`; el loader carga el seed completo en SQLite; una prueba de humo contra PostgreSQL real validó sync, paginación, filtros y `SEVERITY_CHANGED` con rollback al final.

---

### 14) Archivos principales tocados

- `vuln-api/app/seed_data.py`
- `vuln-api/app/db.py`
- `vuln-api/app/main.py`
- `vuln-api/app/models/__init__.py`
- `vuln-api/app/models/user.py`
- `vuln-api/app/models/wazuh_vulnerability.py`
- `vuln-api/app/models/vulnerability_event.py`
- `vuln-api/app/services/wazuh_sync_service.py`
- `vuln-api/app/routers/vulns_router.py`
- `vuln-api/tests/test_api.py`
- `docs/PLAN_TIMESCALEDB.md`
- `vuln-api/app/services/wazuh_sync_service.py`
- `vuln-api/app/routers/vulns_router.py`
- `vuln-api/app/clients/wazuh_client.py`
- `frontend/tools-bd/load-data.py`
- `README.md`
- `docs/FRONTEND_API_NOTES.md`
- `docker-compose.yml`
- `prod_config/docker-compose.nodomain.yml`
- `prod_config/docker-compose.domain.yml`
- `db-init/10-init.sql`
- `.gitignore`
- `.dockerignore`
- `.env.example`
- `iniciar_app.sh`
- `frontend/src/presentation/views/Dashboard.vue`
- `frontend/src/presentation/views/timeline/components/TimelineDetailModal.vue`

---

### 15) Correcciones de la revisión backend

- `GET /vulns` ahora filtra en servidor por `agent_name`, `package_name`, `cve_id`, `tags`, `severity`, `status`, `score_min` y `score_max`; los valores múltiples se envían repetidos y `severity`/`status` no distinguen mayúsculas.
- Se añadió orden server-side con `sort_by`/`sort_dir` para las columnas del Dashboard, incluyendo `connection_name`, severidad, score, tiempos y tags. Un campo inválido devuelve `422`.
- `search` escapa `%`, `_` y `\`, por lo que estos caracteres se buscan literalmente en vez de actuar como comodines SQL.
- La sincronización toma un `pg_advisory_xact_lock` por conexión en PostgreSQL. Dos syncs simultáneos de la misma conexión se serializan y el segundo vuelve a leer el estado ya confirmado, evitando eventos duplicados o inserciones en conflicto.
- Se añadieron tests de filtros avanzados, orden, escape de comodines y persistencia de metadata al crear (`agent_name`, `package_name`/`version`, `severity`, `score_base`, `tags`) y al actualizar (`severity`, `score_base`, `tags`, `agent_name`).
- Verificación: 72 tests de SQLite pasan en el contenedor `devsecops-api`. En un PostgreSQL 15 temporal se validaron el filtro de tags, el orden por longitud de tags y el bloqueo/liberación de `pg_advisory_xact_lock` entre dos sesiones.

---
 
### 16) Filtrado por Etiquetas de Agente (Agent Labels / Tags)
 
- Se implementó el filtrado de vulnerabilidades basado en las etiquetas (`tags`) asignadas al usuario y a cada agente/vulnerabilidad.
- Los usuarios con rol `viewer` ven restringida su vista únicamente a las vulnerabilidades que comparten al menos una etiqueta común con las etiquetas asignadas a su perfil; los administradores mantienen visibilidad global.
- Se actualizó el esquema de usuario (`NewUserRequest`/`UpdateUserRequest`) para gestionar `tags` y `role`.
- Se añadió el endpoint `PUT /users/{id}` (admin-only) para permitir la gestión de etiquetas y roles de usuario.
- Se validó la funcionalidad mediante tests unitarios, asegurando la compatibilidad con el filtrado en servidor ya existente.
 
---
 
### 17) Nota final

Este changelog recoge los cambios realizados hasta el momento de forma práctica y orientada al proyecto real. La rama de trabajo se ha centrado en dejar la aplicación usable localmente, con datos de prueba, TimescaleDB activo, la hypertable `vulnerability_events` creada, eventos emitidos desde la sincronización, funciones PL/pgSQL usadas por la API y el backend de Fase 2 con paginación server-side. El siguiente paso es adaptar el Dashboard, Timeline y etiquetas al contrato documentado en `docs/FRONTEND_API_NOTES.md`.
