# Notas de integración frontend — Fase 2

`GET /vulns` cambió de contrato en la Fase 2. Devuelve una página y cada item
incluye su historial, para que la Timeline pueda reconstruir los intervalos
activos sin una petición por vulnerabilidad.

## Contrato

```http
GET /vulns?page=1&page_size=50
```

Parámetros opcionales:

- `page`: entero `>= 1`. Por defecto `1`.
- `page_size`: entero entre `1` y `500`. Por defecto `50`.
- `connection_id`: filtra por conexión.
- `agent_name`, `package_name`, `cve_id`, `tags`: repetibles
  (`?tags=prod&tags=web`). Dentro de un grupo se aplica OR; entre grupos, AND.
- `severity` / `status`: repetibles y sin distinguir mayúsculas
  (`?severity=HIGH&severity=CRITICAL`). Para "resueltas" enviar
  `status=RESOLVED&status=MITIGATED`; para "activas", `status=ACTIVE`.
- `score_min` / `score_max`: rango CVSS entre `0` y `10`.
- `search`: búsqueda insensible a mayúsculas en `cve_id`, `agent_id`,
  `agent_name`, `package_name` y `description`. `%` y `_` se buscan de forma
  literal.
- `date_from` / `date_to`: rango ISO 8601 sobre `detected_at`; `date_from` es
  inclusivo y `date_to` exclusivo.
- `sort_by`: campo de orden. Por defecto `last_seen`. Valores válidos:
  `last_seen`, `first_seen`, `detected_at`, `published_at`, `severity`,
  `score_base`, `cve_id`, `status`, `agent_name`, `agent_id`, `package_name`,
  `package_arch`, `os_full`, `scanner_vendor`, `connection_name`,
  `dwell_time_days`, `total_age_days` y `tags`.
- `sort_dir`: `asc` o `desc`. Por defecto `desc`. Un `sort_by` inválido devuelve
  `422`.

Respuesta:

```json
{
  "total": 300,
  "page": 1,
  "page_size": 50,
  "items": []
}
```

Cada elemento de `items` conserva los campos anteriores (`id`, `connection_name`,
`cve_id`, `severity`, `status`, `tags`, `first_seen`, `last_seen`,
`dwell_time_days`, `total_age_days`, etc.) e incluye `history` con las acciones
`DETECTED`, `REOPENED`, `RESOLVED`, etc. La lista se carga página a página (50
por defecto), así que la Timeline puede ir acumulando resultados sin pedir el
historial por ID.

El historial completo también sigue disponible para un detalle puntual:

```http
GET /vulns/{id}/history
```

`GET /vulns/events` queda para consultas de solo eventos por rango; la Timeline
no lo necesita si consume `history` desde el listado paginado.

## Migración mínima

En `vulnService.js`, mapear los parámetros de la UI al contrato nuevo:

```js
getVulns: async ({ page, pageSize, connectionId, agentNames, packageNames,
                   cveIds, tags, severities, statuses, scoreMin, scoreMax,
                   search, dateFrom, dateTo, sortBy, sortDir } = {}) => {
  const params = { page, page_size: pageSize, connection_id: connectionId,
                   agent_name: agentNames, package_name: packageNames,
                   cve_id: cveIds, tags, severity: severities, status: statuses,
                   score_min: scoreMin, score_max: scoreMax, search,
                   date_from: dateFrom, date_to: dateTo,
                   sort_by: sortBy, sort_dir: sortDir }
  Object.keys(params).forEach(key => params[key] == null && delete params[key])
  return apiClient.get('/vulns', {
    params,
    paramsSerializer: { indexes: null },
  })
}
```

En `Dashboard.vue`:

- Leer `res.data.items` y `res.data.total`.
- Enviar `page` y `page_size` al backend; eliminar el paginado local.
- Enviar también agentes, paquetes, CVEs, tags, severidades, score, búsqueda y
  orden. Los valores múltiples se envían repetidos; con Axios usar
  `paramsSerializer: { indexes: null }`.
- Traducir el estado de la UI: `active` -> `ACTIVE`; `resolved` ->
  `RESOLVED` + `MITIGATED`.
- Reiniciar `page` a `1` cuando cambie un filtro.
- Un cambio de `page_size`, filtros u orden requiere una nueva petición.
- Los desplegables de filtros no vienen en el listado paginado. Para opciones
  globales hace falta un endpoint de facetas o acumular el inventario completo;
  mientras tanto, se pueden construir con las páginas ya cargadas.

En `useTimelineData.js`:

- Consumir el `history` que viene dentro de cada item de `/vulns`.
- Cargar páginas de 50 en segundo plano y acumular `items` hasta cubrir el
  período o el `total`; no hace falta pedir `/vulns/{id}/history` por cada fila.
- Para el detalle puntual de una vulnerabilidad, `/vulns/{id}/history` sigue
  disponible.
- Si se prefiere una consulta de solo eventos por rango, `/vulns/events` sigue
  existiendo y se pagina con `limit`/`offset`.

En `ConfigUser.vue`:

- La carga con `limit: 500` ya no es válida. Para etiquetas se debe recorrer
  `page` hasta cubrir `total`, o agregar un endpoint específico de etiquetas si
  el volumen lo justifica.

## Impacto

El frontend actual espera un array en `GET /vulns`; con este cambio recibirá un
objeto. Dashboard, Timeline y la carga de etiquetas deben migrarse antes de
desplegar la Fase 2 en un entorno con usuarios. La API ya aplica en servidor los
filtros y el orden documentados arriba. La Timeline ya no necesita una petición
de historial por vulnerabilidad: el historial viene en cada item paginado.
