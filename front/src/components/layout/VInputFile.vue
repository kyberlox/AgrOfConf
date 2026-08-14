<template>
<div class="rounded-[8px] relative flex flex-col-reverse gap-[4px] w-fit">
    <input class="hidden"
           ref=fileInput
           type="file"
           :value="newFileName"
           @change="handleFileUpload" />

    <BaseButton :buttonSettings="{ class: buttonClass, disabled: isLoading }"
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
        const newFileName = ref();

        const handleClick = () => {
            if (fileInput.value)
                (fileInput.value).click()
        }

        const handleFileUpload = () => {
            if (!fileInput.value || !fileInput.value.files.length) return
            newFileName.value = fileInput.value.files[0].name;
            emit('fileUpload', fileInput.value.files[0])
        }

        watch(() => props.fileValue, () => {
            if (props.fileValue) {
                fileInput.value = props.fileValue
            }
        }, { immediate: true })

        watch(() => props.fileName, () => {
            if (props.fileName) {
                newFileName.value = props.fileName
            }
        }, { immediate: true })

        return {
            fileInput,
            newFileName,
            handleClick,
            handleFileUpload
        }
    }
});
</script>