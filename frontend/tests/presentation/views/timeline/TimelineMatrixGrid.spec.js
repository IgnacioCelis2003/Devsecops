import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineMatrixGrid from '@/presentation/views/timeline/components/TimelineMatrixGrid.vue'

describe('TimelineMatrixGrid.vue', () => {
  const mockVulns = [
    {
      id: 1,
      cve_id: 'CVE-2023-1234',
      severity: 'critical',
      score_base: 9.8,
      package_name: 'bash',
      agent_name: 'srv-db',
      status: 'ACTIVE',
      first_seen: '2026-01-10T00:00:00.000Z',
      last_seen: '2026-03-20T00:00:00.000Z'
    },
    {
      id: 2,
      cve_id: 'CVE-2023-5678',
      severity: 'medium',
      score_base: 5.5,
      package_name: 'curl',
      agent_name: 'srv-web',
      status: 'RESOLVED',
      first_seen: '2026-02-01T00:00:00.000Z',
      last_seen: '2026-02-15T00:00:00.000Z',
      history: [
        { action: 'RESOLVED', timestamp: '2026-02-15T12:00:00.000Z' }
      ]
    },
    {
      id: 3,
      cve_id: 'CVE-2023-9999',
      severity: 'high',
      score_base: 7.5,
      package_name: 'openssl',
      agent_name: 'srv-db',
      status: 'MITIGATED',
      first_seen: '2026-01-05T00:00:00.000Z',
      last_seen: '2026-01-25T00:00:00.000Z',
      history: [
        { action: 'STATUS_CHANGED', details: 'Mitigated rule', timestamp: '2026-01-20T00:00:00.000Z' }
      ]
    }
  ]

  const defaultProps = {
    vulns: mockVulns,
    loading: false,
    connections: [{ id: 1, name: 'Conn Prod' }],
    selectedConnection: 1,
    agentOptions: ['srv-db', 'srv-web'],
    selectedAgents: [],
    severityOptions: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
    selectedSeverities: [],
    tagOptions: ['prod', 'linux'],
    selectedTags: [],
    selectedStatus: 'all',
    totalRecords: 3,
    activeCount: 1,
    mitigatedCount: 1,
    resolvedCount: 1,
    currentPage: 1,
    totalPages: 1,
    itemsPerPage: 50,
    perPageOptions: [10, 25, 50]
  }

  it('renders correctly with metrics and rows', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    expect(wrapper.text()).toContain('Total:')
    expect(wrapper.text()).toContain('Activas:')
    expect(wrapper.text()).toContain('Resueltas:')
    expect(wrapper.findAll('.matrix-row').length).toBe(3)
  })

  it('steps year forward and backward', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    const initialYear = wrapper.vm.selectedYear
    wrapper.vm.stepYear(1)
    expect(wrapper.vm.selectedYear).toBe(initialYear + 1)

    wrapper.vm.stepYear(-2)
    expect(wrapper.vm.selectedYear).toBe(initialYear - 1)
  })

  it('applies direct year input and validates range', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.yearInputValue = 2030
    wrapper.vm.applyYearInput()
    expect(wrapper.vm.selectedYear).toBe(2030)

    wrapper.vm.yearInputValue = 1800
    wrapper.vm.applyYearInput()
    expect(wrapper.vm.selectedYear).toBe(2030)
  })

  it('toggles year decade picker and selects decade year', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.toggleYearPicker()
    expect(wrapper.vm.dropdowns.yearPicker).toBe(true)

    wrapper.vm.selectYearFromPicker(2028)
    expect(wrapper.vm.selectedYear).toBe(2028)
    expect(wrapper.vm.dropdowns.yearPicker).toBe(false)
  })

  it('navigates decades forward and backward', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    const initialDecade = wrapper.vm.decadeStart
    wrapper.vm.decadeStart += 10
    expect(wrapper.vm.decadeStart).toBe(initialDecade + 10)
    wrapper.vm.decadeStart -= 20
    expect(wrapper.vm.decadeStart).toBe(initialDecade - 10)
  })

  it('toggles isDetailedView between compact and detailed view', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    expect(wrapper.vm.isDetailedView).toBe(true)
    wrapper.vm.isDetailedView = false
    expect(wrapper.vm.isDetailedView).toBe(false)
  })

  it('toggles severity filter and emits update', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: {
        ...defaultProps,
        selectedSeverities: ['CRITICAL']
      }
    })

    wrapper.vm.toggleSeverity('HIGH')
    expect(wrapper.emitted('update:selected-severities')?.[0]).toEqual([['CRITICAL', 'HIGH']])

    wrapper.vm.toggleSeverity('CRITICAL')
    expect(wrapper.emitted('update:selected-severities')?.[1]).toEqual([[]])
  })

  it('toggles agent and tag filters', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.toggleAgent('srv-db')
    expect(wrapper.emitted('update:selected-agents')?.[0]).toEqual([['srv-db']])

    wrapper.vm.toggleTag('prod')
    expect(wrapper.emitted('update:selected-tags')?.[0]).toEqual([['prod']])
  })

  it('filters agents and tags by search inputs', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.search.agent = 'db'
    expect(wrapper.vm.filteredAgents).toEqual(['srv-db'])

    wrapper.vm.search.tag = 'lin'
    expect(wrapper.vm.filteredTags).toEqual(['linux'])
  })

  it('emits select-vuln on onVulnClick', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.onVulnClick(1)
    expect(wrapper.emitted('select-vuln')?.[0]).toEqual([1])
  })

  it('switches granularity between year, month, and range', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.granularity = 'month'
    wrapper.vm.selectedMonth = 1
    expect(wrapper.vm.granularity).toBe('month')
    expect(wrapper.vm.timeColumns.length).toBeGreaterThan(0)

    wrapper.vm.granularity = 'range'
    wrapper.vm.rangeStartDate = '2026-03-01'
    wrapper.vm.rangeEndDate = '2026-03-10'
    expect(wrapper.vm.granularity).toBe('range')
    expect(wrapper.vm.timeColumns.length).toBe(10)

    wrapper.vm.granularity = 'year'
    expect(wrapper.vm.granularity).toBe('year')
    expect(wrapper.vm.timeColumns.length).toBe(12)
  })

  it('manages date range changes and adjustments', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    // Start date change adjustments
    wrapper.vm.rangeStartDate = '2026-01-01'
    wrapper.vm.rangeEndDate = ''
    wrapper.vm.onStartDateChange()
    expect(wrapper.vm.rangeEndDate).toBe('2026-01-31')

    wrapper.vm.rangeStartDate = '2026-02-01'
    wrapper.vm.rangeEndDate = '2026-01-01' // Diff < 0
    wrapper.vm.onStartDateChange()
    expect(wrapper.vm.rangeEndDate).toBe('2026-03-03')

    // End date change adjustments
    wrapper.vm.rangeStartDate = ''
    wrapper.vm.rangeEndDate = '2026-05-31'
    wrapper.vm.onEndDateChange()
    expect(wrapper.vm.rangeStartDate).toBe('2026-05-01')

    wrapper.vm.clearDateRange()
    expect(wrapper.vm.rangeStartDate).toBe('')
    expect(wrapper.vm.rangeEndDate).toBe('')
  })

  it('clears all filters when resetAllFilters is called', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: {
        ...defaultProps,
        selectedStatus: 'active',
        selectedAgents: ['srv-db']
      }
    })

    expect(wrapper.vm.hasActiveFilters).toBe(true)

    wrapper.vm.resetAllFilters()
    expect(wrapper.emitted('update:selected-status')?.[0]).toEqual(['all'])
    expect(wrapper.emitted('update:selected-agents')?.[0]).toEqual([[]])
    expect(wrapper.emitted('update:selected-severities')?.[0]).toEqual([[]])
    expect(wrapper.emitted('update:selected-tags')?.[0]).toEqual([[]])
  })

  it('returns appropriate severity classes', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    expect(wrapper.vm.getSeverityClass('CRITICAL')).toBe('badge-critical')
    expect(wrapper.vm.getSeverityClass('critica')).toBe('badge-critical')
    expect(wrapper.vm.getSeverityClass('HIGH')).toBe('badge-high')
    expect(wrapper.vm.getSeverityClass('alta')).toBe('badge-high')
    expect(wrapper.vm.getSeverityClass('MEDIUM')).toBe('badge-medium')
    expect(wrapper.vm.getSeverityClass('LOW')).toBe('badge-low')
    expect(wrapper.vm.getSeverityClass('')).toBe('badge-low')
  })

  it('resolves cell state correctly across all branches', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    const startJan = new Date('2026-01-01T00:00:00Z').getTime()
    const endJan = new Date('2026-01-31T23:59:59Z').getTime()

    // Null or invalid vuln
    expect(wrapper.vm.resolveCell(null, startJan, endJan).status).toBe('NONE')
    expect(wrapper.vm.resolveCell({}, startJan, endJan).status).toBe('NONE')
    expect(wrapper.vm.resolveCell({ first_seen: 'invalid' }, startJan, endJan).status).toBe('NONE')

    // History in slot
    const cellResolvedHistory = wrapper.vm.resolveCell(mockVulns[2], startJan, endJan)
    expect(cellResolvedHistory.status).toBe('RESOLVED')

    // History with DETECTED / REOPENED before slot
    const vulnWithReopen = {
      id: 20,
      status: 'ACTIVE',
      first_seen: '2025-11-01T00:00:00Z',
      history: [
        { action: 'RESOLVED', timestamp: '2025-12-01T00:00:00Z' },
        { action: 'REOPENED', timestamp: '2025-12-15T00:00:00Z' }
      ]
    }
    expect(wrapper.vm.resolveCell(vulnWithReopen, startJan, endJan).status).toBe('ACTIVE')

    // History resolved before slot
    const vulnResolvedBefore = {
      id: 21,
      status: 'RESOLVED',
      first_seen: '2025-01-01T00:00:00Z',
      history: [
        { action: 'RESOLVED', timestamp: '2025-05-01T00:00:00Z' }
      ]
    }
    expect(wrapper.vm.resolveCell(vulnResolvedBefore, startJan, endJan).status).toBe('NONE')

    // Fallback without history
    const fallbackActive = { id: 10, status: 'ACTIVE', first_seen: '2026-01-01T00:00:00Z' }
    expect(wrapper.vm.resolveCell(fallbackActive, startJan, endJan).status).toBe('ACTIVE')

    const fallbackMitigated = { id: 13, status: 'MITIGATED', first_seen: '2026-01-01T00:00:00Z', last_seen: '2026-01-15T00:00:00Z' }
    expect(wrapper.vm.resolveCell(fallbackMitigated, startJan, endJan).status).toBe('MITIGATED')

    const fallbackResolvedInSlot = { id: 11, status: 'RESOLVED', first_seen: '2026-01-01T00:00:00Z', last_seen: '2026-01-15T00:00:00Z' }
    expect(wrapper.vm.resolveCell(fallbackResolvedInSlot, startJan, endJan).status).toBe('RESOLVED')

    const fallbackResolvedBeforeSlot = { id: 12, status: 'RESOLVED', first_seen: '2025-10-01T00:00:00Z', last_seen: '2025-11-01T00:00:00Z' }
    expect(wrapper.vm.resolveCell(fallbackResolvedBeforeSlot, startJan, endJan).status).toBe('NONE')

    const vulnResolvedLater = {
      id: 22,
      status: 'RESOLVED',
      first_seen: '2026-01-01T00:00:00Z',
      last_seen: '2026-05-01T00:00:00Z'
    }
    expect(wrapper.vm.resolveCell(vulnResolvedLater, startJan, endJan).status).toBe('ACTIVE')

    // Mitigated in slot via history details
    const vulnMitigatedHistory = {
      id: 25,
      status: 'MITIGATED',
      first_seen: '2026-01-01T00:00:00Z',
      history: [
        { action: 'RULE_APPLIED', details: 'Mitigated by policy', timestamp: '2026-01-15T00:00:00Z' }
      ]
    }
    expect(wrapper.vm.resolveCell(vulnMitigatedHistory, startJan, endJan).status).toBe('MITIGATED')

    // Future vuln returns NONE
    const vulnFuture = {
      id: 26,
      status: 'ACTIVE',
      first_seen: '2026-06-01T00:00:00Z'
    }
    expect(wrapper.vm.resolveCell(vulnFuture, startJan, endJan).status).toBe('NONE')
  })

  it('computes min and max start and end dates and handles NaN year', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    expect(wrapper.vm.minStartDate).toBe('')
    expect(wrapper.vm.maxStartDate).toBe('')

    wrapper.vm.rangeStartDate = '2026-03-01'
    expect(wrapper.vm.minEndDate).toBe('2026-03-01')
    expect(wrapper.vm.maxEndDate).toBe('2026-03-31')

    wrapper.vm.yearInputValue = 'not-a-number'
    wrapper.vm.applyYearInput()
    expect(wrapper.vm.selectedYear).toBe(2026)
  })

  it('handles onEndDateChange with diff out of range and empty shiftDays', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.rangeEndDate = '2026-03-01'
    wrapper.vm.rangeStartDate = '2026-05-01'
    wrapper.vm.onEndDateChange()
    expect(wrapper.vm.rangeStartDate).toBe('2026-01-30')

    wrapper.vm.rangeStartDate = ''
    wrapper.vm.rangeEndDate = ''
    expect(wrapper.vm.shiftDays('', 5)).toBe('')
  })
})
