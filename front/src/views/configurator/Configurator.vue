<template>
<div class="p-[32px] w-full bg-[#FDFDFD] ml-auto border border-gray-200 rounded-xl min-h-[86vh]">
    <div class="flex flex-row gap-[24px] h-full flex-wrap md:flex-wrap lg:flex-nowrap"
         v-if="form.length">
        <div class="flex flex-col gap-[16px] w-full">
            <div
                 class="flex flex-row items-start justify-between gap-[20px] max-w-full content-stretch flex-wrap md:flex-wrap lg:flex-wrap xxl:flex-nowrap">
                <div class="flex flex-row gap-[16px] items-center w-full max-w-fit">
                    <RouterLink :to="{ name: 'homeview' }"
                                class="w-[24px] h-[24px] rounded-[16px] bg-[#F6F7F9] cursor-pointer flex self-start mt-[7px]">
                        <ArrowLeft class="w-full m-auto max-h-[12px]" />
                    </RouterLink>
                    <h1 class="inline-block w-fit max-w-[500px]">{{ productName }}</h1>
                </div>
                <div class="flex flex-col-reverse justify-center">
                    <div v-if="!Object.keys(neuroOlData).length"
                         class="flex flex-row gap-[11px] mt-[10px] items-center">
                        <div class="font-normal w-fit">
                            Свободный режим
                        </div>
                        <div class=" rounded-[49px] px-[4px] w-[48px] h-[24px] flex flex-start items-center cursor-pointer transition-all duration-300"
                             :class="[freeConfigMode ? ' bg-[#F36E3C]' : ' bg-[#B4BCC8]']"
                             @click="setFreeConfig(!freeConfigMode)">
                            <div class="bg-white rounded-[100px] w-[18px] h-[18px] transition-all duration-300"
                                 :class="[freeConfigMode ? 'translate-x-[22px]' : '']"></div>
                        </div>
                    </div>
                    <div
                         class="rounded-[16px]  self-start flex flex-row items-center gap-[4px] bg-[#FFF2E5] pl-[8px] py-[4px] min-w-[104px] font-medium text-[#752209]">
                        <Ellipse />
                        <span>Черновик</span>
                    </div>
                </div>
                <UploadDocButton class="grow"
                                 @readyToUploadFile="(file, fileName) => handleFileUpload(file, fileName)" />
            </div>
            <EngineParams :form="form"
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
                <BaseButton :buttonSettings="{ class: 'button-primary' }"
                            @clicked="tkpModalIsVisible = true">
                    Создать
                </BaseButton>
            </div>
        </div>
        <RightSidebar :id="id"
                      @readyToUploadFile="handleFileUpload" />
    </div>
    <div v-else
         class="engine-params__loader">
        <Loader />
    </div>

    <!-- Модальное окно для TKP вариантов -->
    <TkpVariants :tkpVariants="tkpVariants"
                 :tkpModalIsVisible="tkpModalIsVisible"
                 @closeModal="tkpModalIsVisible = false"
                 @downloadTkp="(id: number) => handleDownloadTkp(id)" />

    <!-- Модалка для промпта для распознавания -->
    <PromptModal :promptModalVisible="promptModalVisible"
                 :formData="olFormData"
                 :uploadedFileName="newFileName || ''"
                 :key="promptModalKey"
                 @closeModal="promptModalVisible = false" />
</div>
</template>

<script lang='ts'>
import { defineComponent, onMounted, ref, computed, watch, onUnmounted } from 'vue';
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
import { watchDebounced } from '@vueuse/core';
import { replaceSpotOrComma } from '@/utils/replaceSpotOrComma.ts';
import { clone } from 'chart.js/helpers';

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
        const paramsLoading = ref(false);
        const paramsGroups = ref<Array<{ name: string; display: string; params: Array<string> }>>();
        // Параметры, которые пользователь выбрал явно (не авто-подставленные).
        const manuallyChanged = ref<Record<string, boolean>>({});
        let abortController: AbortController | null = null;
        // Защита от зацикливания повторного подбора после сброса ошибочных параметров.
        let rerunGuard = false;
        const priorityParam = ref<string>();
        const promptModalKey = ref(1);

        const paramsUpdate = (body: Record<string, string> | null) => {
            if (!body) {
                paramsUpdateRequest()
            } else {
                userInputs.value = body;
            }
        }

        watchDebounced(() => userInputs.value, async () => {
            if (Object.keys(userInputs.value).length) {
                Object.keys(userInputs.value).forEach(key => {
                    const formTarget = form.value.find(formEl => formEl.name == key)
                    if (!formTarget?.response_value || userInputs.value[key] !== formTarget?.response_value) {
                        return paramsUpdateRequest(userInputs.value)
                    }
                })
            } else paramsUpdateRequest({})
        }, { debounce: 500, maxWait: 5000, deep: true })

        const paramsUpdateRequest = async (body: Record<string, string | null> = {}) => {
            if (abortController) {
                abortController.abort();
            }
            let newBody = clone(body);
            // На поиск отправляем только явно выбранные пользователем параметры.
            // Авто-подставленные значения сервер пересчитает сам, поэтому они
            // «адаптируются» при изменении выбора и не залипают как старый выбор.
            if (newBody && Object.keys(newBody).length) {
                newBody = Object.fromEntries(
                    Object.entries(newBody).filter(([key]) => manuallyChanged.value[key])
                )
            }
            if (freeConfigMode.value && Object.keys(newBody).length) {
                return
            }
            abortController = new AbortController();
            const signal = abortController.signal;
            if (newBody && Object.keys(newBody).length) {
                Object.keys(newBody)?.forEach((key, index) => {
                    newBody[key] = replaceSpotOrComma(newBody[key]!, 'comma');
                    if (priorityParam.value)
                        newBody.priority = priorityParam.value;
                })
            }
            try {
                paramsLoading.value = true;
                const data = await Api.post(`/module_search/process_table_data?product_id=${props.id}`, newBody, {}, signal)
                if (data?.files) {
                    configuratorStore.setDocs(data.files)
                }
                const errors: string[] = [];
                let answeredCounter = 0;
                let questionCounter = 0;
                if (!data || !('parameters' in data) || !data.parameters.length) return
                data.parameters.forEach((e: IFormattedData) => {
                    if (e.name == 'Маркировка' && e.response_value) {
                        configuratorStore.setMark(e.response_value)
                    }
                    if ('error' in e && e.error) {
                        errors.push(e.error)
                    }
                    if ('response_value' in e && e.response_value && userInputs.value[e.name] !== e.response_value) {
                        userInputs.value[e.name] = e.response_value
                        answeredCounter++
                    }
                    questionCounter++
                })
                // Параметры, которые сервер пометил как ошибочные, стали несовместимыми
                // с текущим выбором. Убираем их из списка явных выборов, чтобы их старое
                // значение не продолжало отправляться и не блокировало подбор — тогда
                // остальные параметры смогут автоматически «подстроиться» под новый выбор.
                let removedError = false;
                data.parameters.forEach((e: IFormattedData) => {
                    if ('error' in e && e.error) {
                        if (e.name in userInputs.value) {
                            delete userInputs.value[e.name]
                            removedError = true
                        }
                        delete manuallyChanged.value[e.name]
                    }
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

                // Были удалены ошибочные (несовместимые) параметры — пересчитываем
                // подбор без них, чтобы сервер автоматически подставил единственные
                // доступные значения и зависимые параметры адаптировались.
                if (removedError && !rerunGuard) {
                    rerunGuard = true
                    await paramsUpdateRequest(userInputs.value)
                }
            } finally {
                rerunGuard = false
                paramsLoading.value = false
            }
        }

        onMounted(async () => {
            tkpVariants.value = await getTkpVariants(props.id);
            const data = await Api.get(`/blocks/by_product/${props.id}`);
            if (data) {
                paramsGroups.value = data;
            }
            paramsUpdateRequest();
        })

        onUnmounted(() => {
            configuratorStore.$reset();
            useNeuroOlData().$reset();
        })

        watch(neuroOlData, () => {
            if (neuroOlData.value) {
                userInputs.value = neuroOlData.value
                paramsUpdate(neuroOlDataStore.getOlInfo)
            }
        })

        const handleValueChanged = (value: string, key: keyof typeof userInputs.value) => {
            // Сброс значения (resetValue): убираем параметр из явных выборов и
            // перезапрашиваем подбор без него, чтобы зависимые параметры пересчитались.
            if (value == null) {
                delete userInputs.value[key];
                delete manuallyChanged.value[key];
                paramsUpdateRequest(userInputs.value);
                return;
            }
            if (value && userInputs.value[key] !== replaceSpotOrComma(value, 'spot')) {
                userInputs.value[key] = replaceSpotOrComma(value, 'spot') || '';
                // Помечаем как явный выбор пользователя — такой параметр не будет
                // перезаписан авто-подстановкой и останется в приоритете.
                manuallyChanged.value[String(key)] = true;
                priorityParam.value = String(key);
                paramsUpdate(userInputs.value);
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
            console.log(file.get('file'))
            promptModalVisible.value = true;
            olFormData.value = file;
            newFileName.value = fileName;
            promptModalKey.value++;
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
            paramsLoading,
            paramsGroups,
            userInputs,
            promptModalKey,
            handleValueChanged,
            handleDownloadTkp,
            handleFileUpload,
            setFreeConfig,
        }
    }
});
</script>
