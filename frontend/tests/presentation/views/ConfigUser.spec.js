import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ConfigUser from '@/presentation/views/ConfigUser.vue'
import userService from '@/application/services/userService'
import vulnService from '@/application/services/vulnService'
import Swal from 'sweetalert2'

vi.mock('@/application/services/userService', () => ({
    default: {
        getUsers: vi.fn(),
        createUser: vi.fn(),
        updateUser: vi.fn(),
        deleteUser: vi.fn()
    }
}))

vi.mock('@/application/services/vulnService', () => ({
    default: {
        getVulns: vi.fn()
    }
}))

vi.mock('sweetalert2', () => ({
    default: {
        fire: vi.fn()
    }
}))

describe('ConfigUser.vue', () => {
    const mockUsers = [
        { id: 1, username: 'admin', role: 'admin', tags: [] },
        { id: 2, username: 'analista', role: 'viewer', tags: ['linux', 'web'] }
    ]

    beforeEach(() => {
        vi.clearAllMocks()
        userService.getUsers.mockResolvedValue({ data: mockUsers })
        vulnService.getVulns.mockResolvedValue({
            data: [
                { id: 101, tags: ['linux', 'database'] },
                { id: 102, tags: ['web', 'production'] }
            ]
        })
    })

    it('fetches and displays users on mount', async () => {
        const wrapper = mount(ConfigUser)
        expect(wrapper.vm.loadingUsers).toBe(true)

        await flushPromises()

        expect(wrapper.vm.loadingUsers).toBe(false)
        expect(userService.getUsers).toHaveBeenCalledTimes(1)
        expect(wrapper.vm.users.length).toBe(2)

        const rows = wrapper.findAll('tbody tr')
        expect(rows.length).toBe(2)
        expect(rows[0].text()).toContain('admin')
        expect(rows[1].text()).toContain('analista')
    })

    it('shows error if fetch users fails', async () => {
        userService.getUsers.mockRejectedValueOnce(new Error('Network Error'))
        const wrapper = mount(ConfigUser)

        await flushPromises()

        expect(wrapper.vm.usersError).toBe('No se pudieron cargar los usuarios.')
        expect(wrapper.vm.users.length).toBe(0)
    })

    it('opens and closes add user modal', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        // Open modal
        await wrapper.find('.btn-primary').trigger('click')
        expect(wrapper.vm.showModal).toBe(true)

        // Close modal via Cancel button
        const cancelBtn = wrapper.findAll('.btn-outline').find(b => b.text().includes('Cancelar'))
        await cancelBtn.trigger('click')
        expect(wrapper.vm.showModal).toBe(false)
    })

    it('submits new user correctly', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        await wrapper.find('.btn-primary').trigger('click')

        wrapper.vm.formUser.username = 'new_admin'
        wrapper.vm.formUser.password = 'SuperSecret123'
        wrapper.vm.formUser.role = 'admin'

        userService.createUser.mockResolvedValueOnce({})

        await wrapper.find('form').trigger('submit.prevent')
        await flushPromises()

        expect(userService.createUser).toHaveBeenCalledWith({
            username: 'new_admin',
            password: 'SuperSecret123',
            role: 'admin',
            tags: []
        })
        expect(wrapper.vm.showModal).toBe(false)
        expect(userService.getUsers).toHaveBeenCalledTimes(2)
    })

    it('shows error when creating user without data', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        await wrapper.find('.btn-primary').trigger('click')

        wrapper.vm.formUser.username = ''
        wrapper.vm.formUser.password = ''

        await wrapper.find('form').trigger('submit.prevent')

        expect(wrapper.vm.error).toContain('no pueden estar vacíos')
        expect(userService.createUser).not.toHaveBeenCalled()
    })

    it('handles user creation failure gracefully', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        await wrapper.find('.btn-primary').trigger('click')
        wrapper.vm.formUser.username = 'fail_user'
        wrapper.vm.formUser.password = 'pass'

        userService.createUser.mockRejectedValueOnce({ response: { data: { detail: 'User exists' } } })

        await wrapper.find('form').trigger('submit.prevent')
        await flushPromises()

        expect(wrapper.vm.error).toBe('User exists')
        expect(wrapper.vm.showModal).toBe(true)
    })

    it('handles user creation failure with generic error', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        await wrapper.find('.btn-primary').trigger('click')
        wrapper.vm.formUser.username = 'fail2'
        wrapper.vm.formUser.password = 'pass'

        userService.createUser.mockRejectedValueOnce(new Error('Network error'))

        await wrapper.find('form').trigger('submit.prevent')
        await flushPromises()

        expect(wrapper.vm.error).toContain('Error al crear el usuario')
    })

    it('opens edit modal and updates user successfully', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        // Click edit on the second user (analista)
        const editBtn = wrapper.findAll('tbody tr')[1].findAll('.btn-icon')[0]
        await editBtn.trigger('click')
        await flushPromises()

        expect(wrapper.vm.showModal).toBe(true)
        expect(wrapper.vm.isEditing).toBe(true)
        expect(wrapper.vm.formUser.username).toBe('analista')
        expect(wrapper.vm.formUser.role).toBe('viewer')

        // Change tags and password
        wrapper.vm.formUser.password = 'NewPass123'
        wrapper.vm.formUser.tags = ['linux', 'production']

        userService.updateUser.mockResolvedValueOnce({})

        await wrapper.find('form').trigger('submit.prevent')
        await flushPromises()

        expect(userService.updateUser).toHaveBeenCalledWith(2, {
            role: 'viewer',
            tags: ['linux', 'production'],
            password: 'NewPass123'
        })
        expect(wrapper.vm.showModal).toBe(false)
    })

    it('updates local user state when updateUser service call fails', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        const editBtn = wrapper.findAll('tbody tr')[1].findAll('.btn-icon')[0]
        await editBtn.trigger('click')
        await flushPromises()

        wrapper.vm.formUser.role = 'viewer'
        wrapper.vm.formUser.tags = ['staging']

        userService.updateUser.mockRejectedValueOnce(new Error('Endpoint not implemented'))

        await wrapper.find('form').trigger('submit.prevent')
        await flushPromises()

        expect(wrapper.vm.users[1].tags).toEqual(['staging'])
        expect(wrapper.vm.showModal).toBe(false)
    })

    it('selects and clears all tags in the modal form', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        await wrapper.find('.btn-primary').trigger('click')
        await flushPromises()

        expect(wrapper.vm.availableTags.length).toBeGreaterThan(0)

        // Select all tags
        wrapper.vm.selectAllTags()
        expect(wrapper.vm.formUser.tags.length).toBe(wrapper.vm.availableTags.length)

        // Clear all tags
        wrapper.vm.clearAllTags()
        expect(wrapper.vm.formUser.tags.length).toBe(0)

        // Tag filter query
        wrapper.vm.tagFilterQuery = 'linux'
        expect(wrapper.vm.filteredAvailableTags).toContain('linux')
    })

    it('deletes user successfully after confirmation', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        Swal.fire.mockResolvedValueOnce({ isConfirmed: true })
        userService.deleteUser.mockResolvedValueOnce({})

        const deleteBtn = wrapper.findAll('tbody tr')[0].find('.btn-icon-danger')
        await deleteBtn.trigger('click')

        await flushPromises()

        expect(userService.deleteUser).toHaveBeenCalledWith(1)
        expect(userService.getUsers).toHaveBeenCalledTimes(2)
    })

    it('handles delete failure gracefully with alert', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        Swal.fire.mockResolvedValueOnce({ isConfirmed: true })
        userService.deleteUser.mockRejectedValueOnce({ response: { data: { detail: 'Cannot delete root admin' } } })

        const deleteBtn = wrapper.findAll('tbody tr')[0].find('.btn-icon-danger')
        await deleteBtn.trigger('click')

        await flushPromises()

        expect(userService.deleteUser).toHaveBeenCalledWith(1)
        expect(Swal.fire).toHaveBeenCalledWith(expect.objectContaining({
            title: 'Error',
            text: 'Cannot delete root admin'
        }))
    })

    it('does nothing if delete is cancelled', async () => {
        const wrapper = mount(ConfigUser)
        await flushPromises()

        Swal.fire.mockResolvedValueOnce({ isConfirmed: false })

        const deleteBtn = wrapper.findAll('tbody tr')[0].find('.btn-icon-danger')
        await deleteBtn.trigger('click')

        await flushPromises()

        expect(userService.deleteUser).not.toHaveBeenCalled()
    })
})
