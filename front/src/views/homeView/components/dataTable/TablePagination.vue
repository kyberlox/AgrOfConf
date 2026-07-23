<template>
<div class="flex flex-row items-center justify-between pb-[15px]">
    <div class="mt-[24px] pl-[24px] flex flex-row gap-[12px] items-center text-[12px]">
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
    <div class="pr-[24px] flex flex-row gap-[8px] items-center text-[14px]">
        <div class="w-[24px] h-[24px] cursor-pointer flex items-center justify-center content-center">
            <DawLeft />
        </div>
        <div v-for="item in 3"
             :key='"dsadsa"'
             class="w-[36px] h-[36px] m-auto text-center content-center cursor-pointer rounded-[8px] hover:bg-(--color-information-orange-50) transition"
             :class="{ 'bg-(--color-information-orange-50)': activePage == item }">
            {{ item }}
        </div>
        <div class="w-[24px] h-[24px] cursor-pointer flex items-center justify-center content-center">
            <DawRight />
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent, ref } from 'vue';
import DawLeft from '@/assets/icons/DawLeft.svg?component';
import DawRight from '@/assets/icons/DawRight.svg?component';
import DawDown from '@/assets/icons/DawDown.svg?component';

export default defineComponent({
    components: { DawLeft, DawRight, DawDown },
    props: {},
    setup() {
        const activePage = ref<string | number>(1);

        return {
            activePage
        }
    }
});
</script>