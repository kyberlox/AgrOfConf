<template>
<div class="absolute w-fit max-w-full top-[50px] z-10 whitespace-normal  text-black font-semibold text-sm shadow-[0_0_8px_0] rgba(180, 188, 200, 0.5) px-[16px] py-[8px] rounded-[5px]"
     :class="type == 'error' ? 'border border-red-600! bg-[#ffe1e1]! font-normal' : 'bg-white'">

    {{ params?.value }}
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';

export default defineComponent({
    components: {},
    props: {
        params: { type: Object as PropType<{ value: string }> },
        type: {
            type: String,
            default: 'text'
        }
    }
});
</script>