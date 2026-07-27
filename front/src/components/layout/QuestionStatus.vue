<template>
<div class="min-w-[26px] ml-[4px] h-[26px] rounded-xl border border-(--color-information-gray-300) flex flex-col items-center justify-center content-center"
     :class="status == 'checked' ? `bg-(--color-information-green-900)` : status == 'canceled' ? `bg-(--color-information-red-400)` : ''">
    <Checked v-if="status == 'checked'" />
    <Canceled v-else-if="status == 'canceled'" />
    <Loader v-else-if="status == 'loading'" />
</div>
</template>
<script lang='ts'>
import { defineComponent, type PropType } from 'vue';
import Checked from '@/assets/icons/Checked.svg?component';
import Canceled from '@/assets/icons/Cross.svg?component';
import Loader from './Loader.vue';

export default defineComponent({
    components: {
        Checked,
        Canceled,
        Loader
    },
    props: {
        status: String as PropType<'checked' | 'canceled' | 'loading' | ''>
    },
    setup() {
        return {}
    }
});
</script>