<template>
<UploadFileArea :formats="formats"
                :empty="empty"
                @readyToUploadFile="(formData, fileName) => $emit('readyToUploadFile', formData, fileName)">
    <div v-if="empty"
         class="dz-message p-[20px]">
        <span class="text-[16px] font-semibold text-(--color-information-orange-800)">
            Распознать ОЛ
        </span>
        <span class="text-[13px] font-normal text-(--text-text-secondary) block mt-1">
            {{ formats }}
        </span>
        <span class="text-[12px] text-(--text-text-tertiary) block mt-2">
            Перетащите файл сюда или нажмите для выбора
        </span>
    </div>

    <div v-else
         class="flex flex-row items-center justify-between">
        <div class="flex flex-col gap-[4px] text-left">
            <span class="text-[16px] font-semibold text-(--text-text-primary)">
                Поля {{ ' ' + storedFileName + ' ' }} Распознаны
            </span>
            <span class="text-[13px] font-normal text-(--text-text-secondary) block">
                Перепроверьте
            </span>
        </div>
        <span class="text-[16px] text-(--color-information-orange-800) block">
            Загрузить другой
        </span>
    </div>
</UploadFileArea>
</template>

<script lang='ts'>
import { defineComponent, ref, computed } from 'vue';
import { useNeuroOlData } from '@/stores/neuroOl';
import UploadFileArea from '@/components/layout/UploadFileArea.vue';

export default defineComponent({
    name: 'UploadDocButton',
    components: { UploadFileArea },
    emits: ['readyToUploadFile'],
    props: {
        formats: {
            type: String
        }
    },
    setup(_, { emit }) {
        const storedFileName = computed(() => useNeuroOlData().getOlName);
        const storedData = computed(() => useNeuroOlData().getOlInfo);

        return {
            storedFileName,
            storedData,
            empty: computed(() => !Object.keys(storedData.value).length)
        };
    }
});
</script>