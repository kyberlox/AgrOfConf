import { defineStore } from "pinia";
export const useNeuroOlData = defineStore('neuroDataStore', {
    state: () => ({
        olInfo: {}
    }),
    actions: {
        setData(newData: object) {
            this.olInfo = newData
        }
    },
    getters: {
        getOlInfo: (state) => state.olInfo
    }
})