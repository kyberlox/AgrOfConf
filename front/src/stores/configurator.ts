import { defineStore } from "pinia";

export const useConfiguratorStore = defineStore('configuratorStore', {
    state: () => ({
        error: ['Выбирайте параметры последовательно - доступные значения обновляются автоматически в зависимости от выбранных условий.'],
        errorStatus: 'warning'
    }),
    actions: {
        setError(error: string | string[]) {
            this.error.length = 0
            Array.isArray(error) ? this.error = error : this.error.push(error)
            this.errorStatus = 'error'
        },
        setDefaultError() {
            this.error =
                ['Выбирайте параметры последовательно - доступные значения обновляются автоматически в зависимости от выбранных условий.']
            this.errorStatus = 'warning'
        }
    },
    getters: {
        getError: (state) => state.error,
        getErrorStatus: (state) => state.errorStatus
    }
})