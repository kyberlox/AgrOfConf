import type { IFormattedData } from "@/assets/interfaces/IForm";
import { defineStore } from "pinia";

interface ISketch {
    img: string,
    title: string
}

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
        },
        sketch: [] as ISketch[],
        calcParams: [] as IFormattedData[],
        freeModeConfig: false
    }),
    actions: {
        setError(error: string | string[]) {
            this.error.length = 0
            Array.isArray(error) ? this.error = error : this.error.push(error)
            this.errorStatus = 'error'
        },
        setDefaultError() {
            this.error =
                ['Выбирайте параметры последовательно - доступные значения обновляются автоматически в зависимости от выбранных условий.'];
            this.errorStatus = 'warning';
        },
        setMark(mark: string) {
            this.status.mark = mark;
        },
        seftDefaultMark() {
            this.status.mark = 'XXXXX-XXX-XX-XXXX';
        },
        setCovered(count: number) {
            this.status.answeredQuestions = count;
        },
        setAllQuestions(count: number) {
            this.status.allQuestions = count;
        },
        setFreeModeConfig(freeMode: boolean) {
            this.freeModeConfig = freeMode;
        },
        setSketch(sketch: ISketch) {
            this.sketch.length = 0;
            this.sketch.push(sketch);
        },
        setCalcParams(params: IFormattedData[]) {
            const markKey = 'Маркировка';
            const sketchKey = 'Чертеж';
            const targetMark = params.find(e => e.name == markKey);
            const targetSketch = params.find(e => e.name == sketchKey);

            if (targetMark?.response_value) {
                this.setMark(targetMark.response_value)
            }
            if (targetSketch?.response_value) {
                this.setSketch({ title: sketchKey, img: targetSketch.response_value });
            }
            this.calcParams = params.filter(e => e.name !== markKey && e.name !== sketchKey);
        },
    },
    getters: {
        getError: (state) => state.error,
        getErrorStatus: (state) => state.errorStatus,
        getStatus: (state) => state.status,
        getFreeModeConfig: (state) => state.freeModeConfig,
        getCalcParams: (state) => state.calcParams,
        getImages: (state) => state.sketch
    }
})