<template>
<div class="min-w-[26px] ml-[4px] h-[26px] rounded-xl border border-(--color-information-gray-300) flex flex-col items-center justify-center content-center "
     :class="status == 'checked' ? `bg-green-300` : status == 'canceled' ? `bg-(--color-information-red-400)` : ''"
     @mouseenter="isHover = true"
     @mouseleave="isHover = false">
    <Transition name="fade"
                mode="out-in">
        <div class="peer">
            <Checked v-if="status == 'checked'" />
            <Canceled v-else-if="status == 'canceled'" />
            <Loader v-else-if="status == 'loading'" />
        </div>
    </Transition>
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType, ref } from 'vue';
import Checked from '@/assets/icons/Checked.svg?component';
import Canceled from '@/assets/icons/Cross.svg?component';
import Loader from './Loader.vue';

export default defineComponent({
    components: {
        Checked,
        Canceled,
        Loader,
    },
    emits: ['resetValue'],
    props: {
        status: String as PropType<'checked' | 'canceled' | 'loading' | ''>,
    },
    setup() {
        const isHover = ref(false);

        return {
            isHover
        }
    }
});
</script>