<template>
  <div class="card filter-panel">
    <div class="filter-row">
      <!-- 1. Conexión Wazuh -->
      <div class="f-group">
        <label>Conexión Wazuh</label>
        <select v-model="connectionModel" @change="emit('connection-change')" class="filter-input">
          <option value="" disabled>Selecciona servidor...</option>
          <option v-for="conn in connections" :key="conn.id" :value="conn.id">{{ conn.name }}</option>
        </select>
      </div>

      <!-- 2. Equipos / Agentes -->
      <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.agents = false)">
        <label>Equipos / Agentes</label>
        <button class="filter-input dd-btn" @click="dropdowns.agents = !dropdowns.agents" :disabled="!agentOptions.length">
          <span class="btn-truncate">{{ selectedAgentsModel.length ? selectedAgentsModel.length + ' sel.' : 'Todos' }}</span>
          <span class="dd-arrow">▼</span>
        </button>
        <div v-if="dropdowns.agents" class="dd-panel fade-in">
          <input type="text" v-model="search.agent" placeholder="Buscar agente..." class="dd-search" autofocus>
          <div class="dd-actions">
            <span @click="selectedAgentsModel = [...agentOptions]">Todos</span>
            <span @click="selectedAgentsModel = []">Limpiar</span>
          </div>
          <div class="dd-list custom-scroll">
            <label v-for="agent in filteredAgents" :key="agent" class="dd-item">
              <input type="checkbox" :value="agent" v-model="selectedAgentsModel">
              <span class="dd-label-text" :title="agent">{{ agent }}</span>
            </label>
            <div v-if="filteredAgents.length === 0" class="dd-empty">No hay coincidencias</div>
          </div>
        </div>
      </div>

      <!-- 3. Severidad -->
      <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.severity = false)">
        <label>Severidad</label>
        <button class="filter-input dd-btn" @click="dropdowns.severity = !dropdowns.severity">
          <span class="btn-truncate">{{ selectedSeveritiesModel.length ? selectedSeveritiesModel.length + ' sel.' : 'Todas' }}</span>
          <span class="dd-arrow">▼</span>
        </button>
        <div v-if="dropdowns.severity" class="dd-panel fade-in">
          <div class="dd-actions">
            <span @click="selectedSeveritiesModel = [...severityOptions]">Todas</span>
            <span @click="selectedSeveritiesModel = []">Limpiar</span>
          </div>
          <div class="dd-list custom-scroll">
            <label v-for="sev in severityOptions" :key="sev" class="dd-item">
              <input type="checkbox" :value="sev.toUpperCase()" v-model="selectedSeveritiesModel">
              <span class="badge-mini" :class="'badge-' + sev.toLowerCase()">{{ sev }}</span>
            </label>
          </div>
        </div>
      </div>

      <!-- 4. Etiquetas (Tags) -->
      <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.tags = false)">
        <label>Etiquetas (Tags)</label>
        <button class="filter-input dd-btn" @click="dropdowns.tags = !dropdowns.tags" :disabled="!tagOptions.length">
          <span class="btn-truncate">{{ selectedTagsModel.length ? selectedTagsModel.length + ' sel.' : 'Todas' }}</span>
          <span class="dd-arrow">▼</span>
        </button>
        <div v-if="dropdowns.tags" class="dd-panel fade-in">
          <input type="text" v-model="search.tag" placeholder="Buscar etiqueta..." class="dd-search" autofocus>
          <div class="dd-actions">
            <span @click="selectedTagsModel = [...tagOptions]">Todas</span>
            <span @click="selectedTagsModel = []">Limpiar</span>
          </div>
          <div class="dd-list custom-scroll">
            <label v-for="tag in filteredTags" :key="tag" class="dd-item">
              <input type="checkbox" :value="tag" v-model="selectedTagsModel">
              <span class="dd-label-text" :title="tag">{{ tag }}</span>
            </label>
            <div v-if="filteredTags.length === 0" class="dd-empty">No hay coincidencias</div>
          </div>
        </div>
      </div>

      <!-- 5. Vulnerabilidad (CVE) -->
      <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.vulns = false)">
        <label>Vulnerabilidad (CVE)</label>
        <button class="filter-input dd-btn" @click="dropdowns.vulns = !dropdowns.vulns" :disabled="!vulnOptions.length">
          <span class="btn-truncate">{{ selectedVulnsModel.length ? selectedVulnsModel.length + ' sel.' : 'Todas' }}</span>
          <span class="dd-arrow">▼</span>
        </button>
        <div v-if="dropdowns.vulns" class="dd-panel fade-in">
          <input type="text" v-model="search.vuln" placeholder="Buscar CVE-XXXX..." class="dd-search" autofocus>
          <div class="dd-actions">
            <span @click="selectedVulnsModel = [...vulnOptions]">Todas</span>
            <span @click="selectedVulnsModel = []">Limpiar</span>
          </div>
          <div class="dd-list custom-scroll">
            <label v-for="vuln in filteredVulns" :key="vuln" class="dd-item">
              <input type="checkbox" :value="vuln" v-model="selectedVulnsModel">
              <span class="dd-label-text font-mono" :title="vuln">{{ vuln }}</span>
            </label>
            <div v-if="filteredVulns.length === 0" class="dd-empty">No hay coincidencias</div>
          </div>
        </div>
      </div>

      <!-- 6. Estado -->
      <div class="f-group">
        <label>Estado</label>
        <div class="chip-row">
          <button
            class="status-chip"
            :class="{ on: status === 'all' }"
            @click="emit('set-status', 'all')"
          >
            Todas
          </button>
          <button
            class="status-chip"
            :class="{ on: status === 'active' }"
            @click="emit('set-status', 'active')"
          >
            Activas
          </button>
          <button
            class="status-chip"
            :class="{ on: status === 'resolved' }"
            @click="emit('set-status', 'resolved')"
          >
            Resueltas
          </button>
        </div>
      </div>

      <!-- 7. Periodo -->
      <div class="f-group">
        <label>Periodo</label>
        <div class="chip-row">
          <button
            v-for="periodOption in periods"
            :key="periodOption.v"
            class="chip"
            :class="{ on: period === periodOption.v }"
            @click="emit('set-period', periodOption.v)"
          >
            {{ periodOption.l }}
          </button>
        </div>
      </div>

      <div class="f-group" v-if="period === 'day'">
        <label>Día</label>
        <input type="date" v-model="customDateModel" class="filter-input">
      </div>

      <!-- 8. Botón Generar / Aplicar -->
      <div class="f-group f-action">
        <button class="btn btn-primary" @click="emit('build')" :disabled="!selectedConnection || loading">
          {{ loading ? 'Analizando...' : 'Generar Vista' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import vClickOutside from '@/presentation/directives/clickOutside'

const props = defineProps({
  connections: { type: Array, required: true },
  agentOptions: { type: Array, required: true },
  vulnOptions: { type: Array, required: true },
  tagOptions: { type: Array, default: () => [] },
  severityOptions: { type: Array, default: () => ['Critical', 'High', 'Medium', 'Low'] },
  selectedConnection: { type: [String, Number], default: '' },
  selectedAgents: { type: Array, required: true },
  selectedVulns: { type: Array, required: true },
  selectedTags: { type: Array, default: () => [] },
  selectedSeverities: { type: Array, default: () => [] },
  status: { type: String, default: 'all' },
  period: { type: String, required: true },
  periods: { type: Array, required: true },
  customDate: { type: String, required: true },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits([
  'update:selectedConnection',
  'update:selectedAgents',
  'update:selectedVulns',
  'update:selectedTags',
  'update:selectedSeverities',
  'update:customDate',
  'connection-change',
  'set-period',
  'set-status',
  'build'
])

const connectionModel = computed({
  get: () => props.selectedConnection,
  set: value => emit('update:selectedConnection', value)
})

const selectedAgentsModel = computed({
  get: () => props.selectedAgents,
  set: value => emit('update:selectedAgents', value)
})

const selectedVulnsModel = computed({
  get: () => props.selectedVulns,
  set: value => emit('update:selectedVulns', value)
})

const selectedTagsModel = computed({
  get: () => props.selectedTags,
  set: value => emit('update:selectedTags', value)
})

const selectedSeveritiesModel = computed({
  get: () => props.selectedSeverities,
  set: value => emit('update:selectedSeverities', value)
})

const customDateModel = computed({
  get: () => props.customDate,
  set: value => emit('update:customDate', value)
})

const search = reactive({ agent: '', vuln: '', tag: '' })
const dropdowns = reactive({ agents: false, vulns: false, tags: false, severity: false })

// Límite de renderizado (máximo 40 items) para que miles de opciones no congelen el DOM
const filteredAgents = computed(() => {
  const q = search.agent.toLowerCase().trim()
  const list = q ? props.agentOptions.filter(a => a.toLowerCase().includes(q)) : props.agentOptions
  return list.slice(0, 40)
})

const filteredVulns = computed(() => {
  const q = search.vuln.toLowerCase().trim()
  const list = q ? props.vulnOptions.filter(v => v.toLowerCase().includes(q)) : props.vulnOptions
  return list.slice(0, 40)
})

const filteredTags = computed(() => {
  const q = search.tag.toLowerCase().trim()
  const list = q ? props.tagOptions.filter(t => t.toLowerCase().includes(q)) : props.tagOptions
  return list.slice(0, 40)
})
</script>

<style scoped>
.filter-panel { padding: 0; margin-bottom: 1.5rem; overflow: visible; }
.filter-row { 
  display: flex; 
  flex-wrap: wrap; 
  align-items: stretch; 
}
.f-group { 
  display: flex; 
  flex-direction: column; 
  padding: 0.85rem 1rem; 
  border-right: 1px solid var(--border);
  min-width: 140px;
  flex: 1 1 auto;
}
.f-group:last-child { border-right: none; }
.f-group label { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.45rem; }
.filter-input, .dd-btn { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--border); background: var(--bg-dark); border-radius: var(--radius-sm); color: var(--text-main); cursor: pointer; font-size: 0.85rem; }

.f-action { 
  flex: 0 0 auto; 
  min-width: 130px; 
  justify-content: flex-end; 
  align-items: center; 
  background: var(--bg-hover); 
  border-right: none; 
}

.popover-wrap { position: relative; }
.dd-btn { display: flex; justify-content: space-between; align-items: center; gap: 0.4rem; }
.btn-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dd-arrow { font-size: 0.65rem; color: var(--text-muted); }

.dd-panel { 
  position: absolute; 
  top: calc(100% + 6px); 
  left: 0; 
  width: 270px; 
  border: 1px solid var(--border); 
  border-radius: var(--radius-md); 
  background: var(--bg-panel); 
  z-index: 50; 
  overflow: hidden; 
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
}
.dd-search { width: 100%; border: none; border-bottom: 1px solid var(--border); padding: 0.6rem 0.85rem; background: var(--bg-hover); color: var(--text-main); font-size: 0.82rem; outline: none; }
.dd-actions { display: flex; justify-content: space-between; padding: 0.45rem 0.85rem; border-bottom: 1px solid var(--border); font-size: 0.75rem; color: var(--primary); font-weight: 600; }
.dd-actions span { cursor: pointer; }
.dd-actions span:hover { text-decoration: underline; }

/* Altura fija mostrando 5-6 elementos con scroll */
.dd-list { max-height: 220px; overflow-y: auto; }
.dd-item { 
  display: flex; 
  align-items: center; 
  gap: 0.6rem; 
  padding: 0.45rem 0.85rem; 
  font-size: 0.82rem; 
  cursor: pointer; 
  transition: background 0.15s;
}
.dd-item:hover { background: var(--bg-hover); }
.dd-label-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dd-empty { padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.8rem; }
.font-mono { font-family: monospace; font-size: 0.8rem; }

.chip-row { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.chip, .status-chip { padding: 0.35rem 0.65rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-dark); font-size: 0.72rem; font-weight: 700; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.chip.on, .status-chip.on { background: var(--primary); border-color: var(--primary); color: #000; }

.badge-mini {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}
.badge-critical { background: rgba(220, 38, 38, 0.15); color: #dc2626; }
.badge-high { background: rgba(234, 88, 12, 0.15); color: #ea580c; }
.badge-medium { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.badge-low { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }

@media (max-width: 1100px) {
  .f-group { border-right: none; border-bottom: 1px solid var(--border); min-width: 45%; }
  .f-action { width: 100%; min-width: 100%; }
}
</style>
