<template>
<div class="grow"
     :class="{ 'border-r border-[#EAECEF] pr-[32px]': type == 'ol' }">
    <div class="flex flex-row gap-[16px] items-center max-w-[560px]">
        <div class="min-w-fit text-[16px] font-[700] leading-[120%] text-(--text-text-primary)">
            {{ pageTitle }}
        </div>
        <div class="divider"></div>
    </div>
    <div class="mt-[16px] grid grid-cols-2 gap-[16px] max-w-[560px]">
        <div v-for="(block, index) in statBlocks"
             :key="'olBlock' + index"
             class=" h-[160px] rounded-[16px] p-[24px] border border-(--color-information-gray-200)"
             :class="{ 'border-(--color-information-orange-200) bg-[linear-gradient(140deg,#fff_0%,#fff2e5_100%)]': index == 0 }">
            <div class="flex flex-row items-center justify-between">
                <div class="font-bold text-[14px] text-(--color-information-gray-400)"
                     :class="{ 'text-(--color-information-orange-800)': index == 0 }">
                    {{ `${type == 'ol' ? 'ОЛ' : 'Запросы'}` }} {{ block.title }}
                </div>
                <div class="w-[30px] h-[30px] rounded-[8px] bg-(--color-information-gray-50) flex items-center justify-center"
                     :class="{ 'bg-(--color-information-orange-100)': index == 0 }">
                    <Component :is="block.icon" />
                </div>
            </div>
            <div class="mt-[4px]">
                <span class="block font-black! text-[36px] text-(--text-primary)  tracking-[-0.04em] leading-[100%]">
                    {{ block.value }}
                </span>
            </div>
            <div class="mt-[16px] rounded-[12px] px-[12px] py-[6px] flex flex-row items-center justify-start gap-[8px] w-fit bg-(--color-information-gray-50) text-[12px] font-medium"
                 :class="{
                    'bg-(--color-information-green-50)': block.comparsion && block.comparsion > 0,
                    'bg-(--color-information-red-50)': block.comparsion && block.comparsion < 0
                }">
                <span v-if="block.comparsion && block.comparsion !== 0">
                    <Component :is="block.comparsion > 0 ? GraphToTop : GraphToDown"
                               class="w-[12px] h-[12px]" />
                </span>
                <span>
                    {{
                        'comparsion' in block && block.comparsion || block.comparsion == 0 ?
                            `${Number(block.comparsion) > 0 ? '+' : ''}${block.comparsion} ${xlWidth ? '' : block.undertext}` :
                            'с начала работы'
                    }}
                </span>
            </div>
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, computed } from 'vue';
import GraphToTop from '@/assets/icons/GraphToTop.svg?component';
import GraphToDown from '@/assets/icons/GraphToDown.svg?component';
import type { IStatisticBlock } from '@/assets/interfaces/IStatistic.ts';
import { screenMixins } from '@/assets/static/screenMixins';
import { useWindowSize } from '@vueuse/core';

export default defineComponent({
    components: {
        GraphToTop,
        GraphToDown,
    },
    props: {
        statBlocks: {
            type: Array<IStatisticBlock>,
            required: true
        },
        type: {
            type: String,
            default: 'ol'
        }
    },
    setup(props) {
        const { width } = useWindowSize()

        return {
            GraphToTop,
            GraphToDown,
            pageTitle: computed(() => props.type == 'ol' ? 'Опросные листы(ОЛ)' : 'Запросы'),
            xlWidth: computed(() => width.value < screenMixins.xxl),
        }
    }
});
</script>