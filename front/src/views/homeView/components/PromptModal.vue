<template>
<div class="flex flex-col gap-[15px] w-[70vh] h-[70vh]  justify-center px-[25px]">
    <h3 class="text-left">Измените промпт или оставьте стандартный</h3>
    <BaseTextarea :propsClass="'input-param'"
                  :propsValue="defaultPromptToOCR"
                  @valueChanged="(newVal) => promptVal = newVal" />
    <BaseButton :propsClass="'button-primary'"
                @clicked="sendToServer">
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
        const sendToServer = () => {
            const newFormData = props.formData;
            newFormData.append('user_promt', promptVal.value);
            Api.post('http://agrofconf.emk.org.ru/api/AI/upload_OL?product_id=1', newFormData)
                .then((data) => {
                    if (data) {
                        useNeuroOlData().setData(data);
                        useNeuroOlData().setOlName(props.uploadedFileName);
                    }
                })
                .finally(() => router.push({ name: 'configurator', params: { id: 1 } }))
        }
        return {
            defaultPromptToOCR,
            promptVal,
            sendToServer
        }
    }
});
</script>