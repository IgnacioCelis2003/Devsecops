<template>
  <div class="fade-in dashboard-unified">


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

        <div class="title-bar-actions">
          <button v-if="isAdmin" class="btn btn-primary btn-sync-header" @click="syncVulns" :disabled="syncing" title="Sincronizar nuevas detecciones con Wazuh">
            <svg v-if="syncing" class="spin" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.59-9.5l1.75 1.93"></path></svg>
            {{ syncing ? 'Sincronizando...' : 'Forzar Sincronización' }}
          </button>
          <span v-else class="badge-viewer-notice badge-viewer-notice-sm" title="La sincronización está restringida al rol Administrador">
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            Modo Visualizador
          </span>
        </div>
      </div>

      <!-- Matriz Temporal Estilo Gantt con Barra Maestra Integrada (Opción A) -->
      <TimelineMatrixGrid
        :vulns="vulns"
        :loading="loading || timelineLoading"
        :connections="connections"
        :selected-connection="selectedConnection"
        :agent-options="agentOptions"
        :selected-agents="selectedAgents"
        :severity-options="severityOptions"
        :selected-severities="selectedSeverities"
        :tag-options="tagOptions"
        :selected-tags="selectedTags"
        :selected-status="selectedStatus"
        :total-records="totalRecordsDisplay"
        :active-count="activeCount"
        :mitigated-count="mitigatedCount"
        :resolved-count="resolvedCount"
        :current-page="currentPage"
        :total-pages="totalPages"
        :items-per-page="itemsPerPage"
        :per-page-options="perPageOptions"
        @update:selected-connection="onConnectionSelect"
        @update:selected-agents="selectedAgents = $event"
        @update:selected-severities="selectedSeverities = $event"
        @update:selected-tags="selectedTags = $event"
        @update:selected-status="setStatusFilter"
        @update:items-per-page="itemsPerPage = $event"
        @prev-page="prevPage"
        @next-page="nextPage"
        @refresh="onConnectionChange"
        @select-vuln="onMatrixVulnSelect"
      />
    </section>

    <!-- ====================================================================== -->
    <!-- SECCIÓN 2: TABLA DE VULNERABILIDADES (PARTE INFERIOR)                 -->
    <!-- ====================================================================== -->
    <section class="unified-section table-panel-section">
      <div class="table-section-header">
        <div class="title-with-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
          <h2 class="section-heading">Inventario de Vulnerabilidades (CVE)</h2>
          <span class="count-pill">{{ totalRecordsDisplay }} CVEs filtrados</span>
        </div>

        <!-- Selector de Columnas Visibles (Top Right) -->
        <div class="col-picker-container" v-click-outside="closeColumnPicker">
          <button
            type="button"
            class="btn-col-picker"
            :class="{ 'btn-col-picker-active': showColumnPicker }"
            @click="toggleColumnPicker"
            title="Personalizar columnas visibles de la tabla"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="9" y1="3" x2="9" y2="21"></line>
              <line x1="15" y1="3" x2="15" y2="21"></line>
            </svg>
            <span class="btn-picker-text">Columnas</span>
            <span class="col-counter-pill">{{ visibleColumnIds.length }}/{{ AVAILABLE_COLUMNS.length }}</span>
            <svg class="chevron-arrow" :class="{ 'rotate-180': showColumnPicker }" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>

          <!-- Popover desplegable estilo chips/pills -->
          <div v-if="showColumnPicker" class="col-picker-popover shadow-md fade-in">
            <div class="col-picker-header">
              <div class="cp-header-text">
                <div class="cp-title-row">
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2.2">
                    <path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18"/>
                  </svg>
                  <span class="cp-title">Selector de Columnas</span>
                </div>
                <span class="cp-subtitle">Selecciona los campos para mostrar u ocultar</span>
              </div>
              <button
                type="button"
                class="btn-reset-columns"
                @click="resetColumnsToDefault"
                title="Restablecer columnas por defecto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="1 4 1 10 7 10"></polyline>
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
                </svg>
                Restablecer
              </button>
            </div>

            <div class="col-picker-content">
              <div class="pill-chips-container">
                <button
                  v-for="col in AVAILABLE_COLUMNS"
                  :key="col.id"
                  type="button"
                  class="pill-chip-btn"
                  :class="{
                    'is-active': isColVisible(col.id),
                    'is-locked': col.locked
                  }"
                  :disabled="col.locked"
                  @click="toggleColumn(col.id)"
                  :title="col.locked ? 'Esta columna es obligatoria y siempre permanece visible' : `Alternar visibilidad de ${col.label}`"
                >
                  <span class="pill-round-checkbox">
                    <svg v-if="col.locked" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                      <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    <svg v-else-if="isColVisible(col.id)" xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </span>
                  <span class="pill-chip-text">{{ col.label }}</span>
                  <span v-if="col.locked" class="pill-locked-tag">Fija</span>
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- Loading State Inicial (solo si la tabla no tiene datos aún) -->
      <div v-if="loading && totalRecordsDisplay === 0 && (!vulns || vulns.length === 0)" class="empty-state">
        <div class="spinner-box">
          <svg class="spin" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
        </div>
        <p>Cargando datos del cluster...</p>
      </div>

      <!-- Table Container (permanece montado; no se destruye en transiciones de página) -->
      <div v-else class="card" style="padding: 0;">
        <div class="table-wrapper">
          <!-- Top Pagination & Controls Bar (Solo cuando hay registros) -->
          <div v-if="totalRecordsDisplay > 0" class="table-controls-bar">
            <div class="controls-left">
              <label class="per-page-selector">
                <span class="label-text">Mostrar</span>
                <select v-model.number="itemsPerPage" class="per-page-select" aria-label="Cantidad de vulnerabilidades por página">
                  <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="label-text">por página</span>
              </label>
              <span class="pagination-info">
                Mostrando {{ totalRecordsDisplay ? (currentPage - 1) * itemsPerPage + 1 : 0 }} - {{ Math.min(currentPage * itemsPerPage, totalRecordsDisplay) }} de {{ totalRecordsDisplay }} vulnerabilidades
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
          <table v-if="totalRecordsDisplay > 0" class="vuln-table">
            <caption class="visually-hidden">
              Tabla de vulnerabilidades con severidad, CVE, agente, software afectado y linea de tiempo de actividad.
            </caption>
            <thead>
              <tr>
                <!-- 1. Conexión (Fija / Obligatoria) -->
                <th v-if="isColVisible('connection_name')" class="col-connection" @click="sortBy('connection_name')">
                  Conexión
                  <span v-if="sortKey === 'connection_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 2. Severidad (Fija / Obligatoria) -->
                <th v-if="isColVisible('severity')" class="col-severity" @click="sortBy('severity')">
                  Severidad
                  <span v-if="sortKey === 'severity'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 3. CVSS (Fija / Obligatoria) -->
                <th v-if="isColVisible('score_base')" class="col-score" @click="sortBy('score_base')">
                  CVSS
                  <span v-if="sortKey === 'score_base'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 4. CVE ID (Fija / Obligatoria) -->
                <th v-if="isColVisible('cve_id')" class="col-cve" @click="sortBy('cve_id')">
                  CVE ID
                  <span v-if="sortKey === 'cve_id'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 5. Estado (Opcional Wazuh) -->
                <th v-if="isColVisible('status')" class="col-status" @click="sortBy('status')">
                  Estado
                  <span v-if="sortKey === 'status'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 6. Agente / Equipo (Default activo) -->
                <th v-if="isColVisible('agent_name')" class="col-agent" @click="sortBy('agent_name')">
                  Agente / Equipo
                  <span v-if="sortKey === 'agent_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 7. ID Agente (Opcional Wazuh) -->
                <th v-if="isColVisible('agent_id')" class="col-agent-id" @click="sortBy('agent_id')">
                  ID Agente
                  <span v-if="sortKey === 'agent_id'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 8. Sistema Operativo (Opcional Wazuh) -->
                <th v-if="isColVisible('os')" class="col-os" @click="sortBy('os_full')">
                  Sistema Operativo
                  <span v-if="sortKey === 'os_full'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 9. Software Afectado (Default activo) -->
                <th v-if="isColVisible('package_name')" class="col-package" @click="sortBy('package_name')">
                  Software Afectado
                  <span v-if="sortKey === 'package_name'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 10. Arquitectura / Tipo (Opcional Wazuh) -->
                <th v-if="isColVisible('package_arch')" class="col-arch" @click="sortBy('package_arch')">
                  Arquitectura / Tipo
                  <span v-if="sortKey === 'package_arch'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 11. Días Activa (Default activo) -->
                <th v-if="isColVisible('dwell_time_days')" class="col-dwell" @click="sortBy('dwell_time_days')">
                  Días Activa
                  <span v-if="sortKey === 'dwell_time_days'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 12. Tiempo Total (Default activo) -->
                <th v-if="isColVisible('total_age_days')" class="col-age" @click="sortBy('total_age_days')">
                  Tiempo Total
                  <span v-if="sortKey === 'total_age_days'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 13. Fecha Detección (Opcional Wazuh) -->
                <th v-if="isColVisible('detected_at')" class="col-detected" @click="sortBy('detected_at')">
                  Fecha Detección
                  <span v-if="sortKey === 'detected_at'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 14. Fecha NVD (Opcional Wazuh) -->
                <th v-if="isColVisible('published_at')" class="col-published" @click="sortBy('published_at')">
                  Fecha NVD
                  <span v-if="sortKey === 'published_at'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 15. Scanner / Proveedor (Opcional Wazuh) -->
                <th v-if="isColVisible('scanner_vendor')" class="col-vendor" @click="sortBy('scanner_vendor')">
                  Scanner / Proveedor
                  <span v-if="sortKey === 'scanner_vendor'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 16. Etiquetas (Opcional Wazuh) -->
                <th v-if="isColVisible('tags')" class="col-tags" @click="sortBy('tags')">
                  Etiquetas
                  <span v-if="sortKey === 'tags'" class="sort-indicator">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="4" :class="sortOrder === 'asc' ? '' : 'rotate-180'">
                      <path d="M7 14l5-5 5 5z"/>
                    </svg>
                  </span>
                </th>

                <!-- 17. Línea de Tiempo (Default activo) -->
                <th v-if="isColVisible('timeline')" class="col-timeline" @click="sortBy('last_seen')">
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
              <tr
                v-for="vuln in paginatedVulns"
                :key="vuln.id"
                :id="'vuln-row-' + vuln.id"
                :class="{ 'row-matrix-highlighted': highlightedVulnId === vuln.id }"
              >
                <!-- 1. Conexión -->
                <td v-if="isColVisible('connection_name')" :title="vuln.connection_name" class="cell-truncate">
                  {{ vuln.connection_name || '-' }}
                </td>

                <!-- 2. Severidad -->
                <td v-if="isColVisible('severity')">
                  <span :class="getSeverityClass(vuln.severity)">
                    {{ (vuln.severity || 'UNKNOWN').toUpperCase() }}
                  </span>
                </td>

                <!-- 3. CVSS -->
                <td v-if="isColVisible('score_base')" class="font-medium score-cell text-center">
                  {{ vuln.score_base != null ? vuln.score_base.toFixed(1) : 'N/A' }}
                </td>

                <!-- 4. CVE ID -->
                <td v-if="isColVisible('cve_id')" class="font-medium text-black">
                  <code>{{ vuln.cve_id || 'N/A' }}</code>
                </td>

                <!-- 5. Estado -->
                <td v-if="isColVisible('status')" class="text-center">
                  <span
                    class="badge-status-pill"
                    :class="getStatusBadgeClass(vuln.status)"
                  >
                    {{ (vuln.status || 'ACTIVE').toUpperCase() }}
                  </span>
                </td>

                <!-- 6. Agente / Equipo -->
                <td v-if="isColVisible('agent_name')">
                  <div class="agent-info" :title="vuln.agent_name || vuln.agent_id">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>
                    <span class="cell-truncate">{{ vuln.agent_name || vuln.agent_id || 'N/A' }}</span>
                  </div>
                  <div v-if="!isColVisible('tags') && vuln.tags?.length" class="tag-list" aria-label="Etiquetas Wazuh">
                    <span v-for="tag in vuln.tags" :key="tag" class="badge-mini">{{ tag }}</span>
                  </div>
                </td>

                <!-- 7. ID Agente -->
                <td v-if="isColVisible('agent_id')" class="text-center">
                  <code class="agent-id-code">{{ vuln.agent_id || '-' }}</code>
                </td>

                <!-- 8. Sistema Operativo -->
                <td v-if="isColVisible('os')" :title="vuln.os_full || vuln.os_platform || '-'" class="cell-truncate">
                  {{ vuln.os_full || vuln.os_platform || '-' }}
                </td>

                <!-- 9. Software Afectado -->
                <td v-if="isColVisible('package_name')">
                  <div class="package-info" :title="vuln.package_name + ' ' + (vuln.package_version || '')">
                    <span class="pkg-name cell-truncate">{{ vuln.package_name }}</span>
                    <span class="pkg-version cell-truncate">v{{ vuln.package_version }}</span>
                  </div>
                </td>

                <!-- 10. Arquitectura / Tipo -->
                <td v-if="isColVisible('package_arch')" class="cell-truncate" :title="`${vuln.package_arch || '-'} (${vuln.package_type || '-'})`">
                  <span>{{ vuln.package_arch || '-' }}</span>
                  <span v-if="vuln.package_type" class="text-muted" style="font-size: 0.75rem;"> ({{ vuln.package_type }})</span>
                </td>

                <!-- 11. Días Activa -->
                <td v-if="isColVisible('dwell_time_days')" class="font-medium text-center">
                  {{ vuln.dwell_time_days !== undefined && vuln.dwell_time_days !== null ? vuln.dwell_time_days.toFixed(1) : '-' }}
                </td>

                <!-- 12. Tiempo Total -->
                <td v-if="isColVisible('total_age_days')" class="font-medium text-center">
                  {{ vuln.total_age_days !== undefined && vuln.total_age_days !== null ? vuln.total_age_days.toFixed(1) : '-' }}
                </td>

                <!-- 13. Fecha Detección -->
                <td v-if="isColVisible('detected_at')" class="text-muted cell-truncate" :title="formatDate(vuln.detected_at || vuln.first_seen)">
                  {{ formatDate(vuln.detected_at || vuln.first_seen) }}
                </td>

                <!-- 14. Fecha NVD -->
                <td v-if="isColVisible('published_at')" class="text-muted cell-truncate" :title="vuln.published_at ? formatDate(vuln.published_at) : 'Sin fecha publicada NVD'">
                  {{ vuln.published_at ? formatDate(vuln.published_at) : 'N/D' }}
                </td>

                <!-- 15. Scanner / Proveedor -->
                <td v-if="isColVisible('scanner_vendor')" class="cell-truncate" :title="vuln.scanner_vendor || 'Wazuh'">
                  {{ vuln.scanner_vendor || 'Wazuh' }}
                </td>

                <!-- 16. Etiquetas (Tags) -->
                <td v-if="isColVisible('tags')">
                  <div v-if="vuln.tags?.length" class="tag-list" aria-label="Etiquetas Wazuh">
                    <span v-for="tag in vuln.tags" :key="tag" class="badge-mini">{{ tag }}</span>
                  </div>
                  <span v-else class="text-muted">-</span>
                </td>

                <!-- 17. Línea de Tiempo -->
                <td v-if="isColVisible('timeline')">
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
          <!-- Paginación Completa Abajo (Solo cuando existen registros)          -->
          <!-- ================================================================ -->
          <div v-if="totalRecordsDisplay > 0" class="pagination-footer-unified">
            <div class="footer-left">
              <label class="per-page-selector">
                <span class="label-text">Mostrar</span>
                <select v-model.number="itemsPerPage" class="per-page-select" aria-label="Cantidad de vulnerabilidades por página">
                  <option v-for="opt in perPageOptions" :key="opt" :value="opt">{{ opt }}</option>
                </select>
                <span class="label-text">por página</span>
              </label>
              <span class="pagination-info">
                Página {{ totalPages ? currentPage : 0 }} de {{ totalPages }} ({{ totalRecordsDisplay }} registros)
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

          <!-- Empty State (Cuando NO hay registros) -->
          <div v-else-if="!loading" class="empty-state" style="padding: 4.5rem 2rem;">
            <div class="shield-box" style="margin-bottom: 1.25rem;">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="8" y1="12" x2="16" y2="12"></line>
              </svg>
            </div>
            <p style="color: var(--text-main); font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem;">No hay datos disponibles que mostrar</p>
            <p style="color: var(--text-muted); font-size: 0.9rem; max-width: 480px; margin: 0 auto;">
              No se encontraron vulnerabilidades registradas para la conexión o los filtros seleccionados.
            </p>
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
import Swal from 'sweetalert2'
import vulnService from '../../application/services/vulnService'
import wazuhService from '../../application/services/wazuhService'
import vClickOutside from '@/presentation/directives/clickOutside'
import TimelineFilters from './timeline/components/TimelineFilters.vue'
import TimelineKpiStrip from './timeline/components/TimelineKpiStrip.vue'
import TimelineCanvas from './timeline/components/TimelineCanvas.vue'
import TimelineMatrixGrid from './timeline/components/TimelineMatrixGrid.vue'
import TimelineDetailModal from './timeline/components/TimelineDetailModal.vue'
import useTimelineNavigation from './timeline/useTimelineNavigation'
import useTimelineData from './timeline/useTimelineData'
import { fmtYear } from './timeline/timelineFormatters'

// ============================================================================
// Roles y Permisos
// ============================================================================
const isAdmin = computed(() => {
  const current = localStorage.getItem('role') || 'viewer'
  return current === 'admin'
})

// ============================================================================
// Estado General de Vulnerabilidades (Tabla)
// ============================================================================
// ============================================================================
// Configuración de Columnas Visibles (Selector de Columnas)
// ============================================================================
const AVAILABLE_COLUMNS = [
  // 4 columnas obligatorias fijas (Requerimiento estricto)
  { id: 'connection_name', label: 'Conexión', locked: true, default: true, sortKey: 'connection_name' },
  { id: 'severity', label: 'Severidad', locked: true, default: true, sortKey: 'severity' },
  { id: 'score_base', label: 'CVSS', locked: true, default: true, sortKey: 'score_base' },
  { id: 'cve_id', label: 'CVE ID', locked: true, default: true, sortKey: 'cve_id' },

  // 5 columnas activas por defecto (desactivables a gusto)
  { id: 'agent_name', label: 'Agente / Equipo', locked: false, default: true, sortKey: 'agent_name' },
  { id: 'package_name', label: 'Software Afectado', locked: false, default: true, sortKey: 'package_name' },
  { id: 'dwell_time_days', label: 'Días Activa', locked: false, default: true, sortKey: 'dwell_time_days' },
  { id: 'total_age_days', label: 'Tiempo Total', locked: false, default: true, sortKey: 'total_age_days' },
  { id: 'timeline', label: 'Línea de Tiempo', locked: false, default: true, sortKey: 'last_seen' },

  // Columnas adicionales de Wazuh disponibles para activar/desactivar
  { id: 'status', label: 'Estado', locked: false, default: false, sortKey: 'status' },
  { id: 'os', label: 'Sistema Operativo', locked: false, default: false, sortKey: 'os_full' },
  { id: 'agent_id', label: 'ID Agente', locked: false, default: false, sortKey: 'agent_id' },
  { id: 'package_arch', label: 'Arquitectura / Tipo', locked: false, default: false, sortKey: 'package_arch' },
  { id: 'detected_at', label: 'Fecha Detección', locked: false, default: false, sortKey: 'detected_at' },
  { id: 'published_at', label: 'Fecha NVD', locked: false, default: false, sortKey: 'published_at' },
  { id: 'scanner_vendor', label: 'Scanner / Proveedor', locked: false, default: false, sortKey: 'scanner_vendor' },
  { id: 'tags', label: 'Etiquetas (Tags)', locked: false, default: false, sortKey: 'tags' }
]

const MANDATORY_COLUMN_IDS = ['connection_name', 'severity', 'score_base', 'cve_id']
const DEFAULT_COLUMN_IDS = AVAILABLE_COLUMNS.filter(c => c.default).map(c => c.id)
const STORAGE_KEY_COLUMNS = 'dashboard_visible_columns'

const showColumnPicker = ref(false)
const toggleColumnPicker = () => {
  showColumnPicker.value = !showColumnPicker.value
}
const closeColumnPicker = () => {
  showColumnPicker.value = false
}

const loadSavedColumns = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_COLUMNS)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) {
        // Asegurar que las 4 columnas obligatorias siempre estén presentes
        const merged = Array.from(new Set([...MANDATORY_COLUMN_IDS, ...parsed]))
        const validIds = new Set(AVAILABLE_COLUMNS.map(c => c.id))
        return merged.filter(id => validIds.has(id))
      }
    }
  } catch (e) {
    console.warn('Error al cargar columnas desde localStorage', e)
  }
  return [...DEFAULT_COLUMN_IDS]
}

const visibleColumnIds = ref(loadSavedColumns())

const isColVisible = (id) => visibleColumnIds.value.includes(id)

const toggleColumn = (id) => {
  if (MANDATORY_COLUMN_IDS.includes(id)) return // Protegida contra desactivación
  const idx = visibleColumnIds.value.indexOf(id)
  if (idx >= 0) {
    visibleColumnIds.value.splice(idx, 1)
  } else {
    visibleColumnIds.value.push(id)
  }
  try {
    localStorage.setItem(STORAGE_KEY_COLUMNS, JSON.stringify(visibleColumnIds.value))
  } catch (e) {
    console.warn('Error al guardar columnas en localStorage', e)
  }
}

const resetColumnsToDefault = () => {
  visibleColumnIds.value = [...DEFAULT_COLUMN_IDS]
  try {
    localStorage.setItem(STORAGE_KEY_COLUMNS, JSON.stringify(visibleColumnIds.value))
  } catch (e) {
    console.warn('Error al guardar columnas en localStorage', e)
  }
}

const vulns = ref([])
const totalRecords = ref(0)
const isServerPaginated = ref(false)
const loading = ref(true)
const syncing = ref(false)
const error = ref('')
const sortKey = ref('last_seen')
const sortOrder = ref('desc')
const showFilters = ref(false)

// Paginación de la Tabla de Inventario
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

const activeCount = computed(() => {
  if (latestSnap.value && latestSnap.value.pending != null && latestSnap.value.pending > 0) {
    return latestSnap.value.pending
  }
  return vulns.value.filter(v => (v.status || '').toUpperCase() === 'ACTIVE').length
})

const resolvedCount = computed(() => {
  if (latestSnap.value && latestSnap.value.resolved != null && latestSnap.value.resolved > 0) {
    return latestSnap.value.resolved
  }
  return vulns.value.filter(v => (v.status || '').toUpperCase() === 'RESOLVED').length
})

const mitigatedCount = computed(() => {
  return vulns.value.filter(v => (v.status || '').toUpperCase() === 'MITIGATED').length
})

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

const onConnectionSelect = async (val) => {
  selectedConnection.value = val
  await onConnectionChange()
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

const highlightedVulnId = ref(null)

const onMatrixVulnSelect = (vulnId) => {
  highlightedVulnId.value = vulnId
  const el = document.getElementById(`vuln-row-${vulnId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
  setTimeout(() => {
    highlightedVulnId.value = null
  }, 2500)
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

  if (key === 'first_seen' || key === 'last_seen' || key === 'detected_at' || key === 'published_at') {
    aVal = aVal ? new Date(aVal).getTime() : 0
    bVal = bVal ? new Date(bVal).getTime() : 0
    return aVal - bVal
  } else if (key === 'severity') {
    aVal = getSeverityLevel(aVal)
    bVal = getSeverityLevel(bVal)
    return aVal - bVal
  } else if (key === 'tags') {
    const aLen = Array.isArray(a.tags) ? a.tags.length : 0
    const bLen = Array.isArray(b.tags) ? b.tags.length : 0
    return aLen - bLen
  } else if (key === 'os_full') {
    aVal = a.os_full || a.os_platform || ''
    bVal = b.os_full || b.os_platform || ''
    return aVal.toLowerCase().localeCompare(bVal.toLowerCase())
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
  !selectedConnection.value || String(vuln.connection_id) === String(selectedConnection.value)

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
  if (selectedStatus.value === 'resolved') return statusUpper === 'RESOLVED' || statusUpper === 'MITIGATED'
  return true
}

const matchesTags = (vuln) => {
  if (!selectedTags.value || selectedTags.value.length === 0) return true
  if (!Array.isArray(vuln.tags)) return false
  return selectedTags.value.some(tag => vuln.tags.includes(tag))
}

const totalRecordsDisplay = computed(() => {
  return isServerPaginated.value ? totalRecords.value : sortedVulns.value.length
})

const filteredVulns = computed(() => {
  if (isServerPaginated.value) {
    return vulns.value
  }
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
  if (isServerPaginated.value) {
    return vulns.value
  }
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
  const total = totalRecordsDisplay.value
  return Math.max(1, Math.ceil(total / size))
})

const paginatedVulns = computed(() => {
  if (isServerPaginated.value) {
    return vulns.value
  }
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

const onFilterOrSortChange = () => {
  if (currentPage.value === 1) {
    if (isServerPaginated.value) {
      fetchVulns()
    }
  } else {
    currentPage.value = 1
  }
}

watch(currentPage, () => {
  if (isServerPaginated.value) {
    fetchVulns()
  }
})

watch(itemsPerPage, () => {
  onFilterOrSortChange()
})

watch([
  selectedAgents,
  selectedVulns,
  selectedPackages,
  selectedSeverities,
  selectedTags,
  selectedStatus,
  scoreMin,
  scoreMax,
  sortKey,
  sortOrder
], () => {
  onFilterOrSortChange()
}, { deep: true })

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

const onConnectionChange = async () => {
  selectedAgents.value = []
  selectedVulns.value = []
  selectedPackages.value = []
  selectedSeverities.value = []
  selectedTags.value = []
  scoreMin.value = ''
  scoreMax.value = ''
  // Sincronizar inventario completo con la conexión seleccionada (Backend Server-Side)
  await fetchVulns(selectedConnection.value)
  if (selectedConnection.value) {
    await buildTimeline()
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
// Carga de Datos API (Server-Side Puro con Postgres LIMIT/OFFSET)
// ============================================================================
const fetchVulns = async (connectionId = null) => {
  loading.value = true
  error.value = ''
  try {
    const connId = connectionId !== null ? connectionId : selectedConnection.value
    const params = {
      page: currentPage.value || 1,
      pageSize: itemsPerPage.value || 50,
      sortBy: sortKey.value || 'last_seen',
      sortDir: sortOrder.value || 'desc',
    }
    if (connId) {
      params.connectionId = connId
    }
    if (selectedStatus.value && selectedStatus.value !== 'all') {
      if (selectedStatus.value === 'active') {
        params.status = ['ACTIVE']
      } else if (selectedStatus.value === 'resolved') {
        params.status = ['RESOLVED', 'MITIGATED']
      }
    }
    if (selectedSeverities.value && selectedSeverities.value.length > 0) {
      params.severity = selectedSeverities.value
    }
    if (selectedAgents.value && selectedAgents.value.length > 0) {
      params.agentNames = selectedAgents.value
    }
    if (selectedVulns.value && selectedVulns.value.length > 0) {
      params.cveIds = selectedVulns.value
    }
    if (selectedPackages.value && selectedPackages.value.length > 0) {
      params.packageNames = selectedPackages.value
    }
    if (selectedTags.value && selectedTags.value.length > 0) {
      params.tags = selectedTags.value
    }
    if (scoreMin.value !== '' && scoreMin.value != null) {
      params.scoreMin = Number(scoreMin.value)
    }
    if (scoreMax.value !== '' && scoreMax.value != null) {
      params.scoreMax = Number(scoreMax.value)
    }

    const res = await vulnService.getVulns(params)

    if (res?.data) {
      if (res.data.items && Array.isArray(res.data.items)) {
        isServerPaginated.value = true
        vulns.value = res.data.items
        totalRecords.value = res.data.total ?? res.data.items.length
      } else if (Array.isArray(res.data)) {
        isServerPaginated.value = false
        vulns.value = res.data
        totalRecords.value = res.data.length
      } else {
        vulns.value = []
        totalRecords.value = 0
        isServerPaginated.value = false
      }
      updateFilterOptions()
    } else {
      vulns.value = []
      totalRecords.value = 0
      isServerPaginated.value = false
    }
  } catch (err) {
    vulns.value = []
    totalRecords.value = 0
    isServerPaginated.value = false
  } finally {
    loading.value = false
  }
}

const fetchConnections = async () => {
  try {
    const res = await wazuhService.getConnections()
    connections.value = res?.data || []
    if (!selectedConnection.value && connections.value.length > 0) {
      selectedConnection.value = connections.value[0].id
    }
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

const getStatusBadgeClass = (status) => {
  const s = (status || 'ACTIVE').toUpperCase()
  if (s === 'ACTIVE') return 'status-active'
  if (s === 'RESOLVED') return 'status-resolved'
  if (s === 'MITIGATED') return 'status-mitigated'
  if (s === 'IN_REVIEW') return 'status-in-review'
  return 'status-active'
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

onMounted(async () => {
  const accessDeniedMsg = sessionStorage.getItem('access_denied_message')
  if (accessDeniedMsg) {
    sessionStorage.removeItem('access_denied_message')
    Swal.fire({
      title: 'Acceso Restringido',
      text: accessDeniedMsg,
      icon: 'warning',
      confirmButtonColor: 'var(--primary)',
      background: 'var(--bg-panel)',
      color: 'var(--text-main)',
    })
  }
  await fetchConnections()
  await fetchVulns(selectedConnection.value)
  if (selectedConnection.value) {
    buildTimeline()
  }
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
.title-bar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.btn-sync-header {
  padding: 0.42rem 0.95rem;
  font-size: 0.82rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border-radius: var(--radius-sm, 6px);
  white-space: nowrap;
}

.badge-viewer-notice-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  gap: 0.35rem;
}

/* Sections Styling */
.unified-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.timeline-panel-section {
  position: relative;
  z-index: 25;
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
  gap: 0.35rem;
  padding: 0.25rem 0;
  min-width: 110px;
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

.vuln-table {
  width: 100%;
  min-width: 100%;
  table-layout: auto;
  border-collapse: collapse;
}

.vuln-table th,
.vuln-table td {
  padding: 0.8rem 0.75rem;
  font-size: 0.84rem;
  vertical-align: middle;
  white-space: nowrap;
}

.vuln-table th {
  white-space: nowrap;
  user-select: none;
}

.vuln-table .col-connection { min-width: 110px; }
.vuln-table .col-severity { min-width: 105px; }
.vuln-table .col-score { min-width: 75px; text-align: center; }
.vuln-table .col-cve { min-width: 135px; }
.vuln-table .col-status { min-width: 95px; text-align: center; }
.vuln-table .col-agent { min-width: 150px; }
.vuln-table .col-agent-id { min-width: 90px; text-align: center; }
.vuln-table .col-os { min-width: 145px; }
.vuln-table .col-package { min-width: 175px; }
.vuln-table .col-arch { min-width: 130px; }
.vuln-table .col-dwell { min-width: 85px; text-align: center; }
.vuln-table .col-age { min-width: 90px; text-align: center; }
.vuln-table .col-detected { min-width: 135px; }
.vuln-table .col-published { min-width: 135px; }
.vuln-table .col-vendor { min-width: 120px; }
.vuln-table .col-tags { min-width: 140px; }
.vuln-table .col-timeline { min-width: 190px; }

/* Selector de Columnas Visibles (Image 3 inspired) */
.col-picker-container {
  position: relative;
  display: inline-block;
}

.btn-col-picker {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.45rem 0.85rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-main);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-col-picker:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--primary);
}

.btn-col-picker-active {
  border-color: var(--primary);
  background: rgba(110, 164, 42, 0.08);
  color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

.col-counter-pill {
  padding: 0.15rem 0.5rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--text-muted);
}

.btn-col-picker-active .col-counter-pill {
  background: var(--primary);
  color: #ffffff;
  border-color: var(--primary);
}

.chevron-arrow {
  transition: transform 0.2s ease;
  color: var(--text-muted);
}

.col-picker-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 780px;
  max-width: 95vw;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md, 10px);
  box-shadow: 0 12px 30px -5px rgba(0, 0, 0, 0.18), 0 8px 12px -6px rgba(0, 0, 0, 0.1);
  z-index: 50;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.col-picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1.15rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-hover);
}

.cp-header-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.cp-title-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.cp-title {
  font-weight: 700;
  font-size: 0.92rem;
  color: var(--text-main);
}

.cp-subtitle {
  font-size: 0.74rem;
  color: var(--text-muted);
}

.btn-reset-columns {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.65rem;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-reset-columns:hover {
  background: var(--bg-card);
  border-color: var(--primary);
  color: var(--primary);
}

.col-picker-content {
  padding: 1rem 1.15rem;
  max-height: 420px;
  overflow-y: auto;
}

/* Grilla Horizontal de 4 Columnas para Pastillas */
.pill-chips-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.55rem;
}

@media (max-width: 820px) {
  .col-picker-popover {
    width: 95vw;
  }
  .pill-chips-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

.pill-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.4rem 0.65rem;
  background: var(--bg-card);
  border: 1.5px solid var(--border);
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-main);
  cursor: pointer;
  user-select: none;
  transition: all 0.18s ease;
  width: 100%;
  justify-content: flex-start;
  box-sizing: border-box;
}

.pill-chip-btn:hover:not(:disabled) {
  border-color: #9ca3af;
  background: var(--bg-hover);
}

.pill-chip-btn.is-active {
  background: rgba(110, 164, 42, 0.08);
  border-color: var(--primary);
  color: var(--text-main);
  font-weight: 600;
}

.pill-chip-btn.is-locked {
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #374151;
  cursor: not-allowed;
  opacity: 0.95;
}

.pill-round-checkbox {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  border: 1.5px solid #d1d5db;
  background: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
  color: #ffffff;
}

.pill-chip-btn.is-active .pill-round-checkbox {
  background: var(--primary);
  border-color: var(--primary);
}

.pill-chip-btn.is-locked .pill-round-checkbox {
  background: #6b7280;
  border-color: #6b7280;
  color: #ffffff;
}

.pill-chip-text {
  line-height: 1.2;
}

.pill-locked-tag {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  background: #e5e7eb;
  color: #4b5563;
  margin-left: 0.15rem;
}

.col-picker-footer {
  padding: 0.65rem 1.1rem;
  background: var(--bg-hover);
  border-top: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--text-muted);
}

.cp-footer-note {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Badges de estado */
.badge-status-pill {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

.badge-status-pill.status-active {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
  border: 1px solid rgba(220, 38, 38, 0.25);
}


.badge-status-pill.status-mitigated {
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.badge-status-pill.status-in-review {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.badge-status-pill.status-resolved {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.agent-id-code {
  font-size: 0.78rem;
  padding: 0.2rem 0.45rem;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-muted);
}

.cell-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

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

.row-matrix-highlighted {
  background-color: rgba(99, 102, 241, 0.25) !important;
  outline: 2px solid var(--primary);
  transition: all 0.4s ease;
}
</style>
