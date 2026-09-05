import { defineStore } from "pinia";

type nav = 'requests' | 'statistics';
export const useNavStore = defineStore('navStore', {
    state: () => ({
        currentNav: 'requests' as nav
    }),
    actions: {
        setCurrentNav(newNav: 'requests' | 'statistics') {
            this.currentNav = newNav
        }
    },
    getters: {
        getCurrentNav: (state) => state.currentNav
    }
})