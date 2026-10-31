const clickOutside = {
  mounted(el, binding) {
    el.__clickOutsideBinding__ = binding
    el.__clickOutsideHandler__ = event => {
      // Si el elemento clickeado ya fue removido del DOM, ignorar
      if (event.target && !document.contains(event.target)) {
        return
      }
      const currentBinding = el.__clickOutsideBinding__ || binding
      if (!el.contains(event.target) && typeof currentBinding?.value === 'function') {
        currentBinding.value(event)
      }
    }
    document.addEventListener('click', el.__clickOutsideHandler__)
  },
  updated(el, binding) {
    el.__clickOutsideBinding__ = binding
  },
  unmounted(el) {
    document.removeEventListener('click', el.__clickOutsideHandler__)
    delete el.__clickOutsideHandler__
    delete el.__clickOutsideBinding__
  }
}

export default clickOutside
