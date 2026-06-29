import { defineStore } from "pinia";

export const useConfiguratorStore = defineStore('configuratorStore', {
    state: () => ({
        error: ['Выбирайте параметры последовательно - доступные значения обновляются автоматически в зависимости от выбранных условий.'],
        errorStatus: 'warning',
        status: {
            mark: 'XXXXX-XXX-XX-XXXX',
            result: 12,
            status: 'Выполним',
            answeredQuestions: 0,
            allQuestions: 0
        }
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
        },
        setMark(mark: string) {
            this.status.mark = mark
        },
        seftDefaultMark() {
            this.status.mark = 'XXXXX-XXX-XX-XXXX'
        },
        setCovered(count: number) {
            this.status.answeredQuestions = count
        },
        setAllQuestions(count: number) {
            this.status.allQuestions = count
        }
    },
    getters: {
        getError: (state) => state.error,
        getErrorStatus: (state) => state.errorStatus,
        getStatus: (state) => state.status
    }
})