<template>
<div class="flex flex-row flex-wrap py-[12px] px-[32px] justify-between items-center flex-wrap">
    <div class="py-[9px]"
         @click="$router.push({ name: 'homeview' })">
        <LogoIcon class="cursor-pointer" />
    </div>
    <!-- <div class="w-[64px] h-[64px] flex items-center justify-center">
        <div class="w-[40px] h-[40px] flex">
            <img src="./test.jpg"
                 class="rounded-[40px] w-full h-full object-cover cursor-pointer" />
        </div>
    </div> -->
</div>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';
import LogoIcon from '@/assets/img/logo.svg?component';

export default defineComponent({
    components: {
        LogoIcon
    },
    props: {},
    setup() {
        return {}
    }
});
</script>