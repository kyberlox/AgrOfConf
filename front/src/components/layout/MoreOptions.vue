<template>
<div class="absolute bg-white p-[12px] shadow-[0px_0px_8px_0px_#B4BCC8] rounded-[8px] right-0">
    <div class="flex flex-col">
        <div v-for="(variant, index) in list"
             :key="'var' + index"
             class="px-[12px] py-[10px] rounded-[8px] hover:bg-[#FFF2E5]"
             @click.stop.prevent="handleVariantClick(variant)">
            {{ variant }}
        </div>
    </div>
</div>
</template>
<script lang='ts'>
import { defineComponent } from 'vue';

export default defineComponent({
    components: {},
    props: {
        list: {
            type: Array<string>,
        }
    },
    setup(_, { emit }) {
        const handleVariantClick = (variant: string) => {
            emit('valueClicked', variant)
        }
        return {
            handleVariantClick
        }
    }
});
</script>