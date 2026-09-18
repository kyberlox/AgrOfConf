<template>
    <div class="p-[32px] w-full bg-[#FDFDFD] ml-auto border border-gray-200 rounded-xl min-h-[86vh]">
        <div class="flex flex-row gap-[24px] h-full flex-wrap md:flex-wrap lg:flex-nowrap" v-if="form.length">
            <div class="flex flex-col gap-[16px] w-full">
                <ConfiguratorHeader
                    :productName="productName"
                    :neuroOlData="neuroOlData"
                    :docIsLoading="docIsLoading"
                    :freeConfigMode="freeConfigMode"
                    @uploadFile="handleFileUpload" />

                <EngineParams
                    :form="form"
                    :paramsGroups="paramsGroups"
                    :paramsLoading="freeConfigMode ? false : paramsLoading"
                    :type="freeConfigMode ? 'free' : 'auto'"
                    :key="paramsRenderKey"
                    :userParams="userInputs"
                    @valueChanged="(value: string, key: string) => handleValueChanged(value, key)" />

                <div class="flex flex-row justify-end gap-[8px] flex-wrap mt-0">
                    <BaseButton :buttonSettings="{ class: 'button-secondary' }">
                        <span class="block px-[40px] flex flex-row items-center gap-[4px]">
                            <FavoriteIcon />
                            Удалить из Избранных ОЛ
                        </span>
                    </BaseButton>
                    <BaseButton :buttonSettings="{ class: 'button-primary' }" @clicked="tkpModalIsVisible = true">
                        Создать
                    </BaseButton>
                </div>
            </div>
            <RightSidebar :id="id" @readyToUploadFile="handleFileUpload" />
        </div>
        <div v-else class="engine-params__loader">
            <Loader />
        </div>

        <!-- Модальное окно для TKP вариантов -->
        <TkpVariants
            :tkpVariants="tkpVariants"
            :tkpModalIsVisible="tkpModalIsVisible"
            :tkpLoading="tkpLoading"
            @closeModal="tkpModalIsVisible = false"
            @downloadTkp="(TkpId: number) => handleDownloadTkp(TkpId)" />

        <!-- Модалка с распознанными данными -->
        <RecognitionCompare
            :recognitionModalVisible="recognitionModalVisible"
            :imagesUrl="imagesUrl"
            :recognizedTable="recognizedTable"
            :convertAiIsLoading="convertAiIsLoading"
            @closeModal="recognitionModalVisible = false"
            @successRecognized="(newTable) => handleSuccessRecognized(newTable)" />
    </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, computed, watch, onUnmounted } from "vue";
import { BaseButton } from "beans-ui-kit";

import EngineParams from "./components/EngineParams.vue";
import Api from "@/utils/Api";
import type { IFormattedData, userParams } from "@/assets/interfaces/IForm";
import SlotModal from "@/components/layout/SlotModal.vue";
import { useNeuroOlData } from "@/stores/neuroOl";
import UploadDocButton from "@/views/configurator/components/recognition/UploadDocButton.vue";
import RightSidebar from "@/components/layout/RightSidebar.vue";
import { useConfiguratorStore } from "@/stores/configurator.ts";
import FavoriteIcon from "@/assets/icons/Favorite.svg?component";
import TkpVariants from "./components/TkpVariants.vue";
import { type ITkpVariant } from "@/assets/interfaces/ITkpVariant.ts";
import Loader from "@/components/layout/Loader.vue";
import { getTkpVariants } from "@/utils/getTkpVariants.ts";
import { watchDebounced } from "@vueuse/core";
import RecognitionCompare from "./components/recognition/RecognitionCompare.vue";
import { Marked } from "@ts-stack/markdown";
import ConfiguratorHeader from "./components/ConfiguratorHeader.vue";
import { useConfiguratorForm } from "@/composables/useConfiguratorForm";
import { downloadFile } from "@/utils/downloadFile.ts";
import { useRoute } from "vue-router";
import { useHistoryStore } from "@/stores/historyTable.ts";

export default defineComponent({
    components: {
        BaseButton,
        FavoriteIcon,
        TkpVariants,
        EngineParams,
        SlotModal,
        UploadDocButton,
        RightSidebar,
        Loader,
        RecognitionCompare,
        ConfiguratorHeader,
    },
    props: {
        id: {
            type: String,
            required: true,
        },
    },
    setup(props, { emit }) {
        const route = useRoute();
        const neuroOlDataStore = useNeuroOlData();
        const configuratorStore = useConfiguratorStore();
        const form = ref<IFormattedData[]>([]);
        const userInputs = ref<userParams>({});
        const modalVisible = ref(false);
        const paramsRenderKey = ref(0);
        const neuroOlData = computed(() => neuroOlDataStore.getOlInfo);
        const productName = ref("");
        const tkpVariants = ref<ITkpVariant[]>([]);
        const tkpModalIsVisible = ref(false);
        const olFormData = ref<FormData>(new FormData());
        const newFileName = ref<string>();
        const freeConfigMode = computed(() => configuratorStore.getFreeModeConfig);
        const paramsLoading = ref(false);
        const docIsLoading = ref(false);
        const recognizedTable = ref();
        const imagesUrl = ref<string[]>();
        const paramsGroups = ref<Array<{ name: string; display: string; params: Array<string> }>>();
        const convertAiIsLoading = ref<boolean>(false);
        const recognitionModalVisible = ref<boolean>(false);
        const tkpLoading = ref(false);

        // Параметры, которые пользователь выбрал явно (не авто-подставленные).
        const manuallyChanged = ref<Record<string, boolean>>({});
        // Защита от зацикливания повторного подбора после сброса ошибочных параметров.
        const rerunGuard = ref(false);
        const priorityParam = ref<string>("");
        // Имя параметра-состава смеси (type='FormulaMix'). Хранится отдельно,
        // т.к. при выключенном чекбоксе «Смесь» сервер его не возвращает в форме.
        const mixtureCompositionName = ref("");
        const recognitionId = ref("");

        const { paramsUpdateRequest, handleValueChanged, checkForNeedUpdate } = useConfiguratorForm({
            userInputs,
            freeConfigMode,
            priorityParam,
            manuallyChanged,
            form,
            mixtureCompositionName,
            productName,
            rerunGuard,
            productId: props.id,
            configuratorStore,
            paramsLoading,
            recognitionId,
        });

        watchDebounced(
            () => userInputs.value,
            async () => {
                checkForNeedUpdate();
            },
            { debounce: 500, maxWait: 5000, deep: true },
        );

        onMounted(async () => {
            if (route.query.code) {
                recognitionId.value = String(route.query.code);
                const historyRow = await Api.get(`selection_statistic/selection/${recognitionId.value}`);
                paramsUpdateRequest(historyRow.parameters);
            } else {
                paramsUpdateRequest({});
            }
            const data = await Api.get(`/blocks/by_product/${props.id}`);
            if (data) {
                paramsGroups.value = data;
            }
            tkpVariants.value = await getTkpVariants(props.id);
        });

        const sendFileToRecognition = async (fileData: FormData, fileName: string) => {
            docIsLoading.value = true;
            try {
                const data = await Api.post(`AI/upload_OL?product_id=${props.id}`, fileData);
                if (!data) return;
                useNeuroOlData().setOlName(fileName || "");
                recognizedTable.value = Marked.parse(data.markdown);
                imagesUrl.value = data.file.map((e: { image_url: { url: string } }) => e.image_url.url);
                recognitionModalVisible.value = true;
            } finally {
                docIsLoading.value = false;
            }
        };

        const handleSuccessRecognized = async (table: string) => {
            try {
                convertAiIsLoading.value = true;
                const data = await Api.post(`AI/convert-ai-result?product_id=${props.id}`, table);
                useNeuroOlData().setData(data);
            } finally {
                recognitionModalVisible.value = false;
                convertAiIsLoading.value = false;
            }
        };

        const handleFileUpload = (file: FormData, fileName: string) => {
            olFormData.value = file;
            newFileName.value = fileName;
            sendFileToRecognition(file, fileName);
        };

        const handleDownloadTkp = async (tkpId: number) => {
            tkpLoading.value = true;
            try {
                const response = await Api.post(
                    `tkp_generation/create_tkp?file_id=${tkpId}&product_id=${props.id}&recognition_id=${recognitionId.value}&save_to_statistic=true`,
                    userInputs.value,
                    { responseType: "blob" },
                    undefined,
                    true,
                );
                if (response) {
                    const contentDisposition = response.headers["content-disposition"];
                    const filename = contentDisposition?.split("filename=")[1].replaceAll('"', "");
                    await downloadFile(response.data, filename);
                }
            } finally {
                tkpLoading.value = false;
            }
        };

        watch(neuroOlData, () => {
            if (neuroOlData.value) {
                paramsUpdateRequest(neuroOlData.value);
            }
        });

        onUnmounted(() => {
            configuratorStore.$reset();
            useNeuroOlData().$reset();
        });

        return {
            form,
            modalVisible,
            paramsRenderKey,
            neuroOlData,
            productName,
            tkpModalIsVisible,
            tkpVariants,
            olFormData,
            freeConfigMode,
            newFileName,
            paramsLoading,
            paramsGroups,
            userInputs,
            imagesUrl,
            recognizedTable,
            recognitionModalVisible,
            docIsLoading,
            tkpLoading,
            convertAiIsLoading,
            handleDownloadTkp,
            handleSuccessRecognized,
            handleValueChanged,
            handleFileUpload,
        };
    },
});
</script>
