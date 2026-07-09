<template>
<div class="dropzone-container w-[480px] max-w-full border border-(--color-information-orange-200) hover:bg-(--color-information-orange-200) transition-all duration-300 cursor-pointer border-dotted flex flex-col gap-[4px] rounded-[12px] text-center"
     :class="[{ 'bg-gray-300 hover:bg-gray-300!': disabled }, { 'bg-(--color-information-green-50) hover:bg-(--color-information-green-150)!': !empty },
    isDragOver && !empty ? 'bg-(--color-information-orange-200)' : isDragOver && !empty ? 'bg-(--color-information-green-150)!' : '']"
     @dragover.prevent
     @dragover="isDragOver = true"
     @dragleave="isDragOver = false"
     @drop.prevent="dragFile">

    <input type="file"
           ref="fileInput"
           class="hidden"
           id="docUpload"
           accept=".jpg,.jpeg,.png,.webp,.bmp,.tiff,.tif,.pdf,.md,.html,.docx,.odt,.rtf"
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
            handleClick,
            uploadFile,
            dragFile,
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
