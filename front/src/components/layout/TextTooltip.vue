<template>
<div
     class="absolute max-w-full top-[50px] z-10 whitespace-normal bg-white text-black font-semibold text-sm shadow-[0_0_8px_0] rgba(180, 188, 200, 0.5) px-[16px] py-[8px] rounded-[5px]">
    {{ params?.value }}
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';

export default defineComponent({
    components: {},
    props: {
        params: { type: Object as PropType<{ value: string }> }
    }
});
</script>