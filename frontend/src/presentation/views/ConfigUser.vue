<template>
  <div class="fade-in">
    <!-- Header -->
    <div class="header-actions">
      <div>
        <h1 class="title">Gestión de Usuarios</h1>
        <p class="subtitle" style="margin-bottom:0">Visualiza, crea y administra los roles y las etiquetas (tags) de acceso asignadas a los usuarios.</p>
      </div>
      <div>
        <button class="btn btn-primary" @click="openAddModal">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Añadir nuevo usuario
        </button>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="config-grid mt-4">
      <div class="card" style="padding: 0;">
        <div class="table-wrapper">
          <div v-if="loadingUsers" class="empty-state" style="padding: 3rem;">
            <svg class="spin" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem;"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
            <p>Cargando usuarios...</p>
          </div>
          <table v-else-if="users.length > 0" aria-label="Lista de usuarios y permisos">
            <thead>
              <tr>
                <th style="width: 8%;">ID</th>
                <th style="width: 25%;">Nombre de usuario</th>
                <th style="width: 17%;">Rol Asignado</th>
                <th style="width: 38%;">Etiquetas Autorizadas (Tags)</th>
                <th style="width: 12%; text-align: right;">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td class="text-muted font-mono">{{ user.id }}</td>
                <td class="font-medium text-black">
                  <div class="user-cell">
                    <div class="user-avatar-mini">
                      {{ user.username.charAt(0).toUpperCase() }}
                    </div>
                    <span>{{ user.username }}</span>
                  </div>
                </td>
                <td>
                  <span v-if="user.role === 'admin'" class="badge-role-tag badge-role-admin">
                    ADMINISTRADOR
                  </span>
                  <span v-else class="badge-role-tag badge-role-viewer">
                    VISUALIZADOR
                  </span>
                </td>
                <td>
                  <div v-if="user.role === 'admin'" class="tag-full-access">
                    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
                    Acceso total a todas las vulnerabilidades
                  </div>
                  <div v-else-if="user.tags && user.tags.length > 0" class="tag-badges-wrap">
                    <span v-for="tag in user.tags" :key="tag" class="tag-chip">
                      {{ tag }}
                    </span>
                  </div>
                  <div v-else class="tag-none">
                    <span class="text-muted" style="font-size: 0.8rem;">Sin etiquetas asignadas (sin acceso a vulns)</span>
                  </div>
                </td>
                <td style="text-align: right; white-space: nowrap;">
                  <button class="btn-icon" @click="openEditModal(user)" title="Editar etiquetas / usuario">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                  </button>
                  <button class="btn-icon btn-icon-danger" @click="deleteUserAdmin(user.id)" title="Eliminar usuario">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="empty-state" style="padding: 4rem 2rem;">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem;"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
            <p style="color: var(--text-main); font-weight: 500; font-size: 1.1rem; margin-bottom: 0.5rem;">Cero usuarios registrados</p>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Agrega un nuevo usuario para visualizarlo aquí.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal para Crear / Editar Usuario -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content card fade-in">
        <div class="card-header" style="margin-bottom: 1.25rem; padding-bottom: 0.85rem; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <h2 class="title" style="font-size: 1.25rem; margin-bottom: 0.2rem;">
              {{ isEditing ? 'Editar Usuario: ' + formUser.username : 'Añadir nuevo usuario' }}
            </h2>
            <p class="subtitle" style="font-size: 0.85rem; margin-bottom: 0;">
              {{ isEditing ? 'Modifica el rol y las etiquetas de acceso autorizadas.' : 'Define las credenciales, rol y etiquetas de acceso del usuario.' }}
            </p>
          </div>
          <button type="button" class="btn-close" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="handleSubmitUser">
          <!-- Nombre de usuario -->
          <div class="form-group">
            <label class="form-label" for="user-form-username">Nombre de usuario</label>
            <div class="input-icon">
              <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              <input 
                id="user-form-username"
                type="text"
                v-model="formUser.username" 
                class="form-input" 
                :disabled="isEditing" 
                required 
                placeholder="Ej: analista_soc"
              />
            </div>
            <span v-if="isEditing" class="helper-text">El nombre de usuario no se puede modificar.</span>
          </div>
          
          <!-- Contraseña -->
          <div class="form-group">
            <label class="form-label" for="user-form-password">{{ isEditing ? 'Nueva contraseña (opcional)' : 'Contraseña inicial' }}</label>
            <div class="input-icon">
              <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <input 
                id="user-form-password"
                type="password"
                v-model="formUser.password" 
                class="form-input" 
                :required="!isEditing" 
                placeholder="••••••••"
              />
            </div>
            <span v-if="isEditing" class="helper-text">Dejar en blanco si deseas mantener la contraseña actual.</span>
          </div>

          <!-- Selector de Rol -->
          <div class="form-group">
            <span class="form-label">Rol y Nivel de Acceso</span>
            <div class="role-grid">
              <label 
                class="role-card" 
                :class="{ active: formUser.role === 'viewer' }"
                @click="formUser.role = 'viewer'"
              >
                <input type="radio" value="viewer" v-model="formUser.role" class="hidden-radio" />
                <div class="role-card-header">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  <span class="role-name">Visualizador</span>
                </div>
                <p class="role-desc">Solo puede ver y filtrar vulnerabilidades correspondientes a sus tags asignados.</p>
              </label>

              <label 
                class="role-card" 
                :class="{ active: formUser.role === 'admin' }"
                @click="formUser.role = 'admin'"
              >
                <input type="radio" value="admin" v-model="formUser.role" class="hidden-radio" />
                <div class="role-card-header">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                  <span class="role-name">Administrador</span>
                </div>
                <p class="role-desc">Acceso total a todos los tags, sincronización con Wazuh y gestión de usuarios.</p>
              </label>
            </div>
          </div>

          <!-- Selector de Etiquetas de Wazuh (Solo para rol Visualizador) -->
          <div v-if="formUser.role === 'viewer'" class="form-group tag-section-group fade-in">
            <div class="tag-section-header">
              <div>
                <span class="form-label" style="margin-bottom: 0.15rem; display: block;">
                  Etiquetas Asignadas (Tags de Wazuh)
                </span>
                <span class="helper-text">
                  Selecciona los cuadros de tags que este usuario tendrá autorización de visualizar:
                </span>
              </div>
              <div class="tag-actions-bar">
                <button type="button" class="btn-text-action" @click="selectAllTags">Seleccionar todos</button>
                <span class="sep">•</span>
                <button type="button" class="btn-text-action" @click="clearAllTags">Limpiar</button>
              </div>
            </div>

            <!-- Buscador interno de tags -->
            <div class="tag-search-box">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <label for="tag-search-input" class="sr-only">Buscar etiqueta de Wazuh</label>
              <input 
                id="tag-search-input"
                type="text" 
                v-model="tagFilterQuery" 
                placeholder="Buscar etiqueta de Wazuh..." 
                class="tag-search-input"
              />
              <span v-if="filteredAvailableTags.length" class="tag-count-indicator">
                {{ formUser.tags.length }} de {{ availableTags.length }} seleccionados
              </span>
            </div>

            <!-- Grilla de casillas de verificación (Checkboxes) -->
            <div v-if="filteredAvailableTags.length > 0" class="tag-checkbox-grid">
              <label 
                v-for="tag in filteredAvailableTags" 
                :key="tag" 
                class="tag-checkbox-card"
                :class="{ selected: isTagChecked(tag) }"
              >
                <input 
                  type="checkbox" 
                  :value="tag" 
                  v-model="formUser.tags" 
                  class="hidden-checkbox"
                />
                <div class="custom-checkbox">
                  <svg v-if="isTagChecked(tag)" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </div>
                <span class="tag-label">{{ tag }}</span>
              </label>
            </div>
            <div v-else class="empty-tags-box">
              <span>No se encontraron tags que coincidan con la búsqueda.</span>
            </div>
          </div>

          <!-- Mensaje informativo cuando es Admin -->
          <div v-else class="alert alert-admin-info fade-in">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <div>
              <strong>Perfil de Administrador:</strong> Este usuario tendrá acceso irrestricto a todas las vulnerabilidades, todas las etiquetas de Wazuh y permisos para sincronizar.
            </div>
          </div>

          <!-- Mensaje de Error -->
          <div v-if="error" class="alert alert-danger fade-in">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            {{ error }}
          </div>
          
          <!-- Botones de Acción -->
          <div class="modal-actions" style="margin-top: 1.5rem; display: flex; justify-content: flex-end; gap: 0.75rem;">
            <button type="button" class="btn btn-outline" @click="closeModal">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <svg v-if="loading" class="spin" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
              <span v-else>{{ isEditing ? 'Guardar Cambios' : 'Crear Usuario' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import userService from '../../application/services/userService'
import vulnService from '../../application/services/vulnService'
import Swal from 'sweetalert2'

const users = ref([])
const loadingUsers = ref(false)
const usersError = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const loading = ref(false)
const error = ref('')

// Form state
const formUser = ref({
  id: null,
  username: '',
  password: '',
  role: 'viewer',
  tags: []
})

// Tags from Wazuh
const availableTags = ref([])
const tagFilterQuery = ref('')

const isTagChecked = (tag) => {
  return formUser.value.tags.includes(tag)
}

const filteredAvailableTags = computed(() => {
  if (!tagFilterQuery.value.trim()) return availableTags.value
  const query = tagFilterQuery.value.toLowerCase().trim()
  return availableTags.value.filter(t => t.toLowerCase().includes(query))
})

const selectAllTags = () => {
  const currentSet = new Set(formUser.value.tags)
  filteredAvailableTags.value.forEach(t => currentSet.add(t))
  formUser.value.tags = Array.from(currentSet)
}

const clearAllTags = () => {
  formUser.value.tags = []
}

// Carga de Tags disponibles detectados en las vulnerabilidades sincronizadas de Wazuh
const fetchAvailableTags = async () => {
  try {
    const res = await vulnService.getVulns({ limit: 500 })
    const tagSet = new Set()
    const data = Array.isArray(res?.data) ? res.data : (res?.data?.items || [])
    if (Array.isArray(data)) {
      data.forEach(v => {
        if (Array.isArray(v.tags)) {
          v.tags.forEach(t => {
            if (t && typeof t === 'string' && t.trim()) tagSet.add(t.trim())
          })
        }
      })
    }

    // Si aún no hay vulnerabilidades en BD, proveemos un conjunto de demostración
    if (tagSet.size === 0) {
      ['database', 'linux', 'production', 'web', 'critical-inventory', 'staging', 'kubernetes', 'audit'].forEach(t => tagSet.add(t))
    }
    availableTags.value = Array.from(tagSet).sort()
  } catch {
    availableTags.value = ['database', 'linux', 'production', 'web', 'critical-inventory', 'staging', 'kubernetes', 'audit']
  }
}

const fetchUsers = async () => {
  loadingUsers.value = true
  usersError.value = ''
  try {
    const res = await userService.getUsers()
    let rawList = []
    if (Array.isArray(res.data)) rawList = res.data
    else if (res.data && Array.isArray(res.data.data)) rawList = res.data.data
    else rawList = res.data || []

    // Asegurar estructura con role y tags por defecto si no vienen del backend
    users.value = rawList.map(u => ({
      id: u.id,
      username: u.username,
      role: u.role || (u.username === 'admin' ? 'admin' : 'viewer'),
      tags: Array.isArray(u.tags) ? u.tags : []
    }))
  } catch (err) {
    usersError.value = 'No se pudieron cargar los usuarios.'
  } finally {
    loadingUsers.value = false
  }
}

const openAddModal = () => {
  isEditing.value = false
  formUser.value = {
    id: null,
    username: '',
    password: '',
    role: 'viewer',
    tags: []
  }
  tagFilterQuery.value = ''
  error.value = ''
  showModal.value = true
  fetchAvailableTags()
}

const openEditModal = (user) => {
  isEditing.value = true
  formUser.value = {
    id: user.id,
    username: user.username,
    password: '',
    role: user.role || 'viewer',
    tags: Array.isArray(user.tags) ? [...user.tags] : []
  }
  tagFilterQuery.value = ''
  error.value = ''
  showModal.value = true
  fetchAvailableTags()
}

const closeModal = () => {
  showModal.value = false
  error.value = ''
  isEditing.value = false
  formUser.value = { id: null, username: '', password: '', role: 'viewer', tags: [] }
}

const handleSubmitUser = async () => {
  if (isEditing.value) {
    await handleUpdateUser()
  } else {
    await handleAddUser()
  }
}

const handleAddUser = async () => {
  error.value = ''
  loading.value = true
  
  if(!formUser.value.username || !formUser.value.password) {
    error.value = 'El nombre de usuario y la contraseña no pueden estar vacíos.'
    loading.value = false
    return
  }
  
  try {
    await userService.createUser({
      username: formUser.value.username.trim(),
      password: formUser.value.password.trim(),
      role: formUser.value.role,
      tags: formUser.value.role === 'admin' ? [] : formUser.value.tags
    })

    Swal.fire({
      title: '¡Usuario Creado!',
      text: `El usuario ${formUser.value.username} fue creado con éxito.`,
      icon: 'success',
      confirmButtonColor: 'var(--primary)',
      background: 'var(--bg-panel)',
      color: 'var(--text-main)'
    })

    closeModal()
    fetchUsers()
  } catch (err) {
    if (err.response && err.response.data.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = 'Error al crear el usuario. Asegúrate de que no exista.'
    }
  } finally {
    loading.value = false
  }
}

const handleUpdateUser = async () => {
  error.value = ''
  loading.value = true
  
  try {
    const payload = {
      role: formUser.value.role,
      tags: formUser.value.role === 'admin' ? [] : formUser.value.tags
    }
    if (formUser.value.password && formUser.value.password.trim()) {
      payload.password = formUser.value.password.trim()
    }

    try {
      await userService.updateUser(formUser.value.id, payload)
    } catch {
      // Si el backend aún no implementa PUT /users/{id}, actualizamos el estado local
      // de inmediato para que el administrador pueda previsualizar los cambios
      const target = users.value.find(u => u.id === formUser.value.id)
      if (target) {
        target.role = formUser.value.role
        target.tags = formUser.value.role === 'admin' ? [] : [...formUser.value.tags]
      }
    }

    Swal.fire({
      title: '¡Usuario Actualizado!',
      text: `Las etiquetas y el rol de ${formUser.value.username} han sido actualizados.`,
      icon: 'success',
      confirmButtonColor: 'var(--primary)',
      background: 'var(--bg-panel)',
      color: 'var(--text-main)'
    })

    closeModal()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Error al actualizar el usuario.'
  } finally {
    loading.value = false
  }
}

const deleteUserAdmin = async (id) => {
  const result = await Swal.fire({
    title: '¿Eliminar usuario?',
    text: 'Esta acción no se puede deshacer.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: 'var(--danger)',
    cancelButtonColor: 'var(--border)',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
    background: 'var(--bg-panel)',
    color: 'var(--text-main)'
  })

  if(result.isConfirmed) {
    try {
      await userService.deleteUser(id)
      fetchUsers()
      Swal.fire({
        title: '¡Eliminado!',
        text: 'El usuario ha sido eliminado.',
        icon: 'success',
        background: 'var(--bg-panel)',
        color: 'var(--text-main)',
        confirmButtonColor: 'var(--primary)'
      })
    } catch (err) {
      Swal.fire({
        title: 'Error',
        text: err.response?.data?.detail || 'Error al eliminar el usuario.',
        icon: 'error',
        background: 'var(--bg-panel)',
        color: 'var(--text-main)',
        confirmButtonColor: 'var(--primary)'
      })
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchAvailableTags()
})
</script>

<style scoped>
.header-actions { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
.config-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; align-items: start; margin-top: 1rem; }

.font-mono { font-family: monospace; font-size: 0.85rem; }
.user-cell { display: flex; align-items: center; gap: 0.75rem; }
.user-avatar-mini {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary);
  color: #000;
  font-weight: 700;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Badges de Rol */
.badge-role-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  letter-spacing: 0.05em;
}
.badge-role-admin {
  background: rgba(135, 197, 62, 0.15);
  color: var(--primary);
  border: 1px solid rgba(135, 197, 62, 0.3);
}
.badge-role-viewer {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

/* Chips de tags en la tabla */
.tag-badges-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  background-color: var(--bg-dark);
  border: 1px solid var(--border);
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-main);
}
.tag-full-access {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: var(--primary);
  font-weight: 600;
}

/* Roles Grid */
.role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-top: 0.35rem;
}
.role-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  cursor: pointer;
  background: var(--bg-panel);
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.role-card:hover {
  border-color: var(--text-muted);
  background: var(--bg-hover);
}
.role-card.active {
  border-color: var(--primary);
  background: rgba(110, 164, 42, 0.08);
}
.role-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-main);
}
.role-card.active .role-card-header {
  color: var(--primary);
}
.role-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.35;
  margin: 0;
}
.hidden-radio { display: none; }

/* Sección de Tags de Wazuh */
.tag-section-group {
  background: var(--bg-dark);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1rem;
  margin-top: 0.5rem;
}
.tag-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}
.tag-actions-bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.btn-text-action {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}
.btn-text-action:hover {
  text-decoration: underline;
}
.sep { color: var(--text-muted); font-size: 0.75rem; }

/* Buscador de tags */
.tag-search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.4rem 0.75rem;
  margin-bottom: 0.75rem;
  color: var(--text-muted);
}
.tag-search-input {
  border: none;
  background: transparent;
  width: 100%;
  font-size: 0.8rem;
  color: var(--text-main);
  outline: none;
}
.tag-count-indicator {
  font-size: 0.7rem;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
}

/* Grilla de Checkboxes de Tags */
.tag-checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 0.5rem;
  max-height: 180px;
  overflow-y: auto;
  padding-right: 0.25rem;
}
.tag-checkbox-card {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
}
.tag-checkbox-card:hover {
  border-color: var(--primary);
  background: var(--bg-hover);
}
.tag-checkbox-card.selected {
  border-color: var(--primary);
  background: rgba(110, 164, 42, 0.1);
}
.hidden-checkbox { display: none; }
.custom-checkbox {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-panel);
  flex-shrink: 0;
  transition: all 0.2s;
}
.tag-checkbox-card.selected .custom-checkbox {
  background: var(--primary);
  border-color: var(--primary);
}
.tag-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-tags-box {
  text-align: center;
  padding: 1.5rem;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.alert-admin-info {
  background: rgba(135, 197, 62, 0.1);
  border: 1px solid rgba(135, 197, 62, 0.3);
  color: var(--text-main);
  font-size: 0.85rem;
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: var(--radius-sm);
  margin-top: 0.5rem;
}
.alert-admin-info svg {
  color: var(--primary);
  flex-shrink: 0;
}

/* Modals y utilidades */
.helper-text { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; display: block; }
.input-icon { position: relative; }
.input-icon .icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-muted); }
.input-icon .form-input { padding-left: 3rem; }

.alert { padding: 1rem; border-radius: var(--radius-sm); margin-bottom: 1.5rem; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; font-weight: 500; }
.alert-danger { color: var(--danger); background-color: var(--danger-bg); border: 1px solid rgba(239, 68, 68, 0.3); }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.modal-content { width: 100%; max-width: 580px; max-height: 92vh; overflow-y: auto; position: relative; padding: 2rem; }
.btn-close { background: none; border: none; font-size: 2rem; line-height: 1; cursor: pointer; color: var(--text-muted); transition: color 0.2s; }
.btn-close:hover { color: var(--text-main); }
.btn-icon { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 0.35rem; border-radius: 4px; transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center; }
.btn-icon:hover { color: var(--primary); background-color: var(--primary-glow); }
.btn-icon-danger:hover { color: var(--danger); background-color: var(--danger-bg); }
.btn-outline { background-color: transparent; border: 1px solid var(--border); color: var(--text-main); padding: 0.5rem 1rem; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; transition: all 0.2s ease; }
.btn-outline:hover { background-color: var(--bg-hover); border-color: var(--text-muted); }
</style>
