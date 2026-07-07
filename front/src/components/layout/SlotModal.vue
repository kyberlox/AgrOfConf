<template>
<div class="fixed inset-0 flex items-center justify-center bg-[#00000013] w-full"
     @click="$emit('closeModal')">
    <div class="relative w-fit max-w-[80vw] max-h-[80vw]">
        <div class="bg-white p-[12px] rounded-[8px] shadow-sm max-h-screen overflow-y-auto w-full"
             @click.stop>
            <slot></slot>
        </div>
        <div
             class="absolute w-[24px] h-[24px] rounded-[100%] -right-[40px] top-0 bg-white flex items-center justify-center cursor-pointer">
            <Cross @click.stop="$emit('closeModal')" />
        </div>
    </div>
</div>
</template>

<script lang="ts">
import Cross from '@/assets/icons/Cross.svg?component';
import { defineComponent } from 'vue';

export default defineComponent({
    components: {
        Cross
    },
    setup() {
        return {

        }
    }
})
</script>