<template>
<div class="dropzone-container p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     :class="[{ 'bg-(--color-information-green-50) hover:bg-(--color-information-green-150)!': !empty },
    isDragOver && !empty ? 'bg-(--color-information-orange-200)' : isDragOver && !empty ? 'bg-(--color-information-green-150)!' : '']"
     @dragover.prevent
     @dragover="isDragOver = true"
     @dragleave="isDragOver = false"
     @drop.prevent="dragFile">

    <input type="file"
           ref="fileInput"
           class="hidden"
           id="docUpload"
           accept="image/*,.pdf"
           @change="uploadFile">

    <div @click="handleClick">
        <div v-if="empty"
             class="dz-message">
            <span class="text-[16px] font-semibold text-(--color-information-orange-800)">
                Распознать ОЛ
            </span>
            <span class="text-[13px] font-normal text-(--text-text-secondary) block mt-1">
                Фото или PDF до 20мб
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
    </div>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref, computed } from 'vue';
import { useNeuroOlData } from '@/stores/neuroOl';

export default defineComponent({
    name: 'UploadDocButton',
    emits: ['readyToUploadFile'],
    setup(_, { emit }) {
        const fileInput = ref<HTMLInputElement | null>(null);
        const uploadedFileName = ref('');
        const storedFileName = computed(() => useNeuroOlData().getOlName);
        const isDragOver = ref(false);
        const storedData = computed(() => useNeuroOlData().getOlInfo);

        const handleClick = () => {
            if (fileInput.value) {
                fileInput.value.click();
            }
        };

        const uploadFile = (e: Event) => {
            const target = e.target as HTMLInputElement;
            if (target.files && target.files.length > 0) {
                processFile(target.files[0] as File);
                target.value = '';
            }
        };

        const dragFile = (e: DragEvent) => {
            if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                processFile(e.dataTransfer.files[0] as File);
            }
        };

        const processFile = (file: File) => {
            uploadedFileName.value = file.name;
            const formData = new FormData();
            formData.append('file', file);
            uploadToServer(formData);
        };

        const uploadToServer = (formData: FormData) => {
            emit('readyToUploadFile', formData, uploadedFileName.value)
        }

        return {
            fileInput,
            uploadedFileName,
            isDragOver,
            storedFileName,
            storedData,
            handleClick,
            uploadFile,
            dragFile,
            empty: computed(() => !Object.keys(storedData.value).length)
        };
    }
});
</script>

<style>
.dropzone-container {
    cursor: pointer !important;
}

.dz-message {
    margin: 0 !important;
}

.hidden {
    display: none !important;
}
</style>
