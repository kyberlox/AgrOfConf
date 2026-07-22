<template>
<div class="flex flex-col gap-[16px] lg:max-w-[344px] md:max-w-fit">
    <UploadDocButton @readyToUploadFile="(file, fileName) => handleFileUpload(file, fileName)" />
    <!-- Блок параметров запроса -->
    <div v-if="featuresFlags.rightSidebar.description"
         class="sidebar-block">
        <div class="text-[13px]">Параметры запроса</div>
        <div class="divider mt-[10px]!"></div>
        <div class="flex flex-col">
            <div class="mt-[10px] text-[13px] flex flex-row justify-start"
                 v-for="(item, index) in reqParameters"
                 :key='index'>
                <div class="text-(--text-secondary) text-left w-[50%]">{{ item.name }}</div>
                <div class="text-(--text-primary) text-left">{{ item.value }}</div>
            </div>
        </div>
    </div>
    <!-- Блок маркировки -->
    <div v-if="featuresFlags.rightSidebar.mark"
         class="sidebar-block">
        <div class="text-[16px] text-(--text-secondary)">
            Маркировка
        </div>
        <div
             class="mt-[4px] py-[8px] px-[16px] bg-[#F6F7F9] rounded-[8px] font-medium text-[20px] text-(--text-primary)">
            {{ status.mark }}
        </div>
        <div class="mt-[10px] flex flex-row justify-between text-[11px]">
            <span>
                {{
                    Math.round(status.answeredQuestions / status.allQuestions * 100)
                }}%</span>
            <span :class="status.status == 'Выполним' ? 'text-[#2E7D32]' : 'text-[#B71C1C`]'">
                {{ status.status }}
            </span>
        </div>

        <div class="divider relative border-2! border-[#EAECE]!">
            <div class="divider border-2! absolute border-[#8E99A8]! -top-[2px] -left-[2px]"
                 :style="{ width: `calc(${status.result}% + 4px)` }"></div>
        </div>
        <div class="font-[400] text-[14px] text-(--color-information-gray-400) mt-[8px]">
            Заполнено: {{ status.answeredQuestions }} из {{ status.allQuestions }} параметров
        </div>
    </div>
    <!-- Блок расчетных параметров -->
    <div v-if="featuresFlags.rightSidebar.calcParams && calcParams.length"
         class="sidebar-block p-[24px] max-w-[505px]">
        <div class="text-[13px]">Расчетные параметры</div>
        <div class="divider mt-[10px]!"></div>
        <div class="flex max-w-full w-full flex-nowrap gap-[10px] overflow-x-auto">
            <div v-for="(group, index) in formatCalcParams(calcParams)"
                 :key="index"
                 class="text-center w-full text-(--color-information-gray-400) min-w-[74px] cursor-pointer duration-300 transition-all hover:text-(--color-information-gray-800) py-[10px] text-[14px]"
                 :class="{ 'text-(--color-information-gray-800)': activeGroupBlock == index }"
                 @click="activeGroupBlock = index">
                <span>{{ 'Группа ' + index }}</span>
                <div :class="{ 'invisible': activeGroupBlock !== index }"
                     class="mt-[8px] rounded-t-[4px] border border-b border-(--color-information-orange-500) border-[3px]">
                </div>
            </div>
        </div>
        <div class="mt-[15px] text-[13px] flex flex-row justify-between"
             v-for="(item, index) in formatCalcParams(calcParams)[activeGroupBlock]"
             :key='index'>
            <div class="text-(--text-secondary) text-left w-[50%]">{{ item.name }}</div>
            <div class="text-(--text-primary) text-left">{{ item.response_value }}</div>
        </div>
    </div>
    <!-- Блок подсказки и ошибка -->
    <div class="sidebar-block p-[24px] bg-[#FFF2E5] border-[#FFCBA5]! text-[#B8461F]"
         :class="[{ 'border-red-600! text-gray-800 bg-[#ff00000f]': errorStatus == 'error' }]">
        <div class=" text-[#963314] font-[600]">
            {{ errorStatus == 'error' ? 'Ошибка!' : 'Подсказка' }}
        </div>
        <ul class="mt-[10px] ">
            <li v-for="(i, index) in error"
                :key="'error' + index">
                {{ i }}
            </li>
        </ul>
    </div>
    <!-- Блок с картинокй -->
    <div v-if="featuresFlags.rightSidebar.img && images.length"
         class="sidebar-block p-[24px] max-w-[505px]">
        <div class="flex max-w-full w-full flex-nowrap gap-[10px] overflow-x-auto">
            <div v-for="(image, index) in images"
                 :key="index"
                 class="text-center w-full text-(--color-information-gray-400) min-w-[74px] cursor-pointer duration-300 transition-all hover:text-(--color-information-gray-800)"
                 :class="{ 'text-(--color-information-gray-800)': activeImgBlock == index }"
                 @click="activeImgBlock = index">
                <span>{{ image.title }}</span>
                <div :class="{ 'invisible': activeImgBlock !== index }"
                     class="mt-[8px] rounded-t-[4px] border border-b border-(--color-information-orange-500) border-[3px]">
                </div>
            </div>
        </div>
        <div class="mt-[16px] bg-gray-100 bg-contain bg-no-repeat bg-center w-[294px] h-[120px]"
             :style="{ 'background-image': `url(${images[activeImgBlock]?.img})` }">
        </div>
    </div>
    <!-- Блок с документами -->
    <div v-if="featuresFlags.rightSidebar.docs"
         class="sidebar-block p-[24px]">
        <div class="text-13 text-[#343B4C] font-semibold">
            Прилагаемые документы
        </div>
        <div class="mt-[8px] flex flex-col border-b border-b-(--color-information-gray-100) py-[12px]">
            <div class=" flex flex-row items-center flex-nowrap">
                <span class="mr-[10px]">
                    <FileIcon />
                </span>
                <span class="truncate mr-[12px] font-normal!">Декларация о соответствии ТР ТС 010/2011</span>
                <div class="p-[4px] bg-(--color-information-gray-50)">
                    <DownloadIcon />
                </div>
            </div>
        </div>
        <BaseButton class="mt-[24px] flex flex-row items-center"
                    propsClass="button-secondary">
            <DownloadIcon class="w-[24px] h-[24px]" />
            <span>Скачать все</span>
        </BaseButton>
    </div>
</div>
</template>
<script lang='ts'>
import { BaseButton } from 'beans-ui-kit';
import { defineComponent, ref, computed, watch } from 'vue';
import DownloadIcon from '@/assets/icons/DownloadIcon.svg?component';
import FileIcon from '@/assets/icons/FileIcon.svg?component';
import { useConfiguratorStore } from '@/stores/configurator';
import { featuresFlags } from '@/assets/static/featuresFlags.ts';
import UploadDocButton from '@/views/homeView/components/recognition/UploadDocButton.vue';
import type { IFormattedData } from '@/assets/interfaces/IForm';

export default defineComponent({
    components: {
        BaseButton,
        DownloadIcon,
        FileIcon,
        UploadDocButton
    },
    props: {},
    setup(_, { emit }) {
        const activeImgBlock = ref<number>(0);
        const activeGroupBlock = ref<number>(0);
        const configuratorStore = useConfiguratorStore();
        const calcParams = computed(() => configuratorStore.getCalcParams);

        const handleFileUpload = (file: FormData, fileName: string) => {
            emit('readyToUploadFile', file, fileName);
        }

        const formatCalcParams = (calcParams: IFormattedData[]) => {
            const splitNum = 5;
            const formattedParams = [[]] as IFormattedData[][];
            let iteration = 0;
            for (let index = 0; index < calcParams.length; index += splitNum) {
                formattedParams[iteration] = calcParams.slice(index, index + splitNum)
                ++iteration;
                if (calcParams.slice(index, index + splitNum).length < splitNum) break;
            }
            return formattedParams;
        }

        return {
            reqParameters: [
                { name: 'Запрос №', value: 'K-7984561' },
                { name: 'Заказчик', value: 'АО «Газстройпром»' },
                { name: 'ПО', value: 'Энерджи Системс' },
                { name: 'Шифр ОЛ', value: 'BAB-15488-TX' },
            ],
            activeImgBlock,
            calcParams,
            featuresFlags,
            activeGroupBlock,
            error: computed(() => configuratorStore.getError),
            errorStatus: computed(() => configuratorStore.getErrorStatus),
            status: computed(() => configuratorStore.getStatus),
            images: computed(() => configuratorStore.getImages),
            handleFileUpload,
            formatCalcParams
        }
    }
});
</script>