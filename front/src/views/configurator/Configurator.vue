<template>
<div class="p-[32px] w-full bg-[#FDFDFD] max-w-full border border-gray-200 rounded-xl">
    <div class="flex flex-row gap-[24px] flex-wrap md:flex-wrap lg:flex-nowrap">
        <div class="flex flex-col gap-[24px] w-full">
            <div class="flex flex-row items-start justify-between lg:flex-wrap xl:flex-nowrap w-full gap-y-[20px] ">
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
                <UploadDocButton v-if="neuroOlData"
                                 :type="'inConfig'" />
                <div v-if="!neuroOlData"
                     class="flex flex-row gap-[11px] mt-[10px] items-center ml-auto">
                    <div class="font-normal">
                        Свободный режим
                    </div>
                    <div class=" rounded-[49px] px-[4px] w-[48px] h-[24px] flex flex-start items-center cursor-pointer transition-all duration-300"
                         :class="[freeConfigMode ? ' bg-[#F36E3C]' : ' bg-[#B4BCC8]']"
                         @click="freeConfigMode = !freeConfigMode">
                        <div class="bg-white rounded-[100px] w-[18px] h-[18px] transition-all duration-300"
                             :class="[freeConfigMode ? 'translate-x-[22px]' : '']"></div>
                    </div>
                </div>
            </div>
            <EngineParams :form="form"
                          :type="neuroOlData ? 'free' : 'auto'"
                          :key="paramsRenderKey"
                          @valueChanged="(value: string, key: string) => handleValueChanged(value, key)" />
            <div class="flex flex-row justify-end gap-[8px] flex-wrap">
                <BaseButton :propsClass="'button-secondary'">
                    <span class="block px-[40px] flex flex-row items-center gap-[4px]">
                        <FavoriteIcon />
                        Удалить из Избранных ОЛ
                    </span>
                </BaseButton>
                <BaseButton :propsClass="'button-primary'"
                            :disabled="true">
                    Создать ОЛ
                </BaseButton>
            </div>
        </div>
        <RightSidebar />
    </div>
    <!-- Модалка для description -->
    <SlotModal v-if="modalVisible"
               @closeModal="modalVisible = false">
        <h1>dsa</h1>
    </SlotModal>
</div>
</template>
<script lang='ts'>
import { defineComponent, onMounted, ref, computed } from 'vue';
import { BaseButton } from 'beans-ui-kit';
import Ellipse from '@/assets/icons/Ellipse.svg?component';
import ArrowLeft from '@/assets/icons/ArrowLeft.svg?component';
import EngineParams from './components/EngineParams.vue';
import Api from '@/utils/Api';
import type { IFormattedData, IForm } from '@/assets/interfaces/IForm';
import SlotModal from '@/components/layout/SlotModal.vue';
import { useNeuroOlData } from '@/stores/neuroOl';
import UploadDocButton from '@/views/homeView/components/UploadDocButton.vue';
import RightSidebar from '@/components/layout/RightSidebar.vue';
import { useConfiguratorStore } from '@/stores/configurator.ts';
import FavoriteIcon from '@/assets/icons/Favorite.svg?component';
import PromptModal from '../homeView/components/PromptModal.vue';

export default defineComponent({
    components: {
        BaseButton,
        Ellipse,
        ArrowLeft,
        FavoriteIcon,
        EngineParams,
        PromptModal,
        SlotModal,
        UploadDocButton,
        RightSidebar
    },
    props: {
        id: {
            type: String,
            required: true
        }
    },
    setup(props) {
        const form = ref<IFormattedData[]>([]);
        const userInputs = ref<{ [key: string]: string }>({});
        const modalVisible = ref(false);
        const freeConfigMode = ref(false);
        const paramsRenderKey = ref(0);
        const neuroOlDataStore = useNeuroOlData();
        const neuroOlData = computed(() => neuroOlDataStore.getOlInfo);
        const productName = ref('');

        const paramsUpdate = async (body: any | null) => {
            try {
                const data = await Api.post(`/module_search/process_table_data?product_id=${props.id}`, body)
                const errors: string[] = [];
                data.parameters.forEach((e: IFormattedData) => {
                    if ('error' in e && e.error) {
                        errors.push(e.error)
                    }
                })
                if (errors.length) {
                    useConfiguratorStore().setError(errors)
                }
                else useConfiguratorStore().setDefaultError()
                if (!(data && 'parameters' in data)) return
                form.value = data.parameters
                productName.value = data.product_name
            }
            catch (error) {
                console.error(error)
            }
        }

        onMounted(() => {
            paramsUpdate(null);
            if (neuroOlData.value) {
                paramsUpdate(neuroOlDataStore.getOlInfo)
            }
        })

        const handleValueChanged = (value: string, key: keyof typeof userInputs.value) => {
            userInputs.value[key] = value;
            paramsUpdate(userInputs.value)
        }

        return {
            form,
            modalVisible,
            freeConfigMode,
            paramsRenderKey,
            neuroOlData,
            productName,
            handleValueChanged,
        }
    }
});
</script>