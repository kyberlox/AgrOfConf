<template>
    <div class="flex flex-col gap-[15px] w-[70vh] h-[70vh]  justify-center px-[25px]">
        <h3 class="text-left mt-[15px]">Измените промпт или оставьте стандартный</h3>
        <BaseTextarea :propsClass="'prompt-area'" :propsValue="defaultPromptToOCR"
            @valueChanged="(newVal) => promptVal = newVal" />
        <BaseButton :propsClass="'button-primary'" :disabled="docIsLoading" @clicked="sendToServer">
            Отправить
        </BaseButton>
    </div>
</template>
<script lang='ts'>
import SlotModal from '@/components/layout/SlotModal.vue';
import { BaseButton, BaseTextarea } from 'beans-ui-kit';
import { defineComponent, ref } from 'vue';
import Api from '@/utils/Api';
import { useRouter } from 'vue-router';
import { useNeuroOlData } from '@/stores/neuroOl';
import { defaultPromptToOCR } from '@/assets/static/defaultPromptToNeuroOl';
import { copyFormData } from '@/utils/copyFormData';

export default defineComponent({
    components: {
        SlotModal,
        BaseTextarea,
        BaseButton
    },
    props: {
        formData: {
            type: FormData,
            required: true
        },
        uploadedFileName: {
            type: String,
            required: true
        }
    },
    setup(props) {
        const router = useRouter();
        const promptVal = ref(defaultPromptToOCR);
        const docIsLoading = ref(false);
        
        const sendToServer = async () => {
            const newFormData = copyFormData(props.formData);
            newFormData.append('user_promt', promptVal.value);
            docIsLoading.value = true;
            try {
                const data = await Api.post('AI/upload_OL?product_id=1', newFormData)
                if (!data) return
                useNeuroOlData().setData(data);
                useNeuroOlData().setOlName(props.uploadedFileName);
                router.push({ name: 'configurator', params: { id: 1 } });
            }
            catch (e) {
                console.error(e)
            }
            finally {
                docIsLoading.value = false;
            }
        }


        return {
            defaultPromptToOCR,
            promptVal,
            sendToServer,
            docIsLoading
        }
    }
});
</script>

<style>
.prompt-area__wrapper {
    width: 100%;
    height: 100%;
}

.prompt-area {
    resize: none;
    width: 100%;
    height: 100%;
    padding: 25px;
    border: 1px solid #ccc;
    border-radius: 15px;
    background: var(--color-gray-100)
}
</style>