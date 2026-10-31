import { describe, it, expect, vi, beforeEach } from 'vitest'

const useMock = vi.fn()
const mountMock = vi.fn()
const directiveMock = vi.fn()
const createAppMock = vi.fn(() => ({
  use: useMock,
  mount: mountMock,
  directive: directiveMock,
}))

vi.mock('vue', () => ({
  createApp: createAppMock,
}))

vi.mock('../src/App.vue', () => ({
  default: {},
}))

vi.mock('../src/presentation/router', () => ({
  default: { name: 'mock-router' },
}))

vi.mock('../src/presentation/directives/clickOutside', () => ({
  default: { name: 'mock-click-outside' },
}))

describe('src/main.js', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('inicializa Vue con App, registra directivas, usa router y monta la aplicación', async () => {
    const { default: App } = await import('../src/App.vue')
    const { default: router } = await import('../src/presentation/router')
    const { default: clickOutside } = await import('../src/presentation/directives/clickOutside')

    await import('../src/main.js')

    expect(createAppMock).toHaveBeenCalledWith(App)
    expect(directiveMock).toHaveBeenCalledWith('click-outside', clickOutside)
    expect(useMock).toHaveBeenCalledWith(router)
    expect(mountMock).toHaveBeenCalledWith('#app')
  })
})
