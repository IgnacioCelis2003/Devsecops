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
    totalRecords: 2,
    activeCount: 1,
    mitigatedCount: 0,
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
    expect(wrapper.findAll('.matrix-row').length).toBe(2)
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
    expect(wrapper.vm.granularity).toBe('month')
    expect(wrapper.vm.timeColumns.length).toBeGreaterThan(0)

    wrapper.vm.granularity = 'range'
    expect(wrapper.vm.granularity).toBe('range')

    wrapper.vm.granularity = 'year'
    expect(wrapper.vm.granularity).toBe('year')
    expect(wrapper.vm.timeColumns.length).toBe(12)
  })

  it('clears all filters when resetAllFilters is called', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    wrapper.vm.resetAllFilters()
    expect(wrapper.emitted('update:selected-status')?.[0]).toEqual(['all'])
    expect(wrapper.emitted('update:selected-agents')?.[0]).toEqual([[]])
    expect(wrapper.emitted('update:selected-severities')?.[0]).toEqual([[]])
    expect(wrapper.emitted('update:selected-tags')?.[0]).toEqual([[]])
  })

  it('resolves cell state correctly for active and resolved vulns', () => {
    const wrapper = mount(TimelineMatrixGrid, {
      props: defaultProps
    })

    const startJan = new Date('2026-01-01T00:00:00Z').getTime()
    const endJan = new Date('2026-01-31T23:59:59Z').getTime()

    const cell1 = wrapper.vm.resolveCell(mockVulns[0], startJan, endJan)
    expect(cell1.status).toBe('ACTIVE')

    const cell2 = wrapper.vm.resolveCell(mockVulns[1], startJan, endJan)
    expect(cell2.status).toBe('NONE')
  })
})
