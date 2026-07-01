import { defineStore } from "pinia";
import { type IUser } from "@/assets/interfaces/IUser";
import { useHistoryStore } from "@/stores/historyTable.ts";

export const useUserStore = defineStore('userStore', {
    state: () => ({
        user: {} as IUser,
        isLogin: false
    }),
    actions: {
        setUser(user: any) {
            this.user = user;
            this.isLogin = true;
        },
        setLogin(isLogin: boolean) {
            this.user = {} as IUser;
            this.isLogin = isLogin;
            useHistoryStore().setHistoryData([]);
        }
    },
    getters: {
        getId: (state) => state.user.id,
        getAvatar: (state) => state.user.photo,
        getUser: (state) => state.user,
        getFio: (state) => state.user.last_name && state.user.name ? `${state.user.last_name} ${state.user.name} ${state.user.second_name ?? ''}` : null,
        getIsLogin: (state) => state.isLogin

    }
})