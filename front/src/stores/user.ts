import { defineStore } from "pinia";
import { type IUser } from "@/assets/interfaces/IUser";
export const useUserStore = defineStore('userStore', {
    state: () => ({
        user: {} as IUser
    }),
    actions: {
        setUser(user: any) {
            this.user = user
        }
    },
    getters: {
        getId: (state) => state.user.id,
        getAvatar: (state) => '',
        getUser: (state) => state.user,
        getFio: (state) => state.user.last_name && state.user.name ? `${state.user.last_name} ${state.user.name} ${state.user.second_name ?? ''}` : null
    }
})