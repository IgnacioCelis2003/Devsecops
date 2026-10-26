<template>
  <div v-if="!isAuthenticated" class="auth-layout">
    <router-view></router-view>
  </div>
  
  <div v-else class="app-layout fade-in">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand" @click="handleNavClick('/dashboard')" style="cursor: pointer;" title="Ir al Dashboard" role="button" tabindex="0">
        <div class="logo-box">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        </div>
        <span>VulnSync</span>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">MENU PRINCIPAL</div>
        
        <a href="#" @click.prevent="handleNavClick('/dashboard')" class="nav-item" :class="{ 'router-link-active': route.path === '/dashboard' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect></svg>
          Dashboard
        </a>
        
        <a v-if="isAdmin" href="#" @click.prevent="handleNavClick('/config-user')" class="nav-item" :class="{ 'router-link-active': route.path === '/config-user' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          Administrar usuarios
        </a>

        <a v-if="isAdmin" href="#" @click.prevent="handleNavClick('/config-wazuh')" class="nav-item" :class="{ 'router-link-active': route.path === '/config-wazuh' }">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          Administar conexiones Wazuh
        </a>
      </nav>

      <div class="sidebar-footer">
        <router-link to="/change-password" class="nav-item">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          Cambiar Contraseña
        </router-link>
        <button @click="logout" class="nav-item logout-btn">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          Cerrar Sesión
        </button>
      </div>
    </aside>

    <!-- Main Content wrapper -->
    <div class="main-wrapper">
      <header class="header">
        <div class="header-title">{{ currentRouteName }}</div>
        
        <div class="header-user popover-wrap" v-click-outside="() => (userMenuOpen = false)">
          <div class="user-info" @click="userMenuOpen = !userMenuOpen" style="cursor: pointer;" title="Opciones de usuario">
            <span class="user-greeting">Hola,</span>
            <span class="user-name">{{ username }} ▾</span>
          </div>
          <div class="avatar" @click="userMenuOpen = !userMenuOpen" style="cursor: pointer;" title="Opciones de usuario">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
          </div>

          <!-- User Dropdown Menu -->
          <div v-if="userMenuOpen" class="user-dropdown fade-in">
            <div class="user-dropdown-header">
              <span class="user-dd-name">{{ username }}</span>
              <span class="user-dd-role" :class="isAdmin ? 'role-admin' : 'role-viewer'">
                {{ isAdmin ? 'Administrador' : 'Visualizador' }}
              </span>
            </div>
            <div class="user-dropdown-divider"></div>
            <button class="user-dropdown-item" @click="handleNavClick('/change-password'); userMenuOpen = false;">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              <span>Cambiar Contraseña</span>
            </button>
            <button class="user-dropdown-item danger logout-dd-btn" @click="logout">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              <span>Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </header>

      <main class="content">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Swal from 'sweetalert2'
import userService from './application/services/userService'
import vClickOutside from '@/presentation/directives/clickOutside'

const router = useRouter()
const route = useRoute()

const username = ref(localStorage.getItem('username') || 'Usuario')
const userRole = ref(localStorage.getItem('role') || 'admin')
const userMenuOpen = ref(false)

const isAdmin = computed(() => {
  const current = userRole.value || localStorage.getItem('role') || 'admin'
  return current === 'admin'
})

const isAuthenticated = computed(() => {
  return !['Login', 'LoginRoute', 'NotFound'].includes(route.name) && route.path !== '/' && route.path !== '/login'
})

const refreshUserProfile = async () => {
  if (!isAuthenticated.value) return
  const storedUser = localStorage.getItem('username')
  if (storedUser) username.value = storedUser
  const storedRole = localStorage.getItem('role')
  if (storedRole) userRole.value = storedRole

  if (localStorage.getItem('token')) {
    try {
      const res = await userService.getUserMe()
      if (res?.data) {
        if (res.data.username) {
          username.value = res.data.username
          localStorage.setItem('username', res.data.username)
        }
        if (res.data.role) {
          userRole.value = res.data.role
          localStorage.setItem('role', res.data.role)
        }
      }
    } catch {
      // Token will be handled by interceptors/router
    }
  }
}

watch(() => route.path, () => {
  if (isAuthenticated.value) {
    refreshUserProfile()
  }
})

onMounted(() => {
  refreshUserProfile()
})

const currentRouteName = computed(() => {
  switch(route.name) {
    case 'Dashboard': return 'Vulnerabilidades Wazuh'
    case 'ConfigUser': return 'Gestión de Usuarios'
    case 'ConfigWazuh': return 'Configuración de Wazuh'
    case 'ChangePassword': return 'Seguridad de Cuenta'
    case 'NotFound': return 'Página no encontrada'
    default: return ''
  }
})

const handleNavClick = (path) => {
  const mustChange = localStorage.getItem('must_change_password') === 'true'
  if (mustChange) {
    Swal.fire({
      title: 'Acceso bloqueado',
      text: 'Debes cambiar tu contraseña para continuar navegando.',
      icon: 'warning',
      confirmButtonText: 'Entendido',
      background: 'var(--bg-panel)',
      color: 'var(--text-main)',
      confirmButtonColor: 'var(--primary)',
      iconColor: 'var(--warning, #f59e0b)'
    })
  } else {
    router.push(path)
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  userMenuOpen.value = false
  router.push('/login')
}

</script>

<style scoped>
/* App Layout */
.app-layout {
  display: flex;
  height: 100%;
  max-height: 100vh;
  overflow: hidden;
  background-color: var(--bg-dark);
}

.popover-wrap {
  position: relative;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  min-width: 210px;
  background-color: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.45);
  padding: 0.5rem 0;
  z-index: 100;
}

.user-dropdown-header {
  padding: 0.6rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-dd-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-main);
}

.user-dd-role {
  display: inline-block;
  align-self: flex-start;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  letter-spacing: 0.05em;
}

.role-admin {
  background: rgba(135, 197, 62, 0.15);
  color: var(--primary);
  border: 1px solid rgba(135, 197, 62, 0.3);
}

.role-viewer {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.user-dropdown-divider {
  height: 1px;
  background-color: var(--border);
  margin: 0.4rem 0;
}

.user-dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.65rem 1rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-main);
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: var(--transition, all 0.2s);
}

.user-dropdown-item:hover {
  background-color: var(--bg-hover);
  color: var(--primary);
}

.user-dropdown-item.danger {
  color: var(--danger, #ef4444);
}

.user-dropdown-item.danger:hover {
  background-color: var(--danger-bg, rgba(239, 68, 68, 0.1));
  color: #fff;
}

.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top, var(--bg-panel) 0%, var(--bg-dark) 100%);
}

/* Sidebar */
.sidebar {
  width: 280px;
  background-color: var(--bg-panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.sidebar-brand {
  height: 80px;
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  gap: 1rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-main);
  border-bottom: 1px solid var(--border);
}

.logo-box {
  width: 36px;
  height: 36px;
  background: var(--primary);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  box-shadow: 0 0 12px var(--primary-glow);
}

.nav-section {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  padding: 1.5rem 1.5rem 0.75rem;
  letter-spacing: 0.1em;
}

.sidebar-nav {
  flex-grow: 1;
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.85rem 1.5rem;
  color: var(--text-muted);
  font-weight: 500;
  font-size: 0.95rem;
  transition: var(--transition);
  border-left: 3px solid transparent;
  background: transparent;
  width: 100%;
  border-top: none;
  border-right: none;
  border-bottom: none;
  cursor: pointer;
}

.nav-item:hover {
  color: var(--primary);
  background-color: rgba(31, 138, 59, 0.10);
  text-decoration: none;
}

.nav-item.router-link-active {
  color: var(--primary);
  background-color: rgba(135, 197, 62, 0.1);
  border-left-color: var(--primary);
}

.nav-item.router-link-active svg {
  color: var(--primary);
}

.sidebar-footer {
  padding: 1rem 0;
  border-top: 1px solid var(--border);
}

.logout-btn {
  color: var(--danger);
  font-family: inherit;
  text-align: left;
}
.logout-btn:hover {
  color: #fff;
  background-color: var(--danger-bg);
}
.logout-btn:hover svg {
  stroke: var(--danger);
}

/* Main Content Wrapper */
.main-wrapper {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Header */
.header {
  height: 80px;
  min-height: 80px;
  background-color: var(--bg-dark);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-main);
}

.header-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  display: flex;
  flex-direction: column;
  text-align: right;
}

.user-greeting {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.user-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-main);
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  border: 1px solid var(--border);
}

/* Content Area */
.content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 2.5rem;
}
</style>
