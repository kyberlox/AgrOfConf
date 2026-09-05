import { defineStore } from 'pinia'

export const useLayoutStore = defineStore('layoutStore', {
    state: () => ({
        isSidebarRolled: true
    }),
    actions: {
        toggleSidebar() {
            this.isSidebarRolled = !this.isSidebarRolled
        }
    },
    getters: {
        getIsSidebarRolled: (state) => state.isSidebarRolled
    }
})