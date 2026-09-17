<template>
<div
     class="flex flex-row items-start justify-between gap-[20px] max-w-full content-stretch flex-wrap md:flex-wrap lg:flex-wrap xxl:flex-nowrap">
    <div class="flex flex-row gap-[16px] items-center w-full max-w-fit">
        <RouterLink :to="{ name: 'homeview' }"
                    class="w-[24px] h-[24px] rounded-[16px] bg-[#F6F7F9] cursor-pointer flex self-start mt-[7px]">
            <ArrowLeft class="w-full m-auto max-h-[12px]" />
        </RouterLink>
        <h1 class="inline-block w-fit max-w-[500px]">
            {{ productName }}
        </h1>
    </div>
    <div class="flex flex-col-reverse justify-center">
        <div v-if="!Object.keys(neuroOlData).length"
             class="flex flex-row gap-[11px] mt-[10px] items-center">
            <div class="font-normal w-fit">
                Свободный режим
            </div>
            <div class="rounded-[49px] px-[4px] w-[48px] h-[24px] flex flex-start items-center cursor-pointer transition-all duration-300"
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
                     :fileIsLoading="docIsLoading"
                     @readyToUploadFile="(file: FormData, fileName: string) => $emit('uploadFile', file, fileName)" />
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';
import UploadDocButton from '@/views/configurator/components/recognition/UploadDocButton.vue';
import { useConfiguratorStore } from '@/stores/configurator';
import Ellipse from '@/assets/icons/Ellipse.svg?component';
import ArrowLeft from '@/assets/icons/ArrowLeft.svg?component';

export default defineComponent({
    components: {
        UploadDocButton,
        Ellipse,
        ArrowLeft,
    },
    props: {
        productName: {
            type: String
        },
        neuroOlData: {
            type: Object as PropType<Record<string, string>>,
            default: {}
        },
        docIsLoading: {
            type: Boolean,
            default: false
        },
        freeConfigMode: {
            type: Boolean,
            default: false
        }
    },
    emits: ['uploadFile'],
    setup() {
        const setFreeConfig = (mode: boolean) => {
            useConfiguratorStore().setFreeModeConfig(mode)
        }
        return {
            setFreeConfig
        }
    }
});
</script>