import { defineStore } from "pinia";
export const useNeuroOlData = defineStore('neuroDataStore', {
    state: () => ({
        olInfo: {}
    }),
    actions: {
        setData(newData) {
            this.data = newData
        }
    },
    getters: {
        getOlInfo: (state) => state.olInfo
    }
})