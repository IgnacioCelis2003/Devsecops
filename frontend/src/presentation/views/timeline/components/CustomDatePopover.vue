<template>
  <div class="custom-date-popover-wrapper" v-click-outside="closePopover">
    <!-- Botón disparador con estilo de input nativo moderno -->
    <button
      type="button"
      class="custom-date-trigger"
      :class="{ 'is-active': isOpen }"
      @click="togglePopover"
      :title="modelValue ? formattedFullDate : ''"
      :aria-label="label ? `${label}: ${formattedDisplayDate}` : `Seleccionar fecha: ${formattedDisplayDate}`"
    >
      <span class="date-display-text">{{ formattedDisplayDate }}</span>
      <div class="trigger-icons-wrap">
        <!-- Botón rápido de limpiar con la 'x' si ya hay una fecha -->
        <span
          v-if="modelValue"
          class="btn-quick-clear-icon"
          @click.stop="clearDate"
          title="Limpiar fecha seleccionada"
        >
          &times;
        </span>
        <svg class="calendar-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
          <line x1="16" y1="2" x2="16" y2="6"></line>
          <line x1="8" y1="2" x2="8" y2="6"></line>
          <line x1="3" y1="10" x2="21" y2="10"></line>
        </svg>
      </div>
    </button>

    <!-- Panel desplegable con Barra Desplazable de Meses Continuos -->
    <div v-if="isOpen" class="cal-popover-panel shadow-lg fade-in">
      <!-- Cabecera fija con navegación rápida -->
      <div class="cal-top-bar">
        <span class="cal-hint-text">Desplaza con la rueda o barra</span>
        <div class="cal-nav-buttons">
          <button
            type="button"
            class="btn-cal-nav"
            @click.stop="scrollMonth(-1)"
            title="Mes anterior"
            aria-label="Mes anterior"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <button
            type="button"
            class="btn-cal-nav"
            @click.stop="scrollMonth(1)"
            title="Mes siguiente"
            aria-label="Mes siguiente"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>

      <!-- Fila fija de nombres de días de la semana (L M X J V S D) -->
      <div class="cal-weekdays-sticky">
        <span v-for="w in weekdays" :key="w" class="cal-weekday">{{ w }}</span>
      </div>

      <!-- Contenedor con Barra de Desplazamiento Vertical Continua -->
      <div
        ref="scrollContainer"
        class="cal-months-scroll-container custom-cal-scroll"
      >
        <div
          v-for="mObj in monthsList"
          :key="mObj.key"
          :id="mObj.id"
          class="cal-month-section"
        >
          <!-- Título del Mes -->
          <div class="cal-month-header">
            <span class="cal-month-title">{{ mObj.title }}</span>
          </div>

          <!-- Grilla de días del mes -->
          <div class="cal-days-grid">
            <button
              v-for="d in mObj.daysCount"
              :key="`${mObj.key}-${d}`"
              type="button"
              class="cal-day-cell"
              :class="{
                'day-available': !isDayDisabled(mObj.year, mObj.month, d),
                'day-disabled': isDayDisabled(mObj.year, mObj.month, d),
                'day-selected': isDaySelected(mObj.year, mObj.month, d)
              }"
              :style="d === 1 ? { gridColumnStart: mObj.offset + 1 } : {}"
              :disabled="isDayDisabled(mObj.year, mObj.month, d)"
              @click.stop="selectDate(mObj.year, mObj.month, d)"
              :title="getDateString(mObj.year, mObj.month, d)"
            >
              <span class="day-number">{{ d }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Pie con acciones: Botón Limpiar + Hoy + Cerrar -->
      <div class="cal-footer">
        <button
          type="button"
          class="btn-cal-action action-clear"
          @click.stop="clearDate"
          title="Borrar fecha seleccionada"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
          Limpiar
        </button>

        <div class="footer-actions-right">
          <button type="button" class="btn-cal-action" @click.stop="selectToday">
            Hoy
          </button>
          <button type="button" class="btn-cal-action" @click.stop="closePopover">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import vClickOutside from '@/presentation/directives/clickOutside'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  minDate: {
    type: String,
    default: ''
  },
  maxDate: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'dd/mm/aa'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const isOpen = ref(false)
const scrollContainer = ref(null)

const monthNames = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
]
const weekdays = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

// Parsear formato YYYY-MM-DD
const parseDateParts = (str) => {
  if (!str) return null
  const p = str.split('-').map(Number)
  if (p.length === 3 && !Number.isNaN(p[0]) && !Number.isNaN(p[1]) && !Number.isNaN(p[2])) {
    return { year: p[0], month: p[1] - 1, day: p[2] }
  }
  return null
}

// Formato visible en el botón: dd/mm/aa (ej: 13/03/26)
const formattedDisplayDate = computed(() => {
  const parts = parseDateParts(props.modelValue)
  if (!parts) return props.placeholder
  const d = String(parts.day).padStart(2, '0')
  const m = String(parts.month + 1).padStart(2, '0')
  const aa = String(parts.year).slice(-2)
  return `${d}/${m}/${aa}`
})

const formattedFullDate = computed(() => {
  const parts = parseDateParts(props.modelValue)
  if (!parts) return ''
  const d = String(parts.day).padStart(2, '0')
  const m = String(parts.month + 1).padStart(2, '0')
  return `${d}/${m}/${parts.year}`
})

// Construcción de la lista de meses continuos para la barra de desplazamiento
// Dinámico: audita rangos históricos según minDate / maxDate o +/- años desde el año actual
const monthsList = computed(() => {
  const currentY = new Date().getFullYear()
  const minYear = props.minDate ? new Date(props.minDate).getFullYear() : (currentY - 10)
  const maxYear = props.maxDate ? new Date(props.maxDate).getFullYear() : (currentY + 2)
  const startYear = Math.min(minYear, currentY - 10)
  const endYear = Math.max(maxYear, currentY + 2)
  const list = []

  for (let y = startYear; y <= endYear; y++) {
    for (let m = 0; m < 12; m++) {
      const firstDay = new Date(Date.UTC(y, m, 1)).getUTCDay()
      const mondayOffset = (firstDay + 6) % 7
      const daysCount = new Date(Date.UTC(y, m + 1, 0)).getUTCDate()

      list.push({
        key: `${y}-${m}`,
        id: `cal-m-${y}-${m}`,
        year: y,
        month: m,
        title: `${monthNames[m]} de ${y}`,
        offset: mondayOffset,
        daysCount
      })
    }
  }

  return list
})

// Formateador de fecha YYYY-MM-DD
const getDateString = (y, m, d) => {
  const mStr = String(m + 1).padStart(2, '0')
  const dStr = String(d).padStart(2, '0')
  return `${y}-${mStr}-${dStr}`
}

// Evaluación de deshabilitado y selección
const isDayDisabled = (y, m, d) => {
  const dateStr = getDateString(y, m, d)
  const isBeforeMin = props.minDate && dateStr < props.minDate
  const isAfterMax = props.maxDate && dateStr > props.maxDate
  return Boolean(isBeforeMin || isAfterMax)
}

const isDaySelected = (y, m, d) => {
  return props.modelValue === getDateString(y, m, d)
}

// Scroll automático al mes de la fecha activa
// IMPORTANTE: NO usamos targetEl.scrollIntoView() porque eso desplaza toda la ventana del navegador.
// Ajustamos estrictamente el scrollTop del scrollContainer interno.
const scrollToActiveMonth = () => {
  nextTick(() => {
    if (!scrollContainer.value) return
    const parts = parseDateParts(props.modelValue) || {
      year: new Date().getFullYear(),
      month: new Date().getMonth()
    }
    const targetId = `cal-m-${parts.year}-${parts.month}`
    const targetEl = document.getElementById(targetId)
    if (targetEl && scrollContainer.value) {
      const containerRect = scrollContainer.value.getBoundingClientRect()
      const targetRect = targetEl.getBoundingClientRect()
      const diff = targetRect.top - containerRect.top
      scrollContainer.value.scrollTop += diff
    }
  })
}

const togglePopover = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    scrollToActiveMonth()
  }
}

const closePopover = () => {
  isOpen.value = false
}

// Botones de desplazamiento suave por mes
const scrollMonth = (direction) => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({
    top: direction * 230,
    behavior: 'smooth'
  })
}

// Selección de fecha
const selectDate = (y, m, d) => {
  const dateStr = getDateString(y, m, d)
  emit('update:modelValue', dateStr)
  emit('change', dateStr)
  isOpen.value = false
}

// Limpiar fecha seleccionada
const clearDate = () => {
  emit('update:modelValue', '')
  emit('change', '')
  isOpen.value = false
}

const selectToday = () => {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth()
  const d = now.getDate()

  if (!isDayDisabled(y, m, d)) {
    selectDate(y, m, d)
  } else {
    // Si hoy está fuera del rango permitido, solo desplazarse hasta él sin seleccionar
    const targetEl = document.getElementById(`cal-m-${y}-${m}`)
    if (targetEl && scrollContainer.value) {
      const containerRect = scrollContainer.value.getBoundingClientRect()
      const targetRect = targetEl.getBoundingClientRect()
      scrollContainer.value.scrollTop += (targetRect.top - containerRect.top)
    }
  }
}

watch(() => props.modelValue, () => {
  if (isOpen.value) {
    scrollToActiveMonth()
  }
})
</script>

<style scoped>
.custom-date-popover-wrapper {
  position: relative;
  display: inline-block;
}

/* Botón disparador */
.custom-date-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  background: var(--bg-panel, #ffffff);
  border: 1px solid var(--border, #cbd5e1);
  border-radius: 8px;
  padding: 0.38rem 0.65rem;
  font-size: 0.85rem;
  font-family: inherit;
  font-weight: 500;
  color: var(--text-main, #0f172a);
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  min-width: 135px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.custom-date-trigger:hover {
  border-color: var(--primary, #2563eb);
  background: var(--bg-hover, #f8fafc);
}

.custom-date-trigger.is-active {
  border-color: var(--primary, #2563eb);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.trigger-icons-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-quick-clear-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  font-size: 13px;
  line-height: 1;
  color: var(--text-muted, #94a3b8);
  transition: all 0.15s ease;
}

.btn-quick-clear-icon:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.calendar-icon {
  color: var(--text-muted, #64748b);
  flex-shrink: 0;
}

/* Panel Desplegable */
.cal-popover-panel {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 1000;
  width: 285px;
  background: var(--bg-panel, #ffffff);
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  padding: 0.75rem 0.65rem 0.65rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  user-select: none;
}

/* Barra superior del popover */
.cal-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.45rem;
  padding: 0 0.35rem 0.35rem;
  border-bottom: 1px solid var(--border, #f1f5f9);
}

.cal-hint-text {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.cal-nav-buttons {
  display: flex;
  gap: 0.25rem;
}

.btn-cal-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted, #64748b);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cal-nav:hover {
  background: var(--bg-hover, #f1f5f9);
  color: var(--text-main, #0f172a);
  border-color: var(--border, #cbd5e1);
}

/* Nombres de días de la semana fijos */
.cal-weekdays-sticky {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  padding: 0.25rem 0.2rem;
  background: var(--bg-panel, #ffffff);
  border-bottom: 1px solid var(--border, #f1f5f9);
}

.cal-weekday {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
}

/* Contenedor con Barra de Desplazamiento Vertical Continua */
.cal-months-scroll-container {
  max-height: 250px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.4rem 0.2rem;
  /* Scroll instantáneo al abrir (sin animación lenta de bajada) */
}

.custom-cal-scroll {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

.custom-cal-scroll::-webkit-scrollbar {
  width: 6px;
}

.custom-cal-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-cal-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 9999px;
}

.custom-cal-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Cada sección de mes continuo */
.cal-month-section {
  padding-bottom: 0.85rem;
  border-bottom: 1px dashed rgba(203, 213, 225, 0.4);
  margin-bottom: 0.85rem;
}

.cal-month-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.cal-month-header {
  padding: 0.35rem 0.25rem 0.45rem;
  text-align: left;
}

.cal-month-title {
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--text-main, #0f172a);
  text-transform: capitalize;
}

/* Grilla de 7 columnas para los días */
.cal-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.cal-day-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 0.82rem;
  font-family: inherit;
  border-radius: 6px;
  transition: background 0.12s ease, color 0.12s ease;
}

.cal-day-cell.day-available {
  color: #0f172a !important;
  font-weight: 600;
  cursor: pointer;
}

.cal-day-cell.day-available:hover {
  background: #eff6ff !important;
  color: #2563eb !important;
}

.cal-day-cell.day-disabled {
  color: #cbd5e1 !important;
  cursor: not-allowed;
  pointer-events: none;
  opacity: 0.45;
}

.cal-day-cell.day-selected {
  background: var(--primary, #2563eb) !important;
  color: #ffffff !important;
  font-weight: 700 !important;
  box-shadow: 0 2px 5px rgba(37, 99, 235, 0.35);
}

/* Pie con acciones */
.cal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.45rem;
  padding-top: 0.45rem;
  border-top: 1px solid var(--border, #f1f5f9);
}

.footer-actions-right {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-cal-action {
  border: none;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary, #2563eb);
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.btn-cal-action:hover {
  background: var(--bg-hover, #f1f5f9);
}

.btn-cal-action.action-clear {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  color: #f87171;
}

.btn-cal-action.action-clear:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.fade-in {
  animation: fadeIn 0.15s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
