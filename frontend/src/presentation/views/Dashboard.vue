<template>
  <div class="fade-in dashboard-unified">
    <!-- Header Area -->
    <div class="header-actions">
      <div>
        <h1 class="title">Panorama de Amenazas & Línea de Tiempo</h1>
        <p class="subtitle">Visualiza la evolución temporal de eventos y gestiona el inventario de vulnerabilidades reportado por Wazuh.</p>
      </div>
      <div>
        <button v-if="isAdmin" class="btn btn-primary" @click="syncVulns" :disabled="syncing">
          <svg v-if="syncing" class="spin" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.59-9.5l1.75 1.93"></path></svg>
          {{ syncing ? 'Sincronizando con Wazuh...' : 'Forzar Sincronización' }}
        </button>
        <span v-else class="badge-viewer-notice" title="La sincronización está restringida al rol Administrador">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          Modo Visualizador (Sincronización solo Admin)
        </span>
      </div>
    </div>

    <!-- Error/Warning states -->
    <div v-if="error" class="alert alert-danger fade-in">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      {{ error }}
    </div>

    <div v-if="timelineWarning" class="alert alert-warning fade-in">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      {{ timelineWarning }}
    </div>

    <!-- ====================================================================== -->
    <!-- SECCIÓN 1: LÍNEA DE TIEMPO (PARTE SUPERIOR)                            -->
    <!-- ====================================================================== -->
    <section class="unified-section timeline-panel-section">
      <div class="section-title-bar">
        <div class="title-with-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          <h2 class="section-heading">Línea de Tiempo de Vulnerabilidades</h2>
        </div>
        <span class="section-hint">Filtra por etiquetas, periodo temporal y estado para analizar la evolución</span>
      </div>

      <!-- Timeline Filter Controls -->
      <TimelineFilters
        :connections="connections"
        :agent-options="agentOptions"
        :vuln-options="vulnOptions"
        :tag-options="tagOptions"
        :selected-connection="selectedConnection"
        :selected-agents="selectedAgents"
        :selected-vulns="selectedVulns"
        :selected-tags="selectedTags"
        :status="selectedStatus"
        :period="period"
        :periods="periods"
        :custom-date="customDate"
        :loading="timelineLoading"
        @update:selected-connection="onConnectionSelect"
        @update:selected-agents="selectedAgents = $event"
        @update:selected-vulns="selectedVulns = $event"
        @update:selected-tags="selectedTags = $event"
        @update:custom-date="customDate = $event"
        @set-status="setStatusFilter"
        @set-period="setPeriodFilter"
        @connection-change="onConnectionChange"
        @build="buildTimeline"
      />

      <!-- KPI Summary Strip -->
      <TimelineKpiStrip
        :has-built="hasBuilt"
        :painted-count="paintedCount"
        :latest-snap="latestSnap"
      />

      <!-- Interactive Canvas -->
      <TimelineCanvas
        v-if="hasBuilt && visibleSlots.length > 0"
        :all-slots="allSlots"
        :visible-slots="visibleSlots"
        :painted-count="paintedCount"
        :year-label="yearLabel"
        :active-zoom="activeZoom"
        :can-move-left="canMoveLeft"
        :can-move-right="canMoveRight"
        :can-zoom-in="canZoomIn"
        :can-zoom-out="canZoomOut"
        @move-left="moveLeft"
        @move-right="moveRight"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @open-slot="openTimelineSlot"
      />

      <div v-else-if="!hasBuilt" class="card empty-timeline-card">
        <div class="empty-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          <h3>Línea de tiempo sin generar</h3>
          <p>Selecciona una conexión Wazuh y presiona <strong>"Generar Vista"</strong> para visualizar el historial temporal.</p>
        </div>
      </div>
    </section>

    <!-- ====================================================================== -->
    <!-- SECCIÓN 2: TABLA DE VULNERABILIDADES (PARTE INFERIOR)                 -->
    <!-- ====================================================================== -->
    <section class="unified-section table-panel-section">
      <div class="table-section-header">
        <div class="title-with-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
          <h2 class="section-heading">Inventario de Vulnerabilidades (CVE)</h2>
          <span class="count-pill">{{ sortedVulns.length }} CVEs filtrados</span>
        </div>

        <!-- Filter Toggle Bar (minimalista) -->
        <div class="filter-actions-right">
          <button class="btn-filter-toggle" @click="showFilters = !showFilters">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            <span>{{ showFilters ? 'Ocultar filtros avanzados' : 'Filtros avanzados' }}</span>
          </button>
          <button v-if="showFilters" class="btn-clear-filters" @click="clearFilters">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"></path>
              <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
              <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
            </svg>
            <span>Limpiar</span>
          </button>
        </div>
      </div>

      <!-- Advanced Filters Panel -->
      <div v-show="showFilters" class="card filter-panel">
        <div class="filter-row">
          <div class="f-group">
            <label>Conexión Wazuh</label>
            <select v-model="selectedConnection" @change="onConnectionChange" class="filter-input">
              <option value="">Todas las conexiones</option>
              <option v-for="conn in connections" :key="conn.id" :value="conn.id">{{ conn.name }}</option>
            </select>
          </div>

          <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.agents = false)">
            <label>Agentes</label>
            <button class="filter-input dd-btn" @click="dropdowns.agents = !dropdowns.agents" :disabled="!agentOptions.length">
              <span>{{ selectedAgents.length ? selectedAgents.length + ' sel.' : 'Todos' }}</span>
              <span>▼</span>
            </button>
            <div v-if="dropdowns.agents" class="dd-panel fade-in">
              <input type="text" v-model="search.agent" placeholder="Buscar agente..." class="dd-search">
              <div class="dd-actions">
                <span @click="selectedAgents = [...agentOptions]">Todos</span>
                <span @click="selectedAgents = []">Limpiar</span>
              </div>
              <div class="dd-list custom-scroll">
                <label v-for="agent in filteredAgents" :key="agent" class="dd-item">
                  <input type="checkbox" :value="agent" v-model="selectedAgents"> {{ agent }}
                </label>
              </div>
            </div>
          </div>

          <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.vulns = false)">
            <label>CVE ID</label>
            <button class="filter-input dd-btn" @click="dropdowns.vulns = !dropdowns.vulns" :disabled="!vulnOptions.length">
              <span>{{ selectedVulns.length ? selectedVulns.length + ' sel.' : 'Todas' }}</span>
              <span>▼</span>
            </button>
            <div v-if="dropdowns.vulns" class="dd-panel fade-in">
              <input type="text" v-model="search.vuln" placeholder="Buscar CVE..." class="dd-search">
              <div class="dd-actions">
                <span @click="selectedVulns = [...vulnOptions]">Todas</span>
                <span @click="selectedVulns = []">Limpiar</span>
              </div>
              <div class="dd-list custom-scroll">
                <label v-for="vuln in filteredCVEOptions" :key="vuln" class="dd-item">
                  <input type="checkbox" :value="vuln" v-model="selectedVulns"> {{ vuln }}
                </label>
              </div>
            </div>
          </div>

          <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.packages = false)">
            <label>Software Afectado</label>
            <button class="filter-input dd-btn" @click="dropdowns.packages = !dropdowns.packages" :disabled="!packageOptions.length">
              <span>{{ selectedPackages.length ? selectedPackages.length + ' sel.' : 'Todos' }}</span>
              <span>▼</span>
            </button>
            <div v-if="dropdowns.packages" class="dd-panel fade-in">
              <input type="text" v-model="search.package" placeholder="Buscar software..." class="dd-search">
              <div class="dd-actions">
                <span @click="selectedPackages = [...packageOptions]">Todos</span>
                <span @click="selectedPackages = []">Limpiar</span>
              </div>
              <div class="dd-list custom-scroll">
                <label v-for="pkg in filteredPackages" :key="pkg" class="dd-item">
                  <input type="checkbox" :value="pkg" v-model="selectedPackages"> {{ pkg }}
                </label>
              </div>
            </div>
          </div>

          <div class="f-group popover-wrap" v-click-outside="() => (dropdowns.severity = false)">
            <label>Severidad</label>
            <button class="filter-input dd-btn" @click="dropdowns.severity = !dropdowns.severity" :disabled="!severityOptions.length">
              <span>{{ selectedSeverities.length ? selectedSeverities.length + ' sel.' : 'Todas' }}</span>
              <span>▼</span>
            </button>
            <div v-if="dropdowns.severity" class="dd-panel fade-in">
              <div class="dd-actions">
                <span @click="selectedSeverities = [...severityOptions]">Todas</span>
                <span @click="selectedSeverities = []">Limpiar</span>
              </div>
              <div class="dd-list custom-scroll">
                <label v-for="sev in severityOptions" :key="sev" class="dd-item">
                  <input type="checkbox" :value="sev" v-model="selectedSeverities"> 
                  <span :class="'badge-mini ' + getSeverityBadgeClass(sev)">{{ sev }}</span>
                </label>
              </div>
            </div>
          </div>

          <div class="f-group">
            <label>Score CVSS (Base)</label>
            <div class="range-inputs">
              <input type="number" v-model.number="scoreMin" min="0" max="10" step="0.1" placeholder="Min" class="filter-input-sm">
              <span>-</span>
              <input type="number" v-model.number="scoreMax" min="0" max="10" step="0.1" placeholder="Max" class="filter-input-sm">
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="empty-state">
        <div class="spinner-box">
          <svg class="spin" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
        </div>
        <p>Cargando datos del cluster...</p>
      </div>

      <!-- Table Container -->
      <div v-else class="card" style="padding: 0;">
        <div class="table-wrapper">
          <!-- Top Pagination & Controls Bar -->
          <div class="table-controls-bar">
            <div class="controls-left">
              <label class="per-page-selector">
                <span class="label-text">Mostrar</span>
                <select v-model.number="itemsPerPage" class="per-page-select" aria-label="Cantidad de vulnerabilidades por página">
                  <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="label-text">por página</span>
              </label>
              <span class="pagination-info">
                Mostrando {{ sortedVulns.length ? (currentPage - 1) * itemsPerPage + 1 : 0 }} - {{ Math.min(currentPage * itemsPerPage, sortedVulns.length) }} de {{ sortedVulns.length }} vulnerabilidades
              </span>
            </div>

            <!-- Mini Nav on Top -->
            <div v-if="totalPages > 1" class="pagination-nav">
              <button class="btn-icon-page" :disabled="currentPage === 1" @click="jumpBackward" title="Retroceder 10 páginas" aria-label="Retroceder páginas">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 8 12 13 7"></polyline><polyline points="19 17 14 12 19 7"></polyline></svg>
              </button>
              <button class="btn-icon-page" :disabled="currentPage === 1" @click="prevPage" title="Página anterior" aria-label="Página anterior">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>
              <span class="page-current-indicator">{{ currentPage }} / {{ totalPages }}</span>
              <button class="btn-icon-page" :disabled="currentPage === totalPages" @click="nextPage" title="Página siguiente" aria-label="Página siguiente">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </button>
              <button class="btn-icon-page" :disabled="currentPage === totalPages" @click="jumpForward" title="Avanzar 10 páginas" aria-label="Avanzar páginas">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 16 12 11 7"></polyline><polyline points="5 17 10 12 5 7"></polyline></svg>
              </button>
            </div>
          </div>

          <!-- The Table -->
          <table v-if="vulns.length > 0" class="vuln-table">
            <caption class="visually-hidden">
              Tabla de vulnerabilidades con severidad, CVE, agente, software afectado y linea de tiempo de actividad.
            </caption>
            <thead>
              <tr>
                <th style="width: 10%;" @click="sortBy('connection_name')">
                  Conexión Wazuh
                  <span v-if="sortKey === 'connection_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th style="width: 11%;" @click="sortBy('severity')">
                  Severidad
                  <span v-if="sortKey === 'severity'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th style="width: 8%;" @click="sortBy('score_base')">
                  Score CVSS
                  <span v-if="sortKey === 'score_base'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th class="col-cve" @click="sortBy('cve_id')">
                  CVE ID
                  <span v-if="sortKey === 'cve_id'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th class="col-agent" @click="sortBy('agent_name')">
                  Agente
                  <span v-if="sortKey === 'agent_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th class="col-package" @click="sortBy('package_name')">
                  Software Afectado
                  <span v-if="sortKey === 'package_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th style="width: 8%;" @click="sortBy('dwell_time_days')">
                  Días Activa
                  <span v-if="sortKey === 'dwell_time_days'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th style="width: 8%;" @click="sortBy('total_age_days')">
                  Tiempo Total (Días)
                  <span v-if="sortKey === 'total_age_days'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
                <th class="col-timeline" @click="sortBy('last_seen')">
                  Línea de Tiempo
                  <span v-if="sortKey === 'last_seen'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="vuln in paginatedVulns" :key="vuln.id">
                <td>{{ vuln.connection_name || '-' }}</td>
                <td>
                  <span :class="getSeverityClass(vuln.severity)">
                    {{ (vuln.severity || 'UNKNOWN').toUpperCase() }}
                  </span>
                </td>
                <td class="font-medium score-cell">
                  {{ vuln.score_base != null ? vuln.score_base.toFixed(1) : 'N/A' }}
                </td>
                <td class="font-medium text-black">
                  <code>{{ vuln.cve_id || 'N/A' }}</code>
                </td>
                <td>
                  <div class="agent-info">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
                    <span>{{ vuln.agent_name || vuln.agent_id || 'N/A' }}</span>
                  </div>
                  <div v-if="vuln.tags?.length" class="tag-list" aria-label="Etiquetas Wazuh">
                    <span v-for="tag in vuln.tags" :key="tag" class="badge-mini">{{ tag }}</span>
                  </div>
                </td>
                <td>
                  <div class="package-info">
                    <span class="pkg-name">{{ vuln.package_name }}</span>
                    <span class="pkg-version">v{{ vuln.package_version }}</span>
                  </div>
                </td>
                <td class="font-medium text-center">
                  {{ vuln.dwell_time_days !== undefined && vuln.dwell_time_days !== null ? vuln.dwell_time_days.toFixed(2) : '-' }}
                </td>
                <td class="font-medium text-center">
                  {{ vuln.total_age_days !== undefined && vuln.total_age_days !== null ? vuln.total_age_days.toFixed(2) : '-' }}
                </td>
                <td>
                  <div class="visual-timeline">
                    <!-- Punto de Detección -->
                    <div class="timeline-point start">
                      <div class="point-marker">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                      </div>
                      <div class="point-content">
                        <span class="point-title">Detectado</span>
                        <span class="point-time" :title="formatDate(vuln.first_seen)">{{ timeAgo(vuln.first_seen) }}</span>
                      </div>
                    </div>

                    <!-- Línea Conectora y Dwell Time -->
                    <div style="display: flex; align-items: center;">
                      <div class="timeline-track">
                        <div class="track-progress" :style="{ width: getTimelineProgress(vuln) + '%' }"></div>
                      </div>
                      <span v-if="vuln.dwell_time_days !== undefined" style="font-size: 0.7rem; color: #9ca3af; margin-left: 12px; font-weight: 600; text-transform: uppercase;">
                        Dwell: {{ Math.floor(vuln.dwell_time_days) }}d
                      </span>
                    </div>

                    <!-- Punto de Última Vista -->
                    <div class="timeline-point end">
                      <div class="point-marker" :class="{ 'pulse-radar': isRecentlySeen(vuln.last_seen) }">
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                      </div>
                      <div class="point-content">
                        <span class="point-title">Última actividad</span>
                        <span class="point-time" :title="formatDate(vuln.last_seen)">{{ timeAgo(vuln.last_seen) }}</span>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- ================================================================ -->
          <!-- Paginación Completa Abajo (Selector por página + Navegación)       -->
          <!-- ================================================================ -->
          <div class="pagination-footer-unified">
            <div class="footer-left">
              <label class="per-page-selector">
                <span class="label-text">Mostrar</span>
                <select v-model.number="itemsPerPage" class="per-page-select" aria-label="Cantidad de vulnerabilidades por página">
                  <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="label-text">por página</span>
              </label>
              <span class="pagination-info">
                Página {{ totalPages ? currentPage : 0 }} de {{ totalPages }} ({{ sortedVulns.length }} registros)
              </span>
            </div>

            <div v-if="totalPages > 1" class="pagination-nav">
              <!-- Primera Página -->
              <button class="btn-icon-page" :disabled="currentPage === 1" @click="currentPage = 1" title="Primera página" aria-label="Primera página">
                <span class="nav-symbol">«</span>
              </button>
              <!-- Retroceder de a varias (10 páginas) -->
              <button class="btn-icon-page" :disabled="currentPage === 1" @click="jumpBackward" title="Retroceder 10 páginas" aria-label="Retroceder páginas">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 8 12 13 7"></polyline><polyline points="19 17 14 12 19 7"></polyline></svg>
              </button>
              <!-- Anterior de a una -->
              <button class="btn-icon-page" :disabled="currentPage === 1" @click="prevPage" title="Página anterior" aria-label="Página anterior">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
              </button>

              <!-- Botones numéricos 1, 2, 3, 4, 5, 6, ... -->
              <div class="page-numbers">
                <template v-for="(item, idx) in visiblePages" :key="`bottom-${item}-${idx}`">
                  <button
                    v-if="typeof item === 'number'"
                    class="btn-page"
                    :class="{ 'active': currentPage === item }"
                    @click="currentPage = item"
                  >
                    {{ item }}
                  </button>
                  <span v-else class="pagination-ellipsis">...</span>
                </template>
              </div>

              <!-- Siguiente de a una -->
              <button class="btn-icon-page" :disabled="currentPage === totalPages" @click="nextPage" title="Página siguiente" aria-label="Página siguiente">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              </button>
              <!-- Avanzar de a varias (10 páginas) -->
              <button class="btn-icon-page" :disabled="currentPage === totalPages" @click="jumpForward" title="Avanzar 10 páginas" aria-label="Avanzar páginas">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 16 12 11 7"></polyline><polyline points="5 17 10 12 5 7"></polyline></svg>
              </button>
              <!-- Última Página -->
              <button class="btn-icon-page" :disabled="currentPage === totalPages" @click="currentPage = totalPages" title="Última página" aria-label="Última página">
                <span class="nav-symbol">»</span>
              </button>
            </div>
          </div>

          <!-- Empty State (No records found or demo instructions) -->
          <div v-if="vulns.length === 0 && !loading" class="empty-state" style="padding: 4rem 2rem;">
            <div class="shield-box">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M9 12l2 2 4-4"></path></svg>
            </div>
            <p style="color: var(--text-main); font-weight: 600; font-size: 1.15rem; margin-bottom: 0.5rem;">No se encontraron vulnerabilidades</p>
            <p style="color: var(--text-muted); font-size: 0.9rem; max-width: 500px; margin: 0 auto 1.25rem;">
              No hay vulnerabilidades registradas para los filtros aplicados.
            </p>
            <div class="demo-data-card" v-if="!connections.length">
              <span class="demo-badge">Modo de Demostración Local</span>
              <p>Para cargar el dataset de prueba Wazuh en tu entorno local, ejecuta:</p>
              <code>python vuln-api/app/load-data.py --replace</code>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Modal de detalle de la Línea de Tiempo -->
    <TimelineDetailModal
      :show="timelineModalOpen"
      :event-data="selectedTimelineEvent"
      @close="timelineModalOpen = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, reactive } from 'vue'
import vulnService from '../../application/services/vulnService'
import wazuhService from '../../application/services/wazuhService'
import TimelineFilters from './timeline/components/TimelineFilters.vue'
import TimelineKpiStrip from './timeline/components/TimelineKpiStrip.vue'
import TimelineCanvas from './timeline/components/TimelineCanvas.vue'
import TimelineDetailModal from './timeline/components/TimelineDetailModal.vue'
import useTimelineNavigation from './timeline/useTimelineNavigation'
import useTimelineData from './timeline/useTimelineData'
import { fmtYear } from './timeline/timelineFormatters'

// ============================================================================
// Roles y Permisos
// ============================================================================
const isAdmin = computed(() => {
  const current = localStorage.getItem('role') || 'admin'
  return current === 'admin'
})

// ============================================================================
// Estado General de Vulnerabilidades (Tabla)
// ============================================================================
const vulns = ref([])
const loading = ref(true)
const syncing = ref(false)
const error = ref('')
const sortKey = ref('last_seen')
const sortOrder = ref('desc')
const showFilters = ref(false)

// Paginación
const currentPage = ref(1)
const itemsPerPage = ref(50)
const perPageOptions = [1, 5, 10, 25, 50, 100]
const pageJump = 10

// Filtros avanzados
const connections = ref([])
const agentOptions = ref([])
const vulnOptions = ref([])
const packageOptions = ref([])
const severityOptions = ref([])
const tagOptions = ref([])

const selectedConnection = ref('')
const selectedAgents = ref([])
const selectedVulns = ref([])
const selectedPackages = ref([])
const selectedSeverities = ref([])
const selectedTags = ref([])
const selectedStatus = ref('all') // 'all' | 'active' | 'resolved'
const scoreMin = ref('')
const scoreMax = ref('')

// Dropdown state
const search = reactive({ agent: '', vuln: '', package: '', tag: '' })
const dropdowns = reactive({ agents: false, vulns: false, packages: false, severity: false, tags: false })

// Filtered dropdown options
const filteredAgents = computed(() =>
  agentOptions.value.filter(agent => agent.toLowerCase().includes(search.agent.toLowerCase()))
)

const filteredCVEOptions = computed(() =>
  vulnOptions.value.filter(vuln => vuln.toLowerCase().includes(search.vuln.toLowerCase()))
)

const filteredPackages = computed(() =>
  packageOptions.value.filter(pkg => pkg.toLowerCase().includes(search.package.toLowerCase()))
)

// ============================================================================
// Línea de Tiempo (Timeline Composable y Navegación)
// ============================================================================
const periods = [
  { l: '24H', v: '24h' },
  { l: '7D', v: '7d' },
  { l: '30D', v: '30d' },
  { l: 'Dia', v: 'day' },
  { l: 'Todo', v: 'all' }
]
const period = ref('30d')
const customDate = ref(new Date().toISOString().split('T')[0])
const timelineModalOpen = ref(false)
const selectedTimelineEvent = ref(null)

const getConnectionName = () => {
  const found = connections.value.find(conn => String(conn.id) === String(selectedConnection.value))
  return found?.name || ''
}

let allSlotsRef = null
const navigation = useTimelineNavigation(() => (allSlotsRef ? allSlotsRef.value.length : 0))

const timelineData = useTimelineData({
  selectedConnection,
  selectedAgents,
  selectedVulns,
  selectedTags,
  selectedStatus,
  period,
  customDate,
  activeZoom: navigation.activeZoom,
  getConnectionName
})

const {
  loading: timelineLoading,
  hasBuilt,
  allSlots,
  paintedCount,
  latestSnap,
  errorMessage: timelineError,
  warningMessage: timelineWarning
} = timelineData

allSlotsRef = allSlots

const {
  activeZoom,
  visibleCount,
  viewStartIndex,
  canMoveLeft,
  canMoveRight,
  canZoomIn,
  canZoomOut,
  setZoomLevel,
  zoomIn,
  zoomOut,
  moveLeft,
  moveRight,
  jumpToEnd
} = navigation

const visibleSlots = computed(() =>
  allSlots.value.slice(viewStartIndex.value, viewStartIndex.value + visibleCount.value)
)

const yearLabel = computed(() => {
  if (!visibleSlots.value.length) return ''
  const start = fmtYear(visibleSlots.value[0].startMs)
  const end = fmtYear(visibleSlots.value[visibleSlots.value.length - 1].startMs)
  return start === end ? start : `${start} - ${end}`
})

const setPeriodFilter = (val) => {
  period.value = val
}

const setStatusFilter = (val) => {
  selectedStatus.value = val
  currentPage.value = 1
}

const onConnectionSelect = (val) => {
  selectedConnection.value = val
  onConnectionChange()
}

const buildTimeline = async () => {
  if (!selectedConnection.value) return
  try {
    const { initialZoom } = await timelineData.build()
    setZoomLevel(initialZoom)
    jumpToEnd()
  } catch (err) {
    console.error('Error generating timeline:', err)
  }
}

const openTimelineSlot = (slot) => {
  selectedTimelineEvent.value = slot
  timelineModalOpen.value = true
}

// ============================================================================
// Funciones Utilitarias de Comparación y Severidad
// ============================================================================
const getSeverityLevel = (s) => {
  if (!s) return 0
  const severity = s.toLowerCase()
  if (severity === 'critical' || severity === 'critica') return 4
  if (severity === 'high' || severity === 'alta') return 3
  if (severity === 'medium' || severity === 'media') return 2
  return 1 // low or unknown
}

const compareValues = (a, b, key) => {
  let aVal = a[key]
  let bVal = b[key]

  if (key === 'first_seen' || key === 'last_seen') {
    aVal = aVal ? new Date(aVal).getTime() : 0
    bVal = bVal ? new Date(bVal).getTime() : 0
    return aVal - bVal
  } else if (key === 'severity') {
    aVal = getSeverityLevel(aVal)
    bVal = getSeverityLevel(bVal)
    return aVal - bVal
  } else {
    aVal = aVal || ''
    bVal = bVal || ''
    if (typeof aVal === 'string') {
      return aVal.toLowerCase().localeCompare(bVal.toLowerCase())
    }
    return aVal - bVal
  }
}

const updateFilterOptions = () => {
  const agents = new Set()
  const vulnIds = new Set()
  const packages = new Set()
  const severities = new Set()
  const tags = new Set()

  vulns.value.forEach(vuln => {
    if (vuln.agent_name) agents.add(vuln.agent_name)
    if (vuln.cve_id) vulnIds.add(vuln.cve_id)
    if (vuln.package_name) packages.add(vuln.package_name)
    if (vuln.severity) severities.add(vuln.severity.toUpperCase())
    if (Array.isArray(vuln.tags)) {
      vuln.tags.forEach(t => tags.add(t))
    }
  })

  agentOptions.value = Array.from(agents).sort()
  vulnOptions.value = Array.from(vulnIds).sort()
  packageOptions.value = Array.from(packages).sort()
  tagOptions.value = Array.from(tags).sort()
  severityOptions.value = Array.from(severities).sort((a, b) => {
    const levelA = getSeverityLevel(a.toLowerCase())
    const levelB = getSeverityLevel(b.toLowerCase())
    return levelB - levelA
  })
}

// ============================================================================
// Funciones de Coincidencia de Filtros
// ============================================================================
const matchesConnection = (vuln) => 
  !selectedConnection.value || vuln.connection_id === selectedConnection.value

const matchesAgent = (vuln) => 
  selectedAgents.value.length === 0 || selectedAgents.value.includes(vuln.agent_name)

const matchesVuln = (vuln) => 
  selectedVulns.value.length === 0 || selectedVulns.value.includes(vuln.cve_id)

const matchesPackage = (vuln) => 
  selectedPackages.value.length === 0 || selectedPackages.value.includes(vuln.package_name)

const matchesSeverity = (vuln) => {
  if (selectedSeverities.value.length === 0) return true
  const vulnSeverity = (vuln.severity || 'UNKNOWN').toUpperCase()
  return selectedSeverities.value.includes(vulnSeverity)
}

const matchesScore = (vuln) => {
  if (scoreMin.value === '' && scoreMax.value === '') return true
  const score = vuln.score_base
  if (score === null || score === undefined) return false
  const minOk = scoreMin.value === '' || score >= scoreMin.value
  const maxOk = scoreMax.value === '' || score <= scoreMax.value
  return minOk && maxOk
}

const matchesStatus = (vuln) => {
  if (!selectedStatus.value || selectedStatus.value === 'all') return true
  const statusUpper = (vuln.status || '').toUpperCase()
  if (selectedStatus.value === 'active') return statusUpper === 'ACTIVE'
  if (selectedStatus.value === 'resolved') return statusUpper === 'RESOLVED'
  return true
}

const matchesTags = (vuln) => {
  if (!selectedTags.value || selectedTags.value.length === 0) return true
  if (!Array.isArray(vuln.tags)) return false
  return selectedTags.value.some(tag => vuln.tags.includes(tag))
}

const filteredVulns = computed(() => {
  return vulns.value.filter(vuln => {
    return matchesConnection(vuln) &&
           matchesAgent(vuln) &&
           matchesVuln(vuln) &&
           matchesPackage(vuln) &&
           matchesSeverity(vuln) &&
           matchesScore(vuln) &&
           matchesStatus(vuln) &&
           matchesTags(vuln)
  })
})

const sortedVulns = computed(() => {
  if (!sortKey.value) return filteredVulns.value
  return [...filteredVulns.value].sort((a, b) => {
    const cmp = compareValues(a, b, sortKey.value)
    return sortOrder.value === 'asc' ? cmp : -cmp
  })
})

// ============================================================================
// Paginación
// ============================================================================
const totalPages = computed(() => {
  const size = itemsPerPage.value || 50
  return Math.ceil(sortedVulns.value.length / size)
})

const paginatedVulns = computed(() => {
  const size = itemsPerPage.value || 50
  const start = (currentPage.value - 1) * size
  const end = start + size
  return sortedVulns.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value
  const maxNumericButtons = 7

  if (total <= maxNumericButtons) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  const middleSlots = maxNumericButtons - 2
  pages.push(1)

  let start = Math.max(2, current - Math.floor(middleSlots / 2))
  let end = start + middleSlots - 1

  if (end > total - 1) {
    end = total - 1
    start = end - middleSlots + 1
  }

  if (start > 2) pages.push('left-ellipsis')
  for (let i = start; i <= end; i++) pages.push(i)
  if (end < total - 1) pages.push('right-ellipsis')

  pages.push(total)
  return pages
})

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++
}

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--
}

const jumpBackward = () => {
  currentPage.value = Math.max(1, currentPage.value - pageJump)
}

const jumpForward = () => {
  currentPage.value = Math.min(totalPages.value, currentPage.value + pageJump)
}

// Reset page on filter changes
watch(selectedConnection, () => { currentPage.value = 1 })
watch(selectedAgents, () => { currentPage.value = 1 })
watch(selectedVulns, () => { currentPage.value = 1 })
watch(selectedPackages, () => { currentPage.value = 1 })
watch(selectedSeverities, () => { currentPage.value = 1 })
watch(selectedTags, () => { currentPage.value = 1 })
watch(selectedStatus, () => { currentPage.value = 1 })
watch(scoreMin, () => { currentPage.value = 1 })
watch(scoreMax, () => { currentPage.value = 1 })
watch(sortKey, () => { currentPage.value = 1 })
watch(sortOrder, () => { currentPage.value = 1 })
watch(itemsPerPage, () => { currentPage.value = 1 })

const sortBy = (key) => {
  if (sortKey.value !== key) {
    sortKey.value = key
    sortOrder.value = 'asc'
  } else if (sortOrder.value === 'asc') {
    sortOrder.value = 'desc'
  } else {
    sortKey.value = ''
    sortOrder.value = ''
  }
}

const onConnectionChange = () => {
  selectedAgents.value = []
  selectedVulns.value = []
  selectedPackages.value = []
  selectedSeverities.value = []
  selectedTags.value = []
  scoreMin.value = ''
  scoreMax.value = ''
  if (selectedConnection.value) {
    buildTimeline()
  }
}

const clearFilters = () => {
  selectedConnection.value = ''
  selectedAgents.value = []
  selectedVulns.value = []
  selectedPackages.value = []
  selectedSeverities.value = []
  selectedTags.value = []
  selectedStatus.value = 'all'
  scoreMin.value = ''
  scoreMax.value = ''
}

// ============================================================================
// Carga de Datos API
// ============================================================================
const fetchVulns = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await vulnService.getVulns()
    if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
      vulns.value = res.data
      updateFilterOptions()
    } else {
      vulns.value = []
    }
  } catch (err) {
    // Si falla la API, mantenemos estado controlado
    vulns.value = []
  } finally {
    loading.value = false
  }
}

const fetchConnections = async () => {
  try {
    const res = await wazuhService.getConnections()
    connections.value = res?.data || []
  } catch (err) {
    connections.value = []
  }
}

const syncVulns = async () => {
  if (!isAdmin.value) {
    error.value = 'Solo los administradores tienen permiso para forzar la sincronización.'
    return
  }
  syncing.value = true
  error.value = ''
  try {
    await vulnService.syncVulns()
    await fetchVulns()
    if (selectedConnection.value) {
      await buildTimeline()
    }
  } catch (err) {
    error.value = 'Error durante la sincronización con Wazuh. Verifica tu configuración en Admin Wazuh.'
  } finally {
    syncing.value = false
  }
}

// ============================================================================
// Formateo y Visualización de Fechas / Severidades
// ============================================================================
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const d = new Date(dateString)
  return d.toLocaleDateString('es-ES', { 
    day: '2-digit', month: 'short', year: 'numeric', 
    hour: '2-digit', minute: '2-digit' 
  })
}

const isNew = (firstSeenDate) => {
  if (!firstSeenDate) return false
  const now = new Date()
  const firstSeen = new Date(firstSeenDate)
  const diffTime = Math.abs(now - firstSeen)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays <= 1
}

const getSeverityClass = (severity) => {
  if (!severity) return 'badge badge-low'
  const s = severity.toLowerCase()
  if (['critical', 'high', 'alta', 'critica'].includes(s)) return 'badge badge-critical'
  if (['medium', 'media'].includes(s)) return 'badge badge-medium'
  return 'badge badge-low'
}

const getSeverityBadgeClass = (severity) => {
  const s = severity.toLowerCase()
  if (['critical', 'critica'].includes(s)) return 'badge-critical'
  if (['high', 'alta'].includes(s)) return 'badge-high'
  if (['medium', 'media'].includes(s)) return 'badge-medium'
  return 'badge-low'
}

const isRecentlySeen = (lastSeenDate) => {
  if (!lastSeenDate) return false
  const now = new Date()
  const lastSeen = new Date(lastSeenDate)
  const diffMinutes = Math.floor((now - lastSeen) / (1000 * 60))
  return diffMinutes <= 60
}

const getTimelineProgress = (vuln) => {
  if (vuln.dwell_time_days !== undefined && vuln.total_age_days !== undefined && vuln.total_age_days > 0) {
    if (vuln.dwell_time_days === 0) return 0
    return Math.min(100, Math.max(5, (vuln.dwell_time_days / vuln.total_age_days) * 100))
  }
  if (vuln.first_seen && vuln.last_seen) {
    const first = new Date(vuln.first_seen).getTime()
    const last = new Date(vuln.last_seen).getTime()
    const now = Date.now()
    const totalAge = now - first
    const dwell = last - first
    if (dwell <= 0 || totalAge <= 0) return 0
    return Math.min(100, Math.max(5, (dwell / totalAge) * 100))
  }
  return 0
}

const timeAgo = (date) => {
  if (!date) return 'N/A'
  const seconds = Math.floor((new Date() - new Date(date)) / 1000)
  
  let interval = seconds / 31536000
  if (interval > 1) return `Hace ${Math.floor(interval)} años`
  
  interval = seconds / 2592000
  if (interval > 1) return `Hace ${Math.floor(interval)} meses`
  
  interval = seconds / 86400
  if (interval > 1) return `Hace ${Math.floor(interval)} días`
  
  interval = seconds / 3600
  if (interval > 1) return `Hace ${Math.floor(interval)} horas`
  
  interval = seconds / 60
  if (interval > 1) return `Hace ${Math.floor(interval)} min`
  
  return 'Justo ahora'
}

onMounted(() => {
  fetchConnections()
  fetchVulns()
})
</script>

<style scoped>
.dashboard-unified {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Header & Roles */
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.badge-viewer-notice {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.9rem;
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: var(--radius-sm, 6px);
  font-size: 0.82rem;
  font-weight: 600;
}

/* Sections Styling */
.unified-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title-bar,
.table-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.section-heading {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.section-hint {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.count-pill {
  padding: 0.2rem 0.65rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
}

.filter-actions-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Empty Timeline Card */
.empty-timeline-card {
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.empty-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.empty-center h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-main);
  margin: 0;
}

.empty-center p {
  font-size: 0.88rem;
  color: var(--text-muted);
  margin: 0;
}

/* Table Controls Bar (Top) */
.table-controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1.4rem;
  background: var(--bg-hover);
  border-bottom: 1px solid var(--border);
}

.controls-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.per-page-selector {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
  cursor: pointer;
}

.per-page-select {
  padding: 0.3rem 0.6rem;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-main);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.page-current-indicator {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  padding: 0 0.4rem;
}

/* Bottom Pagination */
.pagination-footer-unified {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.4rem;
  border-top: 1px solid var(--border);
  background: var(--bg-card);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.pagination-nav {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.page-numbers {
  display: flex;
  gap: 0.2rem;
}

.btn-icon-page {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  padding: 0 0.35rem;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-main);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 700;
  font-size: 0.9rem;
}

.btn-icon-page:hover:not(:disabled) {
  background-color: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-icon-page:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-symbol {
  line-height: 1;
}

.btn-page {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  padding: 0 0.35rem;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-page:hover:not(.active) {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.btn-page.active {
  background-color: var(--primary);
  color: #000;
  font-weight: 800;
}

.pagination-ellipsis {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 700;
}

.pagination-info {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}

/* Demo Data Notice */
.demo-data-card {
  margin-top: 1.5rem;
  padding: 1.25rem;
  background: var(--bg-panel);
  border: 1px dashed var(--primary);
  border-radius: var(--radius-md, 8px);
  text-align: center;
}

.demo-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--primary);
  background: rgba(135, 197, 62, 0.12);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  margin-bottom: 0.6rem;
}

.demo-data-card code {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.4rem 0.8rem;
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--primary);
  font-family: monospace;
}

/* Mini visual timeline in table */
.visual-timeline {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.5rem 0;
  min-width: 180px;
}

.timeline-point {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.point-marker {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.start .point-marker {
  background-color: #f3f4f6;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.end .point-marker {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.point-content {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.point-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  color: #9ca3af;
  font-weight: 600;
}

.point-time {
  font-size: 0.85rem;
  color: var(--text-main);
  font-weight: 500;
}

.timeline-track {
  background-color: #f3f4f6;
  border-radius: 2px;
  margin-left: 10px;
  width: 2px;
  height: 12px;
  position: relative;
}

.track-progress {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #3b82f6;
  border-radius: 2px;
}

.pulse-radar {
  position: relative;
}

.pulse-radar::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: #3b82f6;
  opacity: 0.4;
  animation: radar-pulse 2s infinite;
}

@keyframes radar-pulse {
  0% { transform: scale(1); opacity: 0.4; }
  100% { transform: scale(2.5); opacity: 0; }
}

th {
  cursor: pointer;
}

.sort-indicator {
  margin-left: 0.5rem;
  display: inline-block;
  transition: transform 0.2s ease;
}

.vuln-table .col-severity { width: 12%; }
.vuln-table .col-cve { width: 15%; }
.vuln-table .col-agent { width: 15%; }
.vuln-table .col-package { width: 28%; }
.vuln-table .col-timeline { width: 20%; }

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.rotate-180 {
  transform: rotate(180deg);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.spinner-box {
  margin-bottom: 1rem;
}

.shield-box {
  width: 80px;
  height: 80px;
  background-color: var(--success-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  border: 4px solid rgba(16, 185, 129, 0.1);
}

.font-medium {
  font-weight: 500;
}
.text-black {
  color: var(--text-main);
  font-weight: 400;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-muted);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.3rem;
}

.tag-list .badge-mini {
  background: var(--bg-hover);
  color: var(--text-muted);
  text-transform: none;
}

.package-info {
  display: flex;
  flex-direction: column;
}

.pkg-name {
  color: var(--text-main);
  font-weight: 500;
}

.pkg-version {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.alert {
  padding: 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 500;
}

.alert-danger {
  color: var(--danger);
  background-color: var(--danger-bg);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.alert-warning {
  color: var(--warning, #d97706);
  background-color: rgba(217, 119, 6, 0.12);
  border: 1px solid rgba(217, 119, 6, 0.35);
}

.btn-filter-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.8rem;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  border-radius: 6px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.btn-filter-toggle:hover {
  background-color: var(--bg-hover);
  border-color: var(--text-muted);
  color: var(--text-main);
}

.btn-clear-filters {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.8rem;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  border-radius: 6px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.btn-clear-filters:hover {
  background-color: var(--bg-hover);
  border-color: var(--danger);
  color: var(--danger);
}

/* Filter panel styles */
.filter-panel { 
  padding: 0; 
  margin-bottom: 1.5rem; 
  overflow: visible; 
}

.filter-row { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
  align-items: center; 
}

.f-group { 
  display: flex; 
  flex-direction: column; 
  padding: 1rem 1.2rem; 
  border-right: 1px solid var(--border); 
}

.f-group:last-child { 
  border-right: none; 
}

.f-group label { 
  font-size: 0.7rem; 
  font-weight: 700; 
  color: var(--text-muted); 
  text-transform: uppercase; 
  margin-bottom: 0.5rem; 
}

.filter-input, .dd-btn { 
  width: 100%; 
  padding: 0.55rem 0.8rem; 
  border: 1px solid var(--border); 
  background: var(--bg-dark); 
  border-radius: var(--radius-sm); 
  color: var(--text-main); 
  cursor: pointer; 
  font-size: 0.85rem;
}

.filter-input:disabled, .dd-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filter-input-sm {
  width: 100%;
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--border);
  background: var(--bg-dark);
  border-radius: var(--radius-sm);
  color: var(--text-main);
  font-size: 0.8rem;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.range-inputs span {
  color: var(--text-muted);
  font-weight: 600;
}

.popover-wrap { 
  position: relative; 
}

.dd-btn { 
  display: flex; 
  justify-content: space-between; 
}

.dd-panel { 
  position: absolute; 
  top: calc(100% + 6px); 
  left: 0; 
  width: 280px; 
  border: 1px solid var(--border); 
  border-radius: var(--radius-md); 
  background: var(--bg-panel); 
  z-index: 20; 
  overflow: hidden; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dd-search { 
  width: 100%; 
  border: none; 
  border-bottom: 1px solid var(--border); 
  padding: 0.65rem 0.9rem; 
  background: var(--bg-hover); 
  color: var(--text-main); 
}

.dd-actions { 
  display: flex; 
  justify-content: space-between; 
  padding: 0.5rem 0.9rem; 
  border-bottom: 1px solid var(--border); 
  font-size: 0.75rem; 
  color: var(--primary); 
}

.dd-actions span { 
  cursor: pointer; 
}

.dd-actions span:hover { 
  text-decoration: underline; 
}

.dd-list { 
  max-height: 220px; 
  overflow-y: auto; 
}

.dd-item { 
  display: flex; 
  gap: 0.6rem; 
  padding: 0.5rem 0.9rem; 
  font-size: 0.82rem; 
  cursor: pointer;
  align-items: center;
}

.dd-item:hover { 
  background: var(--bg-hover); 
}

.badge-mini {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-critical {
  background: rgba(220, 38, 38, 0.15);
  color: #dc2626;
}

.badge-high {
  background: rgba(234, 88, 12, 0.15);
  color: #ea580c;
}

.badge-medium {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
}

.badge-low {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

@media (max-width: 1100px) {
  .header-actions {
    flex-direction: column;
    gap: 1rem;
  }
  .controls-left,
  .footer-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .table-controls-bar,
  .pagination-footer-unified {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style>
