import { defineStore } from "pinia";
export const useNeuroOlData = defineStore('neuroDataStore', {
    state: () => ({
        olInfo: {},
        name: ''
    }),
    actions: {
        setData(newData: object) {
            this.olInfo = newData
        },
        setOlName(newName: string) {
            this.name = newName
        }
    },
    getters: {
        getOlInfo: (state) => Object.keys(state.olInfo).length ? state.olInfo : null,
        getOlName: (state) => state.name
    }
})