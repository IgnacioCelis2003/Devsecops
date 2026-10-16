import apiClient from '../../infrastructure/http/apiClient';

export default {
  getVulns: async (params = {}) => {
    const queryParams = {}

    if (params.limit !== undefined && params.limit !== null) {
      queryParams.limit = params.limit
    }

    if (params.offset !== undefined && params.offset !== null) {
      queryParams.offset = params.offset
    }

    if (params.connectionId !== undefined && params.connectionId !== null) {
      queryParams.connection_id = params.connectionId
    } else if (params.connection_id !== undefined && params.connection_id !== null) {
      queryParams.connection_id = params.connection_id
    }

    return apiClient.get('/vulns', {
      params: queryParams,
    })
  },

  syncVulns: async () => {
    return apiClient.post('/vulns/sync-all')
  },
}
