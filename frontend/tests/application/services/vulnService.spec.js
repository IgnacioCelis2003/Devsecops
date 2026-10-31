import { describe, it, expect, vi } from 'vitest'
import vulnService from '@/application/services/vulnService'
import apiClient from '@/infrastructure/http/apiClient'

// Mock the apiClient module
vi.mock('@/infrastructure/http/apiClient', () => {
    return {
        default: {
            get: vi.fn(),
            post: vi.fn(),
        }
    }
})

describe('vulnService.js', () => {

    it('getVulns calls apiClient.get with default params when empty', async () => {
        const mockResponse = { data: [] }
        apiClient.get.mockResolvedValueOnce(mockResponse)

        const result = await vulnService.getVulns()

        expect(apiClient.get).toHaveBeenCalledWith('/vulns', {
            params: {},
            paramsSerializer: { indexes: null }
        })
        expect(result).toEqual(mockResponse)
    })

    it('getVulns calls apiClient.get with specific params', async () => {
        const mockResponse = { data: [] }
        apiClient.get.mockResolvedValueOnce(mockResponse)

        const result = await vulnService.getVulns({ limit: 50, connectionId: 2 })

        expect(apiClient.get).toHaveBeenCalledWith('/vulns', {
            params: {
                page_size: 50,
                connection_id: 2,
            },
            paramsSerializer: { indexes: null }
        })
        expect(result).toEqual(mockResponse)
    })

    it('getVulns supports server-side pagination, search and sort params', async () => {
        const mockResponse = { data: { total: 100, page: 2, page_size: 25, items: [] } }
        apiClient.get.mockResolvedValueOnce(mockResponse)

        const result = await vulnService.getVulns({
            page: 2,
            pageSize: 25,
            search: 'CVE-2023',
            sortBy: 'severity',
            sortDir: 'asc'
        })

        expect(apiClient.get).toHaveBeenCalledWith('/vulns', {
            params: {
                page: 2,
                page_size: 25,
                search: 'CVE-2023',
                sort_by: 'severity',
                sort_dir: 'asc',
            },
            paramsSerializer: { indexes: null }
        })
        expect(result).toEqual(mockResponse)
    })

    it('syncVulns calls apiClient.post on /vulns/sync-all', async () => {
        const mockResponse = { data: { synced: 10 } }

        apiClient.post.mockResolvedValueOnce(mockResponse)

        const result = await vulnService.syncVulns()

        expect(apiClient.post).toHaveBeenCalledWith('/vulns/sync-all')
        expect(result).toEqual(mockResponse)
    })
})
