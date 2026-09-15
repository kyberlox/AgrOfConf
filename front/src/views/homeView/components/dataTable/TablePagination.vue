<template>
<div class="flex flex-row items-center justify-between pb-[15px]">
    <div class="mt-[24px] pl-[24px] flex flex-row gap-[12px] items-center text-[12px]"
         v-if="canPageSplit">
        <div>Строк на странице</div>
        <div
             class="border border-(--color-information-gray-200) rounded-[8px] px-[12px] py-[7px] flex flex-row justify-between items-center gap-[13px]">
            <div>1</div>
            <DawDown />
        </div>
        <div>
            1-10 из 200
        </div>
    </div>
    <div class="pr-[24px] flex flex-row gap-[8px] items-center text-[14px] ml-auto">
        <div class="w-[24px] h-[24px] cursor-pointer flex items-center justify-center content-center"
             @click="navigateTo(Number(activePage) - 1)">
            <DawLeft />
        </div>
        <div v-for="(item, index) in pagination"
             :key='"pagination" + index'
             class="w-[36px] h-[36px] m-auto text-center content-center cursor-pointer rounded-[8px] hover:bg-(--color-information-orange-50) transition group"
             :class="{ 'bg-(--color-information-orange-50) ': Number(activePage) > total ? total == item : Number(activePage) < 1 ? item == 1 : Number(activePage) == item }">
            <div @click="navigateTo(item)">{{ item }}</div>
            <div v-if="item == '...'"
                 class="absolute shadow-[0_0_8px_0_rgba(180,188,200,0.5)] rounded-sm flex flex-col bottom-[10px] w-[50px] bg-white gap-[4px] py-[5px] invisible group-hover:visible"
                 @click.stop>
                <div v-for="i in total"
                     :key="'pgmodal' + i"
                     class="hover:bg-(--color-information-orange-50)"
                     @click="navigateTo(i)">
                    {{ i }}
                </div>
            </div>
        </div>

        <div class="w-[24px] h-[24px] cursor-pointer flex items-center justify-center content-center"
             @click="navigateTo(Number(activePage) + 1)">
            <DawRight />
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, ref, computed } from 'vue';
import DawLeft from '@/assets/icons/DawLeft.svg?component';
import DawRight from '@/assets/icons/DawRight.svg?component';
import DawDown from '@/assets/icons/DawDown.svg?component';

export default defineComponent({
    components: { DawLeft, DawRight, DawDown },
    props: {
        total: {
            type: Number,
            required: true
        },
        rowsPerPage: {
            type: Number,
            required: true
        },
        activePage: {
            type: String,
            default: 1
        }
    },
    emits: ['toPage'],
    setup(props, { emit }) {
        const pagination = ref(computed(() => initPagination()));

        const initPagination = () => {
            const pagination = []
            const numActivePage = Number(props.activePage)
            for (let i = 1; i <= props.total; i++) {
                if (numActivePage - 1 == i || numActivePage + 1 == i || numActivePage == i) {
                    pagination.push(i)
                }
            }
            if (!pagination.includes(props.total)) {
                pagination.push('...', props.total)
            } else {
                pagination.unshift(1, '...')
            }
            return pagination
        }

        const navigateTo = (item: number | string) => {
            console.log(item)
            if (item == '...') return
            const numItem = Number(item);
            const newPage = numItem > props.total ? props.total : numItem < 1 ? 1 : item
            emit('toPage', newPage)
        }

        return {
            pagination,
            canPageSplit: false,
            navigateTo
        }
    }
});
</script>