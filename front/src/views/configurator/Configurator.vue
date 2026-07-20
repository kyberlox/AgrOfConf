<template>
<div class="p-[32px] w-full bg-[#FDFDFD] max-w-full border border-gray-200 rounded-xl">
    <div class="flex flex-row gap-[24px] h-full flex-wrap md:flex-wrap lg:flex-nowrap">
        <div class="flex flex-col gap-[24px] w-full">
            <div
                 class="flex flex-row items-start justify-between lg:flex-wrap xl:flex-wrap xxl:flex-nowrap w-full gap-y-[20px] ">
                <div class="flex flex-row gap-[16px] items-center w-full max-w-[650px]">
                    <RouterLink :to="{ name: 'homeview' }"
                                class="w-[24px] h-[24px] rounded-[16px] bg-[#F6F7F9] cursor-pointer flex self-start mt-[7px]">
                        <ArrowLeft class="w-full m-auto max-h-[12px]" />
                    </RouterLink>
                    <h1 class="block">{{ productName }}</h1>
                    <div
                         class="rounded-[16px] mt-[10px] self-start flex flex-row items-center gap-[4px] bg-[#FFF2E5] pl-[8px] py-[4px] min-w-[104px] font-medium text-[#752209]">
                        <Ellipse />
                        <span>Черновик</span>
                    </div>
                </div>

                <div v-if="!Object.keys(neuroOlData).length"
                     class="flex flex-row gap-[11px] mt-[10px] items-center ml-auto">
                    <div class="font-normal">
                        Свободный режим
                    </div>
                    <div class=" rounded-[49px] px-[4px] w-[48px] h-[24px] flex flex-start items-center cursor-pointer transition-all duration-300"
                         :class="[freeConfigMode ? ' bg-[#F36E3C]' : ' bg-[#B4BCC8]']"
                         @click="setFreeConfig(!freeConfigMode)">
                        <div class="bg-white rounded-[100px] w-[18px] h-[18px] transition-all duration-300"
                             :class="[freeConfigMode ? 'translate-x-[22px]' : '']"></div>
                    </div>
                </div>
            </div>
            <EngineParams v-if="form.length"
                          :form="form"
                          :type="neuroOlData ? 'free' : 'auto'"
                          :key="paramsRenderKey"
                          @valueChanged="(value: string, key: string) => handleValueChanged(value, key)" />
            <div v-else
                 class="engine-params__loader">
                <Loader />
            </div>
            <div class="flex flex-row justify-end gap-[8px] flex-wrap mt-0">
                <BaseButton :propsClass="'button-secondary'">
                    <span class="block px-[40px] flex flex-row items-center gap-[4px]">
                        <FavoriteIcon />
                        Удалить из Избранных ОЛ
                    </span>
                </BaseButton>
                <BaseButton :propsClass="'button-primary'"
                            @clicked="tkpModalIsVisible = true">
                    Создать
                </BaseButton>
            </div>
        </div>
        <RightSidebar @readyToUploadFile="handleFileUpload" />
    </div>
    <!-- Модалка для description -->
    <SlotModal v-if="modalVisible"
               @closeModal="modalVisible = false">
        <h1>dsa</h1>
    </SlotModal>
    <!-- Модальное окно для TKP вариантов -->
    <SlotModal v-if="tkpModalIsVisible"
               @closeModal="tkpModalIsVisible = false">
        <TkpVariants :tkpVariants="tkpVariants"
                     @downloadTkp="(id: number) => handleDownloadTkp(id)" />
    </SlotModal>
    <!-- Модалка для промпта для распознавания -->
    <SlotModal v-if="promptModalVisible"
               @closeModal="promptModalVisible = false">
        <PromptModal :formData="olFormData"
                     :uploadedFileName="newFileName || ''"
                     @closeModal="promptModalVisible = false" />
    </SlotModal>
</div>
</template>
<script lang='ts'>
import { defineComponent, onMounted, ref, computed, watch } from 'vue';
import { BaseButton } from 'beans-ui-kit';
import Ellipse from '@/assets/icons/Ellipse.svg?component';
import ArrowLeft from '@/assets/icons/ArrowLeft.svg?component';
import EngineParams from './components/EngineParams.vue';
import Api from '@/utils/Api';
import type { IFormattedData } from '@/assets/interfaces/IForm';
import SlotModal from '@/components/layout/SlotModal.vue';
import { useNeuroOlData } from '@/stores/neuroOl';
import UploadDocButton from '@/views/homeView/components/recognition/UploadDocButton.vue';
import RightSidebar from '@/components/layout/RightSidebar.vue';
import { useConfiguratorStore } from '@/stores/configurator.ts';
import FavoriteIcon from '@/assets/icons/Favorite.svg?component';
import PromptModal from '../homeView/components/recognition/PromptModal.vue';
import TkpVariants from './components/TkpVariants.vue';
import { type ITkpVariant } from '@/assets/interfaces/ITkpVariant.ts';
import { downloadFile } from '@/utils/downloadFile.ts';
import Loader from '@/components/layout/Loader.vue';
import { getTkpVariants } from '@/utils/getTkpVariants.ts';
import { toast } from 'vue3-toastify';

export default defineComponent({
    components: {
        BaseButton,
        Ellipse,
        ArrowLeft,
        FavoriteIcon,
        TkpVariants,
        EngineParams,
        PromptModal,
        SlotModal,
        UploadDocButton,
        RightSidebar,
        Loader
    },
    props: {
        id: {
            type: String,
            required: true
        }
    },
    setup(props, { emit }) {
        const form = ref<IFormattedData[]>([]);
        const userInputs = ref<{ [key: string]: string }>({});
        const modalVisible = ref(false);
        const paramsRenderKey = ref(0);
        const neuroOlDataStore = useNeuroOlData();
        const neuroOlData = computed(() => neuroOlDataStore.getOlInfo);
        const productName = ref('');
        const tkpVariants = ref<ITkpVariant[]>([]);
        const tkpModalIsVisible = ref(false);
        const promptModalVisible = ref(false);
        const olFormData = ref<FormData>(new FormData());
        const newFileName = ref<string>();
        const configuratorStore = useConfiguratorStore();
        const freeConfigMode = computed(() => configuratorStore.getFreeModeConfig);

        let abortController: AbortController | null = null;

        const paramsUpdate = async (body: Record<string, string> | null) => {
            if (freeConfigMode.value && body !== null) {
                return
            }
            if (abortController) {
                abortController.abort();
            }
            abortController = new AbortController();
            const signal = abortController.signal;
            try {
                const data = await Api.post(`/module_search/process_table_data?product_id=${props.id}`, body, {}, signal)
                const errors: string[] = [];
                let answeredCounter = 0;
                let questionCounter = 0;
                if (!data || !('parameters' in data) || !data.parameters.length) return
                data.parameters.forEach((e: IFormattedData) => {
                    if ('error' in e && e.error) {
                        errors.push(e.error)
                    }
                    if ('response_value' in e && e.response_value) {
                        userInputs.value[e.name] = e.response_value
                        answeredCounter++
                    }
                    questionCounter++
                })
                configuratorStore.setCalcParams(data.parameters.filter((e: IFormattedData) => e.required_type == 'raschet' && e.response_value));
                configuratorStore.setCovered(Number(answeredCounter));
                configuratorStore.setAllQuestions(Number(questionCounter));
                if (errors.length) {
                    configuratorStore.setError(errors)
                }
                else configuratorStore.setDefaultError()
                if (!(data && 'parameters' in data)) return
                form.value = data.parameters
                productName.value = data.product_name
            }
            catch (error) {
                // console.error(error)
            }
        }

        onMounted(async () => {
            tkpVariants.value = await getTkpVariants(props.id);
            if (!Object.keys(neuroOlData.value).length)
                paramsUpdate(null)

        })

        watch(neuroOlData, () => {
            if (neuroOlData.value) {
                userInputs.value = neuroOlData.value
                paramsUpdate(neuroOlDataStore.getOlInfo)
            }
        })

        const handleValueChanged = (value: string, key: keyof typeof userInputs.value) => {
            if (key == 'Маркировка') {
                configuratorStore.setMark(value)
            }
            if (value || value == '') {
                console.log({ 'val': value, 'key': key })
                userInputs.value[key] = value;
                paramsUpdate(userInputs.value)
            }
        }

        const handleDownloadTkp = async (variantId: number) => {
            try {
                const response = await Api.post(`tkp_generation/create_tkp?file_id=${variantId}&product_id=${props.id}&save_to_statistic=true`, userInputs.value, { responseType: 'blob' }, undefined, true);
                if (response) {
                    const contentDisposition = response.headers['content-disposition'];
                    const filename = contentDisposition?.split('filename=')[1].replaceAll('"', '');
                    await downloadFile(response.data, filename)
                }
            }
            catch (error) {
                toast.error(error)
            }
        }

        const handleFileUpload = (file: FormData, fileName: string) => {
            promptModalVisible.value = true;
            olFormData.value = file;
            newFileName.value = fileName;
        }

        const setFreeConfig = (mode: boolean) => {
            configuratorStore.setFreeModeConfig(mode)
        }

        return {
            form,
            modalVisible,
            paramsRenderKey,
            neuroOlData,
            productName,
            tkpModalIsVisible,
            tkpVariants,
            promptModalVisible,
            olFormData,
            freeConfigMode,
            newFileName,
            handleValueChanged,
            handleDownloadTkp,
            handleFileUpload,
            setFreeConfig,
        }
    }
});
</script>
