<template>
<div class="dropzone-container cursor-pointer w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     :class="[{ 'bg-gray-300 hover:bg-gray-300! cursor-not-allowed! border-none': disabled }, { 'bg-(--color-information-green-50) hover:bg-(--color-information-green-150)!': !empty },
    isDragOver && !empty ? 'bg-(--color-information-orange-200)' : isDragOver && !empty ? 'bg-(--color-information-green-150)!' : '']"
     @dragover.prevent
     @dragover="isDragOver = true"
     @dragleave="isDragOver = false"
     @drop.prevent="dragFile">

    <input type="file"
           ref="fileInput"
           class="hidden"
           id="docUpload"
           :accept="formats"
           :disabled="disabled"
           @change="uploadFile" />

    <div @click="handleClick"
         class="p-[20px]">
        <slot></slot>
    </div>
</div>
</template>

<script lang='ts'>
import { defineComponent, ref } from 'vue';
import { toast } from 'vue3-toastify';

export default defineComponent({
    name: 'UploadDocButton',
    emits: ['readyToUploadFile'],
    props: {
        empty: {
            type: Boolean,
        },
        disabled: {
            type: Boolean,
            default: false
        },
        formats: {
            type: String
        }
    },
    setup(_, { emit }) {
        const fileInput = ref<HTMLInputElement | null>(null);
        const uploadedFileName = ref('');
        const isDragOver = ref(false);

        const handleClick = () => {
            if (fileInput.value) {
                fileInput.value.click();
            }
        };

        const uploadFile = (e: Event) => {
            // больше 800 КБ ограничиваем
            const maxFileSize = 800 * 1024;
            const target = e.target as HTMLInputElement;
            if (target.files && target.files.length > 0) {
                if (!target.files[0]) return
                if (target.files[0].size > maxFileSize) {
                    return toast.error('Файл слишком большой, сервис поддерживает файлы до 800 Кб')
                }
                else
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
            handleClick,
            uploadFile,
            dragFile,
        };
    }
});
</script>