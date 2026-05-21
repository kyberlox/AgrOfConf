<template>
<div class="dropzone-container p-[20px] w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     :class="[{ 'bg-(--color-information-green-50) hover:bg-(--color-information-green-150)!': type == 'inConfig' },
    isDragOver && type !== 'inConfig' ? 'bg-(--color-information-orange-200)' : isDragOver && type == 'inConfig' ? 'bg-(--color-information-green-150)!' : '']"
     @dragend="isDragOver = false"
     @drop.prevent="dragFile"
     @dragover="isDragOver = true"
     @dragleave="isDragOver = false">

    <input type="file"
           ref="fileInput"
           class="hidden"
           accept="image/*,.pdf"
           @change="uploadFile">

    <div @click="handleClick">
        <div class="dz-message"
             v-if="!uploadedFileName && type == 'outer'">
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

        <div class="flex flex-row items-center justify-between"
             v-else-if="type == 'inConfig'">
            <div class="flex flex-col gap-[4px] text-left">
                <span class="text-[16px] font-semibold text-(--text-text-primary)">
                    Поля Распознаны
                </span>
                <span class="text-[13px] font-normal text-(--text-text-secondary) block">
                    Перепроверьте на всякий случай
                </span>
            </div>
            <span class="text-[16px] text-(--color-information-orange-800) block">
                Загрузить другой
            </span>
        </div>

        <div v-else
             class="text-[16px] text-(--text-text-tertiary) block">
            {{ uploadedFileName }}
        </div>
    </div>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useNeuroOlData } from '@/stores/neuroOl';
import Api from '@/utils/Api';

export default defineComponent({
    name: 'UploadDocButton',
    props: {
        type: {
            type: String,
            default: 'outer'
        }
    },
    setup() {
        const fileInput = ref<HTMLInputElement | null>(null);
        const uploadedFileName = ref('');
        const router = useRouter();
        const isDragOver = ref(false);

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

        const uploadToServer = async (formData: FormData) => {
            Api.post('http://agrofconf.emk.org.ru/api/AI/upload_OL', formData)
                .then((data) => {
                    if (data) {
                        useNeuroOlData().setData(data);
                    }
                })
                .finally(() => router.push({ name: 'configurator', params: { id: 1 } }))
        }

        return {
            fileInput,
            uploadedFileName,
            isDragOver,
            handleClick,
            uploadFile,
            dragFile
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