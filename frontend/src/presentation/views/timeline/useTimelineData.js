import { computed, ref } from 'vue'
import vulnService from '../../../application/services/vulnService'
import { DAY_MS, HOUR_MS, alignHour, fmtDDMM, fmtHour, fmtYear } from './timelineFormatters'

const LIMIT = 2000

const startOfLocalDay = ms => {
  const date = new Date(ms)
  date.setHours(0, 0, 0, 0)
  return date.getTime()
}

const initialZoomForPeriod = period => {
  if (period === '7d') return 2
  if (period === '24h') return 4
  if (period === 'day') return 5
  return 0
}


const isResolvedAction = (h) => {
  if (!h) return false
  const action = (h.action || '').toUpperCase()
  const details = (h.details || '').toUpperCase()
  if (action === 'RESOLVED') return true
  if (action === 'STATUS_CHANGED' && (details.includes('RESOLVED') || details.includes('MITIGATED') || details.includes('RESUELT'))) {
    return true
  }
  return false
}

const isReopenedOrActiveAction = (h) => {
  if (!h) return false
  const action = (h.action || '').toUpperCase()
  const details = (h.details || '').toUpperCase()
  if (action === 'REOPENED' || action === 'DETECTED') return true
  if (action === 'STATUS_CHANGED' && details.includes('ACTIVE')) return true
  return false
}

export default function useTimelineData({
  selectedConnection,
  selectedAgents,
  selectedVulns,
  selectedTags = ref([]),
  selectedStatus = ref('all'),
  period,
  customDate,
  activeZoom,
  getConnectionName
}) {
  const loading = ref(false)
  const hasBuilt = ref(false)
  const isTruncated = ref(false)
  const filteredVulnsData = ref([])
  const changeEvents = ref([])
  const latestSnap = ref({ total: 0, pending: 0, resolved: 0 })
  const rangeStartMs = ref(0)
  const rangeEndMs = ref(0)
  const errorMessage = ref('')
  const warningMessage = ref('')
  const snapshotCache = ref(new Map())

  const computeRange = vulns => {
    const now = new Date()
    let start = new Date(0)
    let end = now

    if (period.value === '24h') start = new Date(now.getTime() - DAY_MS)
    if (period.value === '7d') start = new Date(now.getTime() - 7 * DAY_MS)
    if (period.value === '30d') start = new Date(now.getTime() - 30 * DAY_MS)

    if (period.value === 'day') {
      start = new Date(`${customDate.value}T00:00:00`)
      end = new Date(`${customDate.value}T23:59:59`)
    }

    if (period.value === 'all' && vulns.length > 0) {
      const earliest = vulns
        .map(vuln => new Date(vuln.first_seen).getTime())
        .filter(ms => !Number.isNaN(ms))
        .sort((a, b) => a - b)[0]
      if (earliest) {
        start = new Date(earliest)
      }
    }

    return { start, end }
  }

  const summarizeChanges = (startMs, endMs) => {
    let hasDetection = false
    let hasResolution = false

    for (const event of changeEvents.value) {
      if (event.ms < startMs) continue
      if (event.ms > endMs) break
      if (event.kind === 'detection') hasDetection = true
      if (event.kind === 'resolution') hasResolution = true
      if (hasDetection && hasResolution) break
    }

    return { hasDetection, hasResolution }
  }

  const getVulnerabilityStateAtTime = (vuln, ms) => {
    const firstSeenMs = new Date(vuln.first_seen).getTime()
    if (Number.isNaN(firstSeenMs) || firstSeenMs > ms) {
      return null // Vulnerability not yet seen
    }

    let state = 'ACTIVE'
    let resolvedAt = null

    for (const historyItem of vuln.historySorted) {
      const historyMs = new Date(historyItem.timestamp).getTime()
      if (Number.isNaN(historyMs) || historyMs > ms) break
      if (isResolvedAction(historyItem)) {
        state = 'RESOLVED'
        resolvedAt = historyItem.timestamp
      } else if (isReopenedOrActiveAction(historyItem)) {
        state = 'ACTIVE'
        resolvedAt = null
      }
    }

    // Si en BD ya figura como resuelta/mitigada y la fecha del slot es posterior a su última actividad
    if (state === 'ACTIVE' && (vuln.status === 'RESOLVED' || vuln.status === 'MITIGATED') && !resolvedAt) {
      const lastSeenMs = new Date(vuln.last_seen || vuln.first_seen).getTime()
      if (!Number.isNaN(lastSeenMs) && ms >= lastSeenMs) {
        state = 'RESOLVED'
        resolvedAt = vuln.last_seen
      }
    }

    return { state, resolvedAt }
  }

  const buildSnapshotDetails = (vulns, ms) => {
    const details = []

    vulns.forEach(vuln => {
      const vulnState = getVulnerabilityStateAtTime(vuln, ms)
      if (!vulnState) return

      details.push({
        ...vuln,
        // Estado histórico en el slot específico
        slot_status: vulnState.state,
        // Estado actual definitivo en base de datos
        current_status: vuln.status || vulnState.state,
        status: vulnState.state, // para contadores del slot
        resolved_at: vulnState.resolvedAt,
        connection_name: vuln.connection_name || getConnectionName()
      })
    })

    return details
  }

  const snapshotAt = ms => {
    if (snapshotCache.value.has(ms)) {
      return snapshotCache.value.get(ms)
    }

    const details = buildSnapshotDetails(filteredVulnsData.value, ms)

    let total = 0
    let pending = 0
    let resolved = 0

    details.forEach(vuln => {
      total += 1
      if (vuln.status === 'ACTIVE') pending += 1
      else resolved += 1
    })

    const snapshot = { total, pending, resolved, details }
    snapshotCache.value.set(ms, snapshot)
    return snapshot
  }

  const getTimelineEventInSlot = (vuln, startMs, endMs) => {
    const candidates = []

    const firstSeenMs = new Date(vuln.first_seen).getTime()
    if (!Number.isNaN(firstSeenMs) && firstSeenMs >= startMs && firstSeenMs <= endMs) {
      candidates.push({
        at: vuln.first_seen,
        label: 'DETECTED_APP',
        source: 'first_seen'
      })
    }

    for (const historyItem of vuln.historySorted) {
      const historyMs = new Date(historyItem.timestamp).getTime()
      if (Number.isNaN(historyMs) || historyMs < startMs || historyMs > endMs) continue

      if (['DETECTED', 'REOPENED', 'RESOLVED', 'STATUS_CHANGED'].includes(historyItem.action)) {
        let label = historyItem.action
        if (isResolvedAction(historyItem)) {
          label = 'RESOLVED'
        } else if (historyItem.action === 'STATUS_CHANGED') {
          if (historyItem.details?.toUpperCase().includes('MITIGATED')) label = 'MITIGATED'
          else if (historyItem.details?.toUpperCase().includes('IN_REVIEW')) label = 'IN_REVIEW'
          else label = 'STATUS_CHANGED'
        }
        candidates.push({
          at: historyItem.timestamp,
          label: label,
          source: 'history'
        })
      }
    }

    if (!candidates.length) return null

    candidates.sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime())
    return candidates[0]
  }

  const getSlotType = (summary) => {
    if (summary.hasDetection && summary.hasResolution) return 'mixed'
    if (summary.hasDetection) return 'detection'
    if (summary.hasResolution) return 'resolution'
    return 'none'
  }

  const getSlotDetails = (snapshot, startMs, endMs) => {
    if (!snapshot) return []
    // Solo incluir vulnerabilidades que tienen un evento EN este slot específico
    return snapshot.details
      .map(vuln => {
        const timelineEvent = getTimelineEventInSlot(vuln, startMs, endMs)
        return {
          ...vuln,
          timeline_event_at: timelineEvent?.at ?? null,
          timeline_event_label: timelineEvent?.label ?? null,
          timeline_event_source: timelineEvent?.source ?? null
        }
      })
      .filter(vuln => vuln.timeline_event_at !== null) // Solo vulnerabilidades con eventos reales
  }

  const createSlot = (startMs, endMs, summary, snapshot, slotHours) => {
    const painted = summary.hasDetection || summary.hasResolution
    const type = getSlotType(summary)
    const details = getSlotDetails(snapshot, startMs, endMs)

    // Contadores basados en vulnerabilidades con eventos, no en snapshot completo
    const total = details.length
    const pending = details.filter(v => v.status === 'ACTIVE').length
    const resolved = details.filter(v => v.status === 'RESOLVED').length

    return {
      startMs,
      endMs,
      painted,
      type,
      total,
      pending,
      resolved,
      details,
      tickLabel: slotHours >= 24 ? fmtDDMM(startMs) : fmtHour(startMs),
      cardLabel: slotHours >= 24
        ? `${fmtDDMM(startMs)} ${fmtYear(startMs)}`
        : `${fmtDDMM(startMs)} ${fmtHour(startMs)}`
    }
  }

  const allSlots = computed(() => {
    if (!hasBuilt.value || !rangeStartMs.value || !rangeEndMs.value) return []

    const slots = []
    const slotMs = activeZoom.value.slotHours * HOUR_MS
    const isDayGranularity = activeZoom.value.slotHours >= 24
    const baseStartMs = isDayGranularity ? startOfLocalDay(rangeStartMs.value) : rangeStartMs.value
    const totalSlotCount = Math.max(1, Math.ceil((rangeEndMs.value - baseStartMs + 1) / slotMs))

    for (let index = 0; index < totalSlotCount; index++) {
      const startMs = baseStartMs + index * slotMs
      const endMs = Math.min(rangeEndMs.value, startMs + slotMs - 1)
      const summary = summarizeChanges(startMs, endMs)
      const painted = summary.hasDetection || summary.hasResolution
      
      // Solo crear slot si hay eventos reales (detecciones o resoluciones)
      if (painted) {
        const snapshot = snapshotAt(endMs)
        slots.push(createSlot(startMs, endMs, summary, snapshot, activeZoom.value.slotHours))
      }
    }

    return slots
  })

  const paintedCount = computed(() => allSlots.value.filter(slot => slot.painted).length)

  const fetchConnectionVulns = async () => {
    const response = await vulnService.getVulns({
      connectionId: selectedConnection.value,
      limit: LIMIT
    })

    const data = Array.isArray(response.data) ? response.data : []

    if (data.length >= LIMIT) {
      isTruncated.value = true
      warningMessage.value = `Se alcanzaron ${LIMIT} registros. El analisis puede estar truncado.`
    } else {
      isTruncated.value = false
    }

    return data
  }

  const resetBuildState = () => {
    loading.value = true
    hasBuilt.value = false
    isTruncated.value = false
    errorMessage.value = ''
    warningMessage.value = ''
    changeEvents.value = []
    filteredVulnsData.value = []
    snapshotCache.value.clear()
  }

  const filterVulnerabilities = (data) => {
    return data.filter(vuln => {
      const byAgent = !selectedAgents?.value?.length || selectedAgents.value.includes(vuln.agent_name)
      const byVuln = !selectedVulns?.value?.length || selectedVulns.value.includes(vuln.cve_id)
      const byTag = !selectedTags?.value?.length || (Array.isArray(vuln.tags) && vuln.tags.some(t => selectedTags.value.includes(t)))
      const byStatus = !selectedStatus?.value || selectedStatus.value === 'all' ||
        (selectedStatus.value === 'active' && vuln.status === 'ACTIVE') ||
        (selectedStatus.value === 'resolved' && vuln.status === 'RESOLVED')
      return byAgent && byVuln && byTag && byStatus
    })
  }

  const processVulnerabilities = (vulns) => {
    return vulns.map(vuln => ({
      ...vuln,
      historySorted: [...(vuln.history || [])].sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )
    }))
  }

  const buildChangeEvents = (vulns) => {
    const events = []

    vulns.forEach(vuln => {
      const firstSeenMs = new Date(vuln.first_seen).getTime()
      if (firstSeenMs >= rangeStartMs.value && firstSeenMs <= rangeEndMs.value) {
        events.push({ ms: firstSeenMs, kind: 'detection' })
      }

      vuln.historySorted.forEach(historyItem => {
        const historyMs = new Date(historyItem.timestamp).getTime()
        if (historyMs < rangeStartMs.value || historyMs > rangeEndMs.value) return
        if (isResolvedAction(historyItem)) {
          events.push({ ms: historyMs, kind: 'resolution' })
        }
      })
    })

    return events
  }

  const finalizeBuild = (events) => {
    const sortedEvents = [...events].sort((a, b) => a.ms - b.ms)
    changeEvents.value = sortedEvents
    latestSnap.value = snapshotAt(rangeEndMs.value)
    hasBuilt.value = true
    return { initialZoom: initialZoomForPeriod(period.value) }
  }

  const build = async () => {
    if (!selectedConnection.value) return { initialZoom: 0 }

    resetBuildState()

    try {
      const data = await fetchConnectionVulns()
      const filteredVulns = filterVulnerabilities(data)
      const processedVulns = processVulnerabilities(filteredVulns)

      filteredVulnsData.value = processedVulns

      const { start, end } = computeRange(filteredVulnsData.value)
      rangeStartMs.value = alignHour(start.getTime())
      rangeEndMs.value = end.getTime()

      const events = buildChangeEvents(filteredVulnsData.value)
      return finalizeBuild(events)
    } catch (error) {
      errorMessage.value = 'No se pudo generar la linea de tiempo. Intenta nuevamente.'
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    hasBuilt,
    isTruncated,
    allSlots,
    paintedCount,
    latestSnap,
    errorMessage,
    warningMessage,
    filteredVulnsData,
    build,
    fetchConnectionVulns,
    snapshotAt
  }
}
