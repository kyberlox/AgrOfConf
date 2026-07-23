<template>
<SlotModal v-if="promptModalVisible"
           @closeModal="$emit('closeModal')">
    <div class="pb-[15px]">
        <div v-if="!wasRecognized"
             class="prompt-area__actions  flex flex-col gap-[15px] w-[80vh] h-[80vh] justify-center px-[25px]">
            <h3 class="text-left mt-[15px]">Дополните промпт или отправьте без изменений</h3>
            <span>Нередактируемый промпт</span>
            <pre class="bg-blue-50 border border-gray-400 rounded-[16px] p-[25px] max-h-full overflow-auto"
                 v-html="defaultPromptToOCR"></pre>
            <span>Если необходимо дополнить, заполните поле ниже</span>
            <BaseTextarea :propsClass="'prompt-area'"
                          @valueChanged="(newVal) => promptVal = newVal" />
            <BaseButton :propsClass="'button-primary'"
                        :disabled="docIsLoading"
                        @clicked="sendToServer">
                Отправить
            </BaseButton>
        </div>
        <RecognitionCompare v-else
                            :imagesUrl="imagesUrl"
                            :recognizedTable="recognizedTable"
                            :convertAiIsLoading="convertAiIsLoading"
                            @successRecognized="(newTable) => handleSuccessRecognized(newTable)" />
    </div>
</SlotModal>
</template>

<script lang='ts'>
import SlotModal from '@/components/layout/SlotModal.vue';
import { BaseButton, BaseTextarea } from 'beans-ui-kit';
import { defineComponent, ref } from 'vue';
import Api from '@/utils/Api';
import { useRoute, useRouter } from 'vue-router';
import { useNeuroOlData } from '@/stores/neuroOl';
import { defaultPromptToOCR } from '@/assets/static/defaultPromptToNeuroOl';
import { copyFormData } from '@/utils/copyFormData';
import { Marked } from '@ts-stack/markdown';
import RecognitionCompare from './RecognitionCompare.vue';

export default defineComponent({
    components: {
        SlotModal,
        BaseTextarea,
        BaseButton,
        RecognitionCompare
    },
    props: {
        formData: {
            type: FormData,
            required: true
        },
        uploadedFileName: {
            type: String,
            required: true
        },
        promptModalVisible: {
            type: Boolean,
            default: false
        }
    },
    emits: ['closeModal'],
    setup(props, { emit }) {
        const promptVal = ref(defaultPromptToOCR);
        const docIsLoading = ref(false);
        const recognizedTable = ref();
        const wasRecognized = ref(false);
        const route = useRoute();
        const imagesUrl = ref<Array<string>>();
        const router = useRouter();
        const convertAiIsLoading = ref(false);

        const sendToServer = async () => {
            const newFormData = copyFormData(props.formData);
            newFormData.append('user_promt', promptVal.value);
            docIsLoading.value = true;
            try {
                const data = await Api.post(`AI/upload_OL?product_id=${route.params.id}`, newFormData)
                if (!data) return
                useNeuroOlData().setOlName(props.uploadedFileName);
                recognizedTable.value = Marked.parse(data.markdown);
                imagesUrl.value = data.file.map((e: { image_url: { url: string } }) => e.image_url.url);
                wasRecognized.value = true;
            }
            catch (e) {
                console.error(e)
            }
            finally {
                docIsLoading.value = false;
            }
        }

        const handleSuccessRecognized = async (table: string) => {
            try {
                convertAiIsLoading.value = true;
                const data = await Api.post(`AI/convert-ai-result?product_id=${route.params.id}`, table)
                useNeuroOlData().setData(data);
                router.push({ name: 'configurator', params: { id: route.params.id } });
            } catch (e) {
                console.error(e)
            } finally {
                emit('closeModal');
                convertAiIsLoading.value = false;
            }
        }

        return {
            defaultPromptToOCR,
            promptVal,
            recognizedTable,
            docIsLoading,
            wasRecognized,
            imagesUrl,
            convertAiIsLoading,
            Marked,
            sendToServer,
            handleSuccessRecognized
        }
    }
});
</script>

<style>
.prompt-area__wrapper {
    width: 100%;
    height: 80%;
}

.prompt-area__actions>.button-primary__wrapper>.button-primary {
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
