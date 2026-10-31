import apiClient from '../../infrastructure/http/apiClient';

export default {
  getVulns: async (params = {}) => {
    const queryParams = {}

    // Paginación server-side
    if (params.page !== undefined && params.page !== null) {
      queryParams.page = params.page
    }

    if (params.pageSize !== undefined && params.pageSize !== null) {
      queryParams.page_size = params.pageSize
    } else if (params.page_size !== undefined && params.page_size !== null) {
      queryParams.page_size = params.page_size
    } else if (params.limit !== undefined && params.limit !== null) {
      queryParams.page_size = Math.min(params.limit, 500)
    }

    if (params.offset !== undefined && params.offset !== null) {
      queryParams.offset = params.offset
    }

    // Conexión
    if (params.connectionId !== undefined && params.connectionId !== null && params.connectionId !== '') {
      queryParams.connection_id = params.connectionId
    } else if (params.connection_id !== undefined && params.connection_id !== null && params.connection_id !== '') {
      queryParams.connection_id = params.connection_id
    }

    // Búsqueda y Ordenamiento
    if (params.search) {
      queryParams.search = params.search
    }
    if (params.sortBy) {
      queryParams.sort_by = params.sortBy
    } else if (params.sort_by) {
      queryParams.sort_by = params.sort_by
    }
    if (params.sortDir) {
      queryParams.sort_dir = params.sortDir
    } else if (params.sort_dir) {
      queryParams.sort_dir = params.sort_dir
    }

    // Filtros de severidad, estado y tags
    if (params.severity) {
      queryParams.severity = params.severity
    }
    if (params.status) {
      queryParams.status = params.status
    }
    if (params.tags) {
      queryParams.tags = params.tags
    }

    // Agentes, CVEs y paquetes
    if (params.agentNames) {
      queryParams.agent_name = params.agentNames
    } else if (params.agent_name) {
      queryParams.agent_name = params.agent_name
    }

    if (params.cveIds) {
      queryParams.cve_id = params.cveIds
    } else if (params.cve_id) {
      queryParams.cve_id = params.cve_id
    }

    if (params.packageNames) {
      queryParams.package_name = params.packageNames
    } else if (params.package_name) {
      queryParams.package_name = params.package_name
    }

    // Rango CVSS
    if (params.scoreMin !== undefined && params.scoreMin !== null && params.scoreMin !== '') {
      queryParams.score_min = params.scoreMin
    } else if (params.score_min !== undefined && params.score_min !== null && params.score_min !== '') {
      queryParams.score_min = params.score_min
    }

    if (params.scoreMax !== undefined && params.scoreMax !== null && params.scoreMax !== '') {
      queryParams.score_max = params.scoreMax
    } else if (params.score_max !== undefined && params.score_max !== null && params.score_max !== '') {
      queryParams.score_max = params.score_max
    }

    // Fechas
    if (params.dateFrom) queryParams.date_from = params.dateFrom
    else if (params.date_from) queryParams.date_from = params.date_from

    if (params.dateTo) queryParams.date_to = params.dateTo
    else if (params.date_to) queryParams.date_to = params.date_to

    const config = {
      params: queryParams,
      paramsSerializer: { indexes: null },
    }

    return apiClient.get('/vulns', config)
  },

  syncVulns: async () => {
    return apiClient.post('/vulns/sync-all')
  },
}
