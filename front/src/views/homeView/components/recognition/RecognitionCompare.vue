<template>
<div class="max-h-[90vh]">
    <div class="flex flex-row justify-between p-[15px]">
        <div class="flex flex-col justify-center">
            <span class="block text-[16px] text-(--text-primary)">Проверьте корректность распознавания и создайте ОЛ по
                кнопке</span>
            <span class="block text-[15px] text-(--text-secondary)">При наличии несоответствия - нажмите на параметр и
                введите нужное значение</span>
        </div>
        <BaseButton :props-class="'button-primary'"
                    :disabled="convertAiIsLoading"
                    @clicked="$emit('successRecognized', editedTable)">
            <div v-if="convertAiIsLoading"
                 class="button-primary__loader">
                <Loader />
            </div>
            <span v-else>Создать ОЛ</span>
        </BaseButton>
    </div>
    <div class="flex flex-row gap-[25px] items-start justify-center pt-[15px]">
        <div class="flex flex-col gap-[5px] min-w-[40%] sticky top-0  z-10">
            <div class="max-w-[650px] border border-gray-200 rounded-[16px] p-[15px] hover:bg-gray-50 hover:border-gray-500"
                 v-for="image in imagesUrl">
                <VueImageZoomer :regular="image"
                                hover-message="Наведите для приближения" />
            </div>
        </div>
        <div class="max-w-full max-h-[80%] p-[25px] recognition-table-wrapper border border-gray-200 focus:outline-0 focus:border-gray-500 rounded-[16px]"
             contenteditable="true"
             ref=mdTableNode
             v-html="recognizedTable"></div>
    </div>
</div>
</template>
<script lang='ts'>
import { BaseButton } from 'beans-ui-kit';
import { defineComponent, ref, watch } from 'vue';
import { VueImageZoomer } from 'vue-image-zoomer';
import Loader from '@/components/layout/Loader.vue';
import 'vue-image-zoomer/dist/style.css';

export default defineComponent({
    emits: ['successRecognized'],
    components: {
        VueImageZoomer,
        BaseButton,
        Loader
    },
    props: {
        recognizedTable: {
            type: String
        },
        imagesUrl: {
            type: Array<string>
        },
        convertAiIsLoading: {
            type: Boolean,
            default: false
        }
    },
    setup() {
        const editedTable = ref<string>('');
        const mdTableNode = ref<HTMLElement>();

        watch((mdTableNode), () => {
            editedTable.value = String(mdTableNode.value?.innerHTML)
        }, { deep: true, immediate: true })

        return {
            editedTable,
            mdTableNode
        }
    }
});
</script>

<style scoped>
.recognition-table-wrapper :deep(table) {
    width: auto;
    min-width: 100%;
    border-collapse: collapse;
    font-family: 'Inter', 'sans-serif';
    font-size: 12px;
    line-height: 1.2;
    color: #343b4c;
}

.recognition-table-wrapper :deep(thead th) {
    text-align: left;
    font-weight: 500;
    font-size: 14px;
    color: #5e697d;
    padding: 4px 8px;
    white-space: nowrap;
    border-bottom: 1px solid #EAECEF;
}

.recognition-table-wrapper :deep(thead th:first-child) {
    padding-left: 12px;
}

.recognition-table-wrapper :deep(thead th:last-child) {
    padding-right: 12px;
}

.recognition-table-wrapper :deep(tbody td) {
    padding: 3px 8px;
    vertical-align: top;
    color: #343b4c;
    font-weight: 400;
    font-size: 14px;
    line-height: 1.3;
    border-bottom: 1px solid #EAECEF;
    text-decoration: underline dotted;
}

.recognition-table-wrapper :deep(tbody tr:last-child td) {
    border-bottom: none;
}

.recognition-table-wrapper :deep(tbody td:first-child) {
    padding-left: 12px;
    font-weight: 500;
    color: #171b26;
    white-space: nowrap;
    width: 1%;
}

.recognition-table-wrapper :deep(tbody td:last-child) {
    padding-right: 12px;
    color: #343b4c;
    font-weight: 400;
}
</style>