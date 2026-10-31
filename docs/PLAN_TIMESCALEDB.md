# Plan de implementación TimescaleDB — VulnApp

> Estado: Fases 0 y 1 completadas. Fase 2 backend completada; la adaptación del frontend queda pendiente y su contrato está en `docs/FRONTEND_API_NOTES.md`.
> Última actualización: 2026-10-29

## Decisiones acordadas

- TimescaleDB se mantiene como motor de base de datos y se implementa con hypertable, índices y funciones PL/pgSQL.
- La hypertable será `vulnerability_events`; `wazuh_vulnerabilities` seguirá siendo el estado actual de cada vulnerabilidad.
- `vulnerability_history` se conserva como auditoría por vulnerabilidad. `vulnerability_events` será la fuente temporal para métricas y Timeline.
- La gestión del esquema será SQL-only: todo el DDL vive en `db-init/`.
- No se usará Alembic. El entorno es controlado y no se preservan datos entre despliegues.
- Se conservan todos los datos: no se crearán políticas de retención, compresión ni agregados continuos, y no se fijará un intervalo de chunk explícito. Se usará el valor por defecto de TimescaleDB.
- No se implementará un guard automático de limpieza de BD. Los scripts de `db-init` solo se ejecutan con el volumen vacío; el runbook documentará que hay que recrear el volumen cuando cambie el esquema.
- Si en el futuro se necesita preservar datos o actualizar sin recrear la BD, se evaluará introducir Alembic usando este esquema SQL como baseline.
- Reparto de trabajo: el backend de Fase 2 quedó implementado; la adaptación del Dashboard, Timeline y etiquetas queda para el integrante de frontend usando `docs/FRONTEND_API_NOTES.md`.
- Para la carga objetivo de 25k no se requiere un cambio arquitectónico: la paginación server-side y el upsert masivo de Fase 2 cubren el caso. La validación con `EXPLAIN (ANALYZE, BUFFERS)` se añade a Fase 4; si la función de eventos sigue siendo el cuello de botella, se evaluará empujar los filtros y el límite a SQL.

## Fase 0 — Activación de TimescaleDB (completada)

- [x] Cambiar `postgres:15` por `timescale/timescaledb:2.28.3-pg15` en los tres compose.
- [x] Simplificar `db-init/10-init.sql` para crear solo la extensión en `POSTGRES_DB`.
- [x] Eliminar `CREATE DATABASE sonarqube` y el `\c vulnerabilidades_db` hardcodeado.
- [x] Añadir el mount `./db-init:/docker-entrypoint-initdb.d:ro` en `prod_config/docker-compose.domain.yml`.
- [x] Ajustar los certificados de BD al UID 70 de la imagen Alpine de TimescaleDB.
- [x] Añadir guardia de terminal interactiva y `sudo -v` en `iniciar_app.sh`.
- [x] Verificar extensión `timescaledb 2.28.3`, `shared_preload_libraries=timescaledb` y servicios healthy.
- [x] Verificar carga de 300 vulnerabilidades, 445 historial y 4 usuarios.
- [x] Documentar la Fase 0 en `docs/CHANGELOG.md`.

## Fase 1 — Esquema SQL-only + implementación TimescaleDB (completada)

### 1.1 Esquema SQL

- [x] Mover a `db-init/10-init.sql` el DDL de las 5 tablas actuales:
  - `users`
  - `user_interactions`
  - `wazuh_connections`
  - `wazuh_vulnerabilities`
  - `vulnerability_history`
- [x] Crear la tabla `vulnerability_events`:
  - `id BIGSERIAL`
  - `event_time TIMESTAMPTZ NOT NULL DEFAULT now()`
  - `event_type VARCHAR NOT NULL`
  - `vulnerability_id INTEGER`
  - `connection_id INTEGER`
  - `agent_id VARCHAR`
  - `cve_id TEXT`
  - `severity TEXT`
  - `status TEXT`
  - `details JSONB`
  - `UNIQUE (id, event_time)`
- [x] Convertirla en hypertable:
  `create_hypertable('vulnerability_events', 'event_time', if_not_exists => TRUE);`
- [x] Añadir índices de estado actual en `wazuh_vulnerabilities`:
  - `status`
  - `severity`
  - `last_seen DESC`
  - `(connection_id, last_seen DESC)`
  - `cve_id`
- [x] Añadir índices temporales en `vulnerability_events`:
  - `(vulnerability_id, event_time DESC)`
  - `(connection_id, event_time DESC)`
  - `(agent_id, event_time DESC)`
  - `(cve_id, event_time DESC)`
  - `(severity, event_time DESC)`
  - `(event_type, event_time DESC)`
- [x] Crear funciones PL/pgSQL:
  - `fn_calculate_dwell_time(p_first_seen, p_last_seen)`
  - `fn_calculate_total_age(p_first_seen)`
  - `fn_vulnerability_events_in_range(p_connection_id, p_from, p_to)`
- [x] Mantener `db-init/10-init.sql` como archivo principal para que coincida con la referencia de la rúbrica.
- [x] Escribir el DDL de forma idempotente (`IF NOT EXISTS`, `CREATE OR REPLACE`) para que pueda reaplicarse manualmente sin romper el arranque.

### 1.2 Modelo ORM

- [x] Crear `vuln-api/app/models/vulnerability_event.py`.
- [x] Usar `JSONB` en PostgreSQL y `JSON` en SQLite para `details`.
- [x] Registrarlo en `vuln-api/app/models/__init__.py`.
- [x] Verificar que el modelo coincida con el DDL SQL.

### 1.3 Eliminar la creación implícita de esquema en PostgreSQL

- [x] Quitar `Base.metadata.create_all` de `main.py:28-29`.
- [x] Quitar `create_all` de `seed_data.py:53`.
- [x] Retirar `ensure_schema_compatibility` de `db.py` y de sus llamadas.
- [x] Mantener `create_all` únicamente para tests con SQLite.

### 1.4 Verificación de la Fase 1

- [x] Partir de volumen vacío y levantar el stack.
- [x] Confirmar extensión activa.
- [x] Confirmar `vulnerability_events` en `timescaledb_information.hypertables`.
- [x] Confirmar índices y funciones.
- [x] Confirmar que la API arranca y que el seed funciona.
- [x] Ejecutar tests con SQLite para verificar que no se rompió el camino de tests.

## Fase 2 — Backend, API y sincronización (backend completado)

- [x] Reemplazar las actualizaciones por ORM del bucle de sincronización por un lote `bulk_update_mappings`; las inserciones nuevas siguen usando un único `add_all` + `flush`.
- [x] Emitir eventos en `vulnerability_events` para `DETECTED`, `REOPENED`, `RESOLVED` y `SEVERITY_CHANGED`.
- [x] Evitar eventos duplicados en sincronizaciones repetidas.
- [x] Cambiar `GET /vulns` a paginación server-side:
  - `page` (`>= 1`, por defecto `1`) y `page_size` (`1..500`, por defecto `50`)
  - `connection_id`, `severity`, `status`, `search`, `date_from`, `date_to`
  - `date_from`/`date_to` filtran `detected_at`; el rango es `[date_from, date_to)`
  - respuesta `{total, page, page_size, items}`
- [x] Mantener el historial embebido en cada item de `GET /vulns` paginado, para que la Timeline lo consuma sin N+1.
- [x] Crear `GET /vulns/{id}/history`.
- [x] Crear `GET /vulns/events` para la Timeline con filtros por rango.
- [x] Usar las funciones PL/pgSQL para dwell time y edad.
- [x] Actualizar el seed para generar eventos e historial.
- [x] Corregir `README.md:48` y el import de `frontend/tools-bd/load-data.py`.
- [x] Coordinar con frontend el nuevo contrato de Dashboard y Timeline en `docs/FRONTEND_API_NOTES.md`.

## Fase 3 — Operación y despliegue

- [ ] Resolver el SSL de `docker-compose.domain.yml`: alinear `db.py` con `sslmode` configurable o montar certificados.
- [ ] Añadir a `db.py`: `pool_pre_ping`, `pool_recycle`, timeouts y límites de pool.
- [ ] Añadir endpoint `/health` con `SELECT 1` y usarlo en el healthcheck de la API.
- [ ] Crear scripts de backup/restore con `pg_dump`/`pg_restore`.
- [ ] Documentar el procedimiento de despliegue:
  `git pull && docker compose down -v && docker compose up -d --build`
- [ ] Documentar que sin `down -v` los scripts de `db-init` no se re-ejecutan y el esquema nuevo no se aplica.
- [ ] Evaluar si cambiar la opción 2 de `iniciar_app.sh` para que use `down -v` con confirmación.
- [ ] Añadir logging de consultas lentas y verificación de políticas de Timescale.

## Fase 4 — Tests y CI

- [ ] Añadir tests de integración contra TimescaleDB real.
- [ ] Verificar desde BD vacía: extensión, tablas, hypertable, índices, funciones y políticas.
- [ ] Probar paginación, filtros, historial y timeline.
- [ ] Probar que el sync sea idempotente.
- [ ] Medir sync y `GET /vulns` con 25k registros usando `EXPLAIN (ANALYZE, BUFFERS)`; optimizar `fn_vulnerability_events_in_range` si el plan lo requiere.
- [ ] Añadir TimescaleDB como servicio en GitHub Actions.
- [ ] Aplicar `db-init/10-init.sql` en CI antes de pytest.
- [ ] Mantener SQLite solo para unit tests rápidos.

## Fase 5 — Documentación

- [x] Actualizar `docs/CHANGELOG.md` con la decisión SQL-only y la Fase 1.
- [ ] Actualizar `README.md` con instalación, reset de BD, endpoints y backups.
- [ ] Crear un runbook de base de datos en `docs/DATABASE.md`.
- [ ] Marcar en `TODO.md` y `TAREAS_PEP1_DEVSECOPS.md` lo completado.

## Criterios de aceptación globales

- [ ] Un volumen vacío levanta extensión, tablas, hypertable, índices y funciones.
- [ ] `timescaledb_information.hypertables` muestra `vulnerability_events`.
- [ ] Las funciones `fn_*` existen y se usan desde la API.
- [x] `GET /vulns` pagina y filtra en servidor.
- [x] `GET /vulns/{id}/history` y `GET /vulns/events` funcionan.
- [ ] El sync es idempotente y no genera eventos duplicados.
- [ ] La API está healthy y los tests de integración pasan.
- [ ] El procedimiento de despliegue y reset está documentado.

## Decisiones pendientes

- [ ] Definir estrategia SSL para domain (Fase 3).
- [x] Definir contrato final de filtros y respuesta con frontend (`docs/FRONTEND_API_NOTES.md`).
- [ ] Evaluar tabla `schema_version` para detectar esquemas desactualizados.
- [ ] Confirmar si `vulnerability_history` se mantiene indefinidamente como auditoría.

## Riesgos

- Los scripts de `db-init` solo corren con volumen vacío; sin reset no hay migración.
- El DDL SQL y los modelos SQLAlchemy pueden desincronizarse.
- La FK de `vulnerability_events` hacia `wazuh_vulnerabilities` debe validarse con TimescaleDB.
- Cambiar el contrato de `/vulns` requiere coordinar frontend.
- El SSL de domain sigue pendiente y hoy `db.py` fuerza `sslmode=require`.
