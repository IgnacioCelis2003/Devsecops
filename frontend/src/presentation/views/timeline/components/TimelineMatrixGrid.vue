<template>
  <div class="card timeline-matrix-card">
    <!-- ====================================================================== -->
    <!-- BARRA MAESTRA UNIFICADA (OPCIÓN A - ESTILO EJECUTIVO)                  -->
    <!-- ====================================================================== -->
    <div class="matrix-master-toolbar">
      <!-- FILA 1: CONEXIÓN, MICRO-KPIS Y ACCIONES -->
      <div class="toolbar-row-top">
        <div class="top-left-group">
          <!-- Selector de Conexión Wazuh -->
          <div class="conn-selector-wrap" v-if="connections && connections.length > 0">
            <svg class="conn-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            <select
              :value="selectedConnection"
              @change="$emit('update:selected-connection', $event.target.value)"
              class="matrix-select-conn"
              aria-label="Seleccionar conexión Wazuh"
            >
              <option value="" disabled>Seleccionar servidor...</option>
              <option v-for="conn in connections" :key="conn.id" :value="conn.id">
                {{ conn.name }}
              </option>
            </select>
          </div>

          <!-- Micro-Badges de KPI Slim -->
          <div class="master-kpis">
            <span class="kpi-chip kpi-chip-total" title="Total de vulnerabilidades reportadas">
              <span class="kpi-chip-dot dot-total"></span>
              Total: <strong>{{ totalRecords }}</strong>
            </span>
            <span class="kpi-chip kpi-chip-active" title="Vulnerabilidades activas">
              <span class="kpi-chip-dot dot-active"></span>
              Activas: <strong>{{ activeCount }}</strong>
            </span>
            <span v-if="mitigatedCount > 0" class="kpi-chip kpi-chip-mitigated" title="Vulnerabilidades mitigadas">
              <span class="kpi-chip-dot dot-mitigated"></span>
              Mitigadas: <strong>{{ mitigatedCount }}</strong>
            </span>
            <span class="kpi-chip kpi-chip-resolved" title="Vulnerabilidades resueltas">
              <span class="kpi-chip-dot dot-resolved"></span>
              Resueltas: <strong>{{ resolvedCount }}</strong>
            </span>
          </div>
        </div>

        <!-- Derecha: Toggle Vista Compacta/Detallada y Limpiar Filtros -->
        <div class="top-right-group">
          <!-- Selector de cantidad por página sincronizado con Backend -->
          <div class="timeline-limit-group" title="Cantidad de registros por página (Backend)">
            <span class="timeline-limit-label">Mostrar:</span>
            <select
              :value="itemsPerPage"
              @change="$emit('update:items-per-page', Number($event.target.value))"
              class="matrix-select-limit"
              aria-label="Cantidad de vulnerabilidades por página"
            >
              <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </div>

          <!-- Mini Paginador en Línea de Tiempo (Sincronizado con Backend) -->
          <div v-if="totalPages > 1" class="timeline-pager-group" title="Navegar páginas">
            <button
              type="button"
              class="btn-pager-icon"
              :disabled="currentPage === 1"
              @click="$emit('prev-page')"
              title="Página anterior"
              aria-label="Página anterior"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="15 18 9 12 15 6"></polyline>
              </svg>
            </button>
            <span class="pager-indicator">{{ currentPage }} / {{ totalPages }}</span>
            <button
              type="button"
              class="btn-pager-icon"
              :disabled="currentPage === totalPages"
              @click="$emit('next-page')"
              title="Página siguiente"
              aria-label="Página siguiente"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>
          </div>

          <!-- Toggle Vista Detallada / Compacta -->
          <button
            type="button"
            class="btn-master-action"
            @click="isDetailedView = !isDetailedView"
            :title="isDetailedView ? 'Cambiar a vista compacta' : 'Cambiar a vista detallada'"
          >
            <svg v-if="isDetailedView" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="3" y1="15" x2="21" y2="15"></line>
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <span>{{ isDetailedView ? 'Vista Compacta' : 'Vista Detallada' }}</span>
          </button>

          <!-- Botón Limpiar Todos los Filtros -->
          <button
            type="button"
            class="btn-master-action btn-reset-filters"
            :class="{ 'has-active-filters': hasActiveFilters }"
            @click="resetAllFilters"
            title="Restablecer todos los filtros a sus valores por defecto"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="1 4 1 10 7 10"></polyline>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
            </svg>
            <span>Limpiar filtros</span>
          </button>
        </div>
      </div>

      <!-- FILA 2: CONTROLES TEMPORALES Y FILTROS INTEGRADOS (SIN ESPACIO EN BLANCO) -->
      <div class="toolbar-row-bottom">
        <div class="bottom-controls-bar">
          <!-- Selector de Granularidad (Sin la palabra 'Granularidad') -->
          <div class="control-box">
            <select v-model="granularity" class="master-select" aria-label="Granularidad temporal">
              <option value="year">Anual (Meses)</option>
              <option value="month">Mensual (Días)</option>
              <option value="range">Rango de Fechas</option>
            </select>
          </div>

          <!-- Selector Temporal Anual / Mensual: Año con Stepper, Input Libre (auditorías sin límite) y Selector por Décadas -->
          <template v-if="granularity === 'year' || granularity === 'month'">
            <div class="control-box popover-wrap" v-click-outside="() => (dropdowns.yearPicker = false)">
              <span class="control-box-label">Año</span>
              <div class="stepper-select-wrap">
                <button
                  type="button"
                  class="btn-stepper-mini"
                  @click="stepYear(-1)"
                  title="Año anterior"
                  aria-label="Año anterior"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="15 18 9 12 15 6"></polyline>
                  </svg>
                </button>
                <input
                  type="number"
                  v-model.lazy.number="yearInputValue"
                  @change="applyYearInput"
                  @keydown.enter="$event.target.blur()"
                  class="input-year-stepper"
                  min="1970"
                  max="2099"
                  title="Escribe directamente cualquier año para auditoría (ej. 1990) o usa las flechas"
                  aria-label="Año"
                />
                <button
                  type="button"
                  class="btn-stepper-mini"
                  @click="stepYear(1)"
                  title="Año siguiente"
                  aria-label="Año siguiente"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>
                <button
                  type="button"
                  class="btn-year-dropdown-toggle"
                  @click="toggleYearPicker"
                  title="Selector visual de décadas y años"
                  aria-label="Selector de décadas"
                >
                  <span class="dropdown-arrow-icon">▼</span>
                </button>
              </div>

              <!-- Popover de Navegación por Décadas (Flatpickr/AntD style) -->
              <div v-if="dropdowns.yearPicker" class="tray-popover year-decade-popover shadow-lg fade-in">
                <div class="decade-header">
                  <button type="button" class="btn-decade-nav" @click="decadeStart -= 10" title="Década anterior">
                    &laquo;
                  </button>
                  <span class="decade-title">{{ decadeStart }} - {{ decadeStart + 9 }}</span>
                  <button type="button" class="btn-decade-nav" @click="decadeStart += 10" title="Década siguiente">
                    &raquo;
                  </button>
                </div>
                <div class="decade-grid">
                  <button
                    v-for="offset in 10"
                    :key="decadeStart + offset - 1"
                    type="button"
                    class="btn-year-cell"
                    :class="{ 'is-selected': selectedYear === (decadeStart + offset - 1) }"
                    @click="selectYearFromPicker(decadeStart + offset - 1)"
                  >
                    {{ decadeStart + offset - 1 }}
                  </button>
                </div>
                <div class="decade-footer">
                  <button type="button" class="btn-decade-quick" @click="selectYearFromPicker(currentYear)">
                    Hoy ({{ currentYear }})
                  </button>
                </div>
              </div>
            </div>

            <!-- Mes si la granularidad es mensual -->
            <div v-if="granularity === 'month'" class="control-box">
              <span class="control-box-label">Mes</span>
              <select v-model.number="selectedMonth" class="master-select" aria-label="Seleccionar mes">
                <option v-for="(mName, mIdx) in monthNames" :key="mIdx" :value="mIdx">{{ mName }}</option>
              </select>
            </div>
          </template>

          <!-- Selector de Rango con Mini-Calendarios -->
          <template v-if="granularity === 'range'">
            <div class="control-box">
              <span class="control-box-label">Desde</span>
              <CustomDatePopover
                v-model="rangeStartDate"
                :min-date="minStartDate"
                :max-date="maxStartDate"
                label="Desde"
                placeholder="dd/mm/aa"
                @change="onStartDateChange"
              />
            </div>
            <div class="control-box">
              <span class="control-box-label">Hasta</span>
              <CustomDatePopover
                v-model="rangeEndDate"
                :min-date="minEndDate"
                :max-date="maxEndDate"
                label="Hasta"
                placeholder="dd/mm/aa"
                @change="onEndDateChange"
              />
            </div>
            <button
              v-if="rangeStartDate || rangeEndDate"
              type="button"
              class="btn-clear-range-dates"
              @click="clearDateRange"
              title="Limpiar fechas"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
              Limpiar
            </button>
          </template>

          <!-- Separador Vertical Sutil -->
          <div class="toolbar-divider"></div>

          <!-- 1. Severidad (Amenaza / Riesgo) -->
          <div class="control-box popover-wrap" v-click-outside="() => (dropdowns.severity = false)">
            <span class="control-box-label">Severidad</span>
            <button class="inline-filter-btn" @click="dropdowns.severity = !dropdowns.severity">
              <span class="inline-filter-text">{{ selectedSeverities.length ? selectedSeverities.length + ' selec.' : 'Todas' }}</span>
              <span class="dropdown-arrow-icon">▼</span>
            </button>
            <div v-if="dropdowns.severity" class="tray-popover tray-popover-severity shadow-md fade-in">
              <div class="tray-popover-actions">
                <button type="button" @click="$emit('update:selected-severities', [...severityOptions])">Todas</button>
                <button type="button" @click="$emit('update:selected-severities', [])">Limpiar</button>
              </div>
              <div class="tray-popover-grid-2col">
                <label v-for="sev in severityOptions" :key="sev" class="tray-popover-row">
                  <input
                    type="checkbox"
                    :checked="selectedSeverities.includes(sev.toUpperCase())"
                    @change="toggleSeverity(sev.toUpperCase())"
                  >
                  <span class="badge-mini-tag" :class="getSeverityClass(sev)">{{ sev }}</span>
                </label>
              </div>
            </div>
          </div>

          <!-- 2. Filtro de Estado Segmentado (Todas / Activas / Resueltas) -->
          <div class="control-box">
            <span class="control-box-label">Estado</span>
            <div class="status-segment-group">
              <button
                type="button"
                class="segment-btn"
                :class="{ 'is-active': selectedStatus === 'all' }"
                @click="$emit('update:selected-status', 'all')"
              >
                Todas
              </button>
              <button
                type="button"
                class="segment-btn"
                :class="{ 'is-active': selectedStatus === 'active' }"
                @click="$emit('update:selected-status', 'active')"
              >
                Activas
              </button>
              <button
                type="button"
                class="segment-btn"
                :class="{ 'is-active': selectedStatus === 'resolved' }"
                @click="$emit('update:selected-status', 'resolved')"
              >
                Resueltas
              </button>
            </div>
          </div>

          <!-- Separador Vertical Sutil -->
          <div class="toolbar-divider"></div>

          <!-- 3. Equipos / Agentes (Infraestructura) -->
          <div class="control-box popover-wrap" v-click-outside="() => (dropdowns.agents = false)">
            <span class="control-box-label">Equipos</span>
            <button class="inline-filter-btn" @click="dropdowns.agents = !dropdowns.agents" :disabled="!agentOptions.length">
              <span class="inline-filter-text">{{ selectedAgents.length ? selectedAgents.length + ' selec.' : 'Todos' }}</span>
              <span class="dropdown-arrow-icon">▼</span>
            </button>
            <div v-if="dropdowns.agents" class="tray-popover shadow-md fade-in">
              <label for="search-matrix-agent" class="sr-only">Buscar agente</label><input id="search-matrix-agent" type="text" v-model="search.agent" placeholder="Buscar agente..." class="tray-search-input" aria-label="Buscar agente">
              <div class="tray-popover-actions">
                <button type="button" @click="$emit('update:selected-agents', [...agentOptions])">Todos</button>
                <button type="button" @click="$emit('update:selected-agents', [])">Limpiar</button>
              </div>
              <div class="tray-popover-list custom-scroll">
                <label v-for="agent in filteredAgents" :key="agent" class="tray-popover-row">
                  <input
                    type="checkbox"
                    :checked="selectedAgents.includes(agent)"
                    @change="toggleAgent(agent)"
                  >
                  <span class="tray-row-text" :title="agent">{{ agent }}</span>
                </label>
                <div v-if="filteredAgents.length === 0" class="tray-empty">Sin coincidencias</div>
              </div>
            </div>
          </div>

          <!-- 4. Etiquetas (Tags - Contexto Extra) -->
          <div class="control-box popover-wrap" v-click-outside="() => (dropdowns.tags = false)">
            <span class="control-box-label">Etiquetas</span>
            <button class="inline-filter-btn" @click="dropdowns.tags = !dropdowns.tags" :disabled="!tagOptions.length">
              <span class="inline-filter-text">{{ selectedTags.length ? selectedTags.length + ' selec.' : 'Todas' }}</span>
              <span class="dropdown-arrow-icon">▼</span>
            </button>
            <div v-if="dropdowns.tags" class="tray-popover shadow-md fade-in">
              <label for="search-matrix-tag" class="sr-only">Buscar etiqueta</label><input id="search-matrix-tag" type="text" v-model="search.tag" placeholder="Buscar etiqueta..." class="tray-search-input" aria-label="Buscar etiqueta">
              <div class="tray-popover-actions">
                <button type="button" @click="$emit('update:selected-tags', [...tagOptions])">Todas</button>
                <button type="button" @click="$emit('update:selected-tags', [])">Limpiar</button>
              </div>
              <div class="tray-popover-list custom-scroll">
                <label v-for="tag in filteredTags" :key="tag" class="tray-popover-row">
                  <input
                    type="checkbox"
                    :checked="selectedTags.includes(tag)"
                    @change="toggleTag(tag)"
                  >
                  <span class="tray-row-text" :title="tag">{{ tag }}</span>
                </label>
                <div v-if="filteredTags.length === 0" class="tray-empty">Sin coincidencias</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ====================================================================== -->
    <!-- MATRIZ / GANTT GRID                                                    -->
    <!-- ====================================================================== -->
    <div v-if="vulns && vulns.length > 0" class="matrix-scroll-wrapper custom-scroll">
      <table class="matrix-table">
        <thead>
          <tr>
            <!-- Columna Fija Izquierda: Título de Tarea / CVE -->
            <th class="th-fixed-col">
              <div class="th-cve-header">
                <span>Vulnerabilidad ({{ vulns.length }})</span>
              </div>
            </th>

            <!-- Columnas Temporales Dinámicas -->
            <th
              v-for="col in timeColumns"
              :key="col.key"
              class="th-time-slot"
              :class="{ 'is-today': col.isCurrent }"
              :title="col.fullLabel"
            >
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="vuln in vulns"
            :key="vuln.id"
            class="matrix-row"
            :class="{ 'row-detailed': isDetailedView }"
          >
            <!-- Celda Izquierda Fija: Información de la Vulnerabilidad -->
            <td
              class="td-fixed-col"
              @click="onVulnClick(vuln.id)"
              :title="'Clic para enfocar en la tabla de inventario: ' + (vuln.cve_id || 'CVE')"
            >
              <!-- Modo Compacto (Badge + Severidad) -->
              <div v-if="!isDetailedView" class="cve-compact-cell">
                <span class="cve-code-badge font-mono">{{ vuln.cve_id || 'N/A' }}</span>
                <span :class="getSeverityClass(vuln.severity)" class="badge-mini-tag">
                  {{ (vuln.severity || 'UNKNOWN').toUpperCase() }}
                </span>
              </div>

              <!-- Modo Detallado (CVE, Severidad, Paquete y Agente) -->
              <div v-else class="cve-detailed-cell">
                <div class="detailed-header-row">
                  <span class="cve-title font-mono">{{ vuln.cve_id || 'N/A' }}</span>
                  <span :class="getSeverityClass(vuln.severity)" class="badge-mini-tag">
                    {{ (vuln.severity || 'UNKNOWN').toUpperCase() }}
                  </span>
                  <span v-if="vuln.score_base != null" class="cvss-pill">
                    {{ vuln.score_base.toFixed(1) }}
                  </span>
                </div>
                <div class="detailed-sub-row text-truncate">
                  <span class="sub-pkg" :title="vuln.package_name + ' ' + (vuln.package_version || '')">
                    📦 {{ vuln.package_name || 'Software' }} {{ vuln.package_version || '' }}
                  </span>
                  <span class="sub-agent" :title="vuln.agent_name || 'Agente'">
                    🖥️ {{ vuln.agent_name || '-' }}
                  </span>
                </div>
              </div>
            </td>

            <!-- Celdas de Tiempo (Píldoras Delgadas de Color) -->
            <td
              v-for="col in timeColumns"
              :key="`cell-${vuln.id}-${col.key}`"
              class="td-matrix-cell"
            >
              <div
                v-if="resolveCell(vuln, col.startMs, col.endMs).status !== 'NONE'"
                class="matrix-pill"
                :class="'pill-' + resolveCell(vuln, col.startMs, col.endMs).status.toLowerCase()"
                :title="resolveCell(vuln, col.startMs, col.endMs).label"
              >
              </div>
              <div v-else class="matrix-pill-empty" title="Sin presencia en este periodo"></div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State si no hay vulnerabilidades -->
    <div v-else class="matrix-empty-state">
      <div class="empty-icon-wrap">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      </div>
      <h4>Sin datos para la línea de tiempo</h4>
      <p>Asegúrate de haber seleccionado una conexión Wazuh con registros sincronizados.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import CustomDatePopover from './CustomDatePopover.vue'
import vClickOutside from '@/presentation/directives/clickOutside'

const props = defineProps({
  vulns: {
    type: Array,
    required: true,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  connections: {
    type: Array,
    default: () => []
  },
  selectedConnection: {
    type: [String, Number],
    default: ''
  },
  agentOptions: {
    type: Array,
    default: () => []
  },
  selectedAgents: {
    type: Array,
    default: () => []
  },
  severityOptions: {
    type: Array,
    default: () => []
  },
  selectedSeverities: {
    type: Array,
    default: () => []
  },
  tagOptions: {
    type: Array,
    default: () => []
  },
  selectedTags: {
    type: Array,
    default: () => []
  },
  selectedStatus: {
    type: String,
    default: 'all'
  },
  totalRecords: {
    type: Number,
    default: 0
  },
  activeCount: {
    type: Number,
    default: 0
  },
  mitigatedCount: {
    type: Number,
    default: 0
  },
  resolvedCount: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  totalPages: {
    type: Number,
    default: 1
  },
  itemsPerPage: {
    type: Number,
    default: 50
  },
  perPageOptions: {
    type: Array,
    default: () => [1, 5, 10, 25, 50, 100]
  }
})

const emit = defineEmits([
  'select-vuln',
  'update:selected-connection',
  'update:selected-agents',
  'update:selected-severities',
  'update:selected-tags',
  'update:selected-status',
  'update:items-per-page',
  'prev-page',
  'next-page',
  'refresh'
])

// Estados de configuración de vista
const granularity = ref('year') // 'year' | 'month' | 'range'
const isDetailedView = ref(true) // Detallada por defecto como en la referencia del usuario
const selectedYear = ref(2026)
const selectedMonth = ref(2) // 0 = Ene, 2 = Mar (marzo de 2026)
const rangeStartDate = ref('2026-03-01')
const rangeEndDate = ref('2026-03-31')

const search = reactive({ agent: '', tag: '' })
const dropdowns = reactive({ agents: false, severity: false, tags: false, yearPicker: false })

// Control de Año Universal y Auditoría Histórica (Sin límite restrictivo)
const currentYear = new Date().getFullYear()
const yearInputValue = ref(selectedYear.value)
const decadeStart = ref(Math.floor(selectedYear.value / 10) * 10)

watch(selectedYear, (val) => {
  yearInputValue.value = val
  decadeStart.value = Math.floor(val / 10) * 10
})

const stepYear = (delta) => {
  selectedYear.value += delta
}

const applyYearInput = () => {
  let val = Number.parseInt(yearInputValue.value, 10)
  if (Number.isNaN(val) || val < 1970 || val > 2099) {
    yearInputValue.value = selectedYear.value
    return
  }
  selectedYear.value = val
}

const toggleYearPicker = () => {
  dropdowns.yearPicker = !dropdowns.yearPicker
  if (dropdowns.yearPicker) {
    decadeStart.value = Math.floor(selectedYear.value / 10) * 10
  }
}

const selectYearFromPicker = (yr) => {
  selectedYear.value = yr
  dropdowns.yearPicker = false
}
const monthNames = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
const monthShortNames = [
  'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
  'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC'
]

// Búsqueda en desplegables
const filteredAgents = computed(() => {
  if (!search.agent) return props.agentOptions
  return props.agentOptions.filter(a => a.toLowerCase().includes(search.agent.toLowerCase()))
})

const filteredTags = computed(() => {
  if (!search.tag) return props.tagOptions
  return props.tagOptions.filter(t => t.toLowerCase().includes(search.tag.toLowerCase()))
})

// Toggle items de filtros secundarios
const toggleAgent = (agent) => {
  const current = [...props.selectedAgents]
  const idx = current.indexOf(agent)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(agent)
  emit('update:selected-agents', current)
}

const toggleSeverity = (sev) => {
  const current = [...props.selectedSeverities]
  const idx = current.indexOf(sev)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(sev)
  emit('update:selected-severities', current)
}

const toggleTag = (tag) => {
  const current = [...props.selectedTags]
  const idx = current.indexOf(tag)
  if (idx >= 0) current.splice(idx, 1)
  else current.push(tag)
  emit('update:selected-tags', current)
}

const hasActiveFilters = computed(() => {
  return (props.selectedStatus && props.selectedStatus !== 'all') ||
         (props.selectedAgents && props.selectedAgents.length > 0) ||
         (props.selectedSeverities && props.selectedSeverities.length > 0) ||
         (props.selectedTags && props.selectedTags.length > 0) ||
         Boolean(rangeStartDate.value) ||
         Boolean(rangeEndDate.value) ||
         granularity.value !== 'year'
})

const resetAllFilters = () => {
  granularity.value = 'year'
  selectedYear.value = 2026
  selectedMonth.value = 2
  rangeStartDate.value = ''
  rangeEndDate.value = ''
  emit('update:selected-status', 'all')
  emit('update:selected-agents', [])
  emit('update:selected-severities', [])
  emit('update:selected-tags', [])
  emit('refresh')
}

// ============================================================================
// LÓGICA DE CALENDARIO Y BLOQUEO BIDIRECCIONAL (MÁXIMO 31 DÍAS)
// ============================================================================
const shiftDays = (dateStr, days) => {
  if (!dateStr) return ''
  const parts = dateStr.split('-').map(Number)
  const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]))
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().split('T')[0]
}

// 1. Selector DESDE:
// No restringir artificialmente minStartDate para permitir al usuario explorar y seleccionar
// cualquier mes anterior libremente sin quedar bloqueado por Hasta.
const minStartDate = computed(() => '')
const maxStartDate = computed(() => '')

// 2. Selector HASTA:
// No puede ser anterior a DESDE, y máximo 30 días posteriores a DESDE (31 días en total)
const minEndDate = computed(() => {
  return rangeStartDate.value || ''
})
const maxEndDate = computed(() => {
  return rangeStartDate.value ? shiftDays(rangeStartDate.value, 30) : ''
})

const clearDateRange = () => {
  rangeStartDate.value = ''
  rangeEndDate.value = ''
}

const onStartDateChange = () => {
  if (!rangeStartDate.value) return
  if (!rangeEndDate.value) {
    rangeEndDate.value = shiftDays(rangeStartDate.value, 30)
    return
  }
  const start = new Date(rangeStartDate.value).getTime()
  const end = new Date(rangeEndDate.value).getTime()
  const diff = Math.round((end - start) / (1000 * 60 * 60 * 24))
  // Si Hasta quedó anterior a Desde, o la diferencia es mayor a 30 días, ajustar automáticamente Hasta
  if (diff < 0 || diff > 30) {
    rangeEndDate.value = shiftDays(rangeStartDate.value, 30)
  }
}

const onEndDateChange = () => {
  if (!rangeEndDate.value) return
  if (!rangeStartDate.value) {
    rangeStartDate.value = shiftDays(rangeEndDate.value, -30)
    return
  }
  const start = new Date(rangeStartDate.value).getTime()
  const end = new Date(rangeEndDate.value).getTime()
  const diff = Math.round((end - start) / (1000 * 60 * 60 * 24))
  if (diff < 0 || diff > 30) {
    rangeStartDate.value = shiftDays(rangeEndDate.value, -30)
  }
}

// ============================================================================
// GENERACIÓN DE COLUMNAS TEMPORALES (Año, Mes, Rango de Días)
// ============================================================================
const timeColumns = computed(() => {
  const cols = []

  if (granularity.value === 'year') {
    const y = selectedYear.value
    for (let m = 0; m < 12; m++) {
      const start = new Date(Date.UTC(y, m, 1, 0, 0, 0)).getTime()
      const end = new Date(Date.UTC(y, m + 1, 0, 23, 59, 59, 999)).getTime()
      cols.push({
        key: `m-${m}`,
        label: monthShortNames[m],
        fullLabel: `${monthNames[m]} ${y}`,
        startMs: start,
        endMs: end,
        isCurrent: false
      })
    }
  } else if (granularity.value === 'month') {
    const y = selectedYear.value
    const m = selectedMonth.value
    const daysInMonth = new Date(Date.UTC(y, m + 1, 0)).getUTCDate()
    for (let d = 1; d <= daysInMonth; d++) {
      const start = new Date(Date.UTC(y, m, d, 0, 0, 0)).getTime()
      const end = new Date(Date.UTC(y, m, d, 23, 59, 59, 999)).getTime()
      cols.push({
        key: `d-${d}`,
        label: String(d).padStart(2, '0'),
        fullLabel: `${d} de ${monthNames[m]} de ${y}`,
        startMs: start,
        endMs: end,
        isCurrent: false
      })
    }
  } else if (granularity.value === 'range') {
    const startObj = new Date(rangeStartDate.value || '2026-03-01')
    const endObj = new Date(rangeEndDate.value || '2026-03-31')
    const startMs = Date.UTC(startObj.getUTCFullYear(), startObj.getUTCMonth(), startObj.getUTCDate(), 0, 0, 0)
    const endMs = Date.UTC(endObj.getUTCFullYear(), endObj.getUTCMonth(), endObj.getUTCDate(), 23, 59, 59, 999)

    let curMs = startMs
    while (curMs <= endMs) {
      const dt = new Date(curMs)
      const d = dt.getUTCDate()
      const m = dt.getUTCMonth()
      const dayStart = new Date(Date.UTC(dt.getUTCFullYear(), m, d, 0, 0, 0)).getTime()
      const dayEnd = new Date(Date.UTC(dt.getUTCFullYear(), m, d, 23, 59, 59, 999)).getTime()
      cols.push({
        key: `rng-${curMs}`,
        label: `${String(d).padStart(2, '0')}/${monthShortNames[m]}`,
        fullLabel: `${d} ${monthNames[m]} ${dt.getUTCFullYear()}`,
        startMs: dayStart,
        endMs: dayEnd,
        isCurrent: false
      })
      curMs += 24 * 60 * 60 * 1000
    }
  }

  return cols
})

// Algoritmo de Mapeo de Estado de Vulnerabilidad por Celda Temporal
const resolveCell = (vuln, startMs, endMs) => {
  if (!vuln) return { status: 'NONE', label: '' }

  const firstSeenStr = vuln.first_seen || vuln.detected_at
  if (!firstSeenStr) return { status: 'NONE', label: '' }

  const firstSeenMs = new Date(firstSeenStr).getTime()
  if (Number.isNaN(firstSeenMs) || firstSeenMs > endMs) {
    return { status: 'NONE', label: '' }
  }

  // 1. Si cuenta con historial explícito de auditoría
  if (Array.isArray(vuln.history) && vuln.history.length > 0) {
    const historySorted = [...vuln.history].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

    // ¿Se resolvió dentro de este periodo?
    const resolvedInSlot = historySorted.find(h => {
      const hMs = new Date(h.timestamp).getTime()
      if (hMs >= startMs && hMs <= endMs) {
        const act = (h.action || '').toUpperCase()
        const det = (h.details || '').toUpperCase()
        return act === 'RESOLVED' || (act === 'STATUS_CHANGED' && (det.includes('RESOLV') || det.includes('MITIGAT')))
      }
      return false
    })

    if (resolvedInSlot) {
      return { status: 'RESOLVED', label: 'Resuelta' }
    }

    // ¿Se mitigó en este periodo?
    const mitigatedInSlot = historySorted.find(h => {
      const hMs = new Date(h.timestamp).getTime()
      if (hMs >= startMs && hMs <= endMs) {
        const det = (h.details || '').toUpperCase()
        return det.includes('MITIGAT')
      }
      return false
    })
    if (mitigatedInSlot) {
      return { status: 'MITIGATED', label: 'Mitigada' }
    }

    // Evaluar estado acumulado activo
    let lastState = 'ACTIVE'
    let lastResolvedMs = null

    for (const h of historySorted) {
      const hMs = new Date(h.timestamp).getTime()
      if (hMs <= endMs) {
        const act = (h.action || '').toUpperCase()
        const det = (h.details || '').toUpperCase()
        if (act === 'RESOLVED' || (act === 'STATUS_CHANGED' && det.includes('RESOLV'))) {
          lastState = 'RESOLVED'
          lastResolvedMs = hMs
        } else if (act === 'DETECTED' || act === 'REOPENED' || (act === 'STATUS_CHANGED' && det.includes('ACTIVE'))) {
          lastState = 'ACTIVE'
          lastResolvedMs = null
        }
      }
    }

    if (lastState === 'RESOLVED' && lastResolvedMs && lastResolvedMs < startMs) {
      return { status: 'NONE', label: '' }
    }

    if (lastState === 'ACTIVE') {
      return { status: 'ACTIVE', label: 'Activa' }
    }
  }

  // 2. Fallback de estado global
  const statusUpper = (vuln.status || '').toUpperCase()
  const lastSeenMs = vuln.last_seen ? new Date(vuln.last_seen).getTime() : firstSeenMs

  if (statusUpper === 'RESOLVED' || statusUpper === 'MITIGATED') {
    if (lastSeenMs >= startMs && lastSeenMs <= endMs) {
      return statusUpper === 'MITIGATED'
        ? { status: 'MITIGATED', label: 'Mitigada' }
        : { status: 'RESOLVED', label: 'Resuelta' }
    }
    if (lastSeenMs < startMs) {
      return { status: 'NONE', label: '' }
    }
    if (firstSeenMs <= endMs) {
      return { status: 'ACTIVE', label: 'Activa' }
    }
  } else {
    if (firstSeenMs <= endMs) {
      return { status: 'ACTIVE', label: 'Activa' }
    }
  }

  return { status: 'NONE', label: '' }
}

const getSeverityClass = (sev) => {
  const s = (sev || '').toLowerCase()
  if (s === 'critical' || s === 'critica') return 'badge-critical'
  if (s === 'high' || s === 'alta') return 'badge-high'
  if (s === 'medium' || s === 'media') return 'badge-medium'
  return 'badge-low'
}

const onVulnClick = (vulnId) => {
  emit('select-vuln', vulnId)
}
</script>

<style scoped>
.timeline-matrix-card {
  position: relative;
  padding: 0;
  overflow: visible;
  border: 1px solid var(--border);
  background: var(--bg-panel);
  border-radius: 12px;
}

/* ========================================================================== */
/* BARRA MAESTRA UNIFICADA (OPCIÓN A)                                         */
/* ========================================================================== */
.matrix-master-toolbar {
  position: relative;
  z-index: 30;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding: 0.85rem 1.25rem;
  background: var(--bg-hover);
  border-bottom: 1px solid var(--border);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

/* Fila Superior: Conexión + Micro-KPIs + Acciones */
.toolbar-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.85rem;
}

.top-left-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

/* Selector de Conexión Wazuh */
.conn-selector-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.35rem 0.65rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.conn-icon {
  color: var(--primary);
  flex-shrink: 0;
}

.matrix-select-conn {
  border: none;
  background: transparent;
  color: var(--text-main);
  font-size: 0.84rem;
  font-weight: 700;
  outline: none;
  cursor: pointer;
  padding-right: 0.5rem;
}

/* Micro-Badges de KPI Slim */
.master-kpis {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.kpi-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.38rem;
  padding: 0.28rem 0.65rem;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 500;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.kpi-chip strong {
  color: var(--text-main);
  font-weight: 700;
}

.kpi-chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.kpi-chip-total .dot-total {
  background: #3b82f6;
}

.kpi-chip-active .dot-active {
  background: #f87171;
}

.kpi-chip-mitigated .dot-mitigated {
  background: #fbbf24;
}

.kpi-chip-resolved .dot-resolved {
  background: #34d399;
}

/* Botones de acción derecha */
.top-right-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.timeline-limit-group {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 8px;
  font-size: 0.8rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.timeline-limit-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
}

.matrix-select-limit {
  border: none;
  background: transparent;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
  cursor: pointer;
  outline: none;
  padding: 0.1rem 0.2rem;
}

.matrix-select-limit:focus {
  outline: none;
}

.timeline-pager-group {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.18rem 0.35rem;
  border-radius: 8px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
}

.btn-pager-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--text-main);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-pager-icon:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--primary);
}

.btn-pager-icon:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.pager-indicator {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-main);
  padding: 0 0.35rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.btn-master-action {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.38rem 0.75rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-master-action:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-master-action.is-active {
  background: rgba(37, 99, 235, 0.1);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-reset-filters {
  color: var(--text-muted);
}

.btn-reset-filters:hover {
  color: #ef4444;
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

.btn-reset-filters.has-active-filters {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.05);
}

/* Fila Inferior: Controles Temporales y Filtros Directos (Sin espacios en blanco) */
.toolbar-row-bottom {
  display: flex;
  align-items: center;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.bottom-controls-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
  width: 100%;
}

.control-box {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  position: relative;
}

.control-box-label {
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
}

.master-select {
  background: var(--bg-panel);
  color: var(--text-main);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.38rem 0.65rem;
  font-size: 0.84rem;
  font-weight: 600;
  outline: none;
  cursor: pointer;
  transition: border-color 0.15s;
}

.master-select:focus {
  border-color: var(--primary);
}
.stepper-select-wrap {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-card, #ffffff);
  overflow: hidden;
  height: 30px;
}

.btn-stepper-mini {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 28px;
  background: transparent;
  border: none;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
}

.btn-stepper-mini:hover {
  background: var(--bg-hover, #f1f5f9);
  color: var(--primary);
}

.input-year-stepper {
  width: 50px;
  border: none !important;
  background: transparent !important;
  padding: 0.1rem 0.2rem !important;
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--text-main, #0f172a);
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}

.input-year-stepper::-webkit-inner-spin-button,
.input-year-stepper::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.btn-year-dropdown-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 28px;
  background: transparent;
  border: none;
  border-left: 1px solid var(--border);
  color: var(--text-muted, #64748b);
  cursor: pointer;
  padding: 0;
  transition: all 0.15s ease;
}

.btn-year-dropdown-toggle:hover {
  background: var(--bg-hover, #f1f5f9);
  color: var(--primary);
}

.year-decade-popover {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 60;
  width: 240px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem;
}

.decade-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--border);
}

.decade-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
}

.btn-decade-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 4px;
  width: 22px;
  height: 22px;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1;
}

.btn-decade-nav:hover {
  background: var(--bg-hover);
  color: var(--text-main);
  border-color: var(--primary);
}

.decade-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  margin-bottom: 0.5rem;
}

.btn-year-cell {
  font-size: 0.74rem;
  padding: 0.35rem 0.15rem;
  border-radius: 4px;
  border: 1px solid transparent;
  background: var(--bg-card);
  color: var(--text-main);
  cursor: pointer;
  font-weight: 600;
  text-align: center;
  transition: all 0.12s ease;
}

.btn-year-cell:hover {
  background: var(--bg-hover);
  border-color: var(--border);
  color: var(--primary);
}

.btn-year-cell.is-selected {
  background: var(--primary);
  color: #ffffff;
  font-weight: 700;
}

.decade-footer {
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--border);
  padding-top: 0.4rem;
}

.btn-decade-quick {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--primary);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
}

.btn-decade-quick:hover {
  background: rgba(37, 99, 235, 0.08);
}

.toolbar-divider {
  width: 1px;
  height: 22px;
  background: var(--border);
  margin: 0 0.25rem;
}

.inline-filter-btn {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.38rem 0.65rem;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-main);
  cursor: pointer;
  min-width: 95px;
  transition: all 0.15s ease;
}

.inline-filter-btn:hover {
  border-color: var(--primary);
}

.inline-filter-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}

.dropdown-arrow-icon {
  font-size: 0.62rem;
  opacity: 0.6;
}

.btn-clear-range-dates {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  background: var(--bg-panel);
  border: 1px dashed var(--border);
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-clear-range-dates:hover {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
}

/* Segmented Buttons para Estado */
.status-segment-group {
  display: inline-flex;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 2px;
}

.segment-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.28rem 0.65rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.segment-btn.is-active {
  background: var(--primary);
  color: #ffffff;
  font-weight: 700;
}

.bottom-controls-bar .control-box:last-child .tray-popover {
  right: 0;
  left: auto;
}

.tray-popover {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  z-index: 50;
  width: 230px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem;
}

.tray-popover-severity {
  width: 210px;
}

.tray-popover-grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem 0.5rem;
  padding-top: 0.2rem;
}

.tray-popover-severity .badge-mini-tag {
  min-width: 52px;
  text-align: center;
}

.tray-search-input {
  width: 100%;
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-hover);
  color: var(--text-main);
  font-size: 0.78rem;
  margin-bottom: 0.5rem;
  outline: none;
}

.tray-popover-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
  font-size: 0.72rem;
}

.tray-popover-actions button {
  border: none;
  background: transparent;
  color: var(--primary);
  font-weight: 700;
  cursor: pointer;
  padding: 0;
}

.tray-popover-list {
  max-height: 180px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.tray-popover-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.78rem;
  cursor: pointer;
}

.tray-row-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tray-empty {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
  padding: 0.5rem 0;
}

/* ========================================================================== */
/* MATRIZ GANTT GRID                                                          */
/* ========================================================================== */
.matrix-scroll-wrapper {
  overflow-x: auto;
  min-height: 120px;
  max-height: 480px;
  position: relative;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  text-align: left;
}

.matrix-table thead th {
  position: sticky;
  top: 0;
  z-index: 8;
  background: var(--bg-hover);
  border-bottom: 2px solid var(--border);
  padding: 0.6rem 0.4rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  user-select: none;
}

.th-fixed-col {
  position: sticky;
  left: 0;
  z-index: 10 !important;
  width: 290px;
  min-width: 290px;
  max-width: 320px;
  background: var(--bg-panel) !important;
  border-right: 1px solid var(--border);
  box-shadow: 4px 0 8px rgba(0, 0, 0, 0.15);
  padding-left: 1rem !important;
}

.th-cve-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.th-time-slot {
  text-align: center;
  min-width: 38px;
  padding: 0.5rem 0.2rem;
  border-left: 1px solid rgba(255, 255, 255, 0.04);
}

.th-time-slot.is-today {
  color: var(--primary);
  background: rgba(99, 102, 241, 0.08);
}

.matrix-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background-color 0.15s;
}

.matrix-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.td-fixed-col {
  position: sticky;
  left: 0;
  z-index: 9;
  background: var(--bg-panel);
  border-right: 1px solid var(--border);
  box-shadow: 4px 0 8px rgba(0, 0, 0, 0.15);
  padding: 0.55rem 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.td-fixed-col:hover {
  background: var(--bg-hover);
}

/* Modo compacto */
.cve-compact-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.cve-code-badge {
  font-weight: 800;
  font-size: 0.8rem;
  color: var(--text-main);
}

/* Modo detallado */
.cve-detailed-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detailed-header-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.cve-title {
  font-weight: 800;
  font-size: 0.82rem;
  color: var(--text-main);
}

.badge-mini-tag {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.badge-critical { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); }
.badge-high { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.4); }
.badge-medium { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.4); }
.badge-low { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }

.cvss-pill {
  font-size: 0.68rem;
  font-weight: 800;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}

.detailed-sub-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.sub-pkg, .sub-agent {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 130px;
}

.td-matrix-cell {
  text-align: center;
  padding: 0.3rem 0.2rem;
  border-left: 1px solid rgba(255, 255, 255, 0.04);
}

.matrix-pill {
  width: 80%;
  max-width: 44px;
  margin: 0 auto;
  height: 13px;
  border-radius: 9999px;
  transition: transform 0.15s ease, opacity 0.15s ease;
  cursor: default;
}

.matrix-pill:hover {
  transform: scale(1.15);
  opacity: 0.9;
}

.pill-active {
  background: #f87171;
  border: none;
}

.pill-mitigated {
  background: #fbbf24;
  border: none;
}

.pill-resolved {
  background: #34d399;
  border: none;
}

.matrix-pill-empty {
  width: 24px;
  margin: 0 auto;
  height: 6px;
  border-radius: 9999px;
  background: rgba(148, 163, 184, 0.12);
  border: none;
}

.matrix-empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  color: var(--text-muted);
}

.empty-icon-wrap {
  margin-bottom: 0.75rem;
}

.matrix-empty-state h4 {
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.3rem;
}

.matrix-empty-state p {
  font-size: 0.85rem;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.fade-in {
  animation: fadeIn 0.15s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-3px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
