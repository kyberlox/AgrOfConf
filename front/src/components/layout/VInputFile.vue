<template>
<div class="rounded-[8px] relative flex flex-col-reverse gap-[4px] w-fit">
    <input class="hidden"
           ref=fileInput
           type="file"
           @change="handleFileUpload" />
    <BaseButton :props-class="'button-primary'"
                :props-title="fileName"
                @clicked="handleClick">
        {{ fileName }}
    </BaseButton>
</div>
</template>
<script lang='ts'>
import { defineComponent, ref, watch } from 'vue';
import { BaseButton } from 'beans-ui-kit';

export default defineComponent({
    components: {
        BaseButton
    },
    props: {
        placeholder: {
            type: String,
            default: ''
        },
        value: {
            type: [String, Number],
            default: ''
        }
    },
    setup(props, { emit }) {
        const fileInput = ref();
        const fileName = ref('Загрузить фото');
        const handleClick = () => {
            if (fileInput.value)
                (fileInput.value).click()
        }

        const handleFileUpload = () => {
            if (!fileInput.value || !fileInput.value.files.length) return
            fileName.value = fileInput.value.files[0].name;
            emit('fileUpload', fileInput.value.files[0])
        }

        return {
            fileInput,
            fileName,
            handleClick,
            handleFileUpload
        }
    }
});
</script>