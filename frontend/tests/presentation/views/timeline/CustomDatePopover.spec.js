import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CustomDatePopover from '@/presentation/views/timeline/components/CustomDatePopover.vue'

describe('CustomDatePopover.vue', () => {
  it('renders with placeholder when modelValue is empty', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '',
        placeholder: 'Seleccionar fecha'
      }
    })
    expect(wrapper.text()).toContain('Seleccionar fecha')
  })

  it('renders formatted date when modelValue is provided', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15',
        placeholder: 'dd/mm/aa'
      }
    })
    expect(wrapper.text()).toContain('15/03/26')
  })

  it('toggles popover open and close on button click', async () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15'
      }
    })

    const triggerBtn = wrapper.find('.custom-date-trigger')
    expect(wrapper.vm.isOpen).toBe(false)

    await triggerBtn.trigger('click')
    expect(wrapper.vm.isOpen).toBe(true)

    await triggerBtn.trigger('click')
    expect(wrapper.vm.isOpen).toBe(false)
  })

  it('emits update:modelValue and change on selectDate', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15'
      }
    })

    wrapper.vm.selectDate(2026, 2, 20)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['2026-03-20'])
    expect(wrapper.emitted('change')?.[0]).toEqual(['2026-03-20'])
    expect(wrapper.vm.isOpen).toBe(false)
  })

  it('clears date on clearDate', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15'
      }
    })

    wrapper.vm.clearDate()
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([''])
    expect(wrapper.emitted('change')?.[0]).toEqual([''])
    expect(wrapper.vm.isOpen).toBe(false)
  })

  it('sets today date on selectToday', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: ''
      }
    })

    wrapper.vm.selectToday()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const emittedDate = wrapper.emitted('update:modelValue')?.[0]?.[0]
    expect(emittedDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('handles selectToday when today is disabled by minDate', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '',
        minDate: '2099-01-01'
      }
    })

    wrapper.vm.selectToday()
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  it('scrolls to active month when modelValue updates and popover is open', async () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-01-01'
      }
    })

    wrapper.vm.isOpen = true
    await wrapper.setProps({ modelValue: '2026-06-15' })
    expect(wrapper.vm.isOpen).toBe(true)
  })

  it('respects minDate and maxDate in isDayDisabled', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15',
        minDate: '2026-03-10',
        maxDate: '2026-03-20'
      }
    })

    expect(wrapper.vm.isDayDisabled(2026, 2, 5)).toBe(true)
    expect(wrapper.vm.isDayDisabled(2026, 2, 15)).toBe(false)
    expect(wrapper.vm.isDayDisabled(2026, 2, 25)).toBe(true)
  })

  it('closes popover on closePopover', () => {
    const wrapper = mount(CustomDatePopover, {
      props: {
        modelValue: '2026-03-15'
      }
    })

    wrapper.vm.isOpen = true
    wrapper.vm.closePopover()
    expect(wrapper.vm.isOpen).toBe(false)
  })
})
