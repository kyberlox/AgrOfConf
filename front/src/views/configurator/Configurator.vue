<template>
<div class="p-[32px] w-full bg-[#FDFDFD] max-w-full border border-gray-200 rounded-xl">
    <div class="flex flex-row gap-[24px]">
        <div class="flex flex-col gap-[24px] w-full">
            <div class="flex flex-row justify-between w-full flex-wrap">
                <div class="flex flex-row gap-[16px] items-center sm:flex-wrap flex-nowrap">
                    <RouterLink :to="{ name: 'homeview' }"
                                class="w-[24px] h-[24px] rounded-[16px] bg-[#F6F7F9] cursor-pointer flex ">
                        <ArrowLeft class="w-full  m-auto max-h-[12px]" />
                    </RouterLink>
                    <h1>Конфигуратор ЭПН</h1>
                    <div
                         class="rounded-[16px] flex flex-row items-center gap-[4px] bg-[#FFF2E5] pl-[8px] py-[4px] min-w-[104px] font-[500] text-[#752209]">
                        <Ellipse />
                        <span>Черновик</span>
                    </div>
                </div>
                <div class="flex flex-row gap-[11px] items-center ml-auto">
                    <div class="font-[400]">
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
                          :key="paramsRenderKey"
                          @valueChanged="(value: string, key: string) => handleValueChanged(value, key)" />
            <div class="flex flex-row justify-end gap-[8px]">
                <BaseButton :propsClass="'button-secondary'">
                    Удалить из Избранных ОЛ
                </BaseButton>
                <BaseButton :propsClass="'button-primary'"
                            :disabled="true">
                    Создать ОЛ
                </BaseButton>
            </div>
        </div>
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
import { neuroOlData } from '@/stores/neuroOl';

export default defineComponent({
    components: {
        BaseButton,
        Ellipse,
        ArrowLeft,
        EngineParams,
        SlotModal
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
        const neuroOlDataStore = neuroOlData();
        const neuroOlData = computed(() => neuroOlDataStore.getOlInfo);
        const paramsUpdate = (body: any | null) => {
            Api.post(`/module_search/process_table_data?product_id=${props.id}`, body)
                .then((data) => {
                    if (data && 'parameters' in data)
                        form.value = data.parameters
                })
        }

        onMounted(() => {
            paramsUpdate(null);
            if (neuroOlData.value) {
                paramsUpdate(neuroOlDataStore.getOlInfo)
            }
        })

        // const formatData = (data: IFormattedData[]) => {
        //     const formattedData: IFormattedData[] = [];
        //     const dataKeys = Object.keys(data)
        //     dataKeys.forEach(key => {
        //         formattedData.push({ name: key, values: data[key] as string[] })
        //     });
        //     return formattedData;
        // }

        const handleValueChanged = (value: string, key: string) => {
            if (value)
                console.log(value, '|', key);
            userInputs.value[key as keyof typeof userInputs.value] = value;
            paramsUpdate(userInputs.value)
        }

        return {
            form,
            modalVisible,
            freeConfigMode,
            paramsRenderKey,
            handleValueChanged,
        }
    }
});
</script>