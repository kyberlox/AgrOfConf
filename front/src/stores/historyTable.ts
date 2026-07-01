import { defineStore } from "pinia";
export const useHistoryStore = defineStore('historyStore', {
    state: () => ({
        historyData: [] as Array<Array<string>>
    }),
    actions: {
        setHistoryData(data: string[][]) {
            this.historyData = data;
        }
    },
    getters: {
        getHistoryData: (state) => state.historyData
    }
})