import { defineStore } from "pinia";
import { type IUser } from "@/assets/interfaces/IUser";
import { useHistoryStore } from "@/stores/historyTable.ts";
import { type IStatisticBlock, type IYearMetric } from '@/assets/interfaces/IStatistic';

export const useUserStore = defineStore('userStore', {
    state: () => ({
        user: {} as IUser,
        isLogin: false,
        monthMetrics: [] as IStatisticBlock[],
        yearMetrics: {} as IYearMetric
    }),
    actions: {
        setUser(user: IUser) {
            this.user = user;
            this.isLogin = true;
        },
        setLogin(isLogin: boolean) {
            this.user = {} as IUser;
            this.isLogin = isLogin;
            useHistoryStore().setHistoryData([]);
        },
        setMonthMetrics(monthMetrics: IStatisticBlock[]) {
            this.monthMetrics = monthMetrics;
        },
        setYearMetrics(yearMetrics: IYearMetric) {
            this.yearMetrics = yearMetrics;
        }
    },
    getters: {
        getId: (state) => state.user.id,
        getAvatar: (state) => state.user.photo,
        getUser: (state) => state.user,
        getFio: (state) => state.user.last_name && state.user.name ? `${state.user.last_name} ${state.user.name} ${state.user.second_name ?? ''}` : null,
        getIsLogin: (state) => state.isLogin,
        getYearMetrics: (state) => state.yearMetrics,
        getMonthMetrics: (state) => state.monthMetrics

    }
})