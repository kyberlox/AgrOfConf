<template>
<div class="rounded-[8px] relative flex flex-col-reverse gap-[4px] w-fit">
    <input class="hidden"
           ref=fileInput
           type="file"
           :value="fileValue"
           @change="handleFileUpload" />

    <BaseButton :props-class="buttonClass"
                :props-title="needFileNameInTitle ? fileName : 'Загрузить'"
                :disabled="isLoading"
                @clicked="handleClick">
        <span v-if="!isLoading">{{ fileName }}</span>
        <Loader v-else />
    </BaseButton>
</div>
</template>
<script lang='ts'>
import { defineComponent, ref, watch } from 'vue';
import { BaseButton } from 'beans-ui-kit';
import Loader from './Loader.vue';

export default defineComponent({
    components: {
        BaseButton,
        Loader
    },
    props: {
        fileValue: {
            type: File,
        },
        fileName: {
            type: String,
            default: 'Загрузить'
        },
        buttonClass: {
            type: String
        },
        needFileNameInTitle: {
            type: Boolean,
        },
        isLoading: {
            type: Boolean
        }
    },
    emits: ['fileUpload'],
    setup(props, { emit }) {
        const fileInput = ref();
        const fileName = ref();

        const handleClick = () => {
            if (fileInput.value)
                (fileInput.value).click()
        }

        const handleFileUpload = () => {
            if (!fileInput.value || !fileInput.value.files.length) return
            fileName.value = fileInput.value.files[0].name;
            emit('fileUpload', fileInput.value.files[0])
        }

        watch(() => props.fileValue, () => {
            if (props.fileValue) {
                fileInput.value = props.fileValue
            }
        }, { immediate: true })

        watch(() => props.fileName, () => {
            if (props.fileName) {
                fileName.value = props.fileName
            }
        }, { immediate: true })

        return {
            fileInput,
            fileName,
            handleClick,
            handleFileUpload
        }
    }
});
</script>